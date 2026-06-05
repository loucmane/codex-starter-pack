"""Replayable precision corpus artifacts for shadow reconcile apply."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from aegis_foundation.reconcile_apply_scaffold import FIRST_APPLY_CLASS_KEY
from aegis_foundation.reconcile_shadow_apply import (
    SHADOW_ACCUMULATION_REPORT_TYPE,
    SHADOW_CI_VALIDATION_REPORT_TYPE,
    SHADOW_CI_VALIDATION_KILL_SWITCH,
    build_shadow_report,
)
from aegis_foundation.taskmaster_toolchain import compare_taskmaster_toolchain_evidence
from scripts import _aegis_installer as aegis_installer
from scripts._aegis_installer import reconcile

SHADOW_PRECISION_CORPUS_REPORT_TYPE = "reconcile_shadow_precision_corpus"
SHADOW_PRECISION_OBSERVATION_TYPE = "reconcile_shadow_precision_observation"
SHADOW_PRECISION_CORPUS_VERSION = "shadow-precision-corpus-v1"
SHADOW_PRECISION_EVIDENCE_BASIS = "replayable_labeled_precision_corpus"
SHADOW_PRECISION_PRE_REGISTERED_BAR = {
    "record_type": "reconcile_shadow_precision_pre_registered_bar",
    "registered_before_measurement": True,
    "auto_eligible_pairs": [FIRST_APPLY_CLASS_KEY],
    "max_false_positives_per_pair": 0,
    "max_false_negatives_per_pair": 0,
    "max_boundary_leaks": 0,
    "max_label_mismatches": 0,
    "min_true_positives_per_pair": 3,
}

VALID_LABEL_BUCKETS = frozenset({"auto_eligible", "manual_only", "not_a_finding"})
STATE_JSON_BRANCH_PAYLOADS = {
    "legacy_tag": {"tag": "master"},
    "steady_state": {
        "currentTag": "master",
        "lastSwitched": "2025-09-22T11:42:16.191Z",
        "branchTagMapping": {},
        "migrationNoticeShown": True,
    },
}


def build_replayable_shadow_precision_corpus_artifact(
    *,
    labels_path: Path,
    work_root: Path,
    source_root: Path,
    validated_toolchain_evidence: Mapping[str, Any],
    current_toolchain_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Replay the reviewed precision corpus in temp git fixtures and build its artifact."""

    work_root = work_root.resolve()
    _require_temp_work_root(work_root)
    labels_fixture = json.loads(labels_path.read_text(encoding="utf-8"))
    labels = labels_fixture.get("labels")
    if not isinstance(labels, list):
        raise ValueError("shadow precision label fixture must contain labels")
    case_results = [
        _replay_precision_case(
            work_root / str(label["case_id"]),
            label=label,
            source_root=source_root,
            clone_parent=work_root / "clones" / str(label["case_id"]),
        )
        for label in labels
        if isinstance(label, Mapping)
    ]
    label_text = labels_path.read_text(encoding="utf-8")
    return build_shadow_precision_corpus_artifact(
        case_results,
        validated_toolchain_evidence=validated_toolchain_evidence,
        current_toolchain_evidence=current_toolchain_evidence,
        label_source={
            "path": labels_path.as_posix(),
            "sha256": hashlib.sha256(label_text.encode("utf-8")).hexdigest(),
            "schema_version": labels_fixture.get("schema_version"),
            "corpus_version": labels_fixture.get("corpus_version"),
        },
        pre_registered_bar=labels_fixture.get("pre_registered_bar"),
    )


