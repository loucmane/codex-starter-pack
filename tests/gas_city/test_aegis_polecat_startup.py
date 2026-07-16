from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest

from aegis_foundation import task_authority


REPO_ROOT = Path(__file__).resolve().parents[2]
DEPLOY = REPO_ROOT / "deploy/gas-city"
SHIM = DEPLOY / "docker/aegis-runtime-shim.py"
SUPERVISOR = DEPLOY / "docker/provider-supervisor.py"
HELPER = DEPLOY / "docker/aegis-polecat-startup.py"
RUNTIME = DEPLOY / "artifacts/aegis-runtime.whl"
BEAD_ID = "ags-runtime.A_17"
ACTOR = "aegis/gastown.polecat_test"


class _GraphRunner:
    def __init__(
        self,
        helper,
        issues: dict[str, dict[str, object]],
        *,
        children: list[dict[str, str]] | None = None,
        claim: dict[str, object] | None = None,
    ) -> None:
        self.helper = helper
        self.issues = issues
        self.children = children or [{"id": "ags-source"}]
        self.claim = claim
        self.calls: list[list[str]] = []

    def __call__(self, command, cwd, allowed_codes, timeout):
        del cwd, allowed_codes, timeout
        command = list(command)
        self.calls.append(command)
        if command[1:4] == ["hook", "--claim", "--json"]:
            payload = self.claim
            assert payload is not None
            return self.helper.CommandResult(0, json.dumps(payload).encode(), b"")
        if "convoy" in command and "status" in command:
            payload = {
                "schema_version": "1",
                "ok": True,
                "convoy": {"id": "ags-convoy"},
                "children": self.children,
            }
            return self.helper.CommandResult(0, json.dumps(payload).encode(), b"")
        if command[0].endswith("bd") and "show" in command:
            issue_id = command[-1]
            return self.helper.CommandResult(
                0,
                json.dumps([self.issues[issue_id]]).encode(),
                b"",
            )
        raise AssertionError(f"unexpected command: {command}")


class _BranchRunner:
    def __init__(self, helper, source: dict[str, object]) -> None:
        self.helper = helper
        self.source = source
        self.calls: list[list[str]] = []

    def __call__(self, command, cwd, allowed_codes, timeout):
        command = list(command)
        self.calls.append(command)
        if command[0] == "/trusted/gc":
            assert command[1:4] == ["bd", "update", self.source["id"]]
            updates = command[4:]
            assert len(updates) % 2 == 0
            metadata = self.source["metadata"]
            assert isinstance(metadata, dict)
            for option, assignment in zip(updates[::2], updates[1::2], strict=True):
                assert option == "--set-metadata"
                key, value = assignment.split("=", 1)
                metadata[key] = value
            return self.helper.CommandResult(0, b"", b"")
        if command[0] == "/trusted/bd":
            assert command[-3:] == ["show", "--id", self.source["id"]]
            return self.helper.CommandResult(
                0,
                json.dumps([self.source]).encode("utf-8"),
                b"",
            )
        return self.helper._subprocess_runner(command, cwd, allowed_codes, timeout)


