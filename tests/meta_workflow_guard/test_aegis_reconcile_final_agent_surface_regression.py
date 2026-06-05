"""Final agent-surface regression after selected-channel machinery exists."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from aegis_foundation import cli as aegis_cli
from aegis_foundation.reconcile_apply_scaffold import run_disabled_apply_scaffold
from aegis_mcp.server import AegisMCPConfig, create_server
from tests.meta_workflow_guard.reconcile_side_effect_oracle import snapshot_whole_tree
from tests.meta_workflow_guard.test_aegis_installer import (
    RECONCILE_MUTATION_FLAGS,
    REPO_ROOT,
    load_task_module,
)
from tests.meta_workflow_guard.test_aegis_mcp_server import (
    RECONCILE_MUTATION_PARAMETER_NAMES,
    list_tools,
)
from tests.meta_workflow_guard.test_aegis_reconcile_disabled_apply_scaffold import (
    ENABLE_SHAPED_KILL_SWITCH,
    FIRST_CANDIDATE,
    FUTURE_CI_CONTEXT,
)

CONTRACT_PATH = REPO_ROOT / "docs/aegis/reconcile-final-agent-surface-regression-contract.md"
GATE_STATUS_PATH = REPO_ROOT / "docs/aegis/reconcile-enablement-gate-status.json"

FORBIDDEN_APPLY_RUNTIME_TOKENS = (
    "reconcile_apply_runtime",
    "run_reconcile_apply_write_apparatus",
    "run_selected_channel_apply_with_process_oracle",
    "_perform_taskmaster_done_write",
)
FORBIDDEN_APPLY_CONTROL_TOKENS = (
    "build_post_merge_ci_apply_confirmation",
    "evaluate_selected_apply_channel_confirmation",
    "evaluate_kill_switch_control_action",
    "evaluate_terminal_rollback_resolution",
    "build_terminal_rollback_resolution_audit_record",
)
FORBIDDEN_AGENT_INPUT_NAMES = {
    "approved_context_proof",
    "audit_destination",
    "enable_gate_open",
    "enable_write_path",
    "idempotency_claim",
    "idempotency_key",
    "kill_switch_path",
    "kill_switch_state",
    "operator_approval_id",
    "resolution_proof",
    "selected_apply_confirmation",
    "terminal_record",
    "terminal_resolution_gate_open",
    "terminal_resolution_proof",
    "validated_toolchain_evidence",
}
PACKAGE_CLI_DISPATCH_CASES = (
    (["reconcile"], "handle_reconcile"),
    (["repair"], "handle_repair"),
    (["kickoff", "--task", "175", "--slug", "task-175", "--title", "Task 175"], "handle_kickoff"),
    (["start", "Task 175"], "handle_start"),
    (["status"], "handle_status"),
    (["next"], "handle_next"),
    (["doctor"], "handle_doctor"),
    (["closeout", "--dry-run"], "handle_closeout"),
    (["handoff", "repair"], "handle_handoff_repair"),
)
CODEX_TASK_DISPATCH_CASES = (
    (["aegis", "reconcile"], "handle_aegis_reconcile"),
    (["aegis", "repair"], "handle_aegis_repair"),
    (
        ["aegis", "kickoff", "--task", "175", "--slug", "task-175", "--title", "Task 175"],
        "handle_aegis_kickoff",
    ),
    (["aegis", "status"], "handle_aegis_status"),
    (["aegis", "next"], "handle_aegis_next"),
    (["aegis", "doctor"], "handle_aegis_doctor"),
    (["aegis", "closeout", "--dry-run"], "handle_aegis_closeout"),
    (["aegis", "handoff", "repair"], "handle_aegis_handoff_repair"),
)


def _gate_status() -> dict[str, object]:
    return json.loads(GATE_STATUS_PATH.read_text(encoding="utf-8"))


def _agent_surface_paths() -> tuple[Path, ...]:
    roots = [
        REPO_ROOT / "aegis_foundation" / "cli.py",
        REPO_ROOT / "aegis_mcp" / "server.py",
        REPO_ROOT / "scripts" / "codex-task",
        REPO_ROOT / "scripts" / "_aegis_installer.py",
        REPO_ROOT / "aegis_foundation" / "assets" / "scripts" / "codex-task",
        REPO_ROOT / "aegis_foundation" / "assets" / "scripts" / "_aegis_installer.py",
        REPO_ROOT / "aegis_foundation" / "resources.py",
        REPO_ROOT / "aegis_foundation" / "reconcile_shadow_apply.py",
        REPO_ROOT / "aegis_foundation" / "reconcile_shadow_precision.py",
    ]
    roots.extend(sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml")))
    roots.extend(sorted((REPO_ROOT / ".claude" / "scripts").glob("*.sh")))
    roots.extend(sorted((REPO_ROOT / ".claude" / "scripts").glob("*.py")))
    return tuple(path for path in roots if path.exists())


def _assert_dispatch_is_not_apply_runtime(func: object, expected_name: str) -> None:
    assert getattr(func, "__name__", "") == expected_name
    assert getattr(func, "__module__", "") != "aegis_foundation.reconcile_apply_runtime"
    code = getattr(func, "__code__", None)
    if code is not None:
        names = set(code.co_names)
        assert names.isdisjoint(FORBIDDEN_APPLY_RUNTIME_TOKENS)
        assert names.isdisjoint(FORBIDDEN_APPLY_CONTROL_TOKENS)


def test_final_agent_surface_contract_closes_g8_and_keeps_no_go() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    status = _gate_status()

    assert (
        "**Closes:** G8: Final Agent-Surface Regression With The Selected Channel Present."
        in contract
    )
    assert "**Verdict:** G8 closed; NO-GO remains" in contract
    assert status["status"] == "NO-GO"
    assert status["first_guarded_apply_task_allowed"] is False
    assert status["updated_by_task"] == "175"
    assert status["gates"]["G8"]["status"] == "closed"
    assert status["gates"]["G8"]["closed_by_task"] == "175"
    assert status["gates"]["G8"]["contract"] == (
        "docs/aegis/reconcile-final-agent-surface-regression-contract.md"
    )
    assert status["gates"]["G5"]["status"] == "open"
    assert status["gates"]["G5"]["blocking"] is True


def test_single_gated_caller_audit_still_holds_with_selected_channel_present() -> None:
    source = (REPO_ROOT / "aegis_foundation" / "reconcile_apply_runtime.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    references: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id != "_perform_taskmaster_done_write":
                continue
            current: ast.AST | None = node
            while current is not None and not isinstance(current, ast.FunctionDef):
                current = parents.get(current)
            references.append(current.name if isinstance(current, ast.FunctionDef) else "")

    assert references == ["run_reconcile_apply_write_apparatus"]


def test_agent_surfaces_do_not_reference_apply_runtime_or_control_helpers() -> None:
    forbidden = (*FORBIDDEN_APPLY_RUNTIME_TOKENS, *FORBIDDEN_APPLY_CONTROL_TOKENS)

    for path in _agent_surface_paths():
        source = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source, path


def test_real_mcp_surface_exposes_no_apply_or_control_plane_inputs(tmp_path: Path) -> None:
    server = create_server(
        AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    )
    tools = list_tools(server)
    tool_names = {tool.name for tool in tools}

    assert "aegis.apply" not in tool_names
    assert "aegis.reconcile_apply" not in tool_names
    assert not any("apply" in name and name.startswith("aegis.reconcile") for name in tool_names)

    for tool in tools:
        properties = tool.inputSchema.get("properties", {})
        assert isinstance(properties, dict)
        assert set(properties).isdisjoint(FORBIDDEN_AGENT_INPUT_NAMES), tool.name
        if tool.name == "aegis.reconcile":
            assert set(properties).isdisjoint(RECONCILE_MUTATION_PARAMETER_NAMES)


@pytest.mark.parametrize("flag", RECONCILE_MUTATION_FLAGS)
def test_real_cli_reconcile_surfaces_reject_mutation_flags(flag: str) -> None:
    package_parser = aegis_cli.build_arg_parser()
    codex_parser = load_task_module().build_parser()

    with pytest.raises(SystemExit):
        package_parser.parse_args(["reconcile", flag])
    with pytest.raises(SystemExit):
        codex_parser.parse_args(["aegis", "reconcile", flag])


@pytest.mark.parametrize(
    "flag",
    sorted(f"--{name.replace('_', '-')}" for name in FORBIDDEN_AGENT_INPUT_NAMES),
)
def test_real_cli_agent_surfaces_reject_apply_control_inputs(flag: str) -> None:
    package_parser = aegis_cli.build_arg_parser()
    codex_parser = load_task_module().build_parser()

    with pytest.raises(SystemExit):
        package_parser.parse_args(["reconcile", flag, "x"])
    with pytest.raises(SystemExit):
        codex_parser.parse_args(["aegis", "reconcile", flag, "x"])


@pytest.mark.parametrize(("argv", "expected_handler"), PACKAGE_CLI_DISPATCH_CASES)
def test_package_cli_dispatches_to_normal_handlers_not_apply_runtime(
    argv: list[str], expected_handler: str
) -> None:
    args = aegis_cli.build_arg_parser().parse_args(argv)
    _assert_dispatch_is_not_apply_runtime(args.func, expected_handler)


@pytest.mark.parametrize(("argv", "expected_handler"), CODEX_TASK_DISPATCH_CASES)
def test_codex_task_dispatches_to_normal_handlers_not_apply_runtime(
    argv: list[str], expected_handler: str
) -> None:
    args = load_task_module().build_parser().parse_args(argv)
    _assert_dispatch_is_not_apply_runtime(args.func, expected_handler)


def test_open_gate_status_forbids_production_apply_entrypoints() -> None:
    status = _gate_status()
    open_gates = {
        gate_id for gate_id, gate in status["gates"].items() if gate["status"] != "closed"
    }

    assert open_gates == {"G5"}
    assert status["first_guarded_apply_task_allowed"] is False
    for path in _agent_surface_paths():
        source = path.read_text(encoding="utf-8")
        assert "enable_write_path=True" not in source, path
        assert "terminal_resolution_gate_open=True" not in source, path
        assert "run_selected_channel_apply_with_process_oracle" not in source, path
        assert "run_reconcile_apply_write_apparatus" not in source, path


def test_default_config_remains_zero_delta_and_enable_unsatisfiable(tmp_path: Path) -> None:
    before = snapshot_whole_tree(tmp_path)

    result = run_disabled_apply_scaffold(
        FIRST_CANDIDATE,
        approved_context_proof=FUTURE_CI_CONTEXT,
        kill_switch_state=ENABLE_SHAPED_KILL_SWITCH,
    )

    assert result.status == "refused"
    assert result.reason == "enable_gate_unsatisfiable"
    assert result.enabled is False
    assert result.mutated is False
    before.assert_matches(snapshot_whole_tree(tmp_path))
