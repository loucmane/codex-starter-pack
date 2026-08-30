"""Fail-closed fixtures for the generic frozen evidence workflow."""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = REPO_ROOT / "plugins" / "gas-city-workflow" / "scripts" / "evidence"
sys.path.insert(0, str(EVIDENCE))

audit_module = importlib.import_module("audit_blind_bundle")
compare_module = importlib.import_module("compare_review_lanes")
freeze_module = importlib.import_module("freeze_evidence_run")
report_module = importlib.import_module("validate_review_report")
validate_module = importlib.import_module("validate_evidence_run")

EvidenceError = validate_module.EvidenceError


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    subject = tmp_path / "subject"
    subject.mkdir()
    subprocess.run(["git", "init", "-b", "codex/ga-fixture-evidence"], cwd=subject, check=True, capture_output=True)
    _write_json(
        subject / ".gas-city-workflow.json",
        {
            "schema": "gas-city-workflow.project.v1",
            "id": "fixture",
            "repository": "fixture/evidence",
            "rig": "fixture",
            "workflow_authority": "beads",
            "workflow_profile": "beads-with-aegis-evidence",
        },
    )
    (subject / "AGENTS.md").write_text("# fixture\n", encoding="utf-8")
    (subject / "CLAUDE.md").write_text("# fixture\n", encoding="utf-8")
    active = subject / "docs" / "ai" / "work-tracking" / "active" / "fixture-ACTIVE"
    active.mkdir(parents=True)
    (active / "TRACKER.md").write_text("**Status**: ACTIVE\n", encoding="utf-8")
    plan = subject / "plans" / "fixture.md"
    plan.parent.mkdir()
    plan.write_text("# plan\n", encoding="utf-8")
    (plan.parent / "current").symlink_to(plan.name)
    session = subject / "sessions" / "2026" / "08" / "fixture.md"
    session.parent.mkdir(parents=True)
    session.write_text("# session\n", encoding="utf-8")
    (subject / "sessions" / "current").symlink_to(session.relative_to(subject / "sessions"))

    assets = subject / "evidence"
    assets.mkdir()
    (assets / "builder.py").write_text("# project-owned builder\n", encoding="utf-8")
    (assets / "prompt.md").write_text("Review the frozen candidate.\n", encoding="utf-8")
    (assets / "rubric.md").write_text("Report evidence, not a verdict.\n", encoding="utf-8")
    report_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["schema", "run_id", "lane_id", "candidate_id", "status", "summary", "findings"],
        "properties": {
            "schema": {"const": "gas-city-evidence-report.v1"},
            "run_id": {"type": "string"},
            "lane_id": {"const": "blind-quality"},
            "candidate_id": {"type": "string"},
            "status": {"const": "evidence-only"},
            "summary": {"type": "string"},
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "evidence"],
                    "properties": {"id": {"type": "string"}, "evidence": {"type": "string"}},
                },
            },
        },
    }
    _write_json(assets / "report.schema.json", report_schema)
    profile = {
        "schema": "gas-city-evidence-profile.v1",
        "id": "fixture-shadow-v1",
        "project": {"id": "fixture", "rig": "fixture"},
        "lanes": [
            {
                "id": "blind-quality",
                "bundle_builder": "evidence/builder.py",
                "prompt": "evidence/prompt.md",
                "rubric": "evidence/rubric.md",
                "report_schema": "evidence/report.schema.json",
                "declared_bundle_files": ["candidate.json", "instructions.md"],
                "allowed_outputs": ["report.json"],
                "forbidden_patterns": ["answer_key", "rationale", "generator_meta", ".git"],
            }
        ],
    }
    profile_path = assets / "profile.json"
    _write_json(profile_path, profile)
    _write_json(subject / "authoritative.json", {"winner": "candidate-1"})
    _write_json(subject / "fable-input.json", {"candidate": "candidate-1", "full_visibility": True})
    subprocess.run(["git", "add", "."], cwd=subject, check=True)
    subprocess.run(
        [
            "git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test",
            "-c", "commit.gpgsign=false", "commit", "-m", "fixture",
        ],
        cwd=subject,
        check=True,
        capture_output=True,
    )

    external = tmp_path / "external"
    external.mkdir()
    _write_json(external / "parsed.json", {"source": "frozen"})
    run_root = tmp_path / "run-001"
    run_root.mkdir()
    request_path = run_root / "request.json"
    envelope_path = run_root / "authorization.json"
    bundle = run_root / "lanes" / "blind-quality" / "bundle"
    reports = run_root / "lanes" / "blind-quality" / "reports"
    request = {
        "schema": "gas-city-evidence-freeze-request.v1",
        "run_id": "run-001",
        "created_at": "2026-08-30T12:00:00Z",
        "parent_bead": "ga-fixture",
        "mode": "shadow",
        "repair": False,
        "supersedes": None,
        "subject_root": subject.as_posix(),
        "candidates": ["candidate-1"],
        "external_inputs": [{"path": external.as_posix(), "reason": "untracked parsed input"}],
        "fable_inputs": [(subject / "fable-input.json").as_posix()],
        "authoritative_outputs": [(subject / "authoritative.json").as_posix()],
        "lane_io": {"blind-quality": {"bundle_dir": bundle.as_posix(), "report_dir": reports.as_posix()}},
        "authorization_envelope": envelope_path.as_posix(),
        "run_root": run_root.as_posix(),
    }
    _write_json(request_path, request)
    envelope = {
        "schema": "gas-city-evidence-authorization-envelope.v1",
        "request_sha256": validate_module.canonical_sha256(request),
        "authorized_at": "2026-08-30T12:00:01Z",
        "expires_at": "2035-08-30T12:00:00Z",
        "scope": {
            "project_id": "fixture",
            "rig": "fixture",
            "parent_bead": "ga-fixture",
            "run_id": "run-001",
            "mode": "shadow",
            "max_workers": 1,
            "allowed_write_roots": [reports.as_posix()],
            "excluded_actions": [
                "push", "merge", "deploy", "publish", "rig-lifecycle", "authoritative-output-write"
            ],
        },
        "verbatim_authorization": "One bounded report-only shadow review; no project mutation.",
    }
    _write_json(envelope_path, envelope)
    registry = tmp_path / "projects.json"
    _write_json(registry, {"schema": "gas-city-workflow.project-registry.v1", "projects": []})
    monkeypatch.setattr(
        freeze_module,
        "load_bead",
        lambda runner, context, bead_id: {"id": bead_id, "status": "in_progress"},
    )
    manifest_path = run_root / "manifest.json"
    return locals()