def _graph_issues(actor: str = ACTOR, formula_digest: str | None = None):
    formula_digest = formula_digest or hashlib.sha256(b"formula").hexdigest()
    return {
        "ags-step": {
            "id": "ags-step",
            "status": "in_progress",
            "assignee": actor,
            "issue_type": "task",
            "metadata": {
                "gc.step_ref": "mol-polecat-work.implement",
                "gc.root_bead_id": "ags-root",
                "gc.routed_to": "aegis/gastown.polecat",
            },
            "ephemeral": False,
            "no_history": False,
        },
        "ags-root": {
            "id": "ags-root",
            "title": "mol-polecat-work",
            "issue_type": "task",
            "metadata": {
                "gc.kind": "workflow",
                "gc.formula_contract": "graph.v2",
                "gc.formula_hash": formula_digest,
                "gc.input_convoy_id": "ags-convoy",
            },
        },
        "ags-convoy": {
            "id": "ags-convoy",
            "issue_type": "convoy",
            "metadata": {},
        },
        "ags-source": {
            "id": "ags-source",
            "title": "Durable source work",
            "issue_type": "task",
            "status": "in_progress",
            "assignee": actor,
            "ephemeral": False,
            "no_history": False,
            "metadata": {},
        },
    }


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _authority(tmp_path: Path) -> tuple[Path, Path, str]:
    trusted = tmp_path / "trusted"
    trusted.mkdir()
    runtime = trusted / "task-authority.py"
    runtime.write_bytes(Path(task_authority.__file__).read_bytes())
    runtime.chmod(0o444)
    runtime_digest = hashlib.sha256(runtime.read_bytes()).hexdigest()
    receipt = trusted / "authority" / "aegis.json"
    evidence = task_authority.TaskAuthorityEvidence(
        taskmaster_snapshot_sha256=_digest("snapshot"),
        migration_report_sha256=_digest("migration"),
        backup_restore_report_sha256=_digest("restore"),
    )
    task_authority.initialize_taskmaster_authority(
        receipt,
        rig="aegis",
        beads_prefix="ags",
        database="aegis_beads",
        evidence=evidence,
        activated_at="2026-07-15T18:00:00Z",
    )
    task_authority.transition_authority(
        receipt,
        target_mode=task_authority.TaskAuthorityMode.BEADS,
        expected_generation=1,
        expected_rig="aegis",
        expected_beads_prefix="ags",
        expected_database="aegis_beads",
        expected_evidence=evidence,
        activated_at="2026-07-15T18:01:00Z",
    )
    return receipt, runtime, runtime_digest


def _fake_bd(tmp_path: Path, target: Path) -> tuple[Path, str]:
    executable = tmp_path / "trusted/bd"
    issue = {
        "id": BEAD_ID,
        "title": "Exercise immutable Gas City Aegis runtime",
        "status": "in_progress",
        "issue_type": "task",
        "assignee": ACTOR,
        "metadata": {
            "branch": f"polecat/{BEAD_ID}",
            "work_dir": str(target),
        },
        "ephemeral": False,
        "no_history": False,
    }
    payload = json.dumps([issue], sort_keys=True, separators=(",", ":"))
    executable.write_text(
        "#!/usr/bin/python3\n"
        "import sys\n"
        "if sys.argv[1:] == ['--version']:\n"
        "    print('bd version 1.1.0')\n"
        "    raise SystemExit(0)\n"
        "if sys.argv[1:4] != ['--json', '--readonly', '-C']:\n"
        "    raise SystemExit(64)\n"
        f"if sys.argv[5:] != ['show', '--id', {BEAD_ID!r}]:\n"
        "    raise SystemExit(64)\n"
        f"sys.stdout.write({payload!r})\n",
        encoding="utf-8",
    )
    executable.chmod(0o555)
    return executable, hashlib.sha256(executable.read_bytes()).hexdigest()


def _git(target: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(target), *arguments],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def _fresh_target(tmp_path: Path) -> tuple[Path, Path, Path]:
    city = tmp_path / "city"
    rig = tmp_path / "rig"
    target = city / ".gc/worktrees/aegis/polecats/gastown.polecat_test"
    target.mkdir(parents=True)
    rig.mkdir()
    _git(target, "init", "-b", "main")
    _git(target, "config", "user.email", "test@example.invalid")
    _git(target, "config", "user.name", "Aegis Test")
    (target / ".git/info/exclude").write_text(".aegis/bin/\n", encoding="utf-8")
    aegis = target / ".aegis"
    aegis.mkdir()
    (aegis / "brief.json").write_text('{"schema_version":"1.0"}\n', encoding="utf-8")
    hooks = target / ".claude/scripts"
    shutil.copytree(REPO_ROOT / ".claude/scripts", hooks)
    _git(target, "add", ".aegis/brief.json", ".claude/scripts")
    _git(target, "commit", "-m", "baseline")
    _git(target, "switch", "-c", f"polecat/{BEAD_ID}")
    bin_directory = aegis / "bin"
    bin_directory.mkdir(mode=0o700)
    return target.resolve(), city.resolve(), rig.resolve()


