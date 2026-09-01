"""Deterministic cross-project workflow continuity report tests."""

from __future__ import annotations

import fcntl
import importlib.util
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

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
        "residue_dispositions": [],
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


def _preserve(
    *,
    surface: str,
    identity: str,
    bead_id: str,
    head: str,
    clean: bool | None = None,
) -> dict[str, object]:
    disposition: dict[str, object] = {
        "id": f"fixture-{surface}",
        "project_id": "gas-city",
        "surface": surface,
        "identity": identity,
        "bead_id": bead_id,
        "head": head,
        "reason": "fixture evidence",
        "evidence": {
            "kind": "sha256-file",
            "path": "/evidence/fixture.json",
            "sha256": "c" * 64,
        },
    }
    if clean is not None:
        disposition["required_clean"] = clean
    return disposition


def test_exact_residue_dispositions_remain_visible_without_blocking() -> None:
    model = _load("continuity_model")
    project = _project("gas-city", [])
    branch_head = "d" * 40
    project["git"] = {
        "branches": [
            {
                "bead_id": "ga-missing",
                "branch": "codex/ga-missing-history",
                "head": branch_head,
            }
        ],
        "worktrees": [
            {
                "bead_id": "ga-missing",
                "branch": "codex/ga-missing-history",
                "path": "/worktrees/ga-missing",
                "head": branch_head,
                "clean": True,
            }
        ],
        "open_prs": [],
    }
    branch = _preserve(
        surface="branch",
        identity="codex/ga-missing-history",
        bead_id="ga-missing",
        head=branch_head,
    )
    worktree = _preserve(
        surface="worktree",
        identity="/worktrees/ga-missing",
        bead_id="ga-missing",
        head=branch_head,
        clean=True,
    )
    worktree["id"] = "fixture-worktree"
    project["residue_dispositions"] = [branch, worktree]

    report = model.build_report(_snapshot([project]))

    assert report["ok"] is True
    assert report["work"]["orphaned"] == []
    assert [finding["code"] for finding in report["findings"]] == [
        "preserved-unbound-branch",
        "preserved-unbound-worktree",
    ]
    assert all(finding["severity"] == "warning" for finding in report["findings"])


@pytest.mark.parametrize(
    ("observed_head", "clean"),
    [("e" * 40, True), ("d" * 40, False)],
)
def test_residue_disposition_head_or_cleanliness_drift_blocks(
    observed_head: str, clean: bool
) -> None:
    model = _load("continuity_model")
    project = _project("gas-city", [])
    project["git"]["worktrees"] = [
        {
            "bead_id": "ga-missing",
            "branch": "codex/ga-missing-history",
            "path": "/worktrees/ga-missing",
            "head": observed_head,
            "clean": clean,
        }
    ]
    project["residue_dispositions"] = [
        _preserve(
            surface="worktree",
            identity="/worktrees/ga-missing",
            bead_id="ga-missing",
            head="d" * 40,
            clean=True,
        )
    ]

    report = model.build_report(_snapshot([project]))

    assert report["ok"] is False
    assert report["findings"][0]["code"] == "residue-disposition-drift"
    assert report["work"]["orphaned"][0]["reason"] == "residue-disposition-drift"


def test_missing_residue_target_is_a_stale_blocking_disposition() -> None:
    model = _load("continuity_model")
    project = _project("gas-city", [])
    project["residue_dispositions"] = [
        _preserve(
            surface="branch",
            identity="codex/ga-missing-history",
            bead_id="ga-missing",
            head="d" * 40,
        )
    ]

    report = model.build_report(_snapshot([project]))

    assert report["ok"] is False
    assert report["findings"][0]["code"] == "stale-residue-disposition"


def test_disposition_on_non_orphan_surface_blocks_as_no_longer_required() -> None:
    model = _load("continuity_model")
    project = _project("gas-city", [_bead("ga-live", "in_progress")])
    project["git"]["branches"] = [
        {
            "bead_id": "ga-live",
            "branch": "codex/ga-live-history",
            "head": "d" * 40,
        }
    ]
    project["residue_dispositions"] = [
        _preserve(
            surface="branch",
            identity="codex/ga-live-history",
            bead_id="ga-live",
            head="d" * 40,
        )
    ]

    report = model.build_report(_snapshot([project]))

    assert report["ok"] is False
    assert report["findings"][0]["code"] == "residue-disposition-no-longer-required"