def _freeze(values: dict[str, Any]) -> dict[str, Any]:
    return freeze_module.freeze(
        values["request_path"], values["profile_path"], values["manifest_path"], registry=values["registry"]
    )


def _bundle(values: dict[str, Any]) -> None:
    values["bundle"].mkdir(parents=True)
    _write_json(values["bundle"] / "candidate.json", {"id": "candidate-1", "text": "visible stem"})
    (values["bundle"] / "instructions.md").write_text("Use the frozen rubric.\n", encoding="utf-8")


def _report(values: dict[str, Any], *, candidate: str = "candidate-1") -> Path:
    values["reports"].mkdir(parents=True, exist_ok=True)
    path = values["reports"] / "report.json"
    _write_json(
        path,
        {
            "schema": "gas-city-evidence-report.v1",
            "run_id": "run-001",
            "lane_id": "blind-quality",
            "candidate_id": candidate,
            "status": "evidence-only",
            "summary": "One evidence-bearing observation.",
            "findings": [{"id": "clarity-1", "evidence": "The stem is independently understandable."}],
        },
    )
    return path


def test_freeze_validate_and_reject_drift_overwrite_and_authoritative_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = _fixture(tmp_path, monkeypatch)
    manifest = _freeze(values)
    assert manifest["mode"] == "shadow"
    assert validate_module.validate_manifest(values["manifest_path"], registry=values["registry"])["run_id"] == "run-001"
    with pytest.raises(EvidenceError, match="already exists"):
        _freeze(values)

    values["external"].joinpath("parsed.json").write_text('{"source":"drift"}\n', encoding="utf-8")
    with pytest.raises(EvidenceError, match="external input inventory drift"):
        validate_module.validate_manifest(values["manifest_path"], registry=values["registry"])

    values["profile_path"].write_text(values["profile_path"].read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(EvidenceError, match="profile digest drift"):
        validate_module.validate_manifest(values["manifest_path"], registry=values["registry"])

    request = dict(values["request"])
    request["mode"] = "authoritative"
    with pytest.raises(EvidenceError, match="authoritative"):
        validate_module.validate_request(request)
    request = dict(values["request"])
    request["repair"] = True
    with pytest.raises(EvidenceError, match="supersedes"):
        validate_module.validate_request(request)


def test_freeze_rejects_dirty_subject_and_project_rig_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = _fixture(tmp_path, monkeypatch)
    (values["subject"] / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(EvidenceError, match="clean"):
        _freeze(values)
    (values["subject"] / "dirty.txt").unlink()
    profile = json.loads(values["profile_path"].read_text(encoding="utf-8"))
    profile["project"]["rig"] = "wrong-rig"
    _write_json(values["profile_path"], profile)
    subprocess.run(["git", "add", "evidence/profile.json"], cwd=values["subject"], check=True)
    subprocess.run(
        ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "-c", "commit.gpgsign=false", "commit", "-m", "mismatch"],
        cwd=values["subject"], check=True, capture_output=True,
    )
    with pytest.raises(EvidenceError, match="project/rig"):
        _freeze(values)


def test_blind_bundle_rejects_leakage_git_symlink_and_unauthorized_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = _fixture(tmp_path, monkeypatch)
    _freeze(values)
    _bundle(values)
    assert audit_module.audit(values["manifest_path"], "blind-quality", "pre-dispatch")["ok"] is True
    (values["bundle"] / "candidate.json").write_text('{"answer_key":"A"}\n', encoding="utf-8")
    with pytest.raises(EvidenceError, match="forbidden pattern"):
        audit_module.audit(values["manifest_path"], "blind-quality", "pre-dispatch")
    _write_json(values["bundle"] / "candidate.json", {"id": "candidate-1", "text": "visible stem"})
    (values["bundle"] / ".git").symlink_to(values["subject"] / ".git")
    with pytest.raises(EvidenceError, match="Git metadata or a symlink"):
        audit_module.audit(values["manifest_path"], "blind-quality", "pre-dispatch")
    (values["bundle"] / ".git").unlink()
    _report(values)
    (values["reports"] / "unauthorized.txt").write_text("not allowed\n", encoding="utf-8")
    with pytest.raises(EvidenceError, match="output inventory mismatch"):
        audit_module.audit(values["manifest_path"], "blind-quality", "post-collection")


def test_report_validation_and_sealed_comparison_are_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    values = _fixture(tmp_path, monkeypatch)
    _freeze(values)
    _bundle(values)
    report = _report(values)
    assert report_module.validate_report(values["manifest_path"], "blind-quality", report)["candidate_id"] == "candidate-1"
    _report(values, candidate="not-frozen")
    with pytest.raises(EvidenceError, match="outside the frozen set"):
        report_module.validate_report(values["manifest_path"], "blind-quality", report)
    report = _report(values)

    controller = values["run_root"] / "controller"
    controller.mkdir()
    fable = controller / "fable.json"
    _write_json(fable, {"summary": "full-visibility baseline", "findings": ["clarity-1"]})
    seal = controller / "01-seal.json"
    _write_json(
        seal,
        {
            "schema": "gas-city-evidence-controller-event.v1", "event": "seal", "run_id": "run-001",
            "parent_bead": "ga-fixture", "at": "2026-08-30T12:01:00Z",
            "payload": {"fable_report": fable.as_posix(), "sha256": validate_module.sha256_file(fable)},
        },
    )
    readback = controller / "02-readback.json"
    _write_json(
        readback,
        {
            "schema": "gas-city-evidence-controller-event.v1", "event": "fable-readback", "run_id": "run-001",
            "parent_bead": "ga-fixture", "at": "2026-08-30T12:02:00Z",
            "payload": {"seal_event_sha256": validate_module.sha256_file(seal), "fable_report_sha256": validate_module.sha256_file(fable), "confirmed_by": "Fable"},
        },
    )
    dispatch = controller / "03-dispatch.json"
    _write_json(
        dispatch,
        {
            "schema": "gas-city-evidence-controller-event.v1", "event": "dispatch", "run_id": "run-001",
            "parent_bead": "ga-fixture", "at": "2026-08-30T12:03:00Z",
            "payload": {"readback_event_sha256": validate_module.sha256_file(readback)},
        },
    )
    release = controller / "04-release.json"
    _write_json(
        release,
        {
            "schema": "gas-city-evidence-controller-event.v1", "event": "release", "run_id": "run-001",
            "parent_bead": "ga-fixture", "at": "2026-08-30T12:04:00Z",
            "payload": {"dispatch_event_sha256": validate_module.sha256_file(dispatch), "policy_attestation": "Fable did not independently access worker reports before release."},
        },
    )
    base = 2_000_000_000_000_000_000
    os.utime(dispatch, ns=(base, base))
    os.utime(report, ns=(base + 1, base + 1))
    os.utime(release, ns=(base + 2, base + 2))
    output = values["run_root"] / "comparison.json"
    result = compare_module.compare(
        values["manifest_path"], fable, seal, readback, dispatch, release,
        [("blind-quality", report)], output,
    )
    assert result["domain_verdict"] is None
    assert result["shared_finding_ids"] == ["clarity-1"]
    with pytest.raises(EvidenceError):
        compare_module.compare(
            values["manifest_path"], fable, seal, readback, dispatch,
            controller / "missing-release.json", [("blind-quality", report)],
            values["run_root"] / "interrupted.json",
        )
