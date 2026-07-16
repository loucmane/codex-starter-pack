from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import stat
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "deploy" / "gas-city"


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bundle(
    tmp_path: Path,
    *,
    fake_tools: bool = False,
    site_aegis_root: Path | None = None,
) -> Path:
    bundle = tmp_path / "bundle"
    shutil.copytree(DEPLOY, bundle, symlinks=True)
    if site_aegis_root is not None:
        site = bundle / "config" / "site.example.toml"
        site.write_text(
            "# Isolated integration binding.\n"
            'workspace_name = "gas-city"\n\n'
            "[[rig]]\n"
            'name = "aegis"\n'
            f'path = "{site_aegis_root.as_posix()}"\n'
        )
        site.chmod(0o644)
    if fake_tools:
        gc = bundle / "artifacts" / "gc"
        for name in ("gc", "bd", "dolt"):
            (bundle / "artifacts" / name).chmod(0o755)
        gc.write_text(
            """#!/usr/bin/python3 -I
import json
import os
from pathlib import Path
import shutil
import sys
args = sys.argv[1:]
if args == ["version"]:
    print("1.3.5")
elif len(args) >= 4 and args[-3:] == ["supervisor", "status", "--json"]:
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    home = Path(os.environ["HOME"])
    print(json.dumps({
        "schema_version": "1", "ok": True, "running": False, "pid": 0,
        "socket_path": "", "checked_paths": [
            str(runtime / "gc" / "supervisor.sock"),
            str(home / ".gc" / "supervisor.sock"),
        ],
    }))
elif args[:2] == ["init", "--file"] and "--preserve-existing" in args and "--no-start" in args:
    if os.environ.get("GC_DOLT") != "skip" or "--skip-provider-readiness" not in args:
        print("inert init flags are missing", file=sys.stderr)
        raise SystemExit(5)
    tool_root = Path(__file__).resolve().parent
    for dependency in ("bd", "dolt"):
        resolved = shutil.which(dependency)
        if resolved is None or Path(resolved).resolve() != tool_root / dependency:
            print(f"verified sibling dependency missing from PATH: {dependency}", file=sys.stderr)
            raise SystemExit(3)
    template = Path(args[2])
    city = Path(args[-1])
    for launcher in ("claude-container", "codex-container"):
        if not (city / "bin" / launcher).is_file():
            print(f"provider launcher missing before gc init: {launcher}", file=sys.stderr)
            raise SystemExit(4)
    interrupt = os.environ.get("FAKE_GC_INTERRUPT_ONCE")
    if interrupt and not Path(interrupt).exists():
        (city / ".gc").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(template, city / "city.toml")
        (city / "pack.toml").write_text("[pack]\\nname='partial-scaffold'\\n")
        Path(interrupt).write_text("interrupted\\n")
        print("simulated gc init interruption", file=sys.stderr)
        raise SystemExit(99)
    (city / ".gc").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template, city / "city.toml")
    (city / "pack.toml").write_text("[pack]\\nname='init-scaffold'\\n")
    print("Initialized without starting")
elif args[:2] == ["init", "--skip-provider-readiness"] and "--no-start" in args:
    city = Path(args[-1])
    if os.environ.get("GC_DOLT") != "skip" or not (city / ".gc").is_dir():
        print("inert init recovery is incomplete", file=sys.stderr)
        raise SystemExit(6)
    print("Resumed without starting")
elif args[-3:] == ["config", "show", "--validate"]:
    pass
else:
    print(f"unexpected fake gc invocation: {args}", file=sys.stderr)
    raise SystemExit(2)
"""
        )
        (bundle / "artifacts" / "bd").write_text(
            "#!/bin/sh\n[ \"$1\" = version ] && echo 'bd version 1.1.0'\n"
        )
        (bundle / "artifacts" / "dolt").write_text(
            "#!/bin/sh\n[ \"$1\" = version ] && echo 'dolt version 2.2.0'\n"
        )
        for name in ("gc", "bd", "dolt"):
            (bundle / "artifacts" / name).chmod(0o555)
    layout = runpy.run_path((bundle / "bin" / "locked-images").as_posix())[
        "CONTROL_PLANE_LAYOUT"
    ]
    entries = []
    for source, destination, source_mode, destination_mode in layout:
        path = bundle / source
        path.chmod(source_mode)
        entries.append(
            {
                "source": source,
                "destination": destination,
                "sha256": _sha(path),
                "source_mode": f"{source_mode:04o}",
                "destination_mode": f"{destination_mode:04o}",
            }
        )
    assert [entry["source"] for entry in entries] == sorted(
        entry["source"] for entry in entries
    )
    manifest = {
        "schema_version": 1,
        "kind": "gas-city-control-plane",
        "entries": entries,
    }
    manifest_path = bundle / "control-plane-manifest.json"
    manifest_path.write_bytes(_json_bytes(manifest))
    manifest_path.chmod(0o644)

    lock_path = bundle / "runtime-lock.json"
    lock = json.loads(lock_path.read_text())
    for name in ("gc", "bd", "dolt"):
        lock["tools"][name]["binary_sha256"] = _sha(bundle / "artifacts" / name)
    lock["task_authority_runtime"]["sha256"] = _sha(
        bundle / lock["task_authority_runtime"]["source_path"]
    )
    startup = lock["aegis_polecat_startup"]
    startup["sha256"] = _sha(bundle / startup["source_path"])
    startup["formula_sha256"] = _sha(bundle / startup["formula_path"])
    startup["runtime_artifact_sha256"] = _sha(
        bundle / startup["runtime_artifact_source_path"]
    )
    startup["runtime_shim_sha256"] = _sha(
        bundle / startup["runtime_shim_source_path"]
    )
    lock["git_worktree_broker"]["sha256"] = _sha(
        bundle / lock["git_worktree_broker"]["source_path"]
    )
    lock["model_evidence_broker"]["sha256"] = _sha(
        bundle / lock["model_evidence_broker"]["source_path"]
    )
    lock["control_plane_manifest"] = {
        "path": "control-plane-manifest.json",
        "sha256": _sha(manifest_path),
    }
    lock_path.write_bytes(_json_bytes(lock))
    lock_path.chmod(0o644)
    return bundle


