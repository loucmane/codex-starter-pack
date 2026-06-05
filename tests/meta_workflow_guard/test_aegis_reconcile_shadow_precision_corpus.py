"""Replayable precision corpus tests for shadow reconcile apply."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Mapping

import pytest

from aegis_foundation.reconcile_shadow_apply import (
    SHADOW_ACCUMULATION_REPORT_TYPE,
    SHADOW_CI_VALIDATION_REPORT_TYPE,
)
from aegis_foundation.reconcile_shadow_precision import (
    SHADOW_PRECISION_CORPUS_REPORT_TYPE,
    SHADOW_PRECISION_PRE_REGISTERED_BAR,
    build_replayable_shadow_precision_corpus_artifact,
    build_shadow_precision_corpus_artifact,
    classify_shadow_evidence_stream,
    evidence_stream_boundaries,
)
from aegis_foundation.taskmaster_toolchain import (
    TASKMASTER_CI_RUNNER_ARCH,
    TASKMASTER_CI_RUNNER_OS,
    TASKMASTER_PACKAGE_VERSION,
    build_taskmaster_toolchain_evidence,
    build_validated_taskmaster_ci_toolchain_baseline,
)
from tests.meta_workflow_guard.test_aegis_installer import REPO_ROOT

LABEL_FIXTURE = (
    REPO_ROOT / "tests" / "fixtures" / "aegis" / "reconcile_shadow_precision_corpus.json"
)


def _require_taskmaster_cli() -> None:
    if shutil.which("task-master") is None:
        pytest.skip("task-master CLI is required for the shadow precision corpus replay")


def test_shadow_precision_corpus_replays_real_git_histories_and_meets_registered_bar(
    tmp_path: Path,
) -> None:
    _require_taskmaster_cli()

    artifact = build_replayable_shadow_precision_corpus_artifact(
        labels_path=LABEL_FIXTURE,
        work_root=tmp_path / "precision-work",
        source_root=REPO_ROOT,
        validated_toolchain_evidence=_toolchain_evidence(),
    )

    assert artifact["record_type"] == SHADOW_PRECISION_CORPUS_REPORT_TYPE
    assert artifact["executed"] is False
    assert artifact["mutated_live_repo"] is False
    assert artifact["precision_evidence_basis"] == "replayable_labeled_precision_corpus"
    assert artifact["pre_registered_bar"]["registered_before_measurement"] is True
    assert artifact["toolchain_binding"]["comparison"]["matches"] is True
    assert artifact["precision_metrics"]["emitted"] is True
    assert artifact["precision_gate"]["passed"] is True
    by_pair = artifact["precision_metrics"]["by_pair"]
    assert by_pair["merged_but_not_done/git_ancestor"] == {
        "true_positive": 6,
        "false_positive": 0,
        "false_negative": 0,
        "precision": 1.0,
        "precision_observation": True,
    }
    assert "merged_but_not_done/github_pr_merged" not in by_pair
    assert artifact["precision_metrics"]["boundary_leak_count"] == 0
    assert artifact["precision_metrics"]["label_mismatch_count"] == 0
    assert artifact["precision_metrics"]["false_positive_count"] == 0
    assert artifact["precision_metrics"]["false_negative_count"] == 0
    assert artifact["label_source"]["path"].endswith(
        "tests/fixtures/aegis/reconcile_shadow_precision_corpus.json"
    )
    assert artifact["label_source"]["sha256"]

    observed_fixture_axes = {
        (
            observation["fixture"]["merge_topology"],
            observation["fixture"]["state_json_branch"],
            observation["fixture"]["proof_source"],
        )
        for observation in artifact["observations"]
    }
    for topology in ("fast_forward", "true_merge"):
        for state_json_branch in ("absent", "legacy_tag", "steady_state"):
            assert (topology, state_json_branch, "git_ancestor") in observed_fixture_axes
    assert ("squash", "absent", "github_pr_merged") in observed_fixture_axes
    assert (
        "deleted_branch_unknown",
        "steady_state",
        "git_only_non_ancestor_or_missing_base",
    ) in observed_fixture_axes


def test_shadow_precision_corpus_fixture_labels_are_reviewed_data() -> None:
    fixture = _load_label_fixture()

    assert fixture["corpus_version"] == "shadow-precision-corpus-v1"
    assert fixture["pre_registered_bar"] == SHADOW_PRECISION_PRE_REGISTERED_BAR
    assert len({label["case_id"] for label in fixture["labels"]}) == len(fixture["labels"])
    for label in fixture["labels"]:
        assert label["bucket"] in {"auto_eligible", "manual_only", "not_a_finding"}
        assert label["expected_decision"] in {"would_apply", "no_candidate"}
        assert label["merge_topology"]
        assert label["state_json_branch"]
        assert label["proof_source"]


def test_shadow_precision_gate_rejects_manual_boundary_leak() -> None:
    artifact = build_shadow_precision_corpus_artifact(
        [
            {
                "case_id": "manual-leak",
                "fixture": {
                    "merge_topology": "squash",
                    "state_json_branch": "absent",
                    "proof_source": "github_pr_merged",
                },
                "label": {
                    "task_id": "4301",
                    "finding_kind": "merged_but_not_done",
                    "proof": "github_pr_merged",
                    "bucket": "manual_only",
                    "expected_decision": "no_candidate",
                },
                "shadow_report": _fake_shadow_report(
                    would_apply=(
                        {
                            "task_id": "4301",
                            "finding_kind": "merged_but_not_done",
                            "proof": "git_ancestor",
                        },
                    )
                ),
            }
        ],
        validated_toolchain_evidence=_toolchain_evidence(),
        pre_registered_bar={**SHADOW_PRECISION_PRE_REGISTERED_BAR, "min_true_positives_per_pair": 0},
    )

    assert artifact["precision_gate"]["passed"] is False
    assert artifact["precision_gate"]["reason"] == "pre_registered_bar_not_met"
    assert artifact["precision_metrics"]["boundary_leak_count"] == 1
    assert artifact["precision_metrics"]["false_positive_count"] == 1


def test_shadow_precision_gate_rejects_missing_auto_candidate_as_false_negative() -> None:
    artifact = build_shadow_precision_corpus_artifact(
        [
            {
                "case_id": "auto-fn",
                "fixture": {
                    "merge_topology": "fast_forward",
                    "state_json_branch": "absent",
                    "proof_source": "git_ancestor",
                },
                "label": {
                    "task_id": "4201",
                    "finding_kind": "merged_but_not_done",
                    "proof": "git_ancestor",
                    "bucket": "auto_eligible",
                    "expected_decision": "would_apply",
                },
                "shadow_report": _fake_shadow_report(),
            }
        ],
        validated_toolchain_evidence=_toolchain_evidence(),
        pre_registered_bar={**SHADOW_PRECISION_PRE_REGISTERED_BAR, "min_true_positives_per_pair": 0},
    )

    assert artifact["precision_gate"]["passed"] is False
    pair = artifact["precision_metrics"]["by_pair"]["merged_but_not_done/git_ancestor"]
    assert pair["false_negative"] == 1
    assert artifact["precision_metrics"]["false_negative_count"] == 1


def test_shadow_precision_gate_rejects_no_candidate_label_that_only_refuses() -> None:
    artifact = build_shadow_precision_corpus_artifact(
        [
            {
                "case_id": "manual-refused-leak",
                "fixture": {
                    "merge_topology": "squash",
                    "state_json_branch": "absent",
                    "proof_source": "github_pr_merged",
                },
                "label": {
                    "task_id": "4301",
                    "finding_kind": "merged_but_not_done",
                    "proof": "github_pr_merged",
                    "bucket": "manual_only",
                    "expected_decision": "no_candidate",
                },
                "shadow_report": _fake_shadow_report(
                    shadow_refused=(
                        {
                            "task_id": "4301",
                            "finding_kind": "merged_but_not_done",
                            "proof": "github_pr_merged",
                            "reason": "candidate_outside_first_apply_class",
                        },
                    )
                ),
            }
        ],
        validated_toolchain_evidence=_toolchain_evidence(),
        pre_registered_bar={**SHADOW_PRECISION_PRE_REGISTERED_BAR, "min_true_positives_per_pair": 0},
    )

    assert artifact["precision_gate"]["passed"] is False
    assert artifact["precision_metrics"]["label_mismatch_count"] == 1
    assert artifact["precision_gate"]["label_mismatch_count"] == 1


def test_shadow_precision_labels_require_expected_decision_in_artifact_builder() -> None:
    with pytest.raises(ValueError, match="missing expected_decision"):
        build_shadow_precision_corpus_artifact(
            [
                {
                    "case_id": "missing-expected-decision",
                    "fixture": {
                        "merge_topology": "fast_forward",
                        "state_json_branch": "absent",
                        "proof_source": "git_ancestor",
                    },
                    "label": {
                        "task_id": "4201",
                        "finding_kind": "merged_but_not_done",
                        "proof": "git_ancestor",
                        "bucket": "auto_eligible",
                    },
                    "shadow_report": _fake_shadow_report(),
                }
            ],
            validated_toolchain_evidence=_toolchain_evidence(),
        )


def test_shadow_precision_toolchain_mismatch_marks_corpus_stale_and_emits_no_metrics() -> None:
    artifact = build_shadow_precision_corpus_artifact(
        [],
        validated_toolchain_evidence=_toolchain_evidence(task_master_version=TASKMASTER_PACKAGE_VERSION),
        current_toolchain_evidence=_toolchain_evidence(task_master_version="0.99.0"),
    )

    assert artifact["toolchain_binding"]["comparison"]["matches"] is False
    assert artifact["precision_metrics"]["emitted"] is False
    assert artifact["precision_metrics"]["reason"] == "toolchain_mismatch"
    assert artifact["precision_metrics"]["by_pair"] == {}
    assert artifact["precision_gate"]["passed"] is False
    assert artifact["precision_gate"]["reason"] == "toolchain_mismatch"


def test_shadow_precision_ci_baseline_is_frozen_and_compared_to_current_toolchain() -> None:
    env = _toolchain_env()
    baseline = build_validated_taskmaster_ci_toolchain_baseline(env, python_version="3.12.3")
    current = _toolchain_evidence(task_master_version=TASKMASTER_PACKAGE_VERSION)

    assert baseline["evidence_role"] == "validated_ci_baseline"
    assert baseline["baseline_source"]["type"] == "source_controlled_constants"
    assert baseline["task_master"]["version"] == TASKMASTER_PACKAGE_VERSION
    assert baseline["runtime"]["node_version"] == "22"
    assert baseline["runtime"]["node_major"] == "22"
    assert baseline["runner"]["os"] == TASKMASTER_CI_RUNNER_OS
    assert baseline["runner"]["arch"] == TASKMASTER_CI_RUNNER_ARCH

    artifact = build_shadow_precision_corpus_artifact(
        [],
        validated_toolchain_evidence=baseline,
        current_toolchain_evidence=current,
    )

    assert artifact["toolchain_binding"]["comparison"]["matches"] is True

    drifted = build_shadow_precision_corpus_artifact(
        [],
        validated_toolchain_evidence=baseline,
        current_toolchain_evidence=_toolchain_evidence(task_master_version="0.99.0"),
    )

    assert drifted["toolchain_binding"]["comparison"]["matches"] is False
    assert drifted["precision_metrics"]["emitted"] is False
    assert drifted["precision_gate"]["reason"] == "toolchain_mismatch"


def test_shadow_evidence_streams_are_not_interchangeable() -> None:
    boundaries = evidence_stream_boundaries()

    assert boundaries["operational_accumulation"]["precision_observation"] is False
    assert boundaries["cascade_validation_smoke"]["precision_observation"] is False
    assert boundaries["precision_corpus"]["precision_observation"] is True
    assert classify_shadow_evidence_stream(
        {"record_type": SHADOW_ACCUMULATION_REPORT_TYPE}
    )["counts_toward_enablement_precision"] is False
    cascade = classify_shadow_evidence_stream({"record_type": SHADOW_CI_VALIDATION_REPORT_TYPE})
    assert cascade["stream"] == "cascade_validation_smoke"
    assert cascade["precision_observation"] is False
    assert cascade["counts_toward_enablement_precision"] is False
    precision = classify_shadow_evidence_stream({"record_type": SHADOW_PRECISION_CORPUS_REPORT_TYPE})
    assert precision["stream"] == "precision_corpus"
    assert precision["precision_observation"] is True
    assert precision["counts_toward_enablement_precision"] is True


def _toolchain_evidence(*, task_master_version: str = TASKMASTER_PACKAGE_VERSION) -> dict[str, Any]:
    return build_taskmaster_toolchain_evidence(
        _toolchain_env(),
        task_master_version=task_master_version,
        node_version="v22.22.3",
        npm_version="10.9.2",
        python_version="3.12.3",
    )


def _toolchain_env() -> dict[str, str]:
    return {
        "GITHUB_ACTIONS": "true",
        "GITHUB_WORKFLOW": "Precision Corpus",
        "GITHUB_RUN_ID": "162",
        "GITHUB_RUN_ATTEMPT": "1",
        "RUNNER_OS": "Linux",
        "RUNNER_ARCH": "X64",
        "ImageOS": "ubuntu24",
        "ImageVersion": "20260605.1",
    }


def _load_label_fixture() -> dict[str, Any]:
    return json.loads(LABEL_FIXTURE.read_text(encoding="utf-8"))


def _fake_shadow_report(
    *,
    would_apply: tuple[Mapping[str, Any], ...] = (),
    shadow_refused: tuple[Mapping[str, Any], ...] = (),
) -> dict[str, Any]:
    return {
        "record_type": "reconcile_shadow_apply_report",
        "would_apply": list(would_apply),
        "shadow_refused": list(shadow_refused),
        "summary": {
            "would_apply": len(would_apply),
            "shadow_refused": len(shadow_refused),
        },
    }