def build_shadow_precision_corpus_artifact(
    case_results: Sequence[Mapping[str, Any]],
    *,
    validated_toolchain_evidence: Mapping[str, Any],
    current_toolchain_evidence: Mapping[str, Any] | None = None,
    label_source: Mapping[str, Any] | None = None,
    pre_registered_bar: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a precision artifact from replayed shadow corpus cases."""

    bar = dict(pre_registered_bar or SHADOW_PRECISION_PRE_REGISTERED_BAR)
    comparison = compare_taskmaster_toolchain_evidence(
        validated_toolchain_evidence, current_toolchain_evidence or validated_toolchain_evidence
    )
    observations = [_precision_observation(case_result) for case_result in case_results]
    if comparison["matches"]:
        metrics = _precision_metrics(observations, bar)
    else:
        metrics = {
            "record_type": "reconcile_shadow_precision_metrics",
            "emitted": False,
            "reason": "toolchain_mismatch",
            "by_pair": {},
            "boundary_leak_count": 0,
            "false_positive_count": 0,
            "false_negative_count": 0,
            "true_positive_count": 0,
        }
    gate = _precision_gate(metrics, bar, comparison)
    return {
        "record_type": SHADOW_PRECISION_CORPUS_REPORT_TYPE,
        "corpus_version": SHADOW_PRECISION_CORPUS_VERSION,
        "mode": "shadow",
        "executed": False,
        "mutated_live_repo": False,
        "evidence_stream": "precision_corpus",
        "evidence_classification": classify_shadow_evidence_stream(
            {"record_type": SHADOW_PRECISION_CORPUS_REPORT_TYPE}
        ),
        "precision_evidence_basis": SHADOW_PRECISION_EVIDENCE_BASIS,
        "pre_registered_bar": bar,
        "label_source": dict(label_source or {}),
        "toolchain_binding": {
            "comparison": comparison,
            "stale_if_toolchain_mismatch": True,
        },
        "evidence_stream_boundaries": evidence_stream_boundaries(),
        "case_count": len(observations),
        "observations": observations,
        "precision_metrics": metrics,
        "precision_gate": gate,
    }


def classify_shadow_evidence_stream(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Classify shadow evidence streams so smoke and operational ledgers stay separate."""

    record_type = str(payload.get("record_type") or "")
    if record_type == SHADOW_PRECISION_CORPUS_REPORT_TYPE:
        return {
            "record_type": "reconcile_shadow_evidence_stream_classification",
            "stream": "precision_corpus",
            "precision_observation": True,
            "precision_evidence_basis": SHADOW_PRECISION_EVIDENCE_BASIS,
            "counts_toward_enablement_precision": True,
            "reason": "reviewed_replayable_labeled_corpus",
        }
    if record_type == SHADOW_CI_VALIDATION_REPORT_TYPE:
        return {
            "record_type": "reconcile_shadow_evidence_stream_classification",
            "stream": "cascade_validation_smoke",
            "precision_observation": False,
            "precision_evidence_basis": "not_precision_evidence",
            "counts_toward_enablement_precision": False,
            "reason": "synthetic_fixed_fixture_smoke",
        }
    if record_type == SHADOW_ACCUMULATION_REPORT_TYPE:
        return {
            "record_type": "reconcile_shadow_evidence_stream_classification",
            "stream": "operational_accumulation",
            "precision_observation": False,
            "precision_evidence_basis": "not_precision_corpus",
            "counts_toward_enablement_precision": False,
            "reason": "operational_pipeline_evidence_only",
        }
    return {
        "record_type": "reconcile_shadow_evidence_stream_classification",
        "stream": "unknown",
        "precision_observation": False,
        "precision_evidence_basis": "unknown",
        "counts_toward_enablement_precision": False,
        "reason": "unknown_shadow_evidence_stream",
    }


def evidence_stream_boundaries() -> dict[str, Any]:
    """Return the declared separation between shadow evidence streams."""

    return {
        "operational_accumulation": {
            "record_type": SHADOW_ACCUMULATION_REPORT_TYPE,
            "precision_observation": False,
            "counts_toward_enablement_precision": False,
            "purpose": "post-merge inertness and context plumbing evidence",
        },
        "cascade_validation_smoke": {
            "record_type": SHADOW_CI_VALIDATION_REPORT_TYPE,
            "precision_observation": False,
            "counts_toward_enablement_precision": False,
            "purpose": "fixed-fixture Taskmaster cascade smoke",
        },
        "precision_corpus": {
            "record_type": SHADOW_PRECISION_CORPUS_REPORT_TYPE,
            "precision_observation": True,
            "counts_toward_enablement_precision": True,
            "purpose": "reviewed replayable labeled corpus precision measurement",
        },
    }


def pair_key(finding_kind: str, proof: str) -> str:
    return f"{finding_kind}/{proof}"


def _replay_precision_case(
    target: Path,
    *,
    label: Mapping[str, Any],
    source_root: Path,
    clone_parent: Path,
) -> dict[str, Any]:
    _setup_precision_fixture(target, label=label)
    original_gh = aegis_installer._run_gh_pr_list
    if label.get("proof_source") == "github_pr_merged":
        aegis_installer._run_gh_pr_list = lambda _target: _mocked_pr_list(label)
    try:
        report = reconcile(
            target,
            source_root=source_root,
            base_ref="main",
            use_github=label.get("proof_source") == "github_pr_merged",
            preview_candidates=True,
        )
    finally:
        aegis_installer._run_gh_pr_list = original_gh
    preview = report.get("mutation_candidate_preview")
    candidates = []
    if isinstance(preview, Mapping):
        raw_candidates = preview.get("candidates")
        if isinstance(raw_candidates, list):
            candidates = [candidate for candidate in raw_candidates if isinstance(candidate, Mapping)]
    context = _precision_ci_context(label)
    shadow_report = build_shadow_report(
        candidates,
        target_root=target,
        approved_context_proof=context,
        kill_switch_state=SHADOW_CI_VALIDATION_KILL_SWITCH,
        artifact_mode="ci",
        external_anchor=context["external_anchor"],
        clone_parent=clone_parent,
    )
    return {
        "case_id": str(label.get("case_id") or ""),
        "fixture": {
            "merge_topology": str(label.get("merge_topology") or ""),
            "state_json_branch": str(label.get("state_json_branch") or ""),
            "proof_source": str(label.get("proof_source") or ""),
        },
        "label": dict(label),
        "shadow_report": shadow_report,
    }


def _setup_precision_fixture(target: Path, *, label: Mapping[str, Any]) -> None:
    task_id = str(label.get("task_id") or "")
    topology = str(label.get("merge_topology") or "")
    branch = f"feat/task-{task_id}-shadow-precision"
    _init_git_repo(target)
    _write_taskmaster_tasks(
        target,
        [
            {
                "id": int(task_id),
                "title": f"Shadow Precision {task_id}",
                "status": "pending",
                "dependencies": [],
            }
        ],
    )
    _write_state_json(target, str(label.get("state_json_branch") or ""))
    _git(target, "switch", "-c", branch)
    _commit_file(target, f"task-{task_id}.txt", f"task {task_id}\n", f"task {task_id}")
    _git(target, "switch", "main")
    if topology == "fast_forward":
        _git(target, "merge", "--ff-only", branch)
        _commit_file(
            target,
            f"post-ff-{task_id}.txt",
            f"post fast-forward {task_id}\n",
            f"post fast-forward task {task_id}",
        )
    elif topology == "true_merge":
        _git(target, "merge", "--no-ff", branch, "-m", f"merge task {task_id}")
    elif topology in {"squash", "deleted_branch_unknown"}:
        _git(target, "merge", "--squash", branch)
        _git(target, "commit", "-m", f"squash task {task_id}")
        if topology == "deleted_branch_unknown":
            _git(target, "branch", "-D", branch)
    else:
        raise ValueError(f"unknown shadow precision merge topology: {topology}")


def _require_temp_work_root(work_root: Path) -> None:
    temp_root = Path(tempfile.gettempdir()).resolve()
    resolved = work_root.resolve()
    if temp_root != resolved and temp_root not in resolved.parents:
        raise ValueError("shadow precision corpus replay work_root must be under the temp dir")


def _init_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "aegis@example.invalid")
    _git(repo, "config", "user.name", "Aegis Test")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "README.md").write_text("# target\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "initial")


def _write_taskmaster_tasks(repo: Path, tasks: list[dict[str, Any]]) -> None:
    task_dir = repo / ".taskmaster" / "tasks"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "tasks.json").write_text(
        json.dumps({"master": {"tasks": tasks}}, indent=2) + "\n", encoding="utf-8"
    )


