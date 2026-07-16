from __future__ import annotations

import errno
import hashlib
import json
import os
from pathlib import Path
import pty
import select
import stat
import subprocess
import time

import pytest


ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy" / "gas-city"
BOOTSTRAP = DEPLOY / "bin" / "provider-auth-bootstrap"
IMAGE_ID = "sha256:" + "a" * 64
PROXY_IMAGE_ID = "sha256:" + "b" * 64
SECRET_SENTINEL = "TOP_SECRET_SUBSCRIPTION_TOKEN"


def _owner_dir(path: Path) -> Path:
    path.mkdir(mode=0o700)
    path.chmod(0o700)
    return path


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(0o700)


def _bootstrap_fixture(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    city = _owner_dir(tmp_path / "city")
    runtime = _owner_dir(city / "runtime")
    state = _owner_dir(runtime / "state")
    city_bin = _owner_dir(city / "bin")
    fake_bin = _owner_dir(tmp_path / "fake-bin")
    lock = city / "runtime-lock.json"
    lock.write_text("{}\n")
    lock.chmod(0o600)

    locked_log = tmp_path / "locked.log"
    docker_log = tmp_path / "docker.log"
    _write_executable(
        city_bin / "locked-images",
        """#!/usr/bin/env python3
import json, os, pathlib, sys
with pathlib.Path(os.environ["FAKE_LOCKED_LOG"]).open("a") as stream:
    stream.write(json.dumps(sys.argv[1:]) + "\\n")
if os.environ.get("FAKE_LOCK_FAIL") == "1":
    print("LEAK_FROM_LOCKED_VERIFIER", file=sys.stderr)
    raise SystemExit(19)
print(os.environ["FAKE_PROXY_IMAGE_ID"] if sys.argv[-1] == "egress_proxy" else os.environ["FAKE_IMAGE_ID"])
""",
    )
    _write_executable(
        fake_bin / "docker",
        """#!/usr/bin/env python3
import json, os, pathlib, sys
args = sys.argv[1:]
log = pathlib.Path(os.environ["FAKE_DOCKER_LOG"])
with log.open("a") as stream:
    stream.write(json.dumps(args) + "\\n")
if args[:2] == ["image", "inspect"]:
    print(args[-1])
elif args[:2] == ["network", "inspect"]:
    template = args[args.index("--format") + 1]
    network = args[-1]
    if "Internal" in template:
        print("true" if network == "gas-city-hq-control" else "false")
    else:
        print("private-hq-control" if network == "gas-city-hq-control" else "filtered-hq-egress")
elif args and args[0] == "inspect":
    print(json.dumps([{
        "State": {"Running": True},
        "Image": os.environ["FAKE_PROXY_IMAGE_ID"],
        "NetworkSettings": {"Networks": {
            "gas-city-hq-control": {},
            "gas-city-hq-egress": {},
        }},
    }]))
elif args and args[0] == "run":
    mount = args[args.index("--mount") + 1]
    source = mount.split("src=", 1)[1].split(",dst=", 1)[0]
    home = pathlib.Path(source)
    if "codex" in args[args.index("--") + 1:]:
        artifact = home / ".codex" / "auth.json"
    else:
        artifact = home / ".claude" / ".credentials.json"
    artifact.parent.mkdir(mode=0o700)
    artifact.parent.chmod(0o700)
    artifact.write_text(os.environ.get("FAKE_CREDENTIAL_RAW", os.environ["FAKE_CREDENTIAL_JSON"]))
    artifact.chmod(0o600)
    unrelated = home / "provider-login-cache.txt"
    unrelated.write_text("must not become persistent provider-auth state\\n")
    unrelated.chmod(0o600)
else:
    raise SystemExit(23)
""",
    )

    environment = os.environ.copy()
    environment.update(
        {
            "GC_CITY_ROOT": str(city),
            "GAS_CITY_STATE_DIR": str(state),
            "PATH": f"{fake_bin}:{environment['PATH']}",
            "FAKE_LOCKED_LOG": str(locked_log),
            "FAKE_DOCKER_LOG": str(docker_log),
            "FAKE_IMAGE_ID": IMAGE_ID,
            "FAKE_PROXY_IMAGE_ID": PROXY_IMAGE_ID,
            "FAKE_CREDENTIAL_JSON": json.dumps(
                {"access_token": SECRET_SENTINEL}, sort_keys=True
            )
            + "\n",
        }
    )
    return city, environment


def _run_attended(
    arguments: list[str], environment: dict[str, str], timeout: float = 10
) -> tuple[int, str]:
    master, slave = pty.openpty()
    process = subprocess.Popen(
        [str(BOOTSTRAP), *arguments],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        env=environment,
        close_fds=True,
    )
    os.close(slave)
    output = bytearray()
    deadline = time.monotonic() + timeout
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                process.kill()
                raise AssertionError("provider-auth-bootstrap test timed out")
            ready, _, _ = select.select([master], [], [], min(remaining, 0.1))
            if ready:
                try:
                    chunk = os.read(master, 65536)
                except OSError as exc:
                    if exc.errno == errno.EIO:
                        break
                    raise
                if not chunk:
                    break
                output.extend(chunk)
            if process.poll() is not None and not ready:
                try:
                    while True:
                        output.extend(os.read(master, 65536))
                except OSError as exc:
                    if exc.errno != errno.EIO:
                        raise
                break
        return process.wait(timeout=1), output.decode("utf-8", errors="replace")
    finally:
        os.close(master)
        if process.poll() is None:
            process.kill()
            process.wait()


def _docker_calls(environment: dict[str, str]) -> list[list[str]]:
    path = Path(environment["FAKE_DOCKER_LOG"])
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


def _assert_no_disposable_home(city: Path, provider: str) -> None:
    provider_root = city / "runtime" / "state" / "provider-bootstrap" / provider
    assert {path.name for path in provider_root.iterdir()} == {".bootstrap.lock"}
    lock = provider_root / ".bootstrap.lock"
    assert stat.S_IMODE(lock.stat().st_mode) == 0o600
    assert not lock.is_symlink()


@pytest.mark.parametrize(
    ("provider", "seed_name", "image_key", "login_tail"),
    [
        (
            "claude",
            "credentials.json",
            "claude_worker",
            ["--", "claude", "auth", "login", "--claudeai"],
        ),
        (
            "codex",
            "auth.json",
            "codex_worker",
            ["--", "codex", "login", "--device-auth"],
        ),
    ],
)
def test_bootstrap_uses_locked_image_and_copies_only_expected_secret(
    tmp_path: Path,
    provider: str,
    seed_name: str,
    image_key: str,
    login_tail: list[str],
) -> None:
    city, environment = _bootstrap_fixture(tmp_path)

    returncode, output = _run_attended([provider], environment)

    assert returncode == 0, output
    seed = city / "runtime" / "state" / "provider-auth" / provider / seed_name
    assert json.loads(seed.read_text()) == {"access_token": SECRET_SENTINEL}
    assert stat.S_IMODE(seed.stat().st_mode) == 0o600
    assert set(seed.parent.iterdir()) == {seed}
    for directory in (seed.parent, seed.parent.parent):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
        assert not directory.is_symlink()
    _assert_no_disposable_home(city, provider)
    assert SECRET_SENTINEL not in output

    locked_arguments = [
        json.loads(line)
        for line in Path(environment["FAKE_LOCKED_LOG"]).read_text().splitlines()
    ]
    assert locked_arguments == [
        [str(city / "runtime-lock.json"), image_key],
        [str(city / "runtime-lock.json"), "egress_proxy"],
    ]
    run = next(call for call in _docker_calls(environment) if call[0] == "run")
    assert run[-len(login_tail) :] == login_tail
    assert [run[index + 1] for index, value in enumerate(run) if value == "--mount"] == [
        next(value for value in run if value.startswith("type=bind,src="))
    ]
    [mount] = [value for value in run if value.startswith("type=bind,src=")]
    assert mount.endswith(",dst=/home/worker")
    assert "provider-bootstrap" in mount
    assert "provider-auth" not in mount
    assert SECRET_SENTINEL not in json.dumps(run)
    assert run[run.index("--pull") + 1] == "never"
    assert run[run.index("--network") + 1] == "gas-city-hq-control"
    assert run[run.index("--entrypoint") + 1] == "/usr/bin/tini"
    assert IMAGE_ID in run


def test_bootstrap_refuses_non_tty_and_unknown_provider(tmp_path: Path) -> None:
    city, environment = _bootstrap_fixture(tmp_path)
    noninteractive = subprocess.run(
        [str(BOOTSTRAP), "claude"],
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert noninteractive.returncode != 0
    assert "attended TTY" in noninteractive.stderr
    assert not (city / "runtime" / "state" / "provider-auth").exists()

    unknown = subprocess.run(
        [str(BOOTSTRAP), "gemini"],
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert unknown.returncode == 2
    assert "invalid choice" in unknown.stderr


def test_existing_seed_requires_compare_and_swap_rotation(tmp_path: Path) -> None:
    city, environment = _bootstrap_fixture(tmp_path)
    provider_root = _owner_dir(
        _owner_dir(city / "runtime" / "state" / "provider-auth") / "codex"
    )
    target = provider_root / "auth.json"
    old_content = b'{"access_token":"OLD_SECRET"}\n'
    target.write_bytes(old_content)
    target.chmod(0o600)

    refused, output = _run_attended(["codex"], environment)
    assert refused != 0
    assert "compare-and-swap rotation" in output
    assert target.read_bytes() == old_content
    assert _docker_calls(environment) == []

    wrong, output = _run_attended(
        ["codex", "--rotate", "--expected-current-sha256", "0" * 64],
        environment,
    )
    assert wrong != 0
    assert "expected rotation digest" in output
    assert target.read_bytes() == old_content
    assert _docker_calls(environment) == []


def test_rotation_is_atomic_digest_guarded_and_secret_silent(tmp_path: Path) -> None:
    city, environment = _bootstrap_fixture(tmp_path)
    provider_root = _owner_dir(
        _owner_dir(city / "runtime" / "state" / "provider-auth") / "claude"
    )
    target = provider_root / "credentials.json"
    old_content = b'{"access_token":"OLD_SECRET"}\n'
    target.write_bytes(old_content)
    target.chmod(0o600)
    old_inode = target.stat().st_ino
    expected = hashlib.sha256(old_content).hexdigest()

    returncode, output = _run_attended(
        ["claude", "--rotate", "--expected-current-sha256", expected],
        environment,
    )

    assert returncode == 0, output
    assert json.loads(target.read_text()) == {"access_token": SECRET_SENTINEL}
    assert target.stat().st_ino != old_inode
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert "OLD_SECRET" not in output
    assert SECRET_SENTINEL not in output
    assert not list(provider_root.glob(".*.tmp"))


def test_symlink_seed_and_malformed_generated_secret_are_rejected(
    tmp_path: Path,
) -> None:
    city, environment = _bootstrap_fixture(tmp_path)
    provider_root = _owner_dir(
        _owner_dir(city / "runtime" / "state" / "provider-auth") / "claude"
    )
    outside = tmp_path / "outside.json"
    outside.write_text('{"access_token":"OUTSIDE"}\n')
    outside.chmod(0o600)
    target = provider_root / "credentials.json"
    target.symlink_to(outside)

    refused, output = _run_attended(["claude"], environment)
    assert refused != 0
    assert "non-symlink" in output
    assert json.loads(outside.read_text()) == {"access_token": "OUTSIDE"}
    assert _docker_calls(environment) == []

    target.unlink()
    environment["FAKE_CREDENTIAL_RAW"] = "{MALFORMED_SECRET"
    malformed, output = _run_attended(["claude"], environment)
    assert malformed != 0
    assert "valid UTF-8 JSON" in output
    assert "MALFORMED_SECRET" not in output
    assert not target.exists()
    _assert_no_disposable_home(city, "claude")


def test_locked_verifier_failure_is_sanitized_and_stops_before_docker(
    tmp_path: Path,
) -> None:
    _, environment = _bootstrap_fixture(tmp_path)
    environment["FAKE_LOCK_FAIL"] = "1"

    returncode, output = _run_attended(["codex"], environment)

    assert returncode != 0
    assert "locked image verification failed" in output
    assert "LEAK_FROM_LOCKED_VERIFIER" not in output
    assert _docker_calls(environment) == []


def test_non_finite_generated_json_is_rejected(tmp_path: Path) -> None:
    city, environment = _bootstrap_fixture(tmp_path)
    environment["FAKE_CREDENTIAL_RAW"] = '{"access_token":NaN}\n'

    returncode, output = _run_attended(["codex"], environment)

    assert returncode != 0
    assert "non-finite JSON number" in output
    assert not (
        city / "runtime" / "state" / "provider-auth" / "codex" / "auth.json"
    ).exists()
    _assert_no_disposable_home(city, "codex")


def test_stale_disposable_home_is_not_reused_or_silently_deleted(
    tmp_path: Path,
) -> None:
    city, environment = _bootstrap_fixture(tmp_path)
    bootstrap_parent = _owner_dir(city / "runtime" / "state" / "provider-bootstrap")
    provider_root = _owner_dir(bootstrap_parent / "codex")
    stale = _owner_dir(provider_root / "codex-stale-session")
    stale_secret = stale / "auth.json"
    stale_secret.write_text('{"access_token":"STALE_SECRET"}\n')
    stale_secret.chmod(0o600)

    returncode, output = _run_attended(["codex"], environment)

    assert returncode != 0
    assert "stale disposable provider home" in output
    assert stale_secret.exists()
    assert "STALE_SECRET" not in output
    assert _docker_calls(environment) == []


def test_bootstrap_contract_has_no_host_home_mount_or_secret_print() -> None:
    source = BOOTSTRAP.read_text()
    assert "locked-images" in source
    assert '"--pull",\n        "never"' in source
    assert "type=bind,src={home},dst=/home/worker" in source
    assert "src=/home/loucmane" not in source
    assert "src=$HOME" not in source
    assert "read_text" not in source
    assert "print(content" not in source
    assert "--with-api-key" not in source
    assert "--with-access-token" not in source
    assert '("claude", "auth", "login", "--claudeai")' in source
    assert '("codex", "login", "--device-auth")' in source
