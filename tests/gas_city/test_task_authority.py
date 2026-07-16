from __future__ import annotations

import dataclasses
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest

from aegis_foundation import task_authority


RIG = "aegis"
PREFIX = "ags"
DATABASE = "aegis_beads"


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


@pytest.fixture
def evidence() -> task_authority.TaskAuthorityEvidence:
    return task_authority.TaskAuthorityEvidence(
        taskmaster_snapshot_sha256=_digest("taskmaster snapshot"),
        migration_report_sha256=_digest("migration report"),
        backup_restore_report_sha256=_digest("backup restore report"),
    )


def _receipt_path(tmp_path: Path) -> Path:
    return tmp_path / "authority" / "aegis.json"


def _initialize(
    tmp_path: Path,
    evidence: task_authority.TaskAuthorityEvidence,
) -> tuple[Path, task_authority.TaskAuthorityReceipt]:
    path = _receipt_path(tmp_path)
    receipt = task_authority.initialize_taskmaster_authority(
        path,
        rig=RIG,
        beads_prefix=PREFIX,
        database=DATABASE,
        evidence=evidence,
        activated_at="2026-07-15T18:00:00Z",
    )
    return path, receipt


def _load(path: Path) -> task_authority.TaskAuthorityReceipt:
    return task_authority.load_authority_receipt(
        path,
        expected_rig=RIG,
        expected_beads_prefix=PREFIX,
        expected_database=DATABASE,
    )


def test_absent_environment_is_the_only_legacy_taskmaster_fallback(
    tmp_path: Path,
) -> None:
    # Store presence is deliberately irrelevant to selection.
    (tmp_path / ".beads").mkdir()
    (tmp_path / ".taskmaster").mkdir()
    selected = task_authority.load_authority_from_environment({})

    assert selected.mode is task_authority.TaskAuthorityMode.TASKMASTER
    assert selected.explicit is False
    assert selected.receipt is None
    assert selected.receipt_path is None

    with pytest.raises(task_authority.TaskAuthorityError, match="absolute receipt path"):
        task_authority.load_authority_from_environment(
            {task_authority.TASK_AUTHORITY_ENV: ""}
        )
    with pytest.raises(task_authority.TaskAuthorityError, match="absolute path"):
        task_authority.load_authority_from_environment(
            {task_authority.TASK_AUTHORITY_ENV: "relative.json"},
            expected_rig=RIG,
            expected_beads_prefix=PREFIX,
            expected_database=DATABASE,
        )
    with pytest.raises(task_authority.TaskAuthorityError, match="requires expected"):
        task_authority.load_authority_from_environment(
            {task_authority.TASK_AUTHORITY_ENV: str(tmp_path / "missing.json")}
        )


def test_initial_receipt_is_private_canonical_and_exact(
    tmp_path: Path,
    evidence: task_authority.TaskAuthorityEvidence,
) -> None:
    path, receipt = _initialize(tmp_path, evidence)

    assert receipt.mode is task_authority.TaskAuthorityMode.TASKMASTER
    assert receipt.generation == 1
    assert receipt.previous_receipt_sha256 is None
    assert receipt.evidence == evidence
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
    assert path.read_bytes() == task_authority.receipt_bytes(receipt)

    selected = task_authority.load_authority_from_environment(
        {task_authority.TASK_AUTHORITY_ENV: str(path)},
        expected_rig=RIG,
        expected_beads_prefix=PREFIX,
        expected_database=DATABASE,
    )
    assert selected.explicit is True
    assert selected.mode is task_authority.TaskAuthorityMode.TASKMASTER
    assert selected.receipt == receipt
    assert selected.receipt_path == path

    with pytest.raises(task_authority.TaskAuthorityError, match="already exists"):
        task_authority.initialize_taskmaster_authority(
            path,
            rig=RIG,
            beads_prefix=PREFIX,
            database=DATABASE,
            evidence=evidence,
            activated_at="2026-07-15T18:00:01Z",
        )


