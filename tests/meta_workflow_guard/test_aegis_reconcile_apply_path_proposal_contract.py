"""Contract tests for the future reconcile apply path proposal."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from aegis_foundation import cli as aegis_cli
from aegis_mcp.server import AegisMCPConfig, create_server
from scripts import _aegis_installer as aegis_installer
from tests.meta_workflow_guard.test_aegis_installer import (
    RECONCILE_MUTATION_FLAGS,
    REPO_ROOT,
    load_task_module,
)
from tests.meta_workflow_guard.test_aegis_mcp_server import (
    RECONCILE_MUTATION_PARAMETER_NAMES,
    tool_by_name,
)

CONTRACT_PATH = REPO_ROOT / "docs/aegis/reconcile-apply-path-proposal-contract.md"
RELATED_CONTRACTS = (
    "docs/aegis/reconcile-promotion-contract.md",
    "tests/meta_workflow_guard/reconcile_side_effect_oracle.py",
    "docs/aegis/reconcile-precision-corpus.md",
    "docs/aegis/reconcile-mutation-rollback-contract.md",
    "docs/aegis/reconcile-mutation-candidate-preview-contract.md",
)
EXCLUDED_CLASSES = (
    "github_pr_merged",
    "done_but_not_merged",
    "multi_pr_epic_ambiguity",
    "abandoned_in_progress_branch",
    "stale_local_stub",
    "local_ad_hoc_stub",
    "git_only_non_ancestor_or_missing_base",
)


def test_apply_path_contract_is_design_only() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert "**Status:** active Task 149 contract." in contract
    assert "design and review contract only" in contract
    assert "does not add an apply path" in contract
    assert "does not enable mutation" in contract
    assert "No writer function may consume `mutation_candidate_preview`" in contract
    assert "No enabled execution scaffold" in contract
    assert "agent-excluded" in contract


def test_apply_path_contract_decides_agent_excluded_invocation_model() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert "## Invocation And Confirmation Decision" in contract
    assert (
        "The governed agent that produced or consumed a reconcile report cannot invoke apply"
        in contract
    )
    assert "The governed agent cannot satisfy operator confirmation" in contract
    assert "Apply cannot be exposed as an MCP tool for the governed agent" in contract
    assert "Apply must refuse when invoked from a known governed-agent tool context" in contract
    assert "Post-merge CI invocation" in contract
    assert "Operator-controlled local invocation" in contract


def test_apply_path_contract_names_first_candidate_and_exclusions() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert "finding kind: `merged_but_not_done`" in contract
    assert "proof: `git_ancestor`" in contract
    assert "current Taskmaster state: not `done`" in contract
    assert "future requested state: `done`" in contract
    assert ".taskmaster/tasks/tasks.json" in contract
    assert ".taskmaster/tasks/task_<id>.md" in contract
    for excluded in EXCLUDED_CLASSES:
        assert excluded in contract


def test_apply_path_contract_lists_task_144_to_148_preconditions() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    for task_id in ("Task 144", "Task 145", "Task 146", "Task 147", "Task 148"):
        assert task_id in contract
    for path in RELATED_CONTRACTS:
        assert path in contract
    assert "zero auto/manual boundary leaks" in contract
    assert "before breadcrumb must exist before the first write" in contract
    assert "Task 145's side-effect oracle is test-side proof only" in contract
    assert "separate apply-time side-effect oracle" in contract
    assert "## Future Enablement Gate: Live Apply-Time Oracle" in contract
    assert "Task 145's side-effect oracle is the authority" not in contract


def test_apply_path_contract_names_audit_and_kill_switch_prerequisites() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert "Apply audit breadcrumbs are separate from degraded-event breadcrumbs" in contract
    assert "global kill-switch" in contract
    assert "default to disabled" in contract
    assert "Task 150" in contract
    assert "disabled apply orchestration scaffold" in contract
    assert "enable gate that is intentionally unsatisfiable" in contract


def test_apply_path_contract_contains_claude_review_prompt() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert "## Claude Discussion Prompt" in contract
    assert "agent-runtime-first workflow system" in contract
    assert "Could an autonomous agent misread" in contract
    assert "no --apply flag" in contract
    assert "future apply must be agent-excluded" in contract
    assert "What exact test proves the governed agent cannot invoke or confirm apply" in contract
    assert "What kill-switch semantics are sufficient" in contract
    assert "What exact negative test would you require" in contract


def test_reconcile_surfaces_still_reject_apply_mutation_flags() -> None:
    codex_parser = load_task_module().build_parser()
    package_parser = aegis_cli.build_arg_parser()

    codex_preview = codex_parser.parse_args(
        ["aegis", "reconcile", "--target-dir", "/tmp/example", "--preview-candidates"]
    )
    assert codex_preview.preview_candidates is True

    package_preview = package_parser.parse_args(
        ["reconcile", "--target-dir", "/tmp/example", "--preview-candidates"]
    )
    assert package_preview.preview_candidates is True

    for flag in RECONCILE_MUTATION_FLAGS:
        with pytest.raises(SystemExit):
            codex_parser.parse_args(["aegis", "reconcile", flag])
        with pytest.raises(SystemExit):
            package_parser.parse_args(["reconcile", flag])


def test_reconcile_mcp_schema_still_has_no_mutation_parameters(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    tool = tool_by_name(create_server(config), "aegis.reconcile")
    schema = tool.inputSchema

    assert "preview_candidates" in schema["properties"]
    assert set(schema["properties"]).isdisjoint(RECONCILE_MUTATION_PARAMETER_NAMES)


def test_no_existing_writer_consumes_candidate_preview_or_apply_contract() -> None:
    writer_functions = (
        aegis_installer.install,
        aegis_installer.repair,
        aegis_installer.start_local_work,
        aegis_installer.kickoff,
        aegis_installer.log_work,
        aegis_installer.verify,
        aegis_installer.closeout,
        aegis_installer.repair_handoff,
    )

    for function in writer_functions:
        source = inspect.getsource(function)
        assert "mutation_candidate_preview" not in source
        assert "reconcile-apply-path-proposal-contract" not in source


def test_reconcile_runtime_has_no_enabled_apply_path() -> None:
    reconcile_source = inspect.getsource(aegis_installer.reconcile)
    reconcile_signature = inspect.signature(aegis_installer.reconcile)

    assert "preview_candidates" in reconcile_signature.parameters
    for forbidden in ("apply", "auto_fix", "set_status", "mutate", "write", "push"):
        assert forbidden not in reconcile_signature.parameters
    for forbidden_text in (
        "task-master set-status",
        "set_task_status",
        'subprocess.run(["task-master"',
        "mutation_applied",
        "apply_path_exists = True",
    ):
        assert forbidden_text not in reconcile_source
