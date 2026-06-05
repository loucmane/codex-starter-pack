"""Contract tests for the Task 176 reconcile apply enablement decision packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from aegis_foundation.reconcile_apply_scaffold import FIRST_APPLY_CLASS_KEY
from aegis_foundation.reconcile_shadow_precision import (
    SHADOW_PRECISION_CORPUS_REPORT_TYPE,
    SHADOW_PRECISION_EVIDENCE_BASIS,
    SHADOW_PRECISION_PRE_REGISTERED_BAR,
)
from aegis_foundation.taskmaster_toolchain import (
    TASKMASTER_CI_RUNNER_ARCH,
    TASKMASTER_CI_RUNNER_OS,
    TASKMASTER_PACKAGE_NAME,
    TASKMASTER_PACKAGE_VERSION,
    TASKMASTER_PROVISIONING_LOCK_ID,
    TASKMASTER_TOOLCHAIN_LOCK_VERSION,
    taskmaster_install_spec,
)
from tests.meta_workflow_guard.test_aegis_installer import REPO_ROOT

CONTRACT_PATH = REPO_ROOT / "docs" / "aegis" / "reconcile-apply-enablement-decision-packet.md"
PACKET_PATH = REPO_ROOT / "docs" / "aegis" / "reconcile-apply-enablement-decision-packet.json"
GATE_STATUS_PATH = REPO_ROOT / "docs" / "aegis" / "reconcile-enablement-gate-status.json"
OPERATIONAL_EVIDENCE_PATH = (
    REPO_ROOT / "docs" / "aegis" / "evidence" / "reconcile-shadow-operational-0001.json"
)
TASKMASTER_TASKS_PATH = REPO_ROOT / ".taskmaster" / "tasks" / "tasks.json"
REQUIRED_GATES = {"G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"}


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _packet_allows_first_guarded_apply(packet: Mapping[str, Any]) -> bool:
    decision = packet.get("decision")
    if not isinstance(decision, Mapping):
        return False
    operator_decision = decision.get("operator_decision")
    if not isinstance(operator_decision, Mapping):
        return False
    gate_computation = packet.get("gate_computation")
    if not isinstance(gate_computation, Mapping):
        return False
    return (
        decision.get("outcome") == "GO"
        and decision.get("first_guarded_apply_task_allowed") is True
        and operator_decision.get("recorded") is True
        and operator_decision.get("signed") is True
        and gate_computation.get("all_gate_markers_closed") is True
        and not gate_computation.get("open_gates")
    )


def test_enablement_decision_packet_closes_g5_but_remains_no_go() -> None:
    contract = CONTRACT_PATH.read_text(encoding="utf-8")
    packet = _json(PACKET_PATH)
    status = _json(GATE_STATUS_PATH)

    assert "**Closes:** G5: Enablement Evidence Decision Packet." in contract
    assert "packet outcome is NO-GO because no explicit operator GO" in contract
    assert packet["record_type"] == "reconcile_apply_enablement_decision_packet"
    assert packet["gate_closed"] == "G5"
    assert packet["decision"]["outcome"] == "NO-GO"
    assert packet["decision"]["reason"] == "operator_decision_missing"
    assert packet["decision"]["operator_decision"]["recorded"] is False
    assert packet["decision"]["operator_decision"]["signed"] is False
    assert packet["decision"]["first_guarded_apply_task_allowed"] is False
    assert packet["decision"]["may_create_task_177"] is False
    assert packet["decision"]["enables_apply"] is False
    assert packet["decision"]["kill_switch_flip"] is False

    assert status["updated_by_task"] == "176"
    assert status["status"] == "NO-GO"
    assert status["first_guarded_apply_task_allowed"] is False
    assert status["gates"]["G5"]["status"] == "closed"
    assert status["gates"]["G5"]["closed_by_task"] == "176"
    assert status["gates"]["G5"]["decision"] == "NO-GO"
    assert status["closed_gate_markers"]["G5"]["marker"] == (
        "enablement_evidence_decision_packet_closed"
    )


def test_enablement_packet_computes_gate_closure_from_machine_readable_markers() -> None:
    packet = _json(PACKET_PATH)
    status = _json(GATE_STATUS_PATH)

    closed_markers = set(status["closed_gate_markers"])
    gate_statuses = {gate_id: gate["status"] for gate_id, gate in status["gates"].items()}
    computed_closed = {gate_id for gate_id, value in gate_statuses.items() if value == "closed"}
    computed_open = sorted(REQUIRED_GATES - computed_closed)

    assert closed_markers == REQUIRED_GATES
    assert computed_closed == REQUIRED_GATES
    assert computed_open == []
    assert set(packet["gate_computation"]["required_gates"]) == REQUIRED_GATES
    assert set(packet["gate_computation"]["closed_gates"]) == computed_closed
    assert packet["gate_computation"]["open_gates"] == computed_open
    assert packet["gate_computation"]["all_gate_markers_closed"] is True
    assert packet["gate_computation"]["go_refusal_reasons"] == ["operator_decision_missing"]
    assert _packet_allows_first_guarded_apply(packet) is False


def test_enablement_packet_uses_precision_corpus_as_only_precision_basis() -> None:
    packet = _json(PACKET_PATH)
    operational = _json(OPERATIONAL_EVIDENCE_PATH)

    precision = packet["precision_evidence"]
    assert precision["record_type"] == SHADOW_PRECISION_CORPUS_REPORT_TYPE
    assert precision["precision_evidence_basis"] == SHADOW_PRECISION_EVIDENCE_BASIS
    assert precision["counts_toward_enablement_precision"] is True
    assert precision["pre_registered_bar"] == {
        key: value
        for key, value in SHADOW_PRECISION_PRE_REGISTERED_BAR.items()
        if key != "record_type"
    }
    assert precision["result"] == {
        "pair": FIRST_APPLY_CLASS_KEY,
        "true_positive": 6,
        "false_positive": 0,
        "false_negative": 0,
        "boundary_leak_count": 0,
        "label_mismatch_count": 0,
        "precision": 1.0,
        "precision_gate_passed": True,
    }

    operational_packet = packet["non_precision_evidence"]["operational_accumulation"]
    assert operational_packet["source_path"] == (
        "docs/aegis/evidence/reconcile-shadow-operational-0001.json"
    )
    assert operational_packet["run_id"] == operational["source_run"]["run_id"] == "26959807056"
    assert operational_packet["candidate_count"] == operational["summary"]["candidate_count"] == 0
    assert operational_packet["would_apply"] == operational["summary"]["would_apply"] == 0
    assert operational_packet["shadow_refused"] == operational["summary"]["shadow_refused"] == 0
    assert operational_packet["mutated_live_repo"] is False
    assert operational_packet["precision_observation"] is False
    assert operational_packet["counts_toward_enablement_precision"] is False

    cascade = packet["non_precision_evidence"]["cascade_validation_smoke"]
    assert cascade["precision_observation"] is False
    assert cascade["counts_toward_enablement_precision"] is False
    assert cascade["reason"] == "synthetic_fixed_fixture_smoke"


def test_enablement_packet_binds_toolchain_and_refuses_mismatch() -> None:
    toolchain = _json(PACKET_PATH)["toolchain_binding"]

    assert toolchain["task_master_package"] == TASKMASTER_PACKAGE_NAME
    assert toolchain["task_master_version"] == TASKMASTER_PACKAGE_VERSION
    assert toolchain["task_master_install_spec"] == taskmaster_install_spec()
    assert toolchain["task_master_node_major"] == "22"
    assert toolchain["runner_os"] == TASKMASTER_CI_RUNNER_OS
    assert toolchain["runner_arch"] == TASKMASTER_CI_RUNNER_ARCH
    assert toolchain["lock_version"] == TASKMASTER_TOOLCHAIN_LOCK_VERSION
    assert toolchain["lock_id"] == TASKMASTER_PROVISIONING_LOCK_ID
    assert toolchain["live_evidence_must_match_validated_baseline"] is True
    assert toolchain["mismatch_outcome"] == "NO-GO"


def test_enablement_packet_records_readiness_without_enabling_apply_or_task_177() -> None:
    packet = _json(PACKET_PATH)
    taskmaster = _json(TASKMASTER_TASKS_PATH)

    tasks = taskmaster["master"]["tasks"]
    task_ids = {str(task["id"]) for task in tasks}

    assert "176" in task_ids
    assert "177" not in task_ids
    assert packet["taskmaster_boundary"]["task_177_created"] is False
    assert packet["taskmaster_boundary"]["packet_does_not_create_first_guarded_apply_task"] is True
    assert packet["candidate_class"]["class_key"] == FIRST_APPLY_CLASS_KEY
    assert packet["candidate_class"]["no_new_candidate_class"] is True
    assert packet["divergence_review"]["unexplained_divergence_count"] == 0
    assert packet["divergence_review"]["auto_extend_canonicalization"] is False
    assert packet["divergence_review"]["auto_write_exemptions"] is False
    assert packet["readiness_evidence"]["audit_storage"]["gate"] == "G7"
    assert packet["readiness_evidence"]["terminal_resolution"]["gate"] == "G6"
    assert packet["readiness_evidence"]["agent_surface_regression"]["gate"] == "G8"

    for forbidden in (
        "no apply or apply-like command",
        "no kill-switch flip",
        "no MCP apply tool",
        "no Taskmaster status mutation against the governed repository",
        "no automatic creation of Task 177",
    ):
        assert forbidden in packet["non_goals"]


def test_enablement_packet_evidence_paths_exist() -> None:
    status = _json(GATE_STATUS_PATH)
    marker = status["closed_gate_markers"]["G5"]

    for rel_path in marker["evidence"]:
        path = REPO_ROOT / rel_path.split("::", 1)[0]
        assert path.exists(), rel_path