def _write_state_json(target: Path, branch: str) -> None:
    if branch == "absent":
        return
    payload = STATE_JSON_BRANCH_PAYLOADS[branch]
    path = target / ".taskmaster" / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _commit_file(repo: Path, rel_path: str, content: str, message: str) -> None:
    path = repo / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _git(repo, "add", rel_path)
    _git(repo, "commit", "-m", message)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", repo.as_posix(), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return result


def _mocked_pr_list(label: Mapping[str, Any]) -> dict[str, Any]:
    task_id = str(label.get("task_id") or "")
    return {
        "available": True,
        "reason": "",
        "prs": [
            {
                "number": int(task_id),
                "state": "MERGED",
                "title": f"Task {task_id} squashed",
                "headRefName": f"feat/task-{task_id}-shadow-precision",
                "baseRefName": "main",
                "mergedAt": "2026-06-05T08:00:00Z",
                "url": f"https://example.invalid/pr/{task_id}",
                "isDraft": False,
            }
        ],
    }


def _precision_ci_context(label: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "context_type": "post_merge_ci",
        "proof_id": f"shadow-precision:{label.get('case_id')}",
        "task_id": str(label.get("task_id") or ""),
        "proof": str(label.get("proof") or ""),
        "external_anchor": f"shadow-precision://{label.get('case_id')}",
        "valid_for_shadow": True,
    }