def _run(
    *arguments: Path | str,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(argument) for argument in arguments],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )


def _mark_images_promoted(city: Path) -> None:
    lock_path = city / "runtime-lock.json"
    lock = json.loads(lock_path.read_text())
    lock["status"] = "provisioned_pending_canary"
    for index, record in enumerate(lock["images"].values(), start=1):
        record["image_id"] = f"sha256:{index:064x}"
    lock_path.write_bytes(_json_bytes(lock))
    lock_path.chmod(0o600)


def test_prepare_stages_without_overwriting_existing_topology_and_is_idempotent(
    tmp_path: Path,
) -> None:
    bundle = _bundle(tmp_path)
    city = tmp_path / "city"
    city.mkdir(mode=0o700)
    (city / ".gc").mkdir(mode=0o700)
    prior_city = b'[workspace]\nname = "old-managed-city"\n'
    (city / "city.toml").write_bytes(prior_city)
    (city / "city.toml").chmod(0o600)
    transaction = tmp_path / "provision-transaction"
    command = (
        bundle / "bin" / "provision-control-plane",
        "prepare",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )

    first = _run(*command)
    assert first.returncode == 0, first.stderr
    result = json.loads(first.stdout)
    assert result["status"] == "staged"
    assert result["topology_action"] == "requires_hq_external_transition"
    assert (city / "city.toml").read_bytes() == prior_city
    assert stat.S_IMODE((city / "city.toml").stat().st_mode) == 0o600
    assert not (city / "pack.toml").exists()
    assert not (city / "packs.lock").exists()
    assert not (city / ".gc" / "site.toml").exists()
    assert (city / "bin" / "gas-city-admin").is_file()
    assert (city / "bin" / "gc").is_file()
    assert stat.S_IMODE((city / "runtime").stat().st_mode) == 0o700
    assert stat.S_IMODE((city / "runtime" / "authority").stat().st_mode) == 0o700
    assert stat.S_IMODE((city / "runtime-lock.json").stat().st_mode) == 0o600
    stage_receipt = transaction / "stage-receipt.json"
    assert stat.S_IMODE(stage_receipt.stat().st_mode) == 0o600

    verified = _run(
        city / "bin" / "locked-images",
        "--verify-staged",
        city / "runtime-lock.json",
        stage_receipt,
    )
    assert verified.returncode == 0, verified.stderr
    assert verified.stdout == "verified staged control plane\n"

    second = _run(*command)
    assert second.returncode == 0, second.stderr
    assert json.loads(second.stdout)["status"] == "already-staged"
    assert (city / "city.toml").read_bytes() == prior_city


