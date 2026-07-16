from __future__ import annotations

import fcntl
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import time
import types

import pytest


ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy" / "gas-city"
LAUNCHER = DEPLOY / "bin" / "provider-container"
BOOTSTRAP = DEPLOY / "bin" / "provider-auth-bootstrap"
SUPERVISOR = DEPLOY / "docker" / "provider-supervisor.py"


def _bootstrap_module():
    loader = importlib.machinery.SourceFileLoader(
        "provider_auth_reseed_test", str(BOOTSTRAP)
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _supervisor_module():
    spec = importlib.util.spec_from_file_location(
        "provider_home_supervisor_test", SUPERVISOR
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _private_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)
    return path


def _private_json(path: Path, value: dict[str, str]) -> Path:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)
    return path


def _fixture(tmp_path: Path) -> tuple[Path, Path, dict[str, str]]:
    city = _private_directory(tmp_path / "gas-city")
    runtime = _private_directory(city / "runtime")
    state = _private_directory(runtime / "state")
    secrets = _private_directory(runtime / "secrets")
    gc = _private_directory(city / ".gc")
    for name in ("runtime", "cache", "scripts", "system", "agents"):
        _private_directory(gc / name)
    workdir = _private_directory(gc / "agents" / "mayor" / "work")
    rig_root = _private_directory(tmp_path / "aegis")
    _private_directory(rig_root / ".beads")
    hq_beads = _private_directory(city / ".beads")
    shutil.copyfile(DEPLOY / "config/city.toml", city / "city.toml")
    shutil.copyfile(DEPLOY / "config/city.worker.toml", city / "city.worker.toml")
    for name in ("pack.toml", "packs.lock", "runtime-lock.json"):
        (city / name).write_text("{}\n" if name.endswith(".json") else "# fixture\n")
    (hq_beads / "config.yaml").write_text(
        "issue_prefix: gc\n"
        "dolt.auto-start: false\n"
        "gc.endpoint_origin: managed_city\n"
        "gc.endpoint_status: verified\n",
        encoding="utf-8",
    )
    (hq_beads / "config.yaml").chmod(0o600)
    site = gc / "site.toml"
    site.write_text(
        f'workspace_name = "gas-city"\n[[rig]]\nname = "aegis"\npath = "{rig_root}"\n',
        encoding="utf-8",
    )
    site.chmod(0o600)
    (gc / "settings.json").write_text("{}\n", encoding="utf-8")
    provider_config = _private_directory(city / "provider-config")
    (provider_config / "codex.toml").write_text('model = "gpt-5.6-sol"\n', encoding="utf-8")
    (provider_config / "claude-settings.json").write_text("{}\n", encoding="utf-8")
    (secrets / "hq-app-password").write_text("A" * 32, encoding="utf-8")
    (secrets / "hq-app-password").chmod(0o600)

    auth_root = _private_directory(state / "provider-auth")
    codex_auth = _private_directory(auth_root / "codex")
    claude_auth = _private_directory(auth_root / "claude")
    _private_json(codex_auth / "auth.json", {"access_token": "codex-seed"})
    _private_json(claude_auth / "credentials.json", {"access_token": "claude-seed"})
    bootstrap_root = _private_directory(state / "provider-bootstrap")
    for provider in ("codex", "claude"):
        provider_root = _private_directory(bootstrap_root / provider)
        lock = provider_root / ".bootstrap.lock"
        lock.touch(mode=0o600)
        lock.chmod(0o600)

    bin_dir = _private_directory(city / "bin")
    locked = bin_dir / "locked-images"
    locked.write_text(
        "#!/usr/bin/env bash\nprintf 'sha256:%064d\\n' 1\n",
        encoding="utf-8",
    )
    locked.chmod(0o700)
    shutil.copyfile(DEPLOY / "bin/prepare-worker-boundary", bin_dir / "prepare-worker-boundary")
    (bin_dir / "prepare-worker-boundary").chmod(0o700)
    shutil.copyfile(DEPLOY / "bin/git-worktree-broker", bin_dir / "git-worktree-broker")
    (bin_dir / "git-worktree-broker").chmod(0o700)
    fake_bin = _private_directory(tmp_path / "fake-bin")
    docker = fake_bin / "docker"
    docker.write_text(
        """#!/usr/bin/env python3
import json, os, pathlib, signal, sys, time
args = sys.argv[1:]
log = pathlib.Path(os.environ['FAKE_DOCKER_LOG'])
with log.open('a', encoding='utf-8') as stream:
    stream.write(json.dumps(args) + '\\n')
if args[:2] == ['image', 'inspect']:
    raise SystemExit(0)
if args[:2] == ['network', 'inspect']:
    template = args[args.index('-f') + 1]
    print('true' if '.Internal' in template else 'private-hq-control')
    raise SystemExit(0)
if not args or args[0] != 'run':
    raise SystemExit(70)
mounts = [args[index + 1] for index, value in enumerate(args) if value == '--mount']
parsed = {}
for mount in mounts:
    fields = dict(item.split('=', 1) for item in mount.split(',') if '=' in item)
    parsed[fields['dst']] = (pathlib.Path(fields['src']), mount)
provider = args[-1]
stable_home = parsed['/run/gas-city/provider-home'][0]
credential = stable_home / ('auth.json' if provider == 'codex' else 'credentials.json')
observed = json.loads(credential.read_text(encoding='utf-8'))
if os.environ.get('FAKE_OBSERVED_AUTH'):
    pathlib.Path(os.environ['FAKE_OBSERVED_AUTH']).write_text(json.dumps(observed), encoding='utf-8')
refresh = os.environ.get('FAKE_REFRESH_TOKEN')
if refresh:
    temporary = credential.with_name('.credential-refresh.tmp')
    temporary.write_text(json.dumps({'access_token': refresh}) + '\\n', encoding='utf-8')
    temporary.chmod(0o600)
    temporary.replace(credential)
    receipt_root = parsed['/run/gas-city'][0]
    (receipt_root / 'provider-auth-sync.json').write_text(
        json.dumps({'schema_version': 1, 'status': 'synced', 'provider': provider}) + '\\n',
        encoding='utf-8',
    )
session_root = parsed['/run/gas-city/provider-session'][0]
overlay = session_root / ('log' if provider == 'codex' else 'debug')
prior = sorted(path.name for path in overlay.iterdir())
with (log.parent / f'{os.environ["GC_SESSION_ID"]}-prior.json').open('w') as stream:
    json.dump(prior, stream)
(overlay / 'runtime.log').write_text(os.environ['GC_SESSION_ID'], encoding='utf-8')
ephemeral = pathlib.Path(os.environ['FAKE_EPHEMERAL_ROOT']) / os.environ['GC_SESSION_ID']
ephemeral.mkdir(parents=True)
for relative in (
    '.bash_history', '.cache/provider-cache', '.npm/runtime',
    '.codex/history.jsonl', '.codex/models_cache.json', '.codex/state.sqlite',
    '.codex/plugins/plugin.json', '.claude/history.jsonl',
    '.claude/session-env/state', '.claude/file-history/entry', '.claude/cache/item',
):
    target = ephemeral / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(os.environ['GC_SESSION_ID'], encoding='utf-8')
ready = os.environ.get('FAKE_WORKER_READY')
if ready:
    pathlib.Path(ready).write_text('ready', encoding='utf-8')
release = os.environ.get('FAKE_WORKER_RELEASE')
while release and not pathlib.Path(release).exists():
    time.sleep(0.02)
if os.environ.get('FAKE_CRASH_AFTER_RELEASE'):
    os.kill(os.getpid(), signal.SIGKILL)
raise SystemExit(int(os.environ.get('FAKE_DOCKER_EXIT', '0')))
""",
        encoding="utf-8",
    )
    docker.chmod(0o700)
    environment = {
        **os.environ,
        "PATH": f"{fake_bin}:/usr/bin:/bin",
        "GC_CITY_ROOT": str(city),
        "GC_AGENT": "mayor",
        "FAKE_DOCKER_LOG": str(tmp_path / "docker.jsonl"),
        "FAKE_EPHEMERAL_ROOT": str(tmp_path / "ephemeral-container-homes"),
    }
    for name in ("GC_RIG", "GC_RIG_ROOT", "GC_BEADS_PREFIX", "GC_BEAD_ID"):
        environment.pop(name, None)
    return city, workdir, environment