def _precision_observation(case_result: Mapping[str, Any]) -> dict[str, Any]:
    label = case_result.get("label") if isinstance(case_result.get("label"), Mapping) else {}
    bucket = str(label.get("bucket") or "")
    if bucket not in VALID_LABEL_BUCKETS:
        raise ValueError(f"invalid shadow precision label bucket: {bucket}")
    finding_kind = str(label.get("finding_kind") or "")
    proof = str(label.get("proof") or "")
    expected_pair = pair_key(finding_kind, proof) if finding_kind and proof else ""
    shadow_report = (
        case_result.get("shadow_report")
        if isinstance(case_result.get("shadow_report"), Mapping)
        else {}
    )
    would_apply_records = [
        record
        for record in shadow_report.get("would_apply", [])
        if isinstance(record, Mapping)
    ]
    refused_records = [
        record
        for record in shadow_report.get("shadow_refused", [])
        if isinstance(record, Mapping)
    ]
    actual_pairs = sorted(
        {
            pair_key(str(record.get("finding_kind") or ""), str(record.get("proof") or ""))
            for record in would_apply_records
            if record.get("finding_kind") and record.get("proof")
        }
    )
    if would_apply_records:
        actual_decision = "would_apply"
    elif refused_records:
        actual_decision = "shadow_refused"
    else:
        actual_decision = "no_candidate"
    expected_decision = str(label.get("expected_decision") or "")
    if not expected_decision:
        raise ValueError(f"shadow precision label missing expected_decision: {case_result!r}")
    return {
        "record_type": SHADOW_PRECISION_OBSERVATION_TYPE,
        "case_id": str(case_result.get("case_id") or ""),
        "fixture": dict(case_result.get("fixture") or {}),
        "label": {
            "task_id": str(label.get("task_id") or ""),
            "finding_kind": finding_kind,
            "proof": proof,
            "pair": expected_pair,
            "bucket": bucket,
            "expected_decision": expected_decision,
            "expected_refusal_reason": str(label.get("expected_refusal_reason") or ""),
        },
        "actual": {
            "decision": actual_decision,
            "would_apply_count": len(would_apply_records),
            "shadow_refused_count": len(refused_records),
            "would_apply_pairs": actual_pairs,
            "refusal_reasons": sorted(
                {
                    str(record.get("reason") or "")
                    for record in refused_records
                    if record.get("reason")
                }
            ),
        },
        "expected_decision_matches": expected_decision == actual_decision,
    }


