#!/usr/bin/env python3
"""Portable, non-mutating template governance assessment helpers."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _repo_structure import load_repo_structure
from template_versioning import classify_version_change


POLICY_RELATIVE_PATH = Path("metadata") / "template-governance-policy.json"


class GovernanceError(ValueError):
    """Raised when governance policy or assessment input is invalid."""


@dataclass(frozen=True)
class GovernanceReviewClass:
    """Review requirements for a governance class."""

    name: str
    priority: int
    required_roles: Tuple[str, ...]
    approval: str
    escalation: str
    notification_audiences: Tuple[str, ...]
    required_evidence: Tuple[str, ...]


@dataclass(frozen=True)
class TemplateGovernancePolicy:
    """Data-driven template governance policy loaded from the configured templates root."""

    version: str
    schema: str
    roles: Mapping[str, str]
    review_classes: Mapping[str, GovernanceReviewClass]
    version_change_review: Mapping[str, str]
    lifecycle_transition_review: Mapping[str, str]
    default_review_class: str
    emergency_review_class: str
    notification_mode: str = "evidence-only"

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "TemplateGovernancePolicy":
        roles = _string_mapping(payload.get("roles"))
        raw_review_classes = payload.get("review_classes", {})
        if not isinstance(raw_review_classes, Mapping):
            raise GovernanceError("review_classes must be an object")

        review_classes: dict[str, GovernanceReviewClass] = {}
        for name, raw_review_class in raw_review_classes.items():
            if not isinstance(raw_review_class, Mapping):
                raise GovernanceError(f"review class {name!r} must be an object")
            class_name = str(name)
            review_classes[class_name] = GovernanceReviewClass(
                name=class_name,
                priority=int(raw_review_class.get("priority", 0)),
                required_roles=_string_tuple(raw_review_class.get("required_roles")),
                approval=str(raw_review_class.get("approval") or ""),
                escalation=str(raw_review_class.get("escalation") or ""),
                notification_audiences=_string_tuple(raw_review_class.get("notification_audiences")),
                required_evidence=_string_tuple(raw_review_class.get("required_evidence")),
            )

        policy = cls(
            version=str(payload.get("version") or "unversioned"),
            schema=str(payload.get("schema") or "template-governance-review.v1"),
            roles=roles,
            review_classes=review_classes,
            version_change_review=_string_mapping(payload.get("version_change_review")),
            lifecycle_transition_review=_string_mapping(payload.get("lifecycle_transition_review")),
            default_review_class=str(payload.get("default_review_class") or "routine"),
            emergency_review_class=str(payload.get("emergency_review_class") or "emergency"),
            notification_mode=str(payload.get("notification_mode") or "evidence-only"),
        )
        policy.validate()
        return policy

    def review_class(self, name: str) -> GovernanceReviewClass:
        try:
            return self.review_classes[name]
        except KeyError as exc:
            raise GovernanceError(f"Unknown review class: {name}") from exc

    def class_for_version_change(self, change_type: str) -> str:
        return self.version_change_review.get(change_type, self.default_review_class)

    def class_for_lifecycle_transition(self, current: str, target: str) -> str:
        transition_key = f"{current}->{target}"
        return self.lifecycle_transition_review.get(transition_key, self.default_review_class)

    def highest_review_class(self, names: Sequence[str]) -> GovernanceReviewClass:
        if not names:
            return self.review_class(self.default_review_class)
        return max((self.review_class(name) for name in names), key=lambda item: item.priority)

    def validate(self) -> None:
        if not self.roles:
            raise GovernanceError("Governance policy requires at least one role")
        if not self.review_classes:
            raise GovernanceError("Governance policy requires at least one review class")
        for required in (self.default_review_class, self.emergency_review_class):
            if required not in self.review_classes:
                raise GovernanceError(f"Required review class {required!r} is not defined")

        role_names = set(self.roles)
        seen_priorities: set[int] = set()
        for review_class in self.review_classes.values():
            if review_class.priority in seen_priorities:
                raise GovernanceError(f"Duplicate review priority: {review_class.priority}")
            seen_priorities.add(review_class.priority)
            if not review_class.required_roles:
                raise GovernanceError(f"Review class {review_class.name!r} requires at least one role")
            unknown_roles = sorted(set(review_class.required_roles) - role_names)
            if unknown_roles:
                raise GovernanceError(
                    f"Review class {review_class.name!r} references unknown role(s): {', '.join(unknown_roles)}"
                )
            if not review_class.approval.strip():
                raise GovernanceError(f"Review class {review_class.name!r} requires approval guidance")

        known_classes = set(self.review_classes)
        for mapping_name, mapping in (
            ("version_change_review", self.version_change_review),
            ("lifecycle_transition_review", self.lifecycle_transition_review),
        ):
            unknown_classes = sorted(set(mapping.values()) - known_classes)
            if unknown_classes:
                raise GovernanceError(
                    f"{mapping_name} references unknown review class(es): {', '.join(unknown_classes)}"
                )


@dataclass(frozen=True)
class GovernanceReason:
    """Single input signal that influenced governance assessment."""

    signal: str
    value: str
    review_class: str
    message: str


@dataclass(frozen=True)
class GovernanceAssessment:
    """Reviewable template governance assessment."""

    schema: str
    path: str
    review_class: str
    priority: int
    required_roles: Tuple[str, ...]
    approval: str
    escalation: str
    notification_audiences: Tuple[str, ...]
    notification_mode: str
    required_evidence: Tuple[str, ...]
    reasons: Tuple[GovernanceReason, ...]
    note: Optional[str] = None


def load_governance_policy(repo_root: Path | str | None = None) -> TemplateGovernancePolicy:
    """Load the repo-local template governance policy."""
    root = Path(repo_root or Path(__file__).resolve().parent.parent).resolve()
    structure = load_repo_structure(root)
    policy_path = structure.templates_root / POLICY_RELATIVE_PATH
    if not policy_path.exists():
        raise GovernanceError(f"Template governance policy not found: {policy_path}")
    return TemplateGovernancePolicy.from_mapping(json.loads(policy_path.read_text(encoding="utf-8")))


def assess_governance(
    *,
    path: str = "",
    previous_version: Optional[str] = None,
    current_version: Optional[str] = None,
    lifecycle_from: Optional[str] = None,
    lifecycle_to: Optional[str] = None,
    emergency: bool = False,
    note: Optional[str] = None,
    policy: Optional[TemplateGovernancePolicy] = None,
    repo_root: Path | str | None = None,
) -> GovernanceAssessment:
    """Assess the required governance review path without mutating repository files."""
    active_policy = policy or load_governance_policy(repo_root)
    candidate_classes: list[str] = [active_policy.default_review_class]
    reasons: list[GovernanceReason] = []

    if (previous_version is None) != (current_version is None):
        raise GovernanceError("previous_version and current_version must be supplied together")

    if previous_version is not None and current_version is not None:
        change_type = classify_version_change(previous_version, current_version)
        review_class = active_policy.class_for_version_change(change_type)
        candidate_classes.append(review_class)
        reasons.append(
            GovernanceReason(
                "version_change",
                change_type,
                review_class,
                f"Version change {previous_version} -> {current_version} classified as {change_type}",
            )
        )

    if (lifecycle_from is None) != (lifecycle_to is None):
        raise GovernanceError("lifecycle_from and lifecycle_to must be supplied together")

    if lifecycle_from is not None and lifecycle_to is not None:
        transition = f"{lifecycle_from}->{lifecycle_to}"
        review_class = active_policy.class_for_lifecycle_transition(lifecycle_from, lifecycle_to)
        candidate_classes.append(review_class)
        reasons.append(
            GovernanceReason(
                "lifecycle_transition",
                transition,
                review_class,
                f"Lifecycle transition {transition} mapped to {review_class} review",
            )
        )

    if emergency:
        candidate_classes.append(active_policy.emergency_review_class)
        reasons.append(
            GovernanceReason(
                "emergency",
                "true",
                active_policy.emergency_review_class,
                "Emergency flag forces emergency governance review",
            )
        )

    if not reasons:
        reasons.append(
            GovernanceReason(
                "default",
                "none",
                active_policy.default_review_class,
                "No elevated governance signals supplied",
            )
        )

    selected = active_policy.highest_review_class(candidate_classes)
    return GovernanceAssessment(
        schema=active_policy.schema,
        path=path,
        review_class=selected.name,
        priority=selected.priority,
        required_roles=selected.required_roles,
        approval=selected.approval,
        escalation=selected.escalation,
        notification_audiences=selected.notification_audiences,
        notification_mode=active_policy.notification_mode,
        required_evidence=selected.required_evidence,
        reasons=tuple(reasons),
        note=note,
    )


def assessment_to_dict(assessment: GovernanceAssessment) -> dict[str, object]:
    """Return a JSON-serializable governance assessment payload."""
    payload = {
        "schema": assessment.schema,
        "path": assessment.path,
        "review_class": assessment.review_class,
        "priority": assessment.priority,
        "required_roles": list(assessment.required_roles),
        "approval": assessment.approval,
        "escalation": assessment.escalation,
        "notification_audiences": list(assessment.notification_audiences),
        "notification_mode": assessment.notification_mode,
        "required_evidence": list(assessment.required_evidence),
        "reasons": [asdict(reason) for reason in assessment.reasons],
    }
    if assessment.note is not None:
        payload["note"] = assessment.note
    return payload


def _print_assessment_text(assessment: GovernanceAssessment) -> None:
    label = f"{assessment.review_class}: {assessment.path}" if assessment.path else assessment.review_class
    print(label)
    print(f"schema: {assessment.schema}")
    print(f"required_roles: {', '.join(assessment.required_roles)}")
    print(f"approval: {assessment.approval}")
    print(f"escalation: {assessment.escalation}")
    print(f"notification_mode: {assessment.notification_mode}")
    print(f"notification_audiences: {', '.join(assessment.notification_audiences)}")
    print("required_evidence:")
    for evidence in assessment.required_evidence:
        print(f"- {evidence}")
    print("reasons:")
    for reason in assessment.reasons:
        print(f"- {reason.signal}: {reason.value} -> {reason.review_class}: {reason.message}")
    if assessment.note:
        print(f"note: {assessment.note}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assess template governance review requirements.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    assess = subparsers.add_parser("assess", help="Assess a proposed template governance path")
    assess.add_argument("--path", default="")
    assess.add_argument("--previous-version")
    assess.add_argument("--current-version")
    assess.add_argument("--lifecycle-from")
    assess.add_argument("--lifecycle-to")
    assess.add_argument("--emergency", action="store_true")
    assess.add_argument("--note")
    assess.add_argument("--repo-root", default=".")
    assess.add_argument("--format", choices=("text", "json"), default="text")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "assess":
        assessment = assess_governance(
            path=args.path,
            previous_version=args.previous_version,
            current_version=args.current_version,
            lifecycle_from=args.lifecycle_from,
            lifecycle_to=args.lifecycle_to,
            emergency=args.emergency,
            note=args.note,
            repo_root=args.repo_root,
        )
        if args.format == "json":
            print(json.dumps(assessment_to_dict(assessment), indent=2))
        else:
            _print_assessment_text(assessment)
        return 0

    return 2


def _string_tuple(value: object) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return tuple(str(item) for item in value)
    raise GovernanceError(f"Expected string list, got {type(value).__name__}")


def _string_mapping(value: object) -> Mapping[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise GovernanceError(f"Expected object mapping, got {type(value).__name__}")
    return {str(key): str(item) for key, item in value.items()}


if __name__ == "__main__":
    raise SystemExit(main())
