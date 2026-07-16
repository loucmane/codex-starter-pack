from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from aegis_foundation import task_authority
from scripts import _aegis_installer as installer


REPO_ROOT = Path(__file__).resolve().parents[2]
BEAD_ID = "ags-work.A_17"


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _target(tmp_path: Path, *, bead_id: str = BEAD_ID) -> Path:
    target = tmp_path / "target"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.run(
        ["git", "switch", "-c", f"polecat/{bead_id}"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    manifest = target / installer.AEGIS_MANIFEST_REL
    manifest.parent.mkdir(parents=True)
    manifest.write_text('{"capabilities":{}}\n', encoding="utf-8")
    shutil.copytree(
        REPO_ROOT / "templates" / "aegis" / "workflow",
        target / installer.AEGIS_WORKFLOW_TEMPLATE_TARGET_ROOT,
    )
    return target


def _authority(tmp_path: Path) -> tuple[Path, Path, str]:
    trusted = tmp_path / "trusted"
    trusted.mkdir()
    runtime = trusted / "task-authority.py"
    runtime.write_bytes(Path(task_authority.__file__).read_bytes())
    runtime.chmod(0o444)
    runtime_sha256 = hashlib.sha256(runtime.read_bytes()).hexdigest()
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
    return receipt, runtime, runtime_sha256


def _bd(tmp_path: Path, issue: dict[str, object]) -> tuple[Path, str]:
    executable = tmp_path / "trusted" / "bd"
    payload = json.dumps([issue], sort_keys=True, separators=(",", ":"))
    executable.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "if sys.argv[1:] == ['--version']:\n"
        "    print('bd version 1.1.0')\n"
        "    raise SystemExit(0)\n"
        "expected = ['--json', '--readonly', '-C']\n"
        "if sys.argv[1:4] != expected or sys.argv[5:] != ['show', '--id', "
        + repr(str(issue.get("id")))
        + "]:\n"
        "    raise SystemExit(64)\n"
        f"sys.stdout.write({payload!r})\n",
        encoding="utf-8",
    )
    executable.chmod(0o555)
    return executable, hashlib.sha256(executable.read_bytes()).hexdigest()


def _configure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    issue: dict[str, object] | None = None,
) -> dict[str, str]:
    receipt, runtime, runtime_sha256 = _authority(tmp_path)
    configured_issue: dict[str, object] = {
        "id": BEAD_ID,
        "title": "Implement authoritative workflow bridge",
        "status": "in_progress",
        "issue_type": "task",
        "assignee": "aegis-worker-17",
        "metadata": {
            "branch": f"polecat/{BEAD_ID}",
            "work_dir": str((tmp_path / "target").resolve()),
        },
        "ephemeral": False,
        "no_history": False,
    }
    configured_issue.update(issue or {})
    configured_id = str(configured_issue.get("id"))
    if not (issue and "metadata" in issue):
        configured_issue["metadata"] = {
            "branch": f"polecat/{configured_id}",
            "work_dir": str((tmp_path / "target").resolve()),
        }
    executable, bd_sha256 = _bd(
        tmp_path,
        configured_issue,
    )
    values = {
        "AEGIS_TASK_AUTHORITY_FILE": str(receipt),
        "AEGIS_TASK_AUTHORITY_RUNTIME_FILE": str(runtime),
        "AEGIS_TASK_AUTHORITY_RUNTIME_SHA256": runtime_sha256,
        "AEGIS_BD_EXECUTABLE": str(executable),
        "AEGIS_BD_SHA256": bd_sha256,
        "GC_RIG": "aegis",
        "GC_BEADS_PREFIX": "ags",
        "BEADS_DOLT_SERVER_DATABASE": "aegis_beads",
        "GC_DOLT_DATABASE": "aegis_beads",
        "BEADS_ACTOR": "aegis-worker-17",
        "GC_SESSION_NAME": "aegis-worker-17",
        "GC_AGENT": "aegis-worker-17",
        # A convoy/molecule id must be irrelevant to the explicit work-Bead path.
        "GC_BEAD_ID": "ags-convoy-not-the-work-bead",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    return values


def test_kickoff_bead_builds_exact_authority_bound_scaffold_and_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = _target(tmp_path)
    values = _configure(monkeypatch, tmp_path)
    taskmaster = target / ".taskmaster" / "tasks" / "tasks.json"
    taskmaster.parent.mkdir(parents=True)
    taskmaster.write_bytes(b'{"rollback":"must remain byte-identical"}\n')
    before_taskmaster = taskmaster.read_bytes()

    report = installer.kickoff_bead(
        target,
        bead_id=BEAD_ID,
        source_root=REPO_ROOT,
    )
    current = json.loads(
        (target / installer.AEGIS_CURRENT_WORK_REL).read_text(encoding="utf-8")
    )

    assert report["status"] == "started"
    assert current["task"] == {
        "id": BEAD_ID,
        "slug": "implement-authoritative-workflow-bridge",
        "title": "Implement authoritative workflow bridge",
        "status": "in-progress",
        "source": "beads",
        "authority_status": "in_progress",
        "issue_type": "task",
        "assignee": "aegis-worker-17",
    }
    assert current["authority"] == {
        "mode": "beads",
        "rig": "aegis",
        "beads_prefix": "ags",
        "database": "aegis_beads",
        "receipt_generation": 2,
        "receipt_sha256": report["authority"]["receipt_sha256"],
    }
    assert current["beads"] == {
        "issue_id": BEAD_ID,
        "issue_status": "in_progress",
        "bd_executable": values["AEGIS_BD_EXECUTABLE"],
        "bd_sha256": values["AEGIS_BD_SHA256"],
        "command_mode": "--json --readonly -C <repo> show --id <bead>",
        "issue_type": "task",
        "assignee": "aegis-worker-17",
        "assignee_identity_source": "BEADS_ACTOR",
        "metadata_branch": f"polecat/{BEAD_ID}",
        "metadata_work_dir": str(target.resolve()),
        "ephemeral": False,
        "no_history": False,
    }
    assert current["branch"] == {
        "before": f"polecat/{BEAD_ID}",
        "current": f"polecat/{BEAD_ID}",
        "action": "preserved_gas_city_polecat_branch",
        "created": False,
        "requires_task_id": False,
    }
    assert f"-bead-{BEAD_ID}-" in current["paths"]["work_tracking"]
    assert (target / current["paths"]["session"]).is_file()
    assert (target / current["paths"]["plan"]).is_file()
    assert taskmaster.read_bytes() == before_taskmaster
    assert (
        subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=target,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
        == f"polecat/{BEAD_ID}"
    )

    second = installer.kickoff_bead(
        target,
        bead_id=BEAD_ID,
        source_root=REPO_ROOT,
    )
    assert second["status"] == "already_started"
    assert second["idempotent"] is True
    assert taskmaster.read_bytes() == before_taskmaster


def test_opaque_bead_scaffold_supports_log_strict_branch_check_and_closeout_archive_shape(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = _target(tmp_path)
    _configure(monkeypatch, tmp_path)
    installer.kickoff_bead(target, bead_id=BEAD_ID, source_root=REPO_ROOT)
    current = json.loads(
        (target / installer.AEGIS_CURRENT_WORK_REL).read_text(encoding="utf-8")
    )

    logged = installer.log_work(
        target,
        handler="aegis:test",
        evidence=current["paths"]["work_tracking"] + "/FINDINGS.md",
        note="Confirmed opaque Bead scope",
        plan_step="plan-step-scope",
        plan_status="completed",
        event_class="scope",
    )
    checks, _ = installer._strict_current_work_checks(target)
    branch_check = next(
        check for check in checks if check["id"] == "workflow.branch_task_alignment"
    )

    assert logged["status"] == "logged"
    assert logged["entry"]["w"].startswith(f"task{BEAD_ID}-")
    assert branch_check["status"] == "pass"
    assert branch_check["details"]["branch_task_id"] == BEAD_ID
    assert installer._is_task_active_work_tracking_rel(current["paths"]["work_tracking"])


def test_generated_bead_envelope_passes_the_installed_readiness_contract(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = _target(tmp_path)
    _configure(monkeypatch, tmp_path)
    installer.kickoff_bead(target, bead_id=BEAD_ID, source_root=REPO_ROOT)
    readiness = target / ".claude" / "scripts" / "readiness.sh"
    readiness.parent.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / ".claude" / "scripts" / "readiness.sh", readiness)

    result = subprocess.run(
        ["bash", str(readiness), "--all", "--root", str(target)],
        cwd=target,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "STATE: READY" in result.stdout
    assert f"authoritative Bead {BEAD_ID} is in_progress" in result.stdout
    assert "current work is bound to authority receipt generation 2" in result.stdout


def test_both_cli_surfaces_expose_the_same_strict_bead_kickoff(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = _target(tmp_path)
    _configure(monkeypatch, tmp_path)
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    commands = (
        [
            sys.executable,
            "-m",
            "aegis_foundation.cli",
            "kickoff",
            "--target-dir",
            str(target),
            "--bead",
            BEAD_ID,
        ],
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "codex-task"),
            "aegis",
            "kickoff",
            "--target-dir",
            str(target),
            "--bead",
            BEAD_ID,
        ],
    )

    results = [
        subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        for command in commands
    ]

    assert [result.returncode for result in results] == [0, 0], [
        result.stderr for result in results
    ]
    payloads = [json.loads(result.stdout) for result in results]
    assert [payload["status"] for payload in payloads] == ["started", "already_started"]
    assert all(payload["task"]["id"] == BEAD_ID for payload in payloads)
    assert all(payload["authority"]["receipt_generation"] == 2 for payload in payloads)


@pytest.mark.parametrize("status", ["pending", "closed", "done", "active"])
def test_kickoff_bead_rejects_any_issue_not_exactly_in_progress(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    status: str,
) -> None:
    target = _target(tmp_path)
    _configure(
        monkeypatch,
        tmp_path,
        issue={"id": BEAD_ID, "title": "Unsafe status", "status": status},
    )

    with pytest.raises(installer.AegisError, match="expected 'in_progress'"):
        installer.kickoff_bead(target, bead_id=BEAD_ID, source_root=REPO_ROOT)
    assert not (target / installer.AEGIS_CURRENT_WORK_REL).exists()


@pytest.mark.parametrize(
    ("bead_id", "title", "message"),
    [
        ("ags-bad/id", "Safe title", "safe opaque Bead ID"),
        ("other-17", "Safe title", "authoritative Aegis prefix"),
        (BEAD_ID, " leading whitespace", "edge whitespace"),
        (BEAD_ID, "line one\nline two", "control character"),
    ],
)
def test_kickoff_bead_rejects_unsafe_ids_and_authoritative_fields(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    bead_id: str,
    title: str,
    message: str,
) -> None:
    branch_id = bead_id if "/" not in bead_id else BEAD_ID
    target = _target(tmp_path, bead_id=branch_id)
    _configure(
        monkeypatch,
        tmp_path,
        issue={"id": bead_id, "title": title, "status": "in_progress"},
    )

    with pytest.raises(installer.AegisError, match=message):
        installer.kickoff_bead(target, bead_id=bead_id, source_root=REPO_ROOT)


def test_kickoff_bead_rejects_convoy_or_wrong_workspace_branch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = _target(tmp_path, bead_id="ags-different-work")
    _configure(monkeypatch, tmp_path)

    with pytest.raises(installer.AegisError, match=f"polecat/{BEAD_ID}"):
        installer.kickoff_bead(target, bead_id=BEAD_ID, source_root=REPO_ROOT)
    assert not (target / installer.AEGIS_CURRENT_WORK_REL).exists()


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"assignee": "aegis-other-worker"}, "current Gas City work identity"),
        ({"issue_type": "epic"}, "source-work 'task'"),
        ({"issue_type": "molecule"}, "source-work 'task'"),
        ({"issue_type": "wisp"}, "source-work 'task'"),
        ({"ephemeral": True}, "infrastructure/wisp records"),
        (
            {
                "metadata": {
                    "branch": "polecat/ags-some-other-work",
                    "work_dir": "TARGET",
                }
            },
            "metadata.branch",
        ),
        (
            {
                "metadata": {
                    "branch": f"polecat/{BEAD_ID}",
                    "work_dir": "PARENT",
                }
            },
            "canonical target root",
        ),
    ],
)
def test_kickoff_bead_rejects_wrong_owner_or_non_work_workspace_binding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    override: dict[str, object],
    message: str,
) -> None:
    target = _target(tmp_path)
    normalized = json.loads(json.dumps(override))
    metadata = normalized.get("metadata")
    if isinstance(metadata, dict):
        if metadata.get("work_dir") == "TARGET":
            metadata["work_dir"] = str(target.resolve())
        elif metadata.get("work_dir") == "PARENT":
            metadata["work_dir"] = str(target.parent.resolve())
    _configure(monkeypatch, tmp_path, issue=normalized)

    with pytest.raises(installer.AegisError, match=message):
        installer.kickoff_bead(target, bead_id=BEAD_ID, source_root=REPO_ROOT)
    assert not (target / installer.AEGIS_CURRENT_WORK_REL).exists()