def test_tracked_residue_dispositions_validate_against_their_schema() -> None:
    schema = json.loads(
        (SCRIPTS.parent / "config" / "continuity-residue-dispositions.schema.json").read_text(
            encoding="utf-8"
        )
    )
    payload = json.loads(
        (SCRIPTS.parent / "config" / "continuity-residue-dispositions.json").read_text(
            encoding="utf-8"
        )
    )

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)


def test_collector_verifies_file_evidence_and_rejects_digest_drift(tmp_path: Path) -> None:
    capture = _load("continuity_capture")
    evidence = tmp_path / "evidence.json"
    evidence.write_text("preserved\n", encoding="utf-8")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    dispositions = tmp_path / "dispositions.json"
    payload = {
        "schema": "gas-city-workflow.residue-dispositions.v1",
        "dispositions": [
            {
                "id": "fixture-branch",
                "project_id": "gas-city",
                "surface": "branch",
                "identity": "codex/ga-missing-history",
                "bead_id": "ga-missing",
                "head": "d" * 40,
                "reason": "fixture evidence",
                "evidence": {
                    "kind": "sha256-file",
                    "path": str(evidence),
                    "sha256": digest,
                },
            }
        ],
    }
    dispositions.write_text(json.dumps(payload), encoding="utf-8")

    loaded = capture._load_residue_dispositions(
        dispositions,
        [{"id": "gas-city", "root": str(tmp_path)}],
        capture.ReadOnlyRunner(),
    )
    assert loaded["gas-city"][0]["head"] == "d" * 40

    evidence.write_text("drifted\n", encoding="utf-8")
    with pytest.raises(capture.ContinuityError, match="evidence digest drift"):
        capture._load_residue_dispositions(
            dispositions,
            [{"id": "gas-city", "root": str(tmp_path)}],
            capture.ReadOnlyRunner(),
        )


def test_collector_checks_cleanliness_only_for_disposition_bound_worktrees(
    tmp_path: Path,
) -> None:
    capture = _load("continuity_capture")
    tracked = tmp_path / "tracked"
    tracked.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=tracked, check=True, capture_output=True)
    (tracked / "file.txt").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tracked, check=True, capture_output=True)
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
        cwd=tracked,
        check=True,
        capture_output=True,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tracked,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    missing = tmp_path / "missing"
    items = [
        {"bead_id": "ga-bound", "path": str(tracked), "head": head},
        {"bead_id": "ga-other", "path": str(missing), "head": head},
    ]

    result = capture._capture_worktree_cleanliness(
        items,
        capture.ReadOnlyRunner(),
        required_paths={str(tracked)},
    )

    assert result[0]["clean"] is True
    assert "clean" not in result[1]


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


def test_running_obsidian_cycle_is_indeterminate_not_falsely_stale() -> None:
    model = _load("continuity_model")
    project = _project("gas-city-operations", [])
    project["obsidian"].update(
        {
            "filesystem": {"status": None, "completed_at": None},
            "live_index": {
                "status": "pending-cycle-observation",
                "authority": "host-obsidian-ipc",
                "observed_at": "2026-08-31T18:30:00Z",
            },
            "cycle": {
                "status": "running",
                "attempted_at": "2026-08-31T18:31:00Z",
                "pending_candidate": True,
            },
            "process": {
                "status": "active",
                "authority": "systemd-user-manager",
                "units": [],
            },
        }
    )

    report = model.build_report(_snapshot([project]))

    assert report["ok"] is True
    assert [finding["code"] for finding in report["findings"]] == [
        "obsidian-reconciliation-in-progress"
    ]
    assert report["findings"][0]["severity"] == "warning"


def test_obsidian_process_visibility_failure_is_unknown_not_absent() -> None:
    model = _load("continuity_model")
    project = _project("gas-city-operations", [])
    project["obsidian"]["process"] = {
        "status": "unknown",
        "authority": "systemd-user-manager",
        "units": [],
    }

    report = model.build_report(_snapshot([project]))

    assert report["ok"] is True
    assert [finding["code"] for finding in report["findings"]] == [
        "obsidian-process-observation-unknown"
    ]
    assert report["findings"][0]["severity"] == "warning"


def test_interrupted_obsidian_cycle_is_a_real_error() -> None:
    model = _load("continuity_model")
    project = _project("gas-city-operations", [])
    project["obsidian"]["cycle"] = {
        "status": "interrupted",
        "attempted_at": "2026-08-31T18:31:00Z",
        "pending_candidate": True,
    }
    project["obsidian"]["process"] = {
        "status": "active",
        "authority": "systemd-user-manager",
        "units": [],
    }

    report = model.build_report(_snapshot([project]))

    assert report["ok"] is False
    assert [finding["code"] for finding in report["findings"]] == [
        "obsidian-reconciliation-interrupted"
    ]


