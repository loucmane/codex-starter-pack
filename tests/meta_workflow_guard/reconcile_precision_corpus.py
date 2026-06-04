"""Precision corpus helpers for Aegis reconcile tests."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


AUTO_ELIGIBLE_FINDING_PROOFS = frozenset(
    {
        ("merged_but_not_done", "git_ancestor"),
        ("merged_but_not_done", "github_pr_merged"),
        ("done_but_not_merged", "github_pr_open"),
        ("done_but_not_merged", "github_pr_closed_unmerged"),
    }
)
MANUAL_ONLY_FINDING_KINDS = frozenset(
    {
        "multi_pr_epic_ambiguity",
        "abandoned_in_progress_branch",
        "stale_local_stub",
        "local_ad_hoc_stub",
    }
)
MANUAL_ONLY_MERGE_TRUTH_PROOFS = frozenset({"git_only_non_ancestor_or_missing_base"})
VALID_BUCKETS = frozenset({"auto_eligible", "manual_only", "not_a_finding"})


@dataclass(frozen=True)
class FindingKey:
    kind: str
    task_id: str
    proof: str | None = None


@dataclass(frozen=True)
class ExpectedFinding:
    key: FindingKey
    bucket: str


@dataclass(frozen=True)
class ExpectedNonFinding:
    task_id: str
    proof: str
    bucket: str = "not_a_finding"


@dataclass(frozen=True)
class ObservedFinding:
    key: FindingKey
    bucket: str


@dataclass(frozen=True)
class PrecisionMetrics:
    true_positive_by_finding_proof: dict[str, int]
    false_positive_by_finding_proof: dict[str, int]
    precision_by_finding_proof: dict[str, float]
    boundary_leak_count: int
    expected_non_finding_count: int

    @property
    def false_positive_count(self) -> int:
        return sum(self.false_positive_by_finding_proof.values())


def normalize_findings(report: Mapping[str, Any]) -> list[ObservedFinding]:
    findings = report.get("findings") if isinstance(report.get("findings"), list) else []
    observed: list[ObservedFinding] = []
    for finding in findings:
        if not isinstance(finding, Mapping):
            continue
        key = FindingKey(
            kind=str(finding.get("kind") or ""),
            task_id=str(finding.get("task_id") or ""),
            proof=_finding_proof(finding),
        )
        observed.append(ObservedFinding(key=key, bucket=bucket_for_finding(key)))
    return observed


def bucket_for_finding(key: FindingKey) -> str:
    if key.kind in MANUAL_ONLY_FINDING_KINDS:
        return "manual_only"
    if (key.kind, key.proof) in AUTO_ELIGIBLE_FINDING_PROOFS:
        return "auto_eligible"
    return "manual_only"


def validate_expected_labels(
    expected_findings: Iterable[ExpectedFinding],
    expected_non_findings: Iterable[ExpectedNonFinding] = (),
) -> None:
    for expected in expected_findings:
        if expected.bucket not in VALID_BUCKETS - {"not_a_finding"}:
            raise AssertionError(f"invalid expected finding bucket: {expected}")
        actual_bucket = bucket_for_finding(expected.key)
        if expected.bucket != actual_bucket:
            raise AssertionError(
                "auto/manual boundary leak in expected finding label: "
                f"{expected.key} labelled {expected.bucket}, classifier says {actual_bucket}"
            )
    for expected in expected_non_findings:
        if expected.bucket != "not_a_finding":
            raise AssertionError(f"expected non-findings must use not_a_finding bucket: {expected}")
        if expected.proof not in MANUAL_ONLY_MERGE_TRUTH_PROOFS:
            raise AssertionError(f"expected non-finding proof is not registered manual-only: {expected}")


def assert_precision_contract(
    report: Mapping[str, Any],
    *,
    expected_findings: Iterable[ExpectedFinding],
    expected_non_findings: Iterable[ExpectedNonFinding] = (),
) -> PrecisionMetrics:
    expected_findings = list(expected_findings)
    expected_non_findings = list(expected_non_findings)
    validate_expected_labels(expected_findings, expected_non_findings)

    observed = normalize_findings(report)
    expected_by_key = {expected.key: expected for expected in expected_findings}
    observed_by_key = {finding.key: finding for finding in observed}

    missing = [expected.key for expected in expected_findings if expected.key not in observed_by_key]
    if missing:
        raise AssertionError(f"missing expected reconcile findings: {missing!r}")

    unexpected = [finding for finding in observed if finding.key not in expected_by_key]
    if unexpected:
        raise AssertionError(f"unlabelled/false-positive reconcile findings: {unexpected!r}")

    boundary_leaks = [
        finding
        for finding in observed
        if expected_by_key[finding.key].bucket != finding.bucket
        or (finding.key.kind in MANUAL_ONLY_FINDING_KINDS and finding.bucket == "auto_eligible")
    ]
    if boundary_leaks:
        raise AssertionError(f"auto/manual boundary leaks detected: {boundary_leaks!r}")

    _assert_expected_non_findings(report, expected_non_findings)

    true_positive_by_pair = Counter(_finding_proof_metric_key(expected.key) for expected in expected_findings)
    false_positive_by_pair = Counter(_finding_proof_metric_key(finding.key) for finding in unexpected)
    precision_by_pair = {
        pair: true_positive_by_pair[pair] / (true_positive_by_pair[pair] + false_positive_by_pair[pair])
        for pair in sorted(set(true_positive_by_pair) | set(false_positive_by_pair))
    }
    return PrecisionMetrics(
        true_positive_by_finding_proof=dict(true_positive_by_pair),
        false_positive_by_finding_proof=dict(false_positive_by_pair),
        precision_by_finding_proof=precision_by_pair,
        boundary_leak_count=0,
        expected_non_finding_count=len(expected_non_findings),
    )


def _assert_expected_non_findings(report: Mapping[str, Any], expected_non_findings: list[ExpectedNonFinding]) -> None:
    findings_by_task = {
        str(finding.get("task_id") or "")
        for finding in report.get("findings", [])
        if isinstance(finding, Mapping)
    }
    tasks_by_id = {
        str(task.get("task_id") or ""): task
        for task in report.get("tasks", [])
        if isinstance(task, Mapping)
    }
    missing: list[ExpectedNonFinding] = []
    wrong_proof: list[tuple[ExpectedNonFinding, str | None]] = []
    unexpected_findings: list[ExpectedNonFinding] = []
    for expected in expected_non_findings:
        task = tasks_by_id.get(expected.task_id)
        if task is None:
            missing.append(expected)
            continue
        merge_truth = task.get("merge_truth") if isinstance(task.get("merge_truth"), Mapping) else {}
        proof = str(merge_truth.get("proof") or "")
        if proof != expected.proof:
            wrong_proof.append((expected, proof))
        if expected.task_id in findings_by_task:
            unexpected_findings.append(expected)
    if missing:
        raise AssertionError(f"missing expected non-finding task reports: {missing!r}")
    if wrong_proof:
        raise AssertionError(f"expected non-finding proof mismatch: {wrong_proof!r}")
    if unexpected_findings:
        raise AssertionError(f"expected non-finding tasks emitted findings: {unexpected_findings!r}")


def _finding_proof_metric_key(key: FindingKey) -> str:
    proof = key.proof or "none"
    return f"{key.kind}/{proof}"


def _finding_proof(finding: Mapping[str, Any]) -> str | None:
    evidence = finding.get("evidence") if isinstance(finding.get("evidence"), Mapping) else {}
    merge_truth = evidence.get("merge_truth") if isinstance(evidence.get("merge_truth"), Mapping) else {}
    proof = merge_truth.get("proof")
    return str(proof) if proof else None