def test_staged_verifier_rejects_topology_drift(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    city = tmp_path / "city"
    city.mkdir(mode=0o700)
    (city / ".gc").mkdir(mode=0o700)
    (city / "city.toml").write_text('[workspace]\nname = "managed"\n')
    (city / "city.toml").chmod(0o600)
    transaction = tmp_path / "provision-transaction"
    prepared = _run(
        bundle / "bin" / "provision-control-plane",
        "prepare",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )
    assert prepared.returncode == 0, prepared.stderr

    (city / "city.toml").write_text('[workspace]\nname = "changed"\n')
    (city / "city.toml").chmod(0o600)
    rejected = _run(
        city / "bin" / "locked-images",
        "--verify-staged",
        city / "runtime-lock.json",
        transaction / "stage-receipt.json",
    )
    assert rejected.returncode != 0
    assert "deferred destination changed before cutover: city.toml" in rejected.stderr


def test_empty_city_runs_exact_no_start_init_before_staging(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path, fake_tools=True)
    city = tmp_path / "new-city"
    transaction = tmp_path / "provision-transaction"
    prepared = _run(
        bundle / "bin" / "provision-control-plane",
        "prepare",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )
    assert prepared.returncode == 0, prepared.stderr
    result = json.loads(prepared.stdout)
    assert result == {
        "status": "staged",
        "stage_receipt": (transaction / "stage-receipt.json").as_posix(),
        "topology_action": "initialized_external",
        "next_required_action": "initialize-aegis-then-activate-topology",
    }
    init_receipt = json.loads((transaction / "gc-init.json").read_text())
    assert init_receipt["argv"] == [
        (bundle / "artifacts" / "gc").as_posix(),
        "init",
        "--file",
        (bundle / "config" / "city.toml").as_posix(),
        "--preserve-existing",
        "--skip-provider-readiness",
        "--no-start",
        city.as_posix(),
    ]
    assert init_receipt["status"] == "completed"
    assert (city / "city.toml").read_bytes() == (
        bundle / "config" / "city.toml"
    ).read_bytes()
    assert (city / "pack.toml").read_text() == "[pack]\nname='init-scaffold'\n"
    assert not (city / "packs.lock").exists()

    _mark_images_promoted(city)
    activated = _run(
        bundle / "bin" / "provision-control-plane",
        "activate-topology",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )
    assert activated.returncode == 0, activated.stderr
    assert json.loads(activated.stdout)["next_required_action"] == (
        "initialize-hq-then-transition-hq-endpoint"
    )
    repeated_activation = _run(
        bundle / "bin" / "provision-control-plane",
        "activate-topology",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )
    assert repeated_activation.returncode == 0, repeated_activation.stderr
    assert json.loads(repeated_activation.stdout)["status"] == "already-activated"
    rejected = _run(
        bundle / "bin" / "provision-control-plane",
        "finalize",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )
    assert rejected.returncode != 0
    assert "requires an HQ transition receipt" in rejected.stderr
    assert not (transaction / "final-receipt.json").exists()
    for source, destination in (
        ("config/city.toml", "city.toml"),
        ("config/pack.toml", "pack.toml"),
        ("config/packs.lock", "packs.lock"),
        ("config/site.example.toml", ".gc/site.toml"),
    ):
        assert (city / destination).read_bytes() == (bundle / source).read_bytes()
    rolled_back = _run(
        bundle / "bin" / "provision-control-plane",
        "rollback",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )
    assert rolled_back.returncode == 0, rolled_back.stderr
    assert json.loads(rolled_back.stdout)["status"] == "restored"
    assert not (city / "city.toml").exists()
    assert not (city / "pack.toml").exists()
    assert not (city / "packs.lock").exists()
    assert not (city / ".gc" / "site.toml").exists()
    assert not (city / "bin" / "gc").exists()
    assert not (city / "runtime-lock.json").exists()
    assert list(city.iterdir()) == []
    rollback_receipt = json.loads(
        (transaction / "control-rollback-receipt.json").read_text()
    )
    assert rollback_receipt["city_prestate"] == "empty"
    repeated_rollback = _run(
        bundle / "bin" / "provision-control-plane",
        "rollback",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )
    assert repeated_rollback.returncode == 0, repeated_rollback.stderr
    assert json.loads(repeated_rollback.stdout)["status"] == "already-restored"


def test_empty_city_recovers_only_through_upstream_inert_init_resume(
    tmp_path: Path,
) -> None:
    bundle = _bundle(tmp_path, fake_tools=True)
    city = tmp_path / "new-city"
    transaction = tmp_path / "provision-transaction"
    interrupt = tmp_path / "interrupt-once"
    command = (
        bundle / "bin" / "provision-control-plane",
        "prepare",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )
    environment = {**os.environ, "FAKE_GC_INTERRUPT_ONCE": interrupt.as_posix()}

    interrupted = _run(*command, environment=environment)
    assert interrupted.returncode != 0
    assert "simulated gc init interruption" in interrupted.stderr
    assert (transaction / "gc-init-started.json").is_file()
    assert not (transaction / "gc-init.json").exists()
    assert not (transaction / "stage-receipt.json").exists()

    recovered = _run(*command, environment=environment)
    assert recovered.returncode == 0, recovered.stderr
    receipt = json.loads((transaction / "gc-init.json").read_text())
    assert receipt["status"] == "recovered-complete"
    assert receipt["resume"]["argv"] == [
        (bundle / "artifacts" / "gc").as_posix(),
        "init",
        "--skip-provider-readiness",
        "--no-start",
        city.as_posix(),
    ]
    assert receipt["supervisor"]["status"]["running"] is False
    assert (transaction / "stage-receipt.json").is_file()

    repeated = _run(*command, environment=environment)
    assert repeated.returncode == 0, repeated.stderr
    assert json.loads(repeated.stdout)["status"] == "already-staged"


def test_existing_city_cannot_finalize_without_guarded_endpoint_receipt(
    tmp_path: Path,
) -> None:
    bundle = _bundle(tmp_path, fake_tools=True)
    city = tmp_path / "city"
    city.mkdir(mode=0o700)
    (city / ".gc").mkdir(mode=0o700)
    prior = b'[workspace]\nname = "managed"\n'
    (city / "city.toml").write_bytes(prior)
    (city / "city.toml").chmod(0o600)
    transaction = tmp_path / "provision-transaction"
    prepared = _run(
        bundle / "bin" / "provision-control-plane",
        "prepare",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )
    assert prepared.returncode == 0, prepared.stderr
    _mark_images_promoted(city)
    activated = _run(
        bundle / "bin" / "provision-control-plane",
        "activate-topology",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )
    assert activated.returncode == 0, activated.stderr
    activation = json.loads(activated.stdout)
    assert activation["next_required_action"] == "transition-hq-endpoint"
    assert (city / "city.toml").read_bytes() == (
        bundle / "config" / "city.toml"
    ).read_bytes()
    rejected = _run(
        bundle / "bin" / "provision-control-plane",
        "finalize",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )
    assert rejected.returncode != 0
    assert "requires an HQ transition receipt" in rejected.stderr
    assert (city / "city.toml").read_bytes() == (
        bundle / "config" / "city.toml"
    ).read_bytes()
    assert not (transaction / "final-receipt.json").exists()

    rolled_back = _run(
        bundle / "bin" / "provision-control-plane",
        "rollback",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )
    assert rolled_back.returncode == 0, rolled_back.stderr
    assert (city / "city.toml").read_bytes() == prior
    assert not (city / "bin" / "gc").exists()


def test_interrupted_stage_resumes_from_anchored_intent(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path, fake_tools=True)
    city = tmp_path / "city"
    city.mkdir(mode=0o700)
    (city / ".gc").mkdir(mode=0o700)
    prior = b'[workspace]\nname = "managed"\n'
    (city / "city.toml").write_bytes(prior)
    (city / "city.toml").chmod(0o600)
    transaction = tmp_path / "provision-transaction"
    namespace = runpy.run_path((bundle / "bin" / "provision-control-plane").as_posix())
    prepare = namespace["prepare"]
    original_install = namespace["_install_record"]
    calls = 0

    def crashing_install(*args, **kwargs):
        nonlocal calls
        calls += 1
        original_install(*args, **kwargs)
        if calls == 2:
            raise namespace["ProvisionError"]("injected interruption")

    prepare.__globals__["_install_record"] = crashing_install
    with pytest.raises(namespace["ProvisionError"], match="injected interruption"):
        prepare(bundle, city, transaction)
    assert (transaction / "intent.json").is_file()
    assert not (transaction / "stage-receipt.json").exists()
    assert (city / "city.toml").read_bytes() == prior

    prepare.__globals__["_install_record"] = original_install
    resumed = prepare(bundle, city, transaction)
    assert resumed["status"] == "staged"
    assert (city / "city.toml").read_bytes() == prior
    assert (transaction / "stage-receipt.json").is_file()


def test_empty_city_rolls_back_directly_from_exact_gc_init_scaffold(
    tmp_path: Path,
) -> None:
    bundle = _bundle(tmp_path, fake_tools=True)
    city = tmp_path / "new-city"
    transaction = tmp_path / "provision-transaction"
    prepared = _run(
        bundle / "bin" / "provision-control-plane",
        "prepare",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )
    assert prepared.returncode == 0, prepared.stderr
    assert (city / "pack.toml").read_text() == "[pack]\nname='init-scaffold'\n"
    assert (city / "pack.toml").read_bytes() != (
        bundle / "config" / "pack.toml"
    ).read_bytes()

    rolled_back = _run(
        bundle / "bin" / "provision-control-plane",
        "rollback",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )
    assert rolled_back.returncode == 0, rolled_back.stderr
    assert json.loads(rolled_back.stdout)["status"] == "restored"
    assert list(city.iterdir()) == []

    repeated = _run(
        bundle / "bin" / "provision-control-plane",
        "rollback",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )
    assert repeated.returncode == 0, repeated.stderr
    assert json.loads(repeated.stdout)["status"] == "already-restored"


def test_interrupted_topology_activation_resumes_exact_mixture(
    tmp_path: Path,
) -> None:
    bundle = _bundle(tmp_path, fake_tools=True)
    city = tmp_path / "city"
    city.mkdir(mode=0o700)
    (city / ".gc").mkdir(mode=0o700)
    prior = b'[workspace]\nname = "managed"\n'
    (city / "city.toml").write_bytes(prior)
    (city / "city.toml").chmod(0o600)
    transaction = tmp_path / "provision-transaction"
    prepared = _run(
        bundle / "bin" / "provision-control-plane",
        "prepare",
        "--source-root",
        bundle,
        "--city-root",
        city,
        "--transaction-dir",
        transaction,
    )
    assert prepared.returncode == 0, prepared.stderr
    _mark_images_promoted(city)

    namespace = runpy.run_path((bundle / "bin" / "provision-control-plane").as_posix())
    activate = namespace["activate_topology"]
    original_install = namespace["_install_record"]
    calls = 0

    def crashing_install(*args, **kwargs):
        nonlocal calls
        calls += 1
        original_install(*args, **kwargs)
        if calls == 2:
            raise namespace["ProvisionError"]("injected activation interruption")

    activate.__globals__["_install_record"] = crashing_install
    with pytest.raises(
        namespace["ProvisionError"], match="injected activation interruption"
    ):
        activate(bundle, city, transaction)
    assert not (transaction / "activation-receipt.json").exists()

    activate.__globals__["_install_record"] = original_install
    resumed = activate(bundle, city, transaction)
    assert resumed["status"] == "verified"
    assert resumed["next_required_action"] == "transition-hq-endpoint"
    for source, destination in (
        ("config/city.toml", "city.toml"),
        ("config/pack.toml", "pack.toml"),
        ("config/packs.lock", "packs.lock"),
        ("config/site.example.toml", ".gc/site.toml"),
    ):
        assert (city / destination).read_bytes() == (bundle / source).read_bytes()