def test_confirmed_obsidian_index_requires_host_authority_and_observation_time() -> None:
    model = _load("continuity_model")
    project = _project("gas-city-operations", [])
    project["obsidian"]["live_index"] = {
        "status": "confirmed",
        "authority": "caller-asserted",
        "observed_at": None,
    }

    report = model.build_report(_snapshot([project]))

    assert report["ok"] is False
    assert [finding["code"] for finding in report["findings"]] == [
        "obsidian-live-index-authority-invalid",
        "obsidian-live-index-observation-time-missing",
    ]


def test_post_cycle_projection_keeps_authority_without_volatile_observation_time() -> None:
    model = _load("continuity_model")
    project = _project("gas-city-operations", [])
    project["obsidian"]["cycle"] = {
        "status": "idle",
        "attempted_at": None,
        "pending_candidate": False,
        "projection": "post-cycle",
    }
    project["obsidian"]["live_index"] = {
        "status": "confirmed",
        "authority": "host-obsidian-ipc",
        "observed_at": None,
    }

    report = model.build_report(_snapshot([project]))

    assert report["ok"] is True
    assert report["findings"] == []


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

    lock_path = obsidian_state / "registry-cycle.lock"
    lock_path.touch()
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        running = capture.capture_snapshot(
            registry,
            extra_roots=[root],
            obsidian_registry=obsidian_registry,
            obsidian_state=obsidian_state,
            signing_policies=signing,
            runner=Runner(),
        )
        projected = capture.capture_snapshot(
            registry,
            extra_roots=[root],
            obsidian_registry=obsidian_registry,
            obsidian_state=obsidian_state,
            obsidian_cycle_status="idle",
            signing_policies=signing,
            runner=Runner(),
        )

    assert first == second
    assert first["projects"][0]["id"] == "future-project"
    assert first["projects"][0]["obsidian"]["live_index_status"] == "confirmed"
    assert [item["id"] for item in first["ledgers"][0]["beads"]] == ["fp-next"]
    assert running["projects"][0]["obsidian"]["cycle"]["status"] == "running"
    assert projected["projects"][0]["obsidian"]["cycle"]["status"] == "idle"


def test_snapshot_cli_accepts_only_the_post_cycle_idle_projection() -> None:
    cli = _load("continuity")

    args = cli.parse_args(["snapshot", "--obsidian-cycle-status", "idle"])
    assert args.obsidian_cycle_status == "idle"
    with pytest.raises(SystemExit):
        cli.parse_args(["snapshot", "--obsidian-cycle-status", "running"])


def test_read_only_runner_pins_the_managed_operator_path(monkeypatch) -> None:
    capture = _load("continuity_capture")
    observed = {}

    def run(argv, **kwargs):
        observed.update(kwargs)
        return subprocess.CompletedProcess(argv, 0, "ok", "")

    monkeypatch.setattr(capture.subprocess, "run", run)
    capture.ReadOnlyRunner().run(["fixture"])

    assert observed["env"]["PATH"] == capture.OPERATOR_PATH


def test_obsidian_process_observation_uses_systemd_scope_provenance() -> None:
    capture = _load("continuity_capture")

    class Runner(capture.ReadOnlyRunner):
        def run(self, argv, *, cwd=None):
            if "list-units" in argv:
                return subprocess.CompletedProcess(
                    argv,
                    0,
                    "app-md.Obsidian-3168034.scope loaded active running Obsidian\n",
                    "",
                )
            return subprocess.CompletedProcess(
                argv,
                0,
                "\n".join(
                    (
                        "Id=app-md.Obsidian-3168034.scope",
                        "ActiveState=active",
                        "SubState=running",
                        "ControlGroup=/user.slice/app-md.Obsidian-3168034.scope",
                        "InvocationID=05802b4d92d2459caef16a14ef0e9d50",
                    )
                ),
                "",
            )

    observed = capture._obsidian_process(Runner())

    assert observed == {
        "status": "active",
        "authority": "systemd-user-manager",
        "units": [
            {
                "id": "app-md.Obsidian-3168034.scope",
                "active_state": "active",
                "sub_state": "running",
                "control_group": "/user.slice/app-md.Obsidian-3168034.scope",
                "invocation_id": "05802b4d92d2459caef16a14ef0e9d50",
            }
        ],
    }