def test_kickoff_bead_uses_documented_assignee_precedence_and_rejects_unsafe_actor(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = _target(tmp_path)
    _configure(monkeypatch, tmp_path)
    monkeypatch.setenv("BEADS_ACTOR", " unsafe actor ")

    with pytest.raises(installer.AegisError, match="BEADS_ACTOR has an unsafe value"):
        installer.kickoff_bead(target, bead_id=BEAD_ID, source_root=REPO_ROOT)


def test_kickoff_bead_fails_closed_for_implicit_or_tampered_authority_and_bd(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = _target(tmp_path)
    values = _configure(monkeypatch, tmp_path)

    monkeypatch.delenv("AEGIS_TASK_AUTHORITY_FILE")
    with pytest.raises(installer.AegisError, match="implicit Taskmaster authority"):
        installer.kickoff_bead(target, bead_id=BEAD_ID, source_root=REPO_ROOT)

    monkeypatch.setenv("AEGIS_TASK_AUTHORITY_FILE", values["AEGIS_TASK_AUTHORITY_FILE"])
    monkeypatch.setenv("AEGIS_TASK_AUTHORITY_RUNTIME_SHA256", "0" * 64)
    with pytest.raises(installer.AegisError, match="runtime SHA-256"):
        installer.kickoff_bead(target, bead_id=BEAD_ID, source_root=REPO_ROOT)

    monkeypatch.setenv(
        "AEGIS_TASK_AUTHORITY_RUNTIME_SHA256",
        values["AEGIS_TASK_AUTHORITY_RUNTIME_SHA256"],
    )
    monkeypatch.setenv("AEGIS_BD_SHA256", "f" * 64)
    with pytest.raises(installer.AegisError, match="pinned bd SHA-256"):
        installer.kickoff_bead(target, bead_id=BEAD_ID, source_root=REPO_ROOT)


def test_kickoff_bead_rejects_another_active_task_without_rewriting_it(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    target = _target(tmp_path)
    _configure(monkeypatch, tmp_path)
    current = target / installer.AEGIS_CURRENT_WORK_REL
    current.parent.mkdir(parents=True, exist_ok=True)
    original = {
        "status": "in-progress",
        "task": {"id": "ags-other", "slug": "other", "title": "Other"},
    }
    current.write_text(json.dumps(original) + "\n", encoding="utf-8")

    with pytest.raises(installer.AegisError, match="already in progress"):
        installer.kickoff_bead(target, bead_id=BEAD_ID, source_root=REPO_ROOT)
    assert json.loads(current.read_text(encoding="utf-8")) == original