def _run(
    provider: str,
    workdir: Path,
    environment: dict[str, str],
    session: str,
    **extra: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(LAUNCHER), provider],
        cwd=workdir,
        env={**environment, "GC_SESSION_ID": session, **extra},
        text=True,
        capture_output=True,
        check=False,
    )


def _mounts(environment: dict[str, str]) -> list[str]:
    calls = [
        json.loads(line)
        for line in Path(environment["FAKE_DOCKER_LOG"]).read_text(encoding="utf-8").splitlines()
    ]
    run = [call for call in calls if call and call[0] == "run"][-1]
    return [run[index + 1] for index, value in enumerate(run) if value == "--mount"]


def test_refresh_persists_across_fresh_sessions_with_overlay_only_session_state(
    tmp_path: Path,
) -> None:
    city, workdir, environment = _fixture(tmp_path)
    observed = tmp_path / "observed.json"

    first = _run(
        "codex",
        workdir,
        environment,
        "session-one",
        FAKE_REFRESH_TOKEN="refreshed-codex",
    )
    second = _run(
        "codex",
        workdir,
        environment,
        "session-two",
        FAKE_OBSERVED_AUTH=str(observed),
    )

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    home = city / "runtime/state/provider-homes/hq/mayor/codex"
    assert json.loads((home / "auth.json").read_text()) == {
        "access_token": "refreshed-codex"
    }
    assert {path.name for path in home.iterdir()} == {
        "auth.json",
        ".seed-generation.json",
    }
    assert json.loads(observed.read_text()) == {"access_token": "refreshed-codex"}
    sessions = city / "runtime/state/provider-sessions/hq/mayor/codex"
    session_roots = list(sessions.iterdir())
    assert len(session_roots) == 2
    assert all({path.name for path in root.iterdir()} == {"sessions", "log", "shell_snapshots"} for root in session_roots)
    assert not any(path.name in {"auth.json", ".credentials.json", "credentials.json"} for path in sessions.rglob("*"))
    assert not any(
        path.name in {
            ".bash_history", ".cache", ".npm", "history.jsonl", "models_cache.json",
            "state.sqlite", "plugins", "session-env", "file-history", "cache",
        }
        for path in (city / "runtime/state").rglob("*")
    )
    assert json.loads((tmp_path / "session-two-prior.json").read_text()) == []
    mounts = _mounts(environment)
    assert any(
        "dst=/run/gas-city/provider-home" in mount
        and "provider-homes/hq/mayor/codex" in mount
        for mount in mounts
    )
    assert any("dst=/run/gas-city/provider-config,readonly" in mount for mount in mounts)
    assert not any("dst=/home/worker" in mount for mount in mounts)
    docker_calls = Path(environment["FAKE_DOCKER_LOG"]).read_text(encoding="utf-8")
    assert "/home/worker:rw,nosuid,nodev,size=2048m" in docker_calls