def test_receipt_json_rejects_duplicate_unknown_and_noncanonical_content(
    tmp_path: Path,
    evidence: task_authority.TaskAuthorityEvidence,
) -> None:
    path, receipt = _initialize(tmp_path, evidence)
    mapping = task_authority.receipt_mapping(receipt)

    duplicate = task_authority.receipt_bytes(receipt).decode("utf-8").replace(
        '"rig":"aegis"',
        '"rig":"aegis","rig":"other"',
    )
    path.write_text(duplicate, encoding="utf-8")
    path.chmod(0o600)
    with pytest.raises(task_authority.TaskAuthorityError, match="duplicate JSON object key"):
        _load(path)

    mapping["unexpected"] = True
    path.write_text(
        json.dumps(mapping, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    path.chmod(0o600)
    with pytest.raises(task_authority.TaskAuthorityError, match="fields must be exact"):
        _load(path)

    mapping.pop("unexpected")
    path.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)
    with pytest.raises(task_authority.TaskAuthorityError, match="not canonical JSON"):
        _load(path)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("beads_prefix", "ags;rm", "beads_prefix must match"),
        ("database", "Aegis DB", "database must match"),
        ("activated_at", "2026-07-15T20:00:00+02:00", "ending in Z"),
        ("generation", True, "generation must be an integer"),
        ("taskmaster_snapshot_sha256", "A" * 64, "lowercase SHA-256"),
        ("migration_report_sha256", "not-a-digest", "lowercase SHA-256"),
        ("backup_restore_report_sha256", "f" * 63, "lowercase SHA-256"),
    ],
)
def test_receipt_fields_are_strict(
    tmp_path: Path,
    evidence: task_authority.TaskAuthorityEvidence,
    field: str,
    value: object,
    match: str,
) -> None:
    path, receipt = _initialize(tmp_path, evidence)
    mapping = task_authority.receipt_mapping(receipt)
    mapping[field] = value
    path.write_text(
        json.dumps(mapping, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    path.chmod(0o600)

    with pytest.raises(task_authority.TaskAuthorityError, match=match):
        _load(path)


def test_explicit_loader_requires_exact_rig_prefix_and_database(
    tmp_path: Path,
    evidence: task_authority.TaskAuthorityEvidence,
) -> None:
    path, _ = _initialize(tmp_path, evidence)
    environment = {task_authority.TASK_AUTHORITY_ENV: str(path)}

    for values, match in (
        (("other", PREFIX, DATABASE), "rig mismatch"),
        ((RIG, "other", DATABASE), "prefix mismatch"),
        ((RIG, PREFIX, "other"), "database mismatch"),
    ):
        with pytest.raises(task_authority.TaskAuthorityError, match=match):
            task_authority.load_authority_from_environment(
                environment,
                expected_rig=values[0],
                expected_beads_prefix=values[1],
                expected_database=values[2],
            )


def test_receipt_must_be_owner_only_regular_and_non_symlink(
    tmp_path: Path,
    evidence: task_authority.TaskAuthorityEvidence,
) -> None:
    path, receipt = _initialize(tmp_path, evidence)

    path.chmod(0o640)
    with pytest.raises(task_authority.TaskAuthorityError, match="exactly 0600"):
        _load(path)

    path.chmod(0o600)
    target = path.with_name("target.json")
    path.replace(target)
    path.symlink_to(target)
    with pytest.raises(task_authority.TaskAuthorityError, match="symlink"):
        _load(path)

    path.unlink()
    path.mkdir(mode=0o700)
    with pytest.raises(task_authority.TaskAuthorityError, match="regular non-symlink"):
        _load(path)

    assert target.read_bytes() == task_authority.receipt_bytes(receipt)


def test_receipt_rejects_fifo_and_symlinked_parent_components(
    tmp_path: Path,
    evidence: task_authority.TaskAuthorityEvidence,
) -> None:
    path, _ = _initialize(tmp_path, evidence)
    path.unlink()
    os.mkfifo(path, mode=0o600)
    fifo_probe = """
from pathlib import Path
import sys
from aegis_foundation import task_authority
try:
    task_authority.load_authority_receipt(
        Path(sys.argv[1]),
        expected_rig='aegis',
        expected_beads_prefix='ags',
        expected_database='aegis_beads',
    )
except task_authority.TaskAuthorityError:
    raise SystemExit(0)
raise SystemExit(1)
"""
    completed = subprocess.run(
        [sys.executable, "-c", fifo_probe, str(path)],
        cwd=Path(__file__).parents[2],
        check=False,
        timeout=2,
    )
    assert completed.returncode == 0

    path.unlink()
    real_parent = tmp_path / "real-authority"
    real_path = real_parent / "aegis.json"
    task_authority.initialize_taskmaster_authority(
        real_path,
        rig=RIG,
        beads_prefix=PREFIX,
        database=DATABASE,
        evidence=evidence,
        activated_at="2026-07-15T18:00:00Z",
    )
    alias_parent = tmp_path / "authority-alias"
    alias_parent.symlink_to(real_parent, target_is_directory=True)
    with pytest.raises(task_authority.TaskAuthorityError, match="real directories"):
        _load(alias_parent / "aegis.json")


def test_explicit_path_and_json_failures_are_normalized(
    tmp_path: Path,
    evidence: task_authority.TaskAuthorityEvidence,
) -> None:
    expected = {
        "expected_rig": RIG,
        "expected_beads_prefix": PREFIX,
        "expected_database": DATABASE,
    }
    with pytest.raises(task_authority.TaskAuthorityError, match="does not exist"):
        task_authority.load_authority_from_environment(
            {task_authority.TASK_AUTHORITY_ENV: str(tmp_path / "missing.json")},
            **expected,
        )
    with pytest.raises(task_authority.TaskAuthorityError, match="NUL byte"):
        task_authority.load_authority_from_environment(
            {task_authority.TASK_AUTHORITY_ENV: f"{tmp_path}/bad\0receipt.json"},
            **expected,
        )

    path, receipt = _initialize(tmp_path, evidence)
    mapping = task_authority.receipt_mapping(receipt)
    mapping["mode"] = "automatic"
    path.write_text(
        json.dumps(mapping, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    path.chmod(0o600)
    with pytest.raises(task_authority.TaskAuthorityError, match="taskmaster or beads"):
        _load(path)

    mapping["mode"] = "taskmaster"
    mapping["activated_at"] = "2026-02-30T18:00:00Z"
    path.write_text(
        json.dumps(mapping, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    path.chmod(0o600)
    with pytest.raises(task_authority.TaskAuthorityError, match="not a valid UTC"):
        _load(path)

    huge_generation = task_authority.receipt_bytes(receipt).replace(
        b'"generation":1',
        b'"generation":' + (b"9" * 5000),
    )
    path.write_bytes(huge_generation)
    path.chmod(0o600)
    with pytest.raises(task_authority.TaskAuthorityError, match="not valid JSON"):
        _load(path)


def test_transitions_are_generation_chained_and_evidence_is_immutable(
    tmp_path: Path,
    evidence: task_authority.TaskAuthorityEvidence,
) -> None:
    path, initial = _initialize(tmp_path, evidence)
    initial_bytes = path.read_bytes()

    beads = task_authority.transition_authority(
        path,
        target_mode=task_authority.TaskAuthorityMode.BEADS,
        expected_generation=1,
        expected_rig=RIG,
        expected_beads_prefix=PREFIX,
        expected_database=DATABASE,
        expected_evidence=evidence,
        activated_at="2026-07-15T18:01:00Z",
    )
    assert beads.mode is task_authority.TaskAuthorityMode.BEADS
    assert beads.generation == 2
    assert beads.previous_receipt_sha256 == hashlib.sha256(initial_bytes).hexdigest()
    assert beads.evidence == initial.evidence
    assert _load(path) == beads

    taskmaster = task_authority.transition_authority(
        path,
        target_mode=task_authority.TaskAuthorityMode.TASKMASTER,
        expected_generation=2,
        expected_rig=RIG,
        expected_beads_prefix=PREFIX,
        expected_database=DATABASE,
        expected_evidence=evidence,
        activated_at="2026-07-15T18:02:00.123456Z",
    )
    assert taskmaster.mode is task_authority.TaskAuthorityMode.TASKMASTER
    assert taskmaster.generation == 3
    assert taskmaster.previous_receipt_sha256 == task_authority.receipt_sha256(beads)
    assert taskmaster.evidence == initial.evidence

    with pytest.raises(dataclasses.FrozenInstanceError):
        taskmaster.generation = 4  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        taskmaster.evidence.migration_report_sha256 = "0" * 64  # type: ignore[misc]


def test_transition_rejects_stale_same_mode_time_and_evidence_changes(
    tmp_path: Path,
    evidence: task_authority.TaskAuthorityEvidence,
) -> None:
    path, initial = _initialize(tmp_path, evidence)
    common = {
        "path": path,
        "expected_rig": RIG,
        "expected_beads_prefix": PREFIX,
        "expected_database": DATABASE,
        "expected_evidence": evidence,
        "activated_at": "2026-07-15T18:01:00Z",
    }

    with pytest.raises(task_authority.TaskAuthorityError, match="invalid authority transition"):
        task_authority.transition_authority(
            target_mode=task_authority.TaskAuthorityMode.TASKMASTER,
            expected_generation=1,
            **common,
        )
    with pytest.raises(task_authority.TaskAuthorityError, match="generation mismatch"):
        task_authority.transition_authority(
            target_mode=task_authority.TaskAuthorityMode.BEADS,
            expected_generation=2,
            **common,
        )
    with pytest.raises(task_authority.TaskAuthorityError, match="must increase"):
        task_authority.transition_authority(
            target_mode=task_authority.TaskAuthorityMode.BEADS,
            expected_generation=1,
            **{**common, "activated_at": initial.activated_at},
        )

    changed_evidence = task_authority.TaskAuthorityEvidence(
        taskmaster_snapshot_sha256=evidence.taskmaster_snapshot_sha256,
        migration_report_sha256="0" * 64,
        backup_restore_report_sha256=evidence.backup_restore_report_sha256,
    )
    with pytest.raises(task_authority.TaskAuthorityError, match="digests do not match"):
        task_authority.transition_authority(
            target_mode=task_authority.TaskAuthorityMode.BEADS,
            expected_generation=1,
            **{**common, "expected_evidence": changed_evidence},
        )

    assert _load(path) == initial


def test_transition_does_not_delete_or_infer_task_stores(
    tmp_path: Path,
    evidence: task_authority.TaskAuthorityEvidence,
) -> None:
    taskmaster_store = tmp_path / "repo" / ".taskmaster" / "tasks" / "tasks.json"
    beads_store = tmp_path / "city" / ".beads" / "store.marker"
    taskmaster_store.parent.mkdir(parents=True)
    beads_store.parent.mkdir(parents=True)
    taskmaster_store.write_bytes(b"taskmaster sentinel")
    beads_store.write_bytes(b"beads sentinel")
    path, _ = _initialize(tmp_path, evidence)

    task_authority.transition_authority(
        path,
        target_mode=task_authority.TaskAuthorityMode.BEADS,
        expected_generation=1,
        expected_rig=RIG,
        expected_beads_prefix=PREFIX,
        expected_database=DATABASE,
        expected_evidence=evidence,
        activated_at="2026-07-15T18:01:00Z",
    )

    assert taskmaster_store.read_bytes() == b"taskmaster sentinel"
    assert beads_store.read_bytes() == b"beads sentinel"
    assert os.path.lexists(path)


def test_failed_atomic_replacement_preserves_the_current_generation(
    tmp_path: Path,
    evidence: task_authority.TaskAuthorityEvidence,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path, initial = _initialize(tmp_path, evidence)
    initial_bytes = path.read_bytes()

    def fail_replace(*args: object, **kwargs: object) -> None:
        raise OSError("simulated replacement failure")

    monkeypatch.setattr(task_authority.os, "replace", fail_replace)
    with pytest.raises(task_authority.TaskAuthorityError, match="atomically write"):
        task_authority.transition_authority(
            path,
            target_mode=task_authority.TaskAuthorityMode.BEADS,
            expected_generation=1,
            expected_rig=RIG,
            expected_beads_prefix=PREFIX,
            expected_database=DATABASE,
            expected_evidence=evidence,
            activated_at="2026-07-15T18:01:00Z",
        )

    assert path.read_bytes() == initial_bytes
    assert _load(path) == initial


def test_temporary_permission_failure_is_cleaned_up(
    tmp_path: Path,
    evidence: task_authority.TaskAuthorityEvidence,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _receipt_path(tmp_path)

    def fail_fchmod(descriptor: int, mode: int) -> None:
        raise OSError("simulated permission failure")

    monkeypatch.setattr(task_authority.os, "fchmod", fail_fchmod)
    with pytest.raises(task_authority.TaskAuthorityError, match="secure a temporary"):
        task_authority.initialize_taskmaster_authority(
            path,
            rig=RIG,
            beads_prefix=PREFIX,
            database=DATABASE,
            evidence=evidence,
            activated_at="2026-07-15T18:00:00Z",
        )

    assert not path.exists()
    assert sorted(item.name for item in path.parent.iterdir()) == ["aegis.json.lock"]


def test_post_commit_sync_failure_reports_the_live_generation(
    tmp_path: Path,
    evidence: task_authority.TaskAuthorityEvidence,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path, _ = _initialize(tmp_path, evidence)
    real_fsync = task_authority.os.fsync

    def fail_directory_sync(descriptor: int) -> None:
        if stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise OSError("simulated directory sync failure")
        real_fsync(descriptor)

    monkeypatch.setattr(task_authority.os, "fsync", fail_directory_sync)
    with pytest.raises(task_authority.TaskAuthorityCommittedError) as captured:
        task_authority.transition_authority(
            path,
            target_mode=task_authority.TaskAuthorityMode.BEADS,
            expected_generation=1,
            expected_rig=RIG,
            expected_beads_prefix=PREFIX,
            expected_database=DATABASE,
            expected_evidence=evidence,
            activated_at="2026-07-15T18:01:00Z",
        )

    assert captured.value.receipt.mode is task_authority.TaskAuthorityMode.BEADS
    assert captured.value.receipt.generation == 2
    assert _load(path) == captured.value.receipt