def _tree_digest(target: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(target.rglob("*")):
        relative = path.relative_to(target)
        if relative.parts[0] == ".git" or relative.parts[:2] == (".aegis", "bin"):
            continue
        digest.update(relative.as_posix().encode("utf-8") + b"\0")
        if path.is_symlink():
            digest.update(b"L" + os.readlink(path).encode("utf-8"))
        elif path.is_file():
            digest.update(b"F" + path.read_bytes())
        else:
            digest.update(b"D")
    return digest.hexdigest()


def _driver(
    target: Path,
    city: Path,
    rig: Path,
    runtime_root: Path,
) -> Path:
    wrapper = target / ".aegis/bin/aegis"
    wrapper.write_text(
        "#!/usr/bin/python3\n"
        "import importlib.util, pathlib, sys\n"
        f"shim_path = pathlib.Path({str(SHIM)!r})\n"
        "spec = importlib.util.spec_from_file_location('_runtime_shim_e2e', shim_path)\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "sys.modules[spec.name] = module\n"
        "spec.loader.exec_module(module)\n"
        "paths = module.RuntimePaths(\n"
        f" runtime_root=pathlib.Path({str(runtime_root)!r}),\n"
        f" runtime_source_root=pathlib.Path({str(runtime_root / 'aegis_foundation/assets')!r}),\n"
        f" shim=shim_path, city_root=pathlib.Path({str(city)!r}),\n"
        f" rig_root=pathlib.Path({str(rig)!r}),\n"
        f" git_common_dir=pathlib.Path({str(target / '.git')!r}),\n"
        f" worktree_root=pathlib.Path({str(city / '.gc/worktrees/aegis/polecats')!r}),\n"
        " git=pathlib.Path('/usr/bin/git'), require_tmpfs=False)\n"
        "raise SystemExit(module.run(sys.argv[1:], paths=paths))\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o500)
    return wrapper


def _environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    target: Path,
    city: Path,
    rig: Path,
) -> dict[str, str]:
    receipt, authority_runtime, authority_digest = _authority(tmp_path)
    bd, bd_digest = _fake_bd(tmp_path, target)
    values = {
        "AEGIS_TASK_AUTHORITY_FILE": str(receipt),
        "AEGIS_TASK_AUTHORITY_RUNTIME_FILE": str(authority_runtime),
        "AEGIS_TASK_AUTHORITY_RUNTIME_SHA256": authority_digest,
        "AEGIS_BD_EXECUTABLE": str(bd),
        "AEGIS_BD_SHA256": bd_digest,
        "GC_CITY_ROOT": str(city),
        "GC_RIG": "aegis",
        "GC_RIG_ROOT": str(rig),
        "GC_BEADS_PREFIX": "ags",
        "GC_TEMPLATE": "aegis/gastown.polecat",
        "GC_DOLT_DATABASE": "aegis_beads",
        "BEADS_DOLT_SERVER_DATABASE": "aegis_beads",
        "BEADS_ACTOR": ACTOR,
        "GC_SESSION_NAME": ACTOR,
        "GC_AGENT": ACTOR,
        "GC_BEAD_ID": "ags-formula-not-source-work",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    return {**os.environ, **values}


def test_offline_runtime_target_local_kickoff_without_install_is_clean_and_idempotent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target, city, rig = _fresh_target(tmp_path)
    runtime_root = tmp_path / "runtime"
    with zipfile.ZipFile(RUNTIME) as archive:
        archive.extractall(runtime_root)
    wrapper = _driver(target, city, rig, runtime_root)
    environment = _environment(monkeypatch, tmp_path, target, city, rig)
    assert not (target / ".aegis/foundation-manifest.json").exists()

    first = subprocess.run(
        [str(wrapper), "kickoff", "--target-dir", str(target), "--bead", BEAD_ID],
        cwd=target,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert first.returncode == 0, first.stdout + first.stderr
    assert json.loads(first.stdout)["status"] == "started"
    assert not (target / ".aegis/foundation-manifest.json").exists()
    current = json.loads((target / ".aegis/state/current-work.json").read_text())
    assert current["task"]["id"] == BEAD_ID
    assert current["task"]["source"] == "beads"

    dirty = _git(target, "status", "--porcelain=v1", "--untracked-files=all").splitlines()
    paths = {line[3:] for line in dirty}
    assert paths
    assert all(
        path in {"plans/current", "sessions/current", "sessions/state.json"}
        or path.startswith(".aegis/reports/")
        or path.startswith(".aegis/state/")
        or path.startswith("docs/ai/work-tracking/active/")
        or path.startswith("plans/2026-")
        or path.startswith("sessions/2026/")
        for path in paths
    )
    assert not any(path.startswith(".aegis/bin/") for path in paths)
    assert ".aegis/foundation-manifest.json" not in paths
    before_resume = _tree_digest(target)

    second = subprocess.run(
        [str(wrapper), "kickoff", "--target-dir", str(target), "--bead", BEAD_ID],
        cwd=target,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert second.returncode == 0, second.stdout + second.stderr
    assert json.loads(second.stdout)["status"] == "already_started"
    assert _tree_digest(target) == before_resume
    assert not (target / ".aegis/foundation-manifest.json").exists()

    readiness = subprocess.run(
        ["bash", ".claude/scripts/readiness.sh", "--all", "--root", str(target)],
        cwd=target,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert readiness.returncode == 0, readiness.stdout + readiness.stderr
    assert "STATE: READY" in readiness.stdout
    assert f"authoritative Bead {BEAD_ID} is in_progress" in readiness.stdout


def test_runtime_artifact_is_reproducible_and_bound_everywhere(tmp_path: Path) -> None:
    first = RUNTIME.read_bytes()
    result = subprocess.run(
        [str(DEPLOY / "bin/build-aegis-runtime")],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    second = RUNTIME.read_bytes()
    assert first == second
    digest = hashlib.sha256(second).hexdigest()
    lock = json.loads((DEPLOY / "runtime-lock.json").read_text())
    contract = lock["aegis_polecat_startup"]
    assert contract["runtime_artifact_sha256"] == digest
    assert digest in (DEPLOY / "docker/Dockerfile").read_text()
    assert contract["runtime_shim_sha256"] == hashlib.sha256(SHIM.read_bytes()).hexdigest()
    assert contract["sha256"] == hashlib.sha256(HELPER.read_bytes()).hexdigest()


def test_supervisor_launcher_is_exact_and_provider_launcher_uses_nested_tmpfs() -> None:
    supervisor = _load(SUPERVISOR, "_aegis_provider_supervisor_contract")
    launcher = DEPLOY / "bin/provider-container"
    launcher_text = launcher.read_text(encoding="utf-8")
    expected = (
        b"#!/bin/sh\n"
        b"set -eu\n"
        b'exec /usr/bin/python3 -I /opt/gas-city/aegis-runtime-shim.py "$@"\n'
    )
    lock = json.loads((DEPLOY / "runtime-lock.json").read_text())
    assert supervisor.AEGIS_LOCAL_LAUNCHER_CONTENT == expected
    assert hashlib.sha256(expected).hexdigest() == lock["aegis_polecat_startup"][
        "local_launcher_sha256"
    ]
    assert '--tmpfs "$repo_root/.aegis/bin:rw,nosuid,nodev' in launcher_text
    assert "AEGIS_RUNTIME_ARTIFACT_SHA256" in launcher_text
    assert "AEGIS_RUNTIME_SHIM_SHA256" in launcher_text
    assert "BEADS_ACTOR" in launcher_text


def test_formula_override_changes_only_workspace_setup() -> None:
    local = (DEPLOY / "formulas/aegis/mol-polecat-work.toml").read_bytes()
    marker = b'[[steps]]\nid = "workspace-setup"'
    opening = b'description = """'

    def bounds(content: bytes) -> tuple[int, int]:
        step = content.index(marker)
        start = content.index(opening, step)
        end = content.index(b'"""', start + len(opening)) + 3
        return start, end

    local_start, local_end = bounds(local)
    # These are the exact prefix/suffix hashes from pinned gastown commit
    # 33d3a430a67d1782ad364556cb566bdb01d0afe3. Matching both proves the
    # override changed only the workspace-setup description interval.
    assert hashlib.sha256(local[:local_start]).hexdigest() == (
        "7b72b9c1fe4e5f7c2847a47869b5858b34623e3c4b1155dd4a90e9f7f6cc30fc"
    )
    assert hashlib.sha256(local[local_end:]).hexdigest() == (
        "14c779085bd3534be5fd65787773565dc53f69faceeba975acb9dca97097d81d"
    )
    assert hashlib.sha256(local[local_start:local_end]).hexdigest() == (
        "1e09cf7e311a931cbe176c91aafba195cb750267e83ebe46cd9ae4d8519ecadd"
    )
    lock = json.loads((DEPLOY / "runtime-lock.json").read_text())
    assert hashlib.sha256(local).hexdigest() == lock["aegis_polecat_startup"][
        "formula_sha256"
    ]
    assert lock["aegis_polecat_startup"]["upstream_formula_sha256"] == (
        "86878dd7ae180e02905d88ac092944d2fece075ac22dab86dc54b59c10f6319e"
    )


def test_claim_is_atomic_json_and_never_uses_gc_bead_id(tmp_path: Path) -> None:
    helper = _load(HELPER, "_aegis_startup_claim_contract")
    claim = {
        "schema_version": "1",
        "ok": True,
        "command": "hook",
        "action": "work",
        "reason": "claimed",
        "bead_id": "ags-step",
        "assignee": ACTOR,
        "route": "aegis/gastown.polecat",
    }
    runner = _GraphRunner(helper, {}, claim=claim)
    paths = helper.RuntimePaths(gc=Path("/trusted/gc"), bd=Path("/trusted/bd"))
    observed, _ = helper._claim_formula_step(runner, paths, tmp_path, ACTOR)
    assert observed == claim
    assert runner.calls == [["/trusted/gc", "hook", "--claim", "--json"]]
    assert "GC_BEAD_ID" not in HELPER.read_text(encoding="utf-8").split(
        "def _validate_identity", 1
    )[1]


def test_identity_uses_one_canonical_actor_and_ignores_formula_bead_environment(
    tmp_path: Path,
) -> None:
    helper = _load(HELPER, "_aegis_startup_identity_contract")
    city = tmp_path / "city"
    rig = tmp_path / "rig"
    alias = "aegis/gastown.polecat_test"
    worktree_root = city / ".gc/worktrees/aegis/polecats"
    cwd = worktree_root / "gastown.polecat_test"
    cwd.mkdir(parents=True)
    rig.mkdir()
    paths = helper.RuntimePaths(
        helper=tmp_path / "helper",
        gc=tmp_path / "gc",
        bd=tmp_path / "bd",
        city_root=city,
        rig_root=rig,
        git_common_dir=rig / ".git",
        worktree_root=worktree_root,
        receipt=tmp_path / "receipt.json",
        git_broker_receipt=tmp_path / "broker.json",
        authority=tmp_path / "authority.json",
        task_authority_runtime=tmp_path / "task-authority.py",
        runtime_artifact=tmp_path / "runtime.whl",
        runtime_shim=tmp_path / "shim.py",
    )
    environment = {
        "GC_CITY_ROOT": str(city),
        "GC_RIG": "aegis",
        "GC_RIG_ROOT": str(rig),
        "GC_BEADS_PREFIX": "ags",
        "GC_DOLT_DATABASE": "aegis_beads",
        "BEADS_DOLT_SERVER_DATABASE": "aegis_beads",
        "GC_TEMPLATE": "aegis/gastown.polecat",
        "GC_SESSION_ORIGIN": "ephemeral",
        "AEGIS_TASK_AUTHORITY_FILE": str(paths.authority),
        "AEGIS_TASK_AUTHORITY_RUNTIME_FILE": str(paths.task_authority_runtime),
        "AEGIS_GC_EXECUTABLE": str(paths.gc),
        "AEGIS_BD_EXECUTABLE": str(paths.bd),
        "AEGIS_STARTUP_HELPER_FILE": str(paths.helper),
        "AEGIS_STARTUP_RECEIPT_PATH": str(paths.receipt),
        "AEGIS_GIT_BROKER_RECEIPT_PATH": str(paths.git_broker_receipt),
        "AEGIS_RUNTIME_ARTIFACT_FILE": str(paths.runtime_artifact),
        "AEGIS_RUNTIME_SHIM_FILE": str(paths.runtime_shim),
        "AEGIS_BASE_BRANCH": "main",
        "AEGIS_POLECAT_ROUTE": "aegis/gastown.polecat",
        "AEGIS_GASCITY_CORE_PACK_COMMIT": "f895c0ff47d6ee9334ed282a416387eb5b084d24",
        "AEGIS_GASTOWN_PACK_COMMIT": "33d3a430a67d1782ad364556cb566bdb01d0afe3",
        "AEGIS_POLECAT_UPSTREAM_FORMULA_SHA256": (
            "86878dd7ae180e02905d88ac092944d2fece075ac22dab86dc54b59c10f6319e"
        ),
        "GC_ALIAS": alias,
        "GC_SESSION_NAME": ACTOR,
        "GC_AGENT": ACTOR,
        "BEADS_ACTOR": ACTOR,
        "GC_SESSION_ID": "session-17",
        "GC_BEAD_ID": "completely-unrelated-formula-record",
        "GIT_DIR": str(paths.git_common_dir),
        "GIT_WORK_TREE": str(cwd),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
    }
    assert helper._validate_identity(environment, cwd, paths) == ACTOR
    environment["BEADS_ACTOR"] = "another-polecat"
    with pytest.raises(helper.StartupError, match="BEADS_ACTOR"):
        helper._validate_identity(environment, cwd, paths)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("wrong_owner", "durable in_progress source task"),
        ("formula_drift", "pinned mol-polecat-work graph"),
        ("two_children", "exactly one child"),
        ("ephemeral_source", "durable in_progress source task"),
    ],
)
def test_formula_graph_rejects_ownership_hash_cardinality_and_storage_drift(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    helper = _load(HELPER, f"_aegis_startup_graph_{mutation}")
    formula_digest = _digest("formula")
    issues = _graph_issues(formula_digest=formula_digest)
    children = [{"id": "ags-source"}]
    if mutation == "wrong_owner":
        issues["ags-source"]["assignee"] = "another-polecat"
    elif mutation == "formula_drift":
        issues["ags-root"]["metadata"]["gc.formula_hash"] = _digest("tampered")
    elif mutation == "two_children":
        children.append({"id": "ags-other"})
    elif mutation == "ephemeral_source":
        issues["ags-source"]["ephemeral"] = True
    runner = _GraphRunner(helper, issues, children=children)
    paths = helper.RuntimePaths(gc=Path("/trusted/gc"), bd=Path("/trusted/bd"))
    with pytest.raises(helper.StartupError, match=message):
        helper._validate_formula_graph(
            runner,
            paths,
            tmp_path,
            {"bead_id": "ags-step"},
            ACTOR,
            formula_digest,
        )


def test_formula_graph_returns_exact_single_durable_source(tmp_path: Path) -> None:
    helper = _load(HELPER, "_aegis_startup_graph_happy")
    formula_digest = _digest("formula")
    issues = _graph_issues(formula_digest=formula_digest)
    runner = _GraphRunner(helper, issues)
    step, root, convoy, source = helper._validate_formula_graph(
        runner,
        helper.RuntimePaths(gc=Path("/trusted/gc"), bd=Path("/trusted/bd")),
        tmp_path,
        {"bead_id": "ags-step"},
        ACTOR,
        formula_digest,
    )
    assert (step["id"], root["id"], convoy["id"], source["id"]) == (
        "ags-step",
        "ags-root",
        "ags-convoy",
        "ags-source",
    )

    issues["ags-step"]["status"] = "open"
    ready_runner = _GraphRunner(helper, issues)
    ready_step, *_ = helper._validate_formula_graph(
        ready_runner,
        helper.RuntimePaths(gc=Path("/trusted/gc"), bd=Path("/trusted/bd")),
        tmp_path,
        {"bead_id": "ags-step", "reason": "ready_assignment"},
        ACTOR,
        formula_digest,
    )
    assert ready_step["status"] == "open"


def test_runtime_digest_verification_rejects_any_image_artifact_drift(
    tmp_path: Path,
) -> None:
    helper = _load(HELPER, "_aegis_startup_runtime_contract")
    files: dict[str, Path] = {}
    for name, mode in (
        ("helper", 0o444),
        ("gc", 0o555),
        ("bd", 0o555),
        ("artifact", 0o444),
        ("shim", 0o444),
    ):
        path = tmp_path / name
        path.write_bytes(f"{name}-content".encode())
        path.chmod(mode)
        files[name] = path
    paths = helper.RuntimePaths(
        helper=files["helper"],
        gc=files["gc"],
        bd=files["bd"],
        runtime_artifact=files["artifact"],
        runtime_shim=files["shim"],
        image_uid=os.geteuid(),
    )
    environment = {
        "AEGIS_STARTUP_HELPER_SHA256": hashlib.sha256(files["helper"].read_bytes()).hexdigest(),
        "AEGIS_GC_SHA256": hashlib.sha256(files["gc"].read_bytes()).hexdigest(),
        "AEGIS_BD_SHA256": hashlib.sha256(files["bd"].read_bytes()).hexdigest(),
        "AEGIS_POLECAT_FORMULA_SHA256": _digest("formula"),
        "AEGIS_TASK_AUTHORITY_RECEIPT_SHA256": _digest("authority"),
        "AEGIS_TASK_AUTHORITY_RUNTIME_SHA256": _digest("authority-runtime"),
        "AEGIS_RUNTIME_ARTIFACT_SHA256": hashlib.sha256(
            files["artifact"].read_bytes()
        ).hexdigest(),
        "AEGIS_RUNTIME_SHIM_SHA256": hashlib.sha256(files["shim"].read_bytes()).hexdigest(),
        "AEGIS_LOCAL_LAUNCHER_SHA256": _digest("launcher"),
    }
    verified = helper._verify_runtime(environment, paths)
    assert verified["runtime_shim_sha256"] == environment["AEGIS_RUNTIME_SHIM_SHA256"]
    files["shim"].chmod(0o644)
    files["shim"].write_bytes(b"tampered")
    files["shim"].chmod(0o444)
    with pytest.raises(helper.StartupError, match="SHA-256"):
        helper._verify_runtime(environment, paths)


def test_branch_prepare_uses_existing_outer_worktree_and_live_remote_collision(
    tmp_path: Path,
) -> None:
    helper = _load(HELPER, "_aegis_startup_branch_contract")
    origin = tmp_path / "origin.git"
    origin.mkdir()
    _git(origin, "init", "--bare")
    rig = tmp_path / "rig"
    rig.mkdir()
    _git(rig, "init", "-b", "main")
    _git(rig, "config", "user.email", "test@example.invalid")
    _git(rig, "config", "user.name", "Aegis Test")
    (rig / "tracked.txt").write_text("base\n", encoding="utf-8")
    _git(rig, "add", "tracked.txt")
    _git(rig, "commit", "-m", "baseline")
    _git(rig, "remote", "add", "origin", str(origin))
    _git(rig, "push", "-u", "origin", "main")

    worktree_root = tmp_path / "city/.gc/worktrees/aegis/polecats"
    worktree_root.mkdir(parents=True)
    target = worktree_root / "gastown.polecat_branch"
    _git(rig, "worktree", "add", "--detach", str(target), "origin/main")
    source: dict[str, object] = {
        "id": "ags-source",
        "title": "Durable source work",
        "status": "in_progress",
        "issue_type": "task",
        "assignee": ACTOR,
        "ephemeral": False,
        "no_history": False,
        "metadata": {},
    }
    runner = _BranchRunner(helper, source)
    paths = helper.RuntimePaths(
        gc=Path("/trusted/gc"),
        bd=Path("/trusted/bd"),
        git=Path("/usr/bin/git"),
        git_common_dir=rig / ".git",
        worktree_root=worktree_root,
    )
    branch, head, resumed = helper._prepare_branch(
        runner, paths, target.resolve(), source, ACTOR
    )
    base_head = _git(rig, "rev-parse", "origin/main")
    assert (branch, head, resumed) == ("polecat/ags-source", base_head, False)
    assert source["metadata"] == {
        "branch": "polecat/ags-source",
        "work_dir": str(target.resolve()),
        "fork_sha": base_head,
        "target": "main",
    }

    state = target / ".aegis/state"
    state.mkdir(parents=True)
    (state / "current-work.json").write_text(
        json.dumps(
            {
                "task": {"id": "ags-source", "source": "beads"},
                "branch": {"current": "polecat/ags-source"},
            }
        ),
        encoding="utf-8",
    )
    (target / "implementation.txt").write_text("resume dirt is intentional\n")
    resumed_branch, resumed_head, resumed = helper._prepare_branch(
        runner, paths, target.resolve(), source, ACTOR
    )
    assert (resumed_branch, resumed_head, resumed) == (branch, head, True)

    _git(rig, "push", "origin", "main:refs/heads/polecat/ags-collision")
    collision_target = worktree_root / "gastown.polecat_collision"
    _git(
        rig,
        "worktree",
        "add",
        "--detach",
        str(collision_target),
        "origin/main",
    )
    collision_source: dict[str, object] = {
        **source,
        "id": "ags-collision",
        "metadata": {},
    }
    collision_runner = _BranchRunner(helper, collision_source)
    with pytest.raises(helper.StartupError, match="existing remote branch"):
        helper._prepare_branch(
            collision_runner,
            paths,
            collision_target.resolve(),
            collision_source,
            ACTOR,
        )


def test_temporary_manifest_never_overwrites_real_or_unlinks_replacement(
    tmp_path: Path,
) -> None:
    shim = _load(SHIM, "_aegis_runtime_manifest_contract")
    target = tmp_path / "target"
    (target / ".aegis").mkdir(parents=True)
    manifest = target / shim.MANIFEST_REL
    manifest.write_bytes(b'{"real":true}\n')
    descriptor, identity = shim._open_temporary_manifest(target)
    assert descriptor is None and identity is None
    assert manifest.read_bytes() == b'{"real":true}\n'

    manifest.unlink()
    descriptor, identity = shim._open_temporary_manifest(target)
    assert descriptor is not None and identity is not None
    displaced = target / ".aegis/displaced-manifest.json"
    manifest.rename(displaced)
    manifest.write_bytes(b'{"replacement":true}\n')
    with pytest.raises(shim.RuntimeShimError, match="refusing removal"):
        shim._remove_temporary_manifest(target, descriptor, identity)
    assert manifest.read_bytes() == b'{"replacement":true}\n'


def test_runtime_shim_rejects_source_override_and_self_install_churn(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    shim = _load(SHIM, "_aegis_runtime_self_host_contract")
    with pytest.raises(shim.RuntimeShimError, match="source-root overrides"):
        shim._target_from_arguments(
            ["kickoff", "--source-root", "/untrusted", "--target-dir", "."]
        )
    with pytest.raises(shim.RuntimeShimError, match="source-root overrides"):
        shim._target_from_arguments(
            ["kickoff", "--source-root=/untrusted", "--target-dir=."]
        )

    target, city, rig = _fresh_target(tmp_path)
    runtime_root = tmp_path / "unused-runtime"
    paths = shim.RuntimePaths(
        runtime_root=runtime_root,
        runtime_source_root=runtime_root / "aegis_foundation/assets",
        shim=SHIM,
        city_root=city,
        rig_root=rig,
        git_common_dir=target / ".git",
        worktree_root=city / ".gc/worktrees/aegis/polecats",
        git=Path("/usr/bin/git"),
        require_tmpfs=False,
    )
    monkeypatch.setenv("GC_CITY_ROOT", str(city))
    monkeypatch.setenv("GC_RIG", "aegis")
    monkeypatch.setenv("GC_RIG_ROOT", str(rig))
    monkeypatch.setenv("GC_BEADS_PREFIX", "ags")
    monkeypatch.setenv("GC_TEMPLATE", "aegis/gastown.polecat")
    for command in sorted(shim.SELF_HOST_INSTALL_COMMANDS):
        with pytest.raises(shim.RuntimeShimError, match="install/update commands"):
            shim.run(["--target-dir", str(target), command], paths=paths)
        assert not (target / ".aegis/foundation-manifest.json").exists()