def test_claude_and_codex_homes_are_isolated_and_unexpected_artifacts_fail_closed(
    tmp_path: Path,
) -> None:
    city, workdir, environment = _fixture(tmp_path)
    assert _run("codex", workdir, environment, "codex-one").returncode == 0
    assert _run("claude", workdir, environment, "claude-one").returncode == 0

    codex_home = city / "runtime/state/provider-homes/hq/mayor/codex"
    claude_home = city / "runtime/state/provider-homes/hq/mayor/claude"
    assert {path.name for path in codex_home.iterdir()} == {
        "auth.json", ".seed-generation.json"
    }
    assert {path.name for path in claude_home.iterdir()} == {
        "credentials.json", ".seed-generation.json"
    }
    assert not (codex_home / ".claude").exists()
    assert not (claude_home / ".codex").exists()

    (codex_home / "unexpected.txt").write_text("unsafe\n", encoding="utf-8")
    rejected = _run("codex", workdir, environment, "codex-two")
    assert rejected.returncode == 66
    assert "unexpected or missing artifacts" in rejected.stderr


def test_rotated_seed_refuses_old_home_until_explicit_cas_reseed(
    tmp_path: Path,
) -> None:
    city, workdir, environment = _fixture(tmp_path)
    first = _run(
        "codex",
        workdir,
        environment,
        "before-rotation",
        FAKE_REFRESH_TOKEN="locally-refreshed",
    )
    assert first.returncode == 0, first.stderr
    seed = city / "runtime/state/provider-auth/codex/auth.json"
    home_auth = city / "runtime/state/provider-homes/hq/mayor/codex/auth.json"
    _private_json(seed, {"access_token": "rotated-seed"})
    refused = _run("codex", workdir, environment, "after-rotation")
    assert refused.returncode == 66
    assert "attended CAS reseed is required" in refused.stderr
    assert json.loads(home_auth.read_text()) == {"access_token": "locally-refreshed"}

    module = _bootstrap_module()
    arguments = module.parse_args(
        [
            "codex",
            "--reseed-home",
            "--scope",
            "hq",
            "--agent",
            "mayor",
            "--expected-seed-sha256",
            hashlib.sha256(seed.read_bytes()).hexdigest(),
            "--expected-home-sha256",
            hashlib.sha256(home_auth.read_bytes()).hexdigest(),
        ]
    )
    old_environment = os.environ.copy()
    os.environ.update({"GC_CITY_ROOT": str(city)})
    try:
        module.reseed_stable_home(arguments)
    finally:
        os.environ.clear()
        os.environ.update(old_environment)

    assert json.loads(home_auth.read_text()) == {"access_token": "rotated-seed"}
    restored = _run("codex", workdir, environment, "after-reseed")
    assert restored.returncode == 0, restored.stderr


def test_stale_reseed_cas_and_missing_lease_fail_without_overwrite(tmp_path: Path) -> None:
    city, workdir, environment = _fixture(tmp_path)
    assert _run("codex", workdir, environment, "initial").returncode == 0
    module = _bootstrap_module()
    seed = city / "runtime/state/provider-auth/codex/auth.json"
    home_auth = city / "runtime/state/provider-homes/hq/mayor/codex/auth.json"
    original = home_auth.read_bytes()
    arguments = module.parse_args(
        [
            "codex",
            "--reseed-home",
            "--scope",
            "hq",
            "--agent",
            "mayor",
            "--expected-seed-sha256",
            "0" * 64,
            "--expected-home-sha256",
            hashlib.sha256(original).hexdigest(),
        ]
    )
    monkey_environment = os.environ.copy()
    os.environ.update({"GC_CITY_ROOT": str(city)})
    try:
        with pytest.raises(module.BootstrapError, match="seed does not match"):
            module.reseed_stable_home(arguments)
        assert home_auth.read_bytes() == original
        (city / "runtime/state/provider-bootstrap/codex/.bootstrap.lock").unlink()
        valid = module.parse_args(
            [
                "codex",
                "--reseed-home",
                "--scope",
                "hq",
                "--agent",
                "mayor",
                "--expected-seed-sha256",
                hashlib.sha256(seed.read_bytes()).hexdigest(),
                "--expected-home-sha256",
                hashlib.sha256(original).hexdigest(),
            ]
        )
        with pytest.raises(module.BootstrapError, match="missing artifacts"):
            module.reseed_stable_home(valid)
    finally:
        os.environ.clear()
        os.environ.update(monkey_environment)


