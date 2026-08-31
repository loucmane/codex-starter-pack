"""Deterministic cross-project workflow continuity report tests."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "plugins" / "gas-city-workflow" / "scripts"


def _load(name: str):
    module_name = f"gas_city_workflow_{name}_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def _bead(
    bead_id: str,
    status: str,
    *,
    title: str | None = None,
    issue_type: str = "task",
    labels: list[str] | None = None,
    metadata: dict[str, object] | None = None,
    dependencies: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "id": bead_id,
        "title": title or bead_id,
        "status": status,
        "issue_type": issue_type,
        "labels": labels or [],
        "metadata": metadata or {},
        "dependencies": dependencies or [],
    }


def _project(project_id: str, beads: list[dict[str, object]]) -> dict[str, object]:
    return {
        "id": project_id,
        "root": f"/workspace/{project_id}",
        "repository": f"fixture/{project_id}",
        "rig": project_id,
        "workflow_profile": "beads-with-aegis-evidence",
        "beads": beads,
        "aegis": {"active_trackers": []},
        "git": {"branches": [], "worktrees": [], "open_prs": []},
        "runtime": {"transactions": [], "receipts": []},
        "obsidian": {
            "registered": True,
            "registry_project_id": project_id,
            "vault_status": "current",
            "live_index_status": "confirmed",
        },
        "followups": [],
    }


def _snapshot(projects: list[dict[str, object]]) -> dict[str, object]:
    ledgers: dict[str, list[dict[str, object]]] = {}
    projected_projects = []
    for project in projects:
        projected = dict(project)
        beads = projected.pop("beads")
        rig = str(projected["rig"])
        if rig in ledgers:
            assert ledgers[rig] == beads
        else:
            ledgers[rig] = beads
        projected_projects.append(projected)
    return {
        "schema": "gas-city-workflow.continuity-snapshot.v1",
        "registry_sha256": "a" * 64,
        "ledgers": [
            {"rig": rig, "beads": ledgers[rig]}
            for rig in sorted(ledgers)
        ],
        "projects": projected_projects,
    }


def test_report_classifies_all_work_states_and_uses_one_next_action_source() -> None:
    model = _load("continuity_model")
    project = _project(
        "future-project",
        [
            _bead("fp-current", "in_progress"),
            _bead("fp-next", "open"),
            _bead(
                "fp-blocked",
                "open",
                dependencies=[{"depends_on_id": "fp-current", "type": "blocks"}],
            ),
            _bead("fp-deferred", "deferred"),
            _bead("fp-legacy", "open", labels=["legacy"]),
            _bead(
                "fp-generated",
                "closed",
                issue_type="convoy",
                metadata={"gc.formula_name": "fixture"},
            ),
        ],
    )

    first = model.build_report(_snapshot([project]))
    second = model.build_report(_snapshot([project]))

    assert first == second
    assert model.canonical_sha256(first) == model.canonical_sha256(second)
    assert [item["bead_id"] for item in first["work"]["current"]] == ["fp-current"]
    assert [item["bead_id"] for item in first["work"]["next"]] == ["fp-next"]
    assert [item["bead_id"] for item in first["work"]["blocked"]] == ["fp-blocked"]
    assert [item["bead_id"] for item in first["work"]["deferred"]] == ["fp-deferred"]
    assert [item["bead_id"] for item in first["work"]["legacy"]] == ["fp-legacy"]
    assert [item["bead_id"] for item in first["work"]["generated"]] == [
        "fp-generated"
    ]
    assert first["summary"]["next_action_ids"] == ["future-project:fp-next"]
    assert [item["id"] for item in first["next_actions"]] == first["summary"][
        "next_action_ids"
    ]


def test_report_detects_unbound_surfaces_and_terminal_generated_residue() -> None:
    model = _load("continuity_model")
    project = _project(
        "gas-city",
        [
            _bead("ga-live", "in_progress"),
            _bead(
                "ga-generated",
                "closed",
                issue_type="convoy",
                metadata={"gc.graphv2_root_key": "fixture"},
            ),
        ],
    )
    project["aegis"] = {
        "active_trackers": [
            {"bead_id": "ga-missing", "path": "docs/ai/work-tracking/active/missing-ACTIVE"}
        ]
    }
    project["git"] = {
        "branches": [],
        "worktrees": [
            {
                "bead_id": "ga-generated",
                "branch": "codex/ga-generated-fixture",
                "path": "/worktrees/ga-generated",
            }
        ],
        "open_prs": [
            {"bead_id": "ga-missing", "number": 7, "head": "codex/ga-missing-fixture"}
        ],
    }
    project["runtime"] = {
        "transactions": [
            {"bead_id": "ga-live", "phase": "ready", "path": "transactions/ga-live.json"}
        ],
        "receipts": [
            {"bead_id": "ga-missing", "commit": "b" * 40, "path": "receipts/x.json"}
        ],
    }

    report = model.build_report(_snapshot([project]))

    codes = [finding["code"] for finding in report["findings"]]
    assert codes == [
        "terminal-generated-worktree",
        "unbound-active-tracker",
        "unbound-open-pr",
        "unbound-runtime-receipt",
    ]
    assert report["ok"] is False
    assert len(report["work"]["orphaned"]) == 4
    assert not any(finding["surface"] == "transaction" for finding in report["findings"])


def test_followups_require_a_real_bead_or_explicit_disposition() -> None:
    model = _load("continuity_model")
    project = _project("gas-city", [_bead("ga-real", "open")])
    project["followups"] = [
        {"id": "bound", "summary": "Tracked", "bead_id": "ga-real"},
        {"id": "done", "summary": "Not needed", "disposition": "superseded"},
        {"id": "missing", "summary": "Promised but untracked"},
    ]

    report = model.build_report(_snapshot([project]))

    assert [finding["code"] for finding in report["findings"]] == [
        "untracked-promised-followup"
    ]
    assert report["ok"] is False


def test_snapshot_validation_is_descriptor_driven_and_fail_closed() -> None:
    model = _load("continuity_model")
    future = _project("new-product", [_bead("np-one", "open")])
    report = model.build_report(_snapshot([future]))
    assert report["projects"][0]["id"] == "new-product"

    duplicate = _snapshot([future, future])
    with pytest.raises(model.ContinuityError, match="project ids must be unique"):
        model.build_report(duplicate)

    malformed = _snapshot([future])
    malformed["registry_sha256"] = "not-a-digest"
    with pytest.raises(model.ContinuityError, match="registry_sha256"):
        model.build_report(malformed)


def test_shared_rig_is_reported_once_and_active_initiative_scopes_next_work() -> None:
    model = _load("continuity_model")
    beads = [
        _bead(
            "ga-root",
            "open",
            issue_type="epic",
            labels=["initiative:active"],
        ),
        _bead(
            "ga-child",
            "open",
            dependencies=[{"depends_on_id": "ga-root", "type": "parent-child"}],
        ),
        _bead("ga-unrelated", "open"),
    ]
    beads[0]["started_at"] = "2030-01-01T00:00:00Z"
    operations = _project("gas-city-operations", beads)
    operations["rig"] = "gascity"
    core = _project("gas-city", beads)
    core["rig"] = "gascity"
    unrelated = _project("unrelated", [_bead("un-one", "open")])

    report = model.build_report(_snapshot([operations, core, unrelated]))

    assert [item["bead_id"] for item in report["work"]["current"]] == ["ga-root"]
    assert [item["bead_id"] for item in report["work"]["next"]] == ["ga-child"]
    assert report["next_actions"][0]["id"] == "rig:gascity:ga-child"
    assert "ga-unrelated" not in json.dumps(report["work"])
    assert "un-one" not in json.dumps(report["work"])


def test_closed_started_initiative_descendant_is_never_actionable_work() -> None:
    model = _load("continuity_model")
    project = _project(
        "gas-city",
        [
            _bead(
                "ga-root",
                "open",
                issue_type="epic",
                labels=["initiative:active"],
            ),
            _bead(
                "ga-done",
                "closed",
                dependencies=[
                    {"depends_on_id": "ga-root", "type": "parent-child"},
                    {"depends_on_id": "ga-missing", "type": "blocks"},
                ],
            ),
        ],
    )
    project["beads"][0]["started_at"] = "2030-01-01T00:00:00Z"
    project["beads"][1]["started_at"] = "2030-01-02T00:00:00Z"

    report = model.build_report(_snapshot([project]))

    assert [item["bead_id"] for item in report["work"]["current"]] == ["ga-root"]
    assert not any(
        item["bead_id"] == "ga-done"
        for category in ("current", "next", "blocked", "deferred")
        for item in report["work"][category]
    )
    assert report["next_actions"] == []


def test_closed_initiative_label_does_not_scope_the_live_backlog() -> None:
    model = _load("continuity_model")
    project = _project(
        "gas-city",
        [
            _bead(
                "ga-finished",
                "closed",
                issue_type="epic",
                labels=["initiative:active"],
            ),
            _bead("ga-next", "open"),
        ],
    )
    project["beads"][0]["started_at"] = "2030-01-01T00:00:00Z"

    report = model.build_report(_snapshot([project]))

    assert report["work"]["current"] == []
    assert [item["bead_id"] for item in report["work"]["next"]] == ["ga-next"]


def test_obsidian_registration_must_match_the_project_identity() -> None:
    model = _load("continuity_model")
    project = _project("gas-city-operations", [])
    project["obsidian"]["registry_project_id"] = "gas-city"

    report = model.build_report(_snapshot([project]))

    assert [finding["code"] for finding in report["findings"]] == [
        "obsidian-project-id-mismatch"
    ]
    assert report["ok"] is False


def test_human_status_is_derived_from_the_json_report() -> None:
    model = _load("continuity_model")
    project = _project("gas-city", [_bead("ga-next", "open", title="Do the next thing")])
    report = model.build_report(_snapshot([project]))

    rendered = model.render_status(report)

    assert "continuity: PASS" in rendered
    assert "next gas-city:ga-next — Do the next thing" in rendered
    assert f"report_sha256={model.canonical_sha256(report)}" in rendered


def test_cli_audit_and_status_are_byte_deterministic(tmp_path: Path, capsys) -> None:
    cli = _load("continuity")
    project = _project("gas-city", [_bead("ga-next", "open")])
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps(_snapshot([project])), encoding="utf-8")

    assert cli.main(["audit", "--snapshot", str(snapshot)]) == 0
    first = capsys.readouterr().out
    assert cli.main(["audit", "--snapshot", str(snapshot)]) == 0
    second = capsys.readouterr().out
    assert first == second

    assert cli.main(["status", "--snapshot", str(snapshot)]) == 0
    status = capsys.readouterr().out
    assert "next gas-city:ga-next" in status

    report_path = tmp_path / "report.json"
    assert (
        cli.main(
            ["audit", "--snapshot", str(snapshot), "--output", str(report_path)]
        )
        == 0
    )
    assert json.loads(report_path.read_text(encoding="utf-8"))["next_actions"][0][
        "bead_id"
    ] == "ga-next"


def test_live_collector_uses_registry_without_hardcoded_project_ids(tmp_path: Path) -> None:
    capture = _load("continuity_capture")
    root = tmp_path / "future"
    root.mkdir()
    descriptor = {
        "schema": "gas-city-workflow.project.v1",
        "id": "future-project",
        "repository": "fixture/future-project",
        "rig": "future-project",
        "workflow_authority": "beads",
        "workflow_profile": "beads-with-aegis-evidence",
    }
    (root / ".gas-city-workflow.json").write_text(
        json.dumps(descriptor) + "\n", encoding="utf-8"
    )
    subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.test",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            "fixture",
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )
    registry = tmp_path / "projects.json"
    registry.write_text(
        json.dumps(
            {
                "schema": "gas-city-workflow.project-registry.v1",
                "projects": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    obsidian_registry = tmp_path / "obsidian.json"
    obsidian_registry.write_text(
        json.dumps(
            {
                "projects": [
                    {
                        "id": "future-project",
                        "target_dir": str(root),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    obsidian_state = tmp_path / "state"
    obsidian_state.mkdir()
    (obsidian_state / "future-project.json").write_text(
        json.dumps(
            {
                "last_success": {
                    "vault_status": "current",
                    "live_index": {"status": "confirmed"},
                }
            }
        ),
        encoding="utf-8",
    )
    signing = tmp_path / "signing.json"
    signing.write_text(json.dumps({"policies": {}}), encoding="utf-8")

    class Runner(capture.ReadOnlyRunner):
        def run(self, argv, *, cwd=None):
            if "bd" in argv:
                return subprocess.CompletedProcess(
                    argv,
                    0,
                    json.dumps([_bead("fp-next", "open")]),
                    "",
                )
            if argv[:3] == ["gh", "pr", "list"]:
                return subprocess.CompletedProcess(argv, 0, "[]", "")
            return super().run(argv, cwd=cwd)

    first = capture.capture_snapshot(
        registry,
        extra_roots=[root],
        obsidian_registry=obsidian_registry,
        obsidian_state=obsidian_state,
        signing_policies=signing,
        runner=Runner(),
    )
    second = capture.capture_snapshot(
        registry,
        extra_roots=[root],
        obsidian_registry=obsidian_registry,
        obsidian_state=obsidian_state,
        signing_policies=signing,
        runner=Runner(),
    )

    assert first == second
    assert first["projects"][0]["id"] == "future-project"
    assert first["projects"][0]["obsidian"]["live_index_status"] == "confirmed"
    assert [item["id"] for item in first["ledgers"][0]["beads"]] == ["fp-next"]


def test_read_only_runner_pins_the_managed_operator_path(monkeypatch) -> None:
    capture = _load("continuity_capture")
    observed = {}

    def run(argv, **kwargs):
        observed.update(kwargs)
        return subprocess.CompletedProcess(argv, 0, "ok", "")

    monkeypatch.setattr(capture.subprocess, "run", run)
    capture.ReadOnlyRunner().run(["fixture"])

    assert observed["env"]["PATH"] == capture.OPERATOR_PATH


def test_unknown_managed_branch_still_exposes_its_native_bead_candidate() -> None:
    capture = _load("continuity_capture")

    assert (
        capture._bead_for_branch("refs/heads/codex/ga-missing-fixture", set())
        == "ga-missing"
    )
    assert (
        capture._bead_for_branch("codex/ga-ur1c.12-fixture", {"ga-ur1c.1"})
        == "ga-ur1c.12"
    )
    assert capture._bead_for_branch("main", set()) is None


def test_legacy_active_tracker_is_classified_without_inventing_a_bead(tmp_path: Path) -> None:
    capture = _load("continuity_capture")
    model = _load("continuity_model")
    root = tmp_path / "project"
    tracker = (
        root
        / "docs"
        / "ai"
        / "work-tracking"
        / "active"
        / "20260612-task80-history-ACTIVE"
    )
    tracker.mkdir(parents=True)
    (tracker / "TRACKER.md").write_text("# Historical tracker\n", encoding="utf-8")
    project = _project("project", [])
    project["aegis"] = {"active_trackers": capture._active_trackers(root)}

    report = model.build_report(_snapshot([project]))

    assert report["work"]["legacy"][0]["id"] == "project:legacy:task80"
    assert report["findings"][0]["code"] == "legacy-active-tracker"
    assert report["findings"][0]["severity"] == "warning"
    assert report["ok"] is True