def test_obsidian_process_observation_visibility_failure_is_unknown() -> None:
    capture = _load("continuity_capture")

    class Runner(capture.ReadOnlyRunner):
        def run(self, argv, *, cwd=None):
            raise capture.ContinuityError("user bus unavailable")

    assert capture._obsidian_process(Runner()) == {
        "status": "unknown",
        "authority": "systemd-user-manager",
        "units": [],
    }


def test_obsidian_index_keeps_confirmed_success_during_cycle_and_detects_interruption(
    tmp_path: Path,
) -> None:
    capture = _load("continuity_capture")
    root = tmp_path / "project"
    root.mkdir()
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps({"projects": [{"id": "project", "target_dir": str(root)}]}),
        encoding="utf-8",
    )
    state_root = tmp_path / "state"
    state_root.mkdir()
    (state_root / "project.json").write_text(
        json.dumps(
            {
                "last_attempt_at": "2026-08-31T18:31:00Z",
                "last_success": {
                    "completed_at": "2026-08-31T18:30:00Z",
                    "vault_status": "current",
                    "live_index": {
                        "status": "confirmed",
                        "authority": "host-obsidian-ipc",
                        "observed_at": "2026-08-31T18:30:01Z",
                    },
                },
                "pending_success": {
                    "completed_at": "2026-08-31T18:31:00Z",
                    "vault_status": "built",
                    "live_index": {"status": "pending-cycle-observation"},
                },
            }
        ),
        encoding="utf-8",
    )
    process = {
        "status": "active",
        "authority": "systemd-user-manager",
        "units": [],
    }
    lock_path = state_root / "registry-cycle.lock"
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        running = capture._obsidian_index(
            registry,
            state_root,
            process=process,
            registry_cycle_status=capture._obsidian_cycle_status(state_root),
        )[root.resolve().as_posix()]

    interrupted = capture._obsidian_index(
        registry,
        state_root,
        process=process,
        registry_cycle_status=capture._obsidian_cycle_status(state_root),
    )[root.resolve().as_posix()]

    assert running["live_index"] == {
        "status": "confirmed",
        "authority": "host-obsidian-ipc",
        "observed_at": "2026-08-31T18:30:01Z",
    }
    assert running["cycle"]["status"] == "running"
    assert interrupted["cycle"]["status"] == "interrupted"


def test_post_cycle_projection_is_stable_across_success_timestamps(tmp_path: Path) -> None:
    capture = _load("continuity_capture")
    root = tmp_path / "project"
    root.mkdir()
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps({"projects": [{"id": "project", "target_dir": str(root)}]}),
        encoding="utf-8",
    )
    state_root = tmp_path / "state"
    state_root.mkdir()
    state_path = state_root / "project.json"
    process = {
        "status": "active",
        "authority": "systemd-user-manager",
        "units": [],
    }

    def write_state(moment: str) -> None:
        state_path.write_text(
            json.dumps(
                {
                    "last_attempt_at": moment,
                    "last_success": {
                        "completed_at": moment,
                        "vault_status": "current",
                        "live_index": {
                            "status": "confirmed",
                            "authority": "host-obsidian-ipc",
                            "observed_at": moment,
                        },
                    },
                }
            ),
            encoding="utf-8",
        )

    write_state("2026-09-01T13:00:00Z")
    ordinary = capture._obsidian_index(
        registry,
        state_root,
        process=process,
        registry_cycle_status="idle",
    )[root.resolve().as_posix()]
    first = capture._obsidian_index(
        registry,
        state_root,
        process=process,
        registry_cycle_status="idle",
        post_cycle_projection=True,
    )[root.resolve().as_posix()]

    write_state("2026-09-01T13:01:00Z")
    second = capture._obsidian_index(
        registry,
        state_root,
        process=process,
        registry_cycle_status="idle",
        post_cycle_projection=True,
    )[root.resolve().as_posix()]

    assert ordinary["filesystem"]["completed_at"] == "2026-09-01T13:00:00Z"
    assert ordinary["live_index"]["observed_at"] == "2026-09-01T13:00:00Z"
    assert first == second
    assert first["filesystem"]["completed_at"] is None
    assert first["live_index"]["observed_at"] is None
    assert first["cycle"] == {
        "status": "idle",
        "attempted_at": None,
        "pending_candidate": False,
        "projection": "post-cycle",
    }


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