def test_worker_lease_blocks_rotation_and_crash_releases_lease_with_refresh(
    tmp_path: Path,
) -> None:
    city, workdir, environment = _fixture(tmp_path)
    ready = tmp_path / "ready"
    release = tmp_path / "release"
    process = subprocess.Popen(
        [str(LAUNCHER), "codex"],
        cwd=workdir,
        env={
            **environment,
            "GC_SESSION_ID": "crashing-worker",
            "FAKE_REFRESH_TOKEN": "refresh-before-crash",
            "FAKE_WORKER_READY": str(ready),
            "FAKE_WORKER_RELEASE": str(release),
            "FAKE_CRASH_AFTER_RELEASE": "1",
        },
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    deadline = time.monotonic() + 10
    while not ready.exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    assert ready.exists()
    sync_receipts = list(
        (city / "runtime/state/model-receipts/hq/mayor/codex").rglob(
            "provider-auth-sync.json"
        )
    )
    assert len(sync_receipts) == 1
    assert json.loads(sync_receipts[0].read_text())["status"] == "synced"
    lock = city / "runtime/state/provider-bootstrap/codex/.bootstrap.lock"
    with lock.open("r+") as stream:
        with pytest.raises(BlockingIOError):
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    home_lock = city / "runtime/state/provider-homes/hq/mayor/.codex.home.lock"
    with home_lock.open("r+") as stream:
        with pytest.raises(BlockingIOError):
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    release.write_text("release\n", encoding="utf-8")
    stdout, stderr = process.communicate(timeout=10)
    assert process.returncode != 0, stdout + stderr
    with lock.open("r+") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    with home_lock.open("r+") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    home_auth = city / "runtime/state/provider-homes/hq/mayor/codex/auth.json"
    assert json.loads(home_auth.read_text()) == {"access_token": "refresh-before-crash"}
    assert stat.S_IMODE(home_auth.stat().st_mode) == 0o600
    observed = tmp_path / "post-crash-auth.json"
    restarted = _run(
        "codex",
        workdir,
        environment,
        "post-crash-worker",
        FAKE_OBSERVED_AUTH=str(observed),
    )
    assert restarted.returncode == 0, restarted.stderr
    assert json.loads(observed.read_text()) == {"access_token": "refresh-before-crash"}


def _supervisor_layout(module, monkeypatch, tmp_path: Path):
    city = _private_directory(tmp_path / "supervised-city")
    hq_work = _private_directory(city / ".gc/agents/mayor/work")
    beads = _private_directory(city / ".beads")
    worker_home = _private_directory(tmp_path / "worker-home")
    durable = _private_directory(tmp_path / "durable-codex")
    session = _private_directory(tmp_path / "session-codex")
    for name in ("sessions", "log", "shell_snapshots"):
        _private_directory(session / name)
    credential = _private_json(durable / "auth.json", {"access_token": "initial"})
    marker = durable / ".seed-generation.json"
    marker.write_text(
        json.dumps(
            {
                "provider": "codex",
                "schema_version": 1,
                "seed_sha256": hashlib.sha256(credential.read_bytes()).hexdigest(),
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    marker.chmod(0o400)
    config = tmp_path / "codex.toml"
    shutil.copyfile(DEPLOY / "config/codex.toml", config)
    config.chmod(0o644)
    password = tmp_path / "beads-password"
    password.write_text("D" * 32, encoding="utf-8")
    password.chmod(0o600)
    sync_receipt = tmp_path / "provider-auth-sync.json"
    model_receipt = tmp_path / "model-receipt.json"

    monkeypatch.setattr(module, "WORKER_HOME_PATH", worker_home)
    monkeypatch.setattr(module, "PROVIDER_HOME_PATH", durable)
    monkeypatch.setattr(module, "PROVIDER_CONFIG_PATH", config)
    monkeypatch.setattr(module, "PROVIDER_SESSION_PATH", session)
    monkeypatch.setattr(module, "PROVIDER_SYNC_RECEIPT_PATH", sync_receipt)
    monkeypatch.setattr(module, "PASSWORD_SECRET_PATH", password)
    credentials_path = worker_home / ".config/beads/credentials"
    monkeypatch.setattr(module, "DOLT_CREDENTIALS_PATH", credentials_path)
    monkeypatch.setattr(module, "_exact_mount_type", lambda path: "tmpfs" if path == worker_home else None)
    monkeypatch.setattr(module, "validate_worker_boundary", lambda: "hq")
    identity = {
        "GC_CITY_ROOT": str(city),
        "GC_DOLT_HOST": "gas-city-hq-dolt",
        "GC_DOLT_PORT": "3306",
        "GC_DOLT_USER": "gas_city_hq",
        "GC_DOLT_DATABASE": "hq",
        "BEADS_DOLT_SERVER_HOST": "gas-city-hq-dolt",
        "BEADS_DOLT_SERVER_PORT": "3306",
        "BEADS_DOLT_SERVER_USER": "gas_city_hq",
        "BEADS_DOLT_SERVER_DATABASE": "hq",
        "BEADS_CREDENTIALS_FILE": str(credentials_path),
        "BEADS_DIR": str(beads),
        "GC_GITHUB_REQUIRED": "false",
    }
    monkeypatch.setattr(module, "HQ_RUNTIME_IDENTITY", identity)
    for name, value in identity.items():
        monkeypatch.setenv(name, value)
    for name in (
        "GC_RIG", "GC_RIG_ROOT", "GC_BEADS_PREFIX", "AEGIS_TASK_AUTHORITY_FILE",
        "AEGIS_TASK_AUTHORITY_RUNTIME_FILE", "AEGIS_TASK_AUTHORITY_RUNTIME_SHA256",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GC_EXPECTED_MODEL", "gpt-5.6-sol")
    monkeypatch.setenv("GC_EXPECTED_EFFORT", "xhigh")
    monkeypatch.setenv("GC_TRANSCRIPT_ROOT", str(worker_home / ".codex/sessions"))
    monkeypatch.setenv("GC_MODEL_RECEIPT_PATH", str(model_receipt))
    monkeypatch.setenv("GC_PROVIDER_HOME", str(durable))
    monkeypatch.setenv("GC_PROVIDER_CONFIG", str(config))
    monkeypatch.setenv("GC_PROVIDER_SESSION", str(session))
    monkeypatch.setenv("GC_PROVIDER_SYNC_RECEIPT_PATH", str(sync_receipt))
    monkeypatch.setenv("GC_MODEL_RECEIPT_TIMEOUT_SECONDS", "3")
    monkeypatch.setenv("CODEX_HOME", str(worker_home / ".codex"))
    monkeypatch.chdir(hq_work)
    return {
        "city": city,
        "work": hq_work,
        "worker_home": worker_home,
        "durable": durable,
        "session": session,
        "credential": credential,
        "marker": marker,
        "config": config,
        "password": password,
        "sync_receipt": sync_receipt,
        "model_receipt": model_receipt,
    }


def test_supervisor_seeds_tmpfs_and_syncs_atomic_refresh_without_home_leakage(
    tmp_path: Path, monkeypatch
) -> None:
    module = _supervisor_module()
    layout = _supervisor_layout(module, monkeypatch, tmp_path)
    fake_bin = _private_directory(tmp_path / "supervisor-bin")
    fake_codex = fake_bin / "codex"
    fake_codex.write_text(
        """#!/usr/bin/env python3
import json, os, pathlib, sys, time
home = pathlib.Path(os.environ['CODEX_HOME'])
observed = json.loads((home / 'auth.json').read_text(encoding='utf-8'))
pathlib.Path(os.environ['FAKE_OBSERVED_AUTH']).write_text(json.dumps(observed), encoding='utf-8')
pathlib.Path(os.environ['FAKE_ARGUMENTS']).write_text(json.dumps(sys.argv[1:]), encoding='utf-8')
for relative in (
    '../.bash_history', '../.cache/item', 'history.jsonl', 'models_cache.json',
    'state.sqlite', 'plugins/plugin.json',
):
    target = home / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('ephemeral', encoding='utf-8')
temporary = home / '.auth.refresh.tmp'
temporary.write_text(json.dumps({'access_token': os.environ['FAKE_REFRESH']}) + '\\n', encoding='utf-8')
temporary.chmod(0o600)
temporary.replace(home / 'auth.json')
root = pathlib.Path(os.environ['GC_TRANSCRIPT_ROOT'])
event = {'type': 'turn_context', 'payload': {'model': 'gpt-5.6-sol', 'effort': 'xhigh'}}
(root / 'turn.jsonl').write_text(json.dumps(event) + '\\n', encoding='utf-8')
time.sleep(0.5)
""",
        encoding="utf-8",
    )
    fake_codex.chmod(0o700)
    observed = tmp_path / "observed-first.json"
    arguments = tmp_path / "arguments.json"
    monkeypatch.setenv("PATH", f"{fake_bin}:{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_OBSERVED_AUTH", str(observed))
    monkeypatch.setenv("FAKE_ARGUMENTS", str(arguments))
    monkeypatch.setenv("FAKE_REFRESH", "supervisor-refreshed")

    result = module.main(["provider-supervisor", "codex"])

    assert result == 0
    assert json.loads(observed.read_text()) == {"access_token": "initial"}
    assert json.loads(layout["credential"].read_text()) == {
        "access_token": "supervisor-refreshed"
    }
    assert {path.name for path in layout["durable"].iterdir()} == {
        "auth.json", ".seed-generation.json"
    }
    assert json.loads(layout["sync_receipt"].read_text())["status"] == "synced"
    assert json.loads(layout["model_receipt"].read_text())["status"] == "verified"
    locked_arguments = json.loads(arguments.read_text())
    assert ["--model", "gpt-5.6-sol"] == locked_arguments[1:3]
    assert "danger-full-access" in locked_arguments
    assert "mcp_servers={}" in locked_arguments
    assert not any(
        path.name in {
            ".bash_history", ".cache", "history.jsonl", "models_cache.json",
            "state.sqlite", "plugins",
        }
        for path in layout["durable"].rglob("*")
    )

    # A new container receives only the refreshed credential. Its new session
    # overlay cannot observe the previous session's transcript or log state.
    shutil.rmtree(layout["worker_home"])
    _private_directory(layout["worker_home"])
    second_session = _private_directory(tmp_path / "session-codex-two")
    for name in ("sessions", "log", "shell_snapshots"):
        _private_directory(second_session / name)
    second_sync = tmp_path / "provider-auth-sync-two.json"
    monkeypatch.setattr(module, "PROVIDER_SESSION_PATH", second_session)
    monkeypatch.setattr(module, "PROVIDER_SYNC_RECEIPT_PATH", second_sync)
    monkeypatch.setenv("GC_PROVIDER_SESSION", str(second_session))
    monkeypatch.setenv("GC_PROVIDER_SYNC_RECEIPT_PATH", str(second_sync))
    monkeypatch.setenv("GC_TRANSCRIPT_ROOT", str(layout["worker_home"] / ".codex/sessions"))
    monkeypatch.setenv("CODEX_HOME", str(layout["worker_home"] / ".codex"))
    monkeypatch.setenv("GC_DOLT_USER", "gas_city_hq")
    monkeypatch.setenv("FAKE_REFRESH", "second-refresh")
    observed_second = tmp_path / "observed-second.json"
    monkeypatch.setenv("FAKE_OBSERVED_AUTH", str(observed_second))
    assert module.main(["provider-supervisor", "codex"]) == 0
    assert json.loads(observed_second.read_text()) == {
        "access_token": "supervisor-refreshed"
    }
    assert all(
        not any(second_session.joinpath(name).iterdir())
        for name in ("log", "shell_snapshots")
    )


def test_supervisor_rejects_transcript_truncation_after_model_event(
    tmp_path: Path, monkeypatch
) -> None:
    module = _supervisor_module()
    layout = _supervisor_layout(module, monkeypatch, tmp_path)
    fake_bin = _private_directory(tmp_path / "truncate-bin")
    fake_codex = fake_bin / "codex"
    fake_codex.write_text(
        """#!/usr/bin/env python3
import json, os, pathlib, time
root = pathlib.Path(os.environ['GC_TRANSCRIPT_ROOT'])
path = root / 'turn.jsonl'
event = {'type': 'turn_context', 'payload': {'model': 'gpt-5.6-sol', 'effort': 'xhigh'}}
path.write_text(json.dumps(event) + '\\n', encoding='utf-8')
time.sleep(0.6)
path.write_text('', encoding='utf-8')
time.sleep(0.6)
""",
        encoding="utf-8",
    )
    fake_codex.chmod(0o700)
    monkeypatch.setenv("PATH", f"{fake_bin}:{os.environ['PATH']}")

    assert module.main(["provider-supervisor", "codex"]) == 90
    receipt = json.loads(layout["model_receipt"].read_text(encoding="utf-8"))
    assert receipt["status"] == "rejected"
    assert receipt["reason"] == "transcript_truncated"


def test_supervisor_rejects_removal_of_observed_event_from_final_transcript(
    tmp_path: Path, monkeypatch
) -> None:
    module = _supervisor_module()
    layout = _supervisor_layout(module, monkeypatch, tmp_path)
    fake_bin = _private_directory(tmp_path / "rewrite-bin")
    fake_codex = fake_bin / "codex"
    fake_codex.write_text(
        """#!/usr/bin/env python3
import json, os, pathlib, time
root = pathlib.Path(os.environ['GC_TRANSCRIPT_ROOT'])
path = root / 'turn.jsonl'
event = {'type': 'turn_context', 'payload': {'model': 'gpt-5.6-sol', 'effort': 'xhigh'}}
original = json.dumps(event) + '\\n'
path.write_text(original, encoding='utf-8')
time.sleep(0.6)
replacement = original.replace('turn_context', 'turn_contexx')
assert len(replacement) == len(original)
path.write_text(replacement, encoding='utf-8')
time.sleep(0.3)
""",
        encoding="utf-8",
    )
    fake_codex.chmod(0o700)
    monkeypatch.setenv("PATH", f"{fake_bin}:{os.environ['PATH']}")

    assert module.main(["provider-supervisor", "codex"]) == 89
    receipt = json.loads(layout["model_receipt"].read_text(encoding="utf-8"))
    assert receipt["status"] == "rejected"
    assert receipt["reason"] == "verified_transcript_unavailable"
    assert "absent from final transcript" in receipt["error"]


@pytest.mark.parametrize(
    ("target_name", "tamper", "message"),
    [
        ("auth.json", "symlink", "non-symlink"),
        ("auth.json", "mode", "unsafe ownership"),
        ("auth.json", "hardlink", "unsafe ownership"),
        ("auth.json", "size", "unsafe ownership"),
        (".seed-generation.json", "symlink", "non-symlink"),
        (".seed-generation.json", "mode", "unsafe ownership"),
        (".seed-generation.json", "hardlink", "unsafe ownership"),
        (".seed-generation.json", "size", "unsafe ownership"),
    ],
)
def test_supervisor_rejects_unsafe_credential_and_marker_artifacts(
    tmp_path: Path,
    monkeypatch,
    target_name: str,
    tamper: str,
    message: str,
) -> None:
    module = _supervisor_module()
    layout = _supervisor_layout(module, monkeypatch, tmp_path)
    target = layout["durable"] / target_name
    if tamper == "symlink":
        external = tmp_path / f"external-{target_name.lstrip('.')}"
        external.write_bytes(target.read_bytes())
        external.chmod(stat.S_IMODE(target.stat().st_mode))
        target.unlink()
        target.symlink_to(external)
    elif tamper == "mode":
        target.chmod(0o644)
    elif tamper == "hardlink":
        os.link(target, tmp_path / f"hardlink-{target_name.lstrip('.')}")
    elif tamper == "size":
        target.chmod(0o600)
        target.write_bytes(b"{" + b"x" * (module.MAX_PROVIDER_CREDENTIAL_BYTES + 1))
        if target_name.startswith("."):
            target.chmod(0o400)
    sync = module.ProviderCredentialSync("codex", layout["sync_receipt"])
    with pytest.raises(RuntimeError, match=message):
        sync.initialize()


def test_secure_reader_rejects_owner_toctou_and_secret_artifact_tampering(
    tmp_path: Path, monkeypatch
) -> None:
    module = _supervisor_module()
    secret = tmp_path / "secret"
    secret.write_text("S" * 32, encoding="utf-8")
    secret.chmod(0o600)

    with pytest.raises(RuntimeError, match="unsafe ownership"):
        module._secure_read(
            secret,
            "owner-negative",
            maximum_bytes=64,
            allowed_modes={0o600},
            allowed_uids={os.geteuid() + 10000},
        )

    real_fstat = module.os.fstat
    calls = 0

    def drifting_fstat(descriptor: int):
        nonlocal calls
        calls += 1
        info = real_fstat(descriptor)
        if calls != 2:
            return info
        return types.SimpleNamespace(
            st_mode=info.st_mode,
            st_uid=info.st_uid,
            st_nlink=info.st_nlink,
            st_size=info.st_size,
            st_dev=info.st_dev,
            st_ino=info.st_ino,
            st_mtime_ns=info.st_mtime_ns + 1,
            st_ctime_ns=info.st_ctime_ns,
        )

    monkeypatch.setattr(module.os, "fstat", drifting_fstat)
    with pytest.raises(RuntimeError, match="changed while it was read"):
        module._secure_read(
            secret,
            "TOCTOU-negative",
            maximum_bytes=64,
            allowed_modes={0o600},
        )
    monkeypatch.setattr(module.os, "fstat", real_fstat)

    external = tmp_path / "external-secret"
    external.write_text("E" * 32, encoding="utf-8")
    external.chmod(0o600)
    secret.unlink()
    secret.symlink_to(external)
    with pytest.raises(RuntimeError, match="non-symlink"):
        module._secret_text(secret, "symlink secret", minimum=16, maximum=64)
    secret.unlink()
    secret.write_text("S" * 32, encoding="utf-8")
    secret.chmod(0o644)
    with pytest.raises(RuntimeError, match="unsafe ownership"):
        module._secret_text(secret, "mode secret", minimum=16, maximum=64)
    secret.chmod(0o600)
    os.link(secret, tmp_path / "secret-hardlink")
    with pytest.raises(RuntimeError, match="unsafe ownership"):
        module._secret_text(secret, "hardlink secret", minimum=16, maximum=64)
    (tmp_path / "secret-hardlink").unlink()
    secret.write_bytes(b"S" * (module.MAX_SECRET_BYTES + 1))
    with pytest.raises(RuntimeError, match="unsafe ownership"):
        module._secret_text(secret, "oversize secret", minimum=16, maximum=64)


def test_supervisor_detects_out_of_band_and_racing_durable_credential_changes(
    tmp_path: Path, monkeypatch
) -> None:
    module = _supervisor_module()
    layout = _supervisor_layout(module, monkeypatch, tmp_path)
    sync = module.ProviderCredentialSync("codex", layout["sync_receipt"])
    sync.initialize()

    # Even when the tmpfs credential is unchanged, a direct mutation of the
    # mounted durable directory is detected on the next poll.
    _private_json(layout["credential"], {"access_token": "out-of-band"})
    with pytest.raises(RuntimeError, match="outside the supervisor"):
        sync.sync()

    # Restore a clean instance, then race the final compare-and-swap recheck.
    shutil.rmtree(layout["worker_home"])
    _private_directory(layout["worker_home"])
    _private_json(layout["credential"], {"access_token": "initial"})
    clean = module.ProviderCredentialSync("codex", layout["sync_receipt"])
    clean.initialize()
    _private_json(clean.visible_path, {"access_token": "valid-refresh"})
    original_reader = module._provider_credential
    raced = False

    def racing_reader(path: Path, label: str):
        nonlocal raced
        if label == "compare-and-swap provider credential" and not raced:
            raced = True
            _private_json(layout["credential"], {"access_token": "racing-write"})
        return original_reader(path, label)

    monkeypatch.setattr(module, "_provider_credential", racing_reader)
    with pytest.raises(RuntimeError, match="changed during synchronization"):
        clean.sync()
    assert json.loads(layout["credential"].read_text()) == {
        "access_token": "racing-write"
    }


def test_claude_visible_credential_supports_in_place_refresh(
    tmp_path: Path, monkeypatch
) -> None:
    module = _supervisor_module()
    worker_home = _private_directory(tmp_path / "claude-worker-home")
    durable = _private_directory(tmp_path / "claude-durable")
    session = _private_directory(tmp_path / "claude-session")
    for name in ("projects", "debug", "todos"):
        _private_directory(session / name)
    credential = _private_json(
        durable / "credentials.json", {"access_token": "claude-initial"}
    )
    marker = durable / ".seed-generation.json"
    marker.write_text(
        json.dumps(
            {
                "provider": "claude",
                "schema_version": 1,
                "seed_sha256": hashlib.sha256(credential.read_bytes()).hexdigest(),
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    marker.chmod(0o400)
    monkeypatch.setattr(module, "WORKER_HOME_PATH", worker_home)
    monkeypatch.setattr(module, "PROVIDER_HOME_PATH", durable)
    monkeypatch.setattr(module, "PROVIDER_SESSION_PATH", session)
    sync = module.ProviderCredentialSync("claude", tmp_path / "claude-sync.json")
    sync.initialize()

    assert json.loads(sync.visible_path.read_text()) == {
        "access_token": "claude-initial"
    }
    assert sync.visible_path == worker_home / ".claude/.credentials.json"
    # A validated in-place rewrite is supported in addition to atomic rename.
    _private_json(sync.visible_path, {"access_token": "claude-refreshed"})
    assert sync.sync() is True
    assert json.loads(credential.read_text()) == {
        "access_token": "claude-refreshed"
    }


@pytest.mark.parametrize(
    ("provider", "arguments"),
    [
        ("codex", ["--model", "other"]),
        ("codex", ["-mother"]),
        ("codex", ["--config=model=\"other\""]),
        ("claude", ["--model=other"]),
        ("claude", ["--settings", "/tmp/other.json"]),
        ("claude", ["--bare"]),
        ("claude", ["--mcp-config=other.json"]),
    ],
)
def test_provider_argument_overrides_are_rejected(
    provider: str, arguments: list[str]
) -> None:
    module = _supervisor_module()
    with pytest.raises(RuntimeError, match="cannot override locked"):
        module._reject_provider_overrides(provider, arguments)


@pytest.mark.parametrize(
    ("provider", "arguments", "expected"),
    [
        (
            "codex",
            [
                "resume",
                "--full-auto",
                "--model",
                "gpt-5.6-sol",
                "-c",
                "model_reasoning_effort=xhigh",
                "session-1",
            ],
            ["resume", "session-1"],
        ),
        (
            "codex",
            [
                "--model=gpt-5.6-sol",
                "--sandbox",
                "danger-full-access",
                "--ask-for-approval=never",
                "prompt",
            ],
            ["prompt"],
        ),
        (
            "claude",
            [
                "--model",
                "claude-fable-5",
                "--effort",
                "max",
                "--permission-mode",
                "auto",
            ],
            ["--effort", "max", "--permission-mode", "auto"],
        ),
    ],
)
def test_exact_gas_city_locked_arguments_are_consumed_once(
    provider: str, arguments: list[str], expected: list[str]
) -> None:
    module = _supervisor_module()
    assert module._strip_locked_provider_arguments(provider, arguments) == expected


@pytest.mark.parametrize(
    ("provider", "arguments"),
    [
        ("codex", ["--model", "gpt-5.6"]),
        ("codex", ["-c", "model_reasoning_effort=high"]),
        ("codex", ["--sandbox", "workspace-write"]),
        ("codex", ["--ask-for-approval", "on-request"]),
        ("codex", ["--full-auto", "--full-auto"]),
        ("codex", ["--model", "gpt-5.6-sol", "-m", "gpt-5.6-sol"]),
        ("claude", ["--model", "claude-sonnet-5"]),
        (
            "claude",
            ["--model", "claude-fable-5", "--model=claude-fable-5"],
        ),
    ],
)
def test_gas_city_locked_argument_conflicts_and_duplicates_fail_closed(
    provider: str, arguments: list[str]
) -> None:
    module = _supervisor_module()
    with pytest.raises(RuntimeError, match="locked"):
        module._strip_locked_provider_arguments(provider, arguments)


def test_pinned_gas_city_resume_command_reaches_locked_codex_boundary(
    tmp_path: Path, monkeypatch
) -> None:
    """Exercise the actual v1.3.5 resolver output through the wrapper policy."""

    lock = json.loads((DEPLOY / "runtime-lock.json").read_text(encoding="utf-8"))
    gc = DEPLOY / "artifacts" / "gc"
    assert hashlib.sha256(gc.read_bytes()).hexdigest() == lock["tools"]["gc"][
        "binary_sha256"
    ]

    # The provider prefix is copied byte-for-byte from the production city file,
    # while imports and rig bindings are excluded so the resolver probe is fully
    # offline and cannot touch a real city.
    production = (DEPLOY / "config" / "city.toml").read_text(encoding="utf-8")
    provider_only, separator, _ = production.partition("\n[dolt]\n")
    assert separator
    city = _private_directory(tmp_path / "resolver-city")
    (city / "city.toml").write_text(provider_only + "\n", encoding="utf-8")
    home = _private_directory(tmp_path / "resolver-home")
    environment = dict(os.environ)
    environment.update(
        {
            "HOME": str(home),
            "XDG_CACHE_HOME": str(home / "cache"),
            "XDG_CONFIG_HOME": str(home / "config"),
            "XDG_STATE_HOME": str(home / "state"),
        }
    )
    resolved = subprocess.run(
        [
            str(gc),
            "--city",
            str(city),
            "config",
            "explain",
            "--provider",
            "codex-container",
            "--json",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        check=False,
    )
    assert resolved.returncode == 0, resolved.stderr
    payload = json.loads(resolved.stdout)
    command_text = payload["resolved"]["resume_command"]
    tokens = shlex.split(command_text)
    assert tokens[0] == "/home/loucmane/gas-city/bin/codex-container"
    assert "--full-auto" in tokens
    assert ["--model", "gpt-5.6-sol"] == tokens[tokens.index("--model") :][0:2]

    module = _supervisor_module()
    monkeypatch.setattr(module, "PROVIDER_CONFIG_PATH", DEPLOY / "config" / "codex.toml")
    final = module._provider_command("codex", tokens[1:])
    assert final.count("--model") == 1
    assert final.count("--sandbox") == 1
    assert final.count("--ask-for-approval") == 1
    assert "--full-auto" not in final
    assert final[-2:] == ["resume", "{{.SessionKey}}"]
