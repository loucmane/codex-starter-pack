#!/usr/bin/env python3
"""Portable template version comparison and compatibility helpers."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _repo_structure import load_repo_structure


POLICY_RELATIVE_PATH = Path("metadata") / "template-versioning-policy.json"
VERSION_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)"
    r"(?:\.(?P<patch>0|[1-9]\d*))?"
    r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
CHANGE_TYPES = ("same", "patch", "minor", "major", "downgrade", "release", "prerelease")


class VersioningError(ValueError):
    """Raised when template versioning policy or input data is invalid."""


@dataclass(frozen=True)
class TemplateVersioningPolicy:
    """Data-driven template versioning policy loaded from the configured templates root."""

    version: str
    compatible_changes: Tuple[str, ...]
    migration_required_changes: Tuple[str, ...]
    warning_changes: Tuple[str, ...]
    history_schema: str = "template-version-history.v1"
    required_history_fields: Tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "TemplateVersioningPolicy":
        history = payload.get("history", {})
        if history is None:
            history = {}
        if not isinstance(history, Mapping):
            raise VersioningError("history must be an object")

        policy = cls(
            version=str(payload.get("version") or "unversioned"),
            compatible_changes=_string_tuple(payload.get("compatible_changes")),
            migration_required_changes=_string_tuple(payload.get("migration_required_changes")),
            warning_changes=_string_tuple(payload.get("warning_changes")),
            history_schema=str(history.get("schema") or "template-version-history.v1"),
            required_history_fields=_string_tuple(history.get("required_fields")),
        )
        policy.validate()
        return policy

    @property
    def known_change_types(self) -> Tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                (
                    *CHANGE_TYPES,
                    *self.compatible_changes,
                    *self.migration_required_changes,
                    *self.warning_changes,
                )
            )
        )

    def validate(self) -> None:
        known = set(CHANGE_TYPES)
        for group_name, group in (
            ("compatible_changes", self.compatible_changes),
            ("migration_required_changes", self.migration_required_changes),
            ("warning_changes", self.warning_changes),
        ):
            if not group:
                raise VersioningError(f"{group_name} requires at least one change type")
            unknown = sorted(set(group) - known)
            if unknown:
                raise VersioningError(f"{group_name} contains unknown change type(s): {', '.join(unknown)}")
        if not self.history_schema.strip():
            raise VersioningError("history.schema must not be empty")


@dataclass(frozen=True)
class TemplateVersion:
    """Parsed semantic template version with optional prerelease/build metadata."""

    major: int
    minor: int
    patch: int
    prerelease: Tuple[str, ...] = ()
    build: Tuple[str, ...] = ()
    raw: str = ""

    @classmethod
    def parse(cls, value: str) -> "TemplateVersion":
        text = str(value or "").strip()
        match = VERSION_RE.match(text)
        if not match:
            raise VersioningError(f"Invalid semantic version: {value}")

        prerelease = _identifier_tuple(match.group("prerelease"), label="prerelease")
        build = _identifier_tuple(match.group("build"), label="build")
        return cls(
            major=int(match.group("major")),
            minor=int(match.group("minor")),
            patch=int(match.group("patch") or 0),
            prerelease=prerelease,
            build=build,
            raw=text,
        )

    @property
    def core(self) -> Tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    @property
    def normalized(self) -> str:
        value = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            value += "-" + ".".join(self.prerelease)
        if self.build:
            value += "+" + ".".join(self.build)
        return value

    @property
    def comparable(self) -> str:
        value = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            value += "-" + ".".join(self.prerelease)
        return value


@dataclass(frozen=True)
class VersioningIssue:
    """Single compatibility issue or warning."""

    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class VersionCompatibilityAssessment:
    """Compatibility assessment for a template version transition."""

    path: str
    previous_version: str
    current_version: str
    change_type: str
    compatible: bool
    migration_required: bool
    rollback_version: str
    issues: Tuple[VersioningIssue, ...]

    @property
    def ok(self) -> bool:
        return self.compatible and not any(issue.severity == "error" for issue in self.issues)


@dataclass(frozen=True)
class VersionHistoryEntry:
    """Reviewable, non-mutating template version history entry."""

    schema: str
    path: str
    previous_version: str
    current_version: str
    change_type: str
    changed_at: str
    compatible: bool
    migration_required: bool
    rollback_version: str
    issues: Tuple[VersioningIssue, ...]
    note: Optional[str] = None


def load_versioning_policy(repo_root: Path | str | None = None) -> TemplateVersioningPolicy:
    """Load the repo-local template versioning policy."""
    root = Path(repo_root or Path(__file__).resolve().parent.parent).resolve()
    structure = load_repo_structure(root)
    policy_path = structure.templates_root / POLICY_RELATIVE_PATH
    if not policy_path.exists():
        raise VersioningError(f"Template versioning policy not found: {policy_path}")
    return TemplateVersioningPolicy.from_mapping(json.loads(policy_path.read_text(encoding="utf-8")))


def parse_version(value: str) -> TemplateVersion:
    """Parse a semantic template version."""
    return TemplateVersion.parse(value)


def compare_versions(left: str | TemplateVersion, right: str | TemplateVersion) -> int:
    """Compare two semantic versions, ignoring build metadata."""
    left_version = left if isinstance(left, TemplateVersion) else parse_version(str(left))
    right_version = right if isinstance(right, TemplateVersion) else parse_version(str(right))

    if left_version.core != right_version.core:
        return -1 if left_version.core < right_version.core else 1

    return _compare_prerelease(left_version.prerelease, right_version.prerelease)


def classify_version_change(previous: str, current: str) -> str:
    """Classify a previous/current version transition."""
    previous_version = parse_version(previous)
    current_version = parse_version(current)
    comparison = compare_versions(previous_version, current_version)
    if comparison == 0:
        return "same"
    if comparison > 0:
        return "downgrade"

    if current_version.prerelease:
        return "prerelease"
    if previous_version.prerelease and previous_version.core == current_version.core and not current_version.prerelease:
        return "release"
    if current_version.major > previous_version.major:
        return "major"
    if current_version.minor > previous_version.minor:
        return "minor"
    return "patch"


def assess_version_change(
    previous: str,
    current: str,
    *,
    policy: Optional[TemplateVersioningPolicy] = None,
    repo_root: Path | str | None = None,
    path: str = "",
) -> VersionCompatibilityAssessment:
    """Assess compatibility for a previous/current template version pair without mutating files."""
    active_policy = policy or load_versioning_policy(repo_root)
    previous_version = parse_version(previous)
    current_version = parse_version(current)
    change_type = classify_version_change(previous_version.normalized, current_version.normalized)
    issues: list[VersioningIssue] = []

    compatible = change_type in active_policy.compatible_changes
    migration_required = change_type in active_policy.migration_required_changes
    if change_type in active_policy.warning_changes:
        issues.append(
            VersioningIssue(
                "warning",
                f"{change_type}_version",
                f"Version change {previous_version.normalized} -> {current_version.normalized} is {change_type}",
            )
        )
    if migration_required:
        issues.append(
            VersioningIssue(
                "error" if not compatible else "warning",
                "migration_required",
                f"Version change {previous_version.normalized} -> {current_version.normalized} requires migration review",
            )
        )

    return VersionCompatibilityAssessment(
        path=path,
        previous_version=previous_version.normalized,
        current_version=current_version.normalized,
        change_type=change_type,
        compatible=compatible,
        migration_required=migration_required,
        rollback_version=previous_version.normalized,
        issues=tuple(issues),
    )


def build_history_entry(
    *,
    path: str,
    previous: str,
    current: str,
    changed_at: str,
    note: Optional[str] = None,
    policy: Optional[TemplateVersioningPolicy] = None,
    repo_root: Path | str | None = None,
) -> VersionHistoryEntry:
    """Build a reviewable version history entry without changing template files."""
    if not path.strip():
        raise VersioningError("history entry requires path")
    if not changed_at.strip():
        raise VersioningError("history entry requires changed_at")
    active_policy = policy or load_versioning_policy(repo_root)
    assessment = assess_version_change(previous, current, policy=active_policy, path=path)
    return VersionHistoryEntry(
        schema=active_policy.history_schema,
        path=path,
        previous_version=assessment.previous_version,
        current_version=assessment.current_version,
        change_type=assessment.change_type,
        changed_at=changed_at,
        compatible=assessment.compatible,
        migration_required=assessment.migration_required,
        rollback_version=assessment.rollback_version,
        issues=assessment.issues,
        note=note,
    )


def assessment_to_dict(assessment: VersionCompatibilityAssessment) -> dict[str, object]:
    """Return a JSON-serializable assessment payload."""
    return {
        "path": assessment.path,
        "previous_version": assessment.previous_version,
        "current_version": assessment.current_version,
        "change_type": assessment.change_type,
        "compatible": assessment.compatible,
        "migration_required": assessment.migration_required,
        "rollback_version": assessment.rollback_version,
        "ok": assessment.ok,
        "issues": [asdict(issue) for issue in assessment.issues],
    }


def history_entry_to_dict(entry: VersionHistoryEntry) -> dict[str, object]:
    """Return a JSON-serializable history entry payload."""
    payload = {
        "schema": entry.schema,
        "path": entry.path,
        "previous_version": entry.previous_version,
        "current_version": entry.current_version,
        "change_type": entry.change_type,
        "changed_at": entry.changed_at,
        "compatible": entry.compatible,
        "migration_required": entry.migration_required,
        "rollback_version": entry.rollback_version,
        "issues": [asdict(issue) for issue in entry.issues],
    }
    if entry.note is not None:
        payload["note"] = entry.note
    return payload


def _identifier_tuple(value: Optional[str], *, label: str) -> Tuple[str, ...]:
    if not value:
        return ()
    identifiers = tuple(value.split("."))
    for identifier in identifiers:
        if not identifier:
            raise VersioningError(f"{label} identifiers must not be empty")
        if identifier.isdigit() and len(identifier) > 1 and identifier.startswith("0"):
            raise VersioningError(f"{label} numeric identifiers must not contain leading zeroes")
    return identifiers


def _compare_prerelease(left: Tuple[str, ...], right: Tuple[str, ...]) -> int:
    if left == right:
        return 0
    if not left:
        return 1
    if not right:
        return -1
    for left_part, right_part in zip(left, right):
        if left_part == right_part:
            continue
        left_numeric = left_part.isdigit()
        right_numeric = right_part.isdigit()
        if left_numeric and right_numeric:
            left_int = int(left_part)
            right_int = int(right_part)
            return -1 if left_int < right_int else 1
        if left_numeric:
            return -1
        if right_numeric:
            return 1
        return -1 if left_part < right_part else 1
    return -1 if len(left) < len(right) else 1


def _string_tuple(value: object) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return tuple(str(item) for item in value)
    raise VersioningError(f"Expected string list, got {type(value).__name__}")


def _comparison_symbol(comparison: int) -> str:
    if comparison < 0:
        return "<"
    if comparison > 0:
        return ">"
    return "=="


def _print_assessment_text(assessment: VersionCompatibilityAssessment) -> None:
    label = "compatible" if assessment.compatible else "incompatible"
    location = f"{assessment.path}: " if assessment.path else ""
    print(
        f"{label}: {location}{assessment.previous_version} -> {assessment.current_version} "
        f"({assessment.change_type})"
    )
    print(f"migration_required: {str(assessment.migration_required).lower()}")
    print(f"rollback_version: {assessment.rollback_version}")
    for issue in assessment.issues:
        print(f"{issue.severity}: {issue.code}: {issue.message}")


def _print_history_text(entry: VersionHistoryEntry) -> None:
    print(f"{entry.schema}: {entry.path}: {entry.previous_version} -> {entry.current_version} ({entry.change_type})")
    print(f"changed_at: {entry.changed_at}")
    print(f"compatible: {str(entry.compatible).lower()}")
    print(f"migration_required: {str(entry.migration_required).lower()}")
    print(f"rollback_version: {entry.rollback_version}")
    if entry.note:
        print(f"note: {entry.note}")
    for issue in entry.issues:
        print(f"{issue.severity}: {issue.code}: {issue.message}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare and assess template semantic versions.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compare = subparsers.add_parser("compare", help="Compare two semantic versions")
    compare.add_argument("left")
    compare.add_argument("right")

    assess = subparsers.add_parser("assess", help="Assess compatibility for a version transition")
    assess.add_argument("previous")
    assess.add_argument("current")
    assess.add_argument("--path", default="")
    assess.add_argument("--repo-root", default=".")
    assess.add_argument("--format", choices=("text", "json"), default="text")

    history = subparsers.add_parser("history-entry", help="Build a reviewable version history entry")
    history.add_argument("previous")
    history.add_argument("current")
    history.add_argument("--path", required=True)
    history.add_argument("--changed-at", required=True)
    history.add_argument("--note")
    history.add_argument("--repo-root", default=".")
    history.add_argument("--format", choices=("text", "json"), default="text")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "compare":
        left = parse_version(args.left)
        right = parse_version(args.right)
        comparison = compare_versions(left, right)
        print(f"{left.comparable} {_comparison_symbol(comparison)} {right.comparable}")
        return 0

    if args.command == "assess":
        assessment = assess_version_change(args.previous, args.current, repo_root=args.repo_root, path=args.path)
        if args.format == "json":
            print(json.dumps(assessment_to_dict(assessment), indent=2))
        else:
            _print_assessment_text(assessment)
        return 0

    if args.command == "history-entry":
        entry = build_history_entry(
            path=args.path,
            previous=args.previous,
            current=args.current,
            changed_at=args.changed_at,
            note=args.note,
            repo_root=args.repo_root,
        )
        if args.format == "json":
            print(json.dumps(history_entry_to_dict(entry), indent=2))
        else:
            _print_history_text(entry)
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
