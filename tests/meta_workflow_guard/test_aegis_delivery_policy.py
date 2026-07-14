"""Deterministic evidence-gated delivery-policy tests."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = REPO_ROOT / "aegis.delivery-policy.json"
BRIEF_PATH = REPO_ROOT / ".aegis" / "brief.json"
CODEX_PROFILE_PATH = REPO_ROOT / ".codex" / "deep-work.config.toml"
SCRIPT_PATH = REPO_ROOT / "scripts" / "aegis-delivery-policy"
PACKAGED_SCRIPT_PATH = (
    REPO_ROOT / "aegis_foundation" / "assets" / "scripts" / "aegis-delivery-policy"
)
SCHEMA_PATH = REPO_ROOT / "schemas" / "aegis" / "delivery-policy.schema.json"
PACKAGED_SCHEMA_PATH = (
    REPO_ROOT / "aegis_foundation" / "assets" / "schemas" / "aegis" / "delivery-policy.schema.json"
)
PR264_FIXTURE_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "aegis" / "pr264-autonomous-delivery-self-gating.json"
)
PR269_FIXTURE_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "aegis" / "pr269-autonomous-delivery-unstable.json"
)
PR276_FIXTURE_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "aegis" / "pr276-executor-self-unstable.json"
)
HEAD_SHA = "a" * 40
BASE_SHA = "b" * 40


def _load_module():
    name = "aegis_delivery_policy_test_module"
    sys.modules.pop(name, None)
    loader = importlib.machinery.SourceFileLoader(name, str(SCRIPT_PATH))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


policy_module = _load_module()


def _policy() -> dict[str, object]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _workflow_run(
    name: str, *, status: str = "completed", conclusion: str = "success"
) -> dict[str, object]:
    return {
        "id": len(name) + 100,
        "name": name,
        "event": "pull_request",
        "head_sha": HEAD_SHA,
        "status": status,
        "conclusion": conclusion,
        "run_attempt": 1,
        "run_started_at": "2030-01-01T00:00:00Z",
    }


def _evidence(*, files: list[dict[str, object]] | None = None) -> dict[str, object]:
    inventory = (
        files if files is not None else [{"filename": "src/feature.py", "status": "modified"}]
    )
    policy = _policy()
    required = policy["merge"]["required_workflows"]  # type: ignore[index]
    return {
        "repository": "loucmane/codex-starter-pack",
        "expected_head_sha": HEAD_SHA,
        "current_default_sha": BASE_SHA,
        "pull_request": {
            "number": 999,
            "state": "open",
            "draft": False,
            "base": {"ref": "main", "sha": BASE_SHA},
            "head": {
                "ref": "feat/task-247-routine-change",
                "sha": HEAD_SHA,
                "repo": {"full_name": "loucmane/codex-starter-pack"},
            },
            "mergeable": True,
            "mergeable_state": "clean",
            "changed_files": len(inventory),
            "labels": [],
        },
        "files": inventory,
        "workflow_runs": [_workflow_run(str(name)) for name in required],
        "review": {
            "decision": "",
            "unresolved_threads": 0,
            "threads_truncated": False,
        },
    }


def test_source_policy_and_packaged_assets_are_valid_and_identical() -> None:
    policy = policy_module.validate_policy(_policy())

    assert policy["mode"] == "evidence-gated"
    assert all(policy["routine"].values())
    assert SCRIPT_PATH.read_bytes() == PACKAGED_SCRIPT_PATH.read_bytes()
    assert SCHEMA_PATH.read_bytes() == PACKAGED_SCHEMA_PATH.read_bytes()


def test_codex_profile_enables_scoped_autonomy_without_full_access() -> None:
    config = tomllib.loads(CODEX_PROFILE_PATH.read_text(encoding="utf-8"))

    assert config["approval_policy"] == "never"
    assert config["default_permissions"] == "aegis-autonomous"
    assert "approvals_reviewer" not in config
    assert "sandbox_mode" not in config
    assert "sandbox_workspace_write" not in config

    profile = config["permissions"]["aegis-autonomous"]
    assert profile["extends"] == ":workspace"
    assert profile["filesystem"][":workspace_roots"][".git"] == "write"
    assert profile["network"]["enabled"] is True

    domains = profile["network"]["domains"]
    assert "*" not in domains
    assert {
        "**.github.com",
        "**.githubusercontent.com",
        "**.npmjs.org",
        "**.pypi.org",
        "**.pythonhosted.org",
        "**.openai.com",
    } <= domains.keys()


def test_witness_scope_accounts_for_delivery_authority_surfaces() -> None:
    brief = json.loads(BRIEF_PATH.read_text(encoding="utf-8"))
    always_in_scope = set(brief["witness"]["always_in_scope"])

    assert ".codex/" in always_in_scope
    assert "aegis.delivery-policy.json" in always_in_scope


def test_routine_exact_head_with_complete_evidence_is_allowed() -> None:
    result = policy_module.evaluate(_policy(), _evidence())

    assert result["decision"] == "allow"
    assert result["reasons"] == []
    assert result["evidence"]["head_sha"] == HEAD_SHA


def test_pr264_self_gating_replay_is_provisional_not_authorized() -> None:
    fixture = json.loads(PR264_FIXTURE_PATH.read_text(encoding="utf-8"))

    result = policy_module.evaluate(_policy(), fixture["evidence"])

    assert fixture["expected_decision"] == "provisional"
    assert result["decision"] == "provisional"
    assert result["evidence"]["mergeability_recheck_required"] is True
    assert result["reasons"] == [
        {
            "category": "mergeability-self-check-pending",
            "mergeable": True,
            "state": "blocked",
        }
    ]


def test_pr269_unstable_replay_is_provisional_not_authorized() -> None:
    fixture = json.loads(PR269_FIXTURE_PATH.read_text(encoding="utf-8"))

    result = policy_module.evaluate(_policy(), fixture["evidence"])

    assert fixture["replay_assumption"]["direct_telemetry"] is False
    assert fixture["replay_assumption"]["confidence"] == "medium"
    assert fixture["observed"]["post_run_mergeable_state"] == "clean"
    assert fixture["expected_decision"] == "provisional"
    assert result["decision"] == "provisional"
    assert result["evidence"]["mergeability_recheck_required"] is True
    assert result["reasons"] == [
        {
            "category": "mergeability-self-check-pending",
            "mergeable": True,
            "state": "unstable",
        }
    ]


def test_pr276_live_executor_replay_allows_only_the_verified_self_check() -> None:
    fixture = json.loads(PR276_FIXTURE_PATH.read_text(encoding="utf-8"))

    evaluator = policy_module.evaluate(_policy(), fixture["evidence"])
    executor = policy_module.evaluate(
        _policy(),
        fixture["evidence"],
        phase="executor",
        executor_run_id=fixture["executor_run_id"],
    )

    assert fixture["observed"]["direct_telemetry"] is True
    assert evaluator["decision"] == fixture["expected_evaluator_decision"]
    assert executor["decision"] == fixture["expected_executor_decision"]
    assert executor["reasons"] == []
    assert executor["evidence"]["evaluation_phase"] == "executor"
    assert executor["evidence"]["mergeability_self_check_verified"] is True
    assert executor["evidence"]["check_inventory"] == {
        "current_self_check": True,
        "ignored_self_checks": 1,
        "independent_checks": 4,
        "status_contexts": 0,
    }


def test_executor_clean_mergeability_still_requires_complete_check_inventory() -> None:
    fixture = json.loads(PR276_FIXTURE_PATH.read_text(encoding="utf-8"))
    fixture["evidence"]["pull_request"]["mergeable_state"] = "clean"

    result = policy_module.evaluate(
        _policy(),
        fixture["evidence"],
        phase="executor",
        executor_run_id=fixture["executor_run_id"],
    )

    assert result["decision"] == "allow"
    assert result["evidence"]["mergeability_self_check_verified"] is False
    assert result["evidence"]["check_inventory"]["current_self_check"] is True


@pytest.mark.parametrize(
    ("mutation", "category"),
    [
        ("independent-pending", "check-run-pending"),
        ("independent-failed", "check-run-not-successful"),
        ("self-app-spoof", "executor-self-check-missing"),
        ("self-run-mismatch", "executor-self-check-missing"),
        ("self-already-completed", "executor-self-check-missing"),
        ("checks-incomplete", "check-run-inventory-incomplete"),
        ("statuses-incomplete", "status-context-inventory-incomplete"),
        ("legacy-status-failed", "status-context-not-successful"),
    ],
)
def test_executor_self_exception_never_masks_other_status_evidence(
    mutation: str,
    category: str,
) -> None:
    fixture = json.loads(PR276_FIXTURE_PATH.read_text(encoding="utf-8"))
    evidence = fixture["evidence"]
    if mutation == "independent-pending":
        evidence["check_runs"][0]["status"] = "in_progress"
        evidence["check_runs"][0]["conclusion"] = None
    elif mutation == "independent-failed":
        evidence["check_runs"][0]["conclusion"] = "failure"
    elif mutation == "self-app-spoof":
        evidence["check_runs"][1]["app"]["slug"] = "untrusted-app"
    elif mutation == "self-run-mismatch":
        evidence["check_runs"][1]["details_url"] = (
            "https://github.com/loucmane/codex-starter-pack/actions/runs/999/job/1"
        )
    elif mutation == "self-already-completed":
        evidence["check_runs"][1]["status"] = "completed"
        evidence["check_runs"][1]["conclusion"] = "failure"
    elif mutation == "checks-incomplete":
        evidence["check_runs_complete"] = False
    elif mutation == "statuses-incomplete":
        evidence["status_contexts_complete"] = False
    else:
        evidence["status_contexts"] = [
            {
                "id": 1,
                "context": "external/security",
                "state": "failure",
                "sha": evidence["expected_head_sha"],
                "created_at": "2026-07-14T05:16:00Z",
            }
        ]

    result = policy_module.evaluate(
        _policy(),
        evidence,
        phase="executor",
        executor_run_id=fixture["executor_run_id"],
    )

    assert result["decision"] == "defer"
    assert category in {reason["category"] for reason in result["reasons"]}


def test_executor_self_exception_never_masks_an_attended_path() -> None:
    fixture = json.loads(PR276_FIXTURE_PATH.read_text(encoding="utf-8"))
    fixture["evidence"]["files"] = [{"filename": ".github/workflows/ci.yml", "status": "modified"}]

    result = policy_module.evaluate(
        _policy(),
        fixture["evidence"],
        phase="executor",
        executor_run_id=fixture["executor_run_id"],
    )

    assert result["decision"] == "attended"
    assert any(reason["category"] == "attended-path" for reason in result["reasons"])


@pytest.mark.parametrize("executor_run_id", [None, "", "0", "not-a-run"])
def test_executor_phase_requires_a_trusted_numeric_run_id(
    executor_run_id: str | None,
) -> None:
    fixture = json.loads(PR276_FIXTURE_PATH.read_text(encoding="utf-8"))

    with pytest.raises(policy_module.PolicyError, match="numeric executor_run_id"):
        policy_module.evaluate(
            _policy(),
            fixture["evidence"],
            phase="executor",
            executor_run_id=executor_run_id,
        )


@pytest.mark.parametrize(
    ("mergeable", "state"),
    [
        (False, "dirty"),
        (True, "dirty"),
        (None, "unknown"),
        (True, "behind"),
    ],
)
def test_non_provisional_mergeability_remains_deferred(
    mergeable: bool | None,
    state: str,
) -> None:
    evidence = _evidence()
    evidence["pull_request"]["mergeable"] = mergeable  # type: ignore[index]
    evidence["pull_request"]["mergeable_state"] = state  # type: ignore[index]

    result = policy_module.evaluate(_policy(), evidence)

    assert result["decision"] == "defer"
    assert any(reason["category"] == "mergeability-not-clean" for reason in result["reasons"])


@pytest.mark.parametrize(
    ("mutation", "category"),
    [
        ("workflow-pending", "workflow-pending"),
        ("workflow-failed", "workflow-not-successful"),
        ("review-required", "review-required"),
        ("changes-requested", "changes-requested"),
        ("thread", "unresolved-review-threads"),
    ],
)
@pytest.mark.parametrize("mergeability_state", ["blocked", "unstable"])
def test_provisional_mergeability_never_masks_another_gate(
    mutation: str,
    category: str,
    mergeability_state: str,
) -> None:
    evidence = _evidence()
    evidence["pull_request"]["mergeable_state"] = mergeability_state  # type: ignore[index]
    if mutation == "workflow-pending":
        evidence["workflow_runs"][0]["status"] = "in_progress"  # type: ignore[index]
        evidence["workflow_runs"][0]["conclusion"] = None  # type: ignore[index]
    elif mutation == "workflow-failed":
        evidence["workflow_runs"][0]["conclusion"] = "failure"  # type: ignore[index]
    elif mutation == "review-required":
        evidence["review"]["decision"] = "REVIEW_REQUIRED"  # type: ignore[index]
    elif mutation == "changes-requested":
        evidence["review"]["decision"] = "CHANGES_REQUESTED"  # type: ignore[index]
    else:
        evidence["review"]["unresolved_threads"] = 1  # type: ignore[index]

    result = policy_module.evaluate(_policy(), evidence)

    assert result["decision"] == "defer"
    assert category in {reason["category"] for reason in result["reasons"]}


def test_unstable_provisional_state_never_masks_attended_path() -> None:
    evidence = _evidence(files=[{"filename": ".github/workflows/ci.yml", "status": "modified"}])
    evidence["pull_request"]["mergeable_state"] = "unstable"  # type: ignore[index]

    result = policy_module.evaluate(_policy(), evidence)

    assert result["decision"] == "attended"
    assert any(reason["category"] == "attended-path" for reason in result["reasons"])


@pytest.mark.parametrize(
    "path",
    [
        "aegis.delivery-policy.json",
        ".github/workflows/ci.yml",
        "scripts/aegis-delivery-policy",
        "scripts/_aegis_installer.py",
        "aegis_foundation/assets/scripts/_aegis_installer.py",
        "scripts/codex-guard",
        ".claude/scripts/witness_lib.py",
    ],
)
def test_authority_and_governance_paths_remain_attended(path: str) -> None:
    result = policy_module.evaluate(
        _policy(),
        _evidence(files=[{"filename": path, "status": "modified"}]),
    )

    assert result["decision"] == "attended"
    assert any(reason["category"] == "attended-path" for reason in result["reasons"])


def test_candidate_policy_change_cannot_self_authorize() -> None:
    candidate_policy = _policy()
    candidate_policy["attended"]["path_patterns"] = []  # type: ignore[index]
    evidence = _evidence(files=[{"filename": "aegis.delivery-policy.json", "status": "modified"}])

    result = policy_module.evaluate(_policy(), evidence)

    assert candidate_policy != _policy()
    assert result["decision"] == "attended"


@pytest.mark.parametrize("label", ["authority-change", "secrets", "deployment", "high-risk"])
def test_high_risk_labels_remain_attended(label: str) -> None:
    evidence = _evidence()
    evidence["pull_request"]["labels"] = [{"name": label}]  # type: ignore[index]

    result = policy_module.evaluate(_policy(), evidence)

    assert result["decision"] == "attended"
    assert {reason["label"] for reason in result["reasons"] if "label" in reason} == {label}


def test_test_deletion_remains_attended() -> None:
    result = policy_module.evaluate(
        _policy(),
        _evidence(files=[{"filename": "tests/test_feature.py", "status": "removed"}]),
    )

    assert result["decision"] == "attended"
    assert any(reason["category"] == "test-deletion" for reason in result["reasons"])


def test_incomplete_file_inventory_is_denied() -> None:
    evidence = _evidence()
    evidence["pull_request"]["changed_files"] = 2  # type: ignore[index]

    result = policy_module.evaluate(_policy(), evidence)

    assert result["decision"] == "deny"
    assert result["reasons"][0]["category"] == "incomplete-file-inventory"


@pytest.mark.parametrize(
    ("mutation", "category"),
    [
        ("head", "head-moved"),
        ("base", "base-not-current"),
        ("thread", "unresolved-review-threads"),
        ("workflow", "workflow-not-successful"),
    ],
)
def test_incomplete_or_stale_evidence_defers(mutation: str, category: str) -> None:
    evidence = _evidence()
    if mutation == "head":
        evidence["expected_head_sha"] = "c" * 40
    elif mutation == "base":
        evidence["current_default_sha"] = "c" * 40
    elif mutation == "thread":
        evidence["review"]["unresolved_threads"] = 1  # type: ignore[index]
    else:
        evidence["workflow_runs"][0]["conclusion"] = "failure"  # type: ignore[index]

    result = policy_module.evaluate(_policy(), evidence)

    assert result["decision"] == "defer"
    assert category in {reason["category"] for reason in result["reasons"]}


def test_attended_mode_and_fork_heads_never_auto_merge() -> None:
    policy = _policy()
    policy["mode"] = "attended"
    attended = policy_module.evaluate(policy, _evidence())
    assert attended["decision"] == "attended"

    evidence = _evidence()
    evidence["pull_request"]["head"]["repo"]["full_name"] = "fork/example"  # type: ignore[index]
    fork = policy_module.evaluate(_policy(), evidence)
    assert fork["decision"] == "attended"


def test_cli_fails_closed_on_malformed_policy(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    input_path = tmp_path / "input.json"
    policy_path.write_text("{}\n", encoding="utf-8")
    input_path.write_text(json.dumps(_evidence()) + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "evaluate",
            "--policy",
            str(policy_path),
            "--input",
            str(input_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert json.loads(result.stdout)["decision"] == "deny"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("unknown", "unknown fields"),
        ("issued_at", "ISO-8601"),
        ("expires_on", "non-empty array"),
        ("routine", "must be boolean"),
    ],
)
def test_validator_rejects_schema_skew_in_authority_contract(
    mutation: str,
    message: str,
) -> None:
    policy = _policy()
    if mutation == "unknown":
        policy["unknown"] = True
    elif mutation == "issued_at":
        policy["authority"]["issued_at"] = "not-a-time"  # type: ignore[index]
    elif mutation == "expires_on":
        policy["authority"]["expires_on"] = []  # type: ignore[index]
    else:
        policy["routine"]["allow_safe_repairs"] = "yes"  # type: ignore[index]

    with pytest.raises(policy_module.PolicyError, match=message):
        policy_module.validate_policy(policy)