def _precision_metrics(
    observations: Sequence[Mapping[str, Any]], bar: Mapping[str, Any]
) -> dict[str, Any]:
    true_positive = Counter()
    false_positive = Counter()
    false_negative = Counter()
    boundary_leak_count = 0
    label_mismatch_count = 0
    for observation in observations:
        label = observation["label"]
        actual = observation["actual"]
        expected_pair = str(label["pair"])
        expected_bucket = str(label["bucket"])
        actual_pairs = tuple(str(pair) for pair in actual["would_apply_pairs"])
        if not observation.get("expected_decision_matches", False):
            label_mismatch_count += 1
        if expected_bucket == "auto_eligible":
            if expected_pair in actual_pairs:
                true_positive[expected_pair] += 1
            else:
                false_negative[expected_pair] += 1
            for actual_pair in actual_pairs:
                if actual_pair != expected_pair:
                    false_positive[actual_pair] += 1
        elif actual_pairs:
            boundary_leak_count += 1
            for actual_pair in actual_pairs:
                false_positive[actual_pair] += 1

    all_pairs = sorted(
        set(bar.get("auto_eligible_pairs", ()))
        | set(true_positive)
        | set(false_positive)
        | set(false_negative)
    )
    by_pair = {}
    for pair in all_pairs:
        tp = true_positive[pair]
        fp = false_positive[pair]
        fn = false_negative[pair]
        denominator = tp + fp
        by_pair[pair] = {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "precision": (tp / denominator) if denominator else None,
            "precision_observation": denominator > 0,
        }
    return {
        "record_type": "reconcile_shadow_precision_metrics",
        "emitted": True,
        "basis": SHADOW_PRECISION_EVIDENCE_BASIS,
        "by_pair": by_pair,
        "boundary_leak_count": boundary_leak_count,
        "label_mismatch_count": label_mismatch_count,
        "false_positive_count": sum(false_positive.values()),
        "false_negative_count": sum(false_negative.values()),
        "true_positive_count": sum(true_positive.values()),
        "zero_observation_pairs_omitted_from_precision": [
            pair for pair, values in by_pair.items() if not values["precision_observation"]
        ],
    }


def _precision_gate(
    metrics: Mapping[str, Any],
    bar: Mapping[str, Any],
    toolchain_comparison: Mapping[str, Any],
) -> dict[str, Any]:
    if not toolchain_comparison.get("matches"):
        return {
            "record_type": "reconcile_shadow_precision_gate",
            "passed": False,
            "reason": "toolchain_mismatch",
        }
    if not metrics.get("emitted"):
        return {
            "record_type": "reconcile_shadow_precision_gate",
            "passed": False,
            "reason": str(metrics.get("reason") or "metrics_not_emitted"),
        }
    by_pair = metrics.get("by_pair") if isinstance(metrics.get("by_pair"), Mapping) else {}
    pair_results = {}
    for pair in bar.get("auto_eligible_pairs", ()):
        values = by_pair.get(pair, {})
        pair_results[pair] = {
            "passed": (
                values.get("false_positive", 0) <= bar.get("max_false_positives_per_pair", 0)
                and values.get("false_negative", 0) <= bar.get("max_false_negatives_per_pair", 0)
                and values.get("true_positive", 0) >= bar.get("min_true_positives_per_pair", 0)
            ),
            "required_true_positives": bar.get("min_true_positives_per_pair", 0),
            "observed_true_positives": values.get("true_positive", 0),
            "false_positive": values.get("false_positive", 0),
            "false_negative": values.get("false_negative", 0),
        }
    boundary_ok = metrics.get("boundary_leak_count", 0) <= bar.get("max_boundary_leaks", 0)
    labels_ok = metrics.get("label_mismatch_count", 0) <= bar.get("max_label_mismatches", 0)
    passed = boundary_ok and labels_ok and all(result["passed"] for result in pair_results.values())
    return {
        "record_type": "reconcile_shadow_precision_gate",
        "passed": passed,
        "reason": "pre_registered_bar_met" if passed else "pre_registered_bar_not_met",
        "pair_results": pair_results,
        "boundary_leak_count": metrics.get("boundary_leak_count", 0),
        "max_boundary_leaks": bar.get("max_boundary_leaks", 0),
        "label_mismatch_count": metrics.get("label_mismatch_count", 0),
        "max_label_mismatches": bar.get("max_label_mismatches", 0),
    }
