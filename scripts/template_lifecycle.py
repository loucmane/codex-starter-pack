#!/usr/bin/env python3
"""Template lifecycle policy, transition, versioning, and audit helpers."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _repo_structure import load_repo_structure
from template_registry import TemplateRecord, TemplateRegistry, parse_frontmatter


POLICY_RELATIVE_PATH = Path("metadata") / "template-lifecycle-policy.json"
SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)"
    r"(?:\.(?P<patch>0|[1-9]\d*))?(?P<suffix>[-+][0-9A-Za-z.-]+)?$"
)


class LifecycleError(ValueError):
    """Raised when lifecycle policy or input data is invalid."""


@dataclass(frozen=True)
class TemplateLifecyclePolicy:
    """Data-driven template lifecycle policy loaded from the configured templates root."""

    version: str
    states: Tuple[str, ...]
    compatibility_statuses: Mapping[str, str]
    ignored_statuses: Tuple[str, ...]
    transitions: Mapping[str, Tuple[str, ...]]
    grace_days: int
    archive_after_days: int
    deprecated_since_key: str = "deprecated_since"
    replacement_key: str = "replacement"
    migration_notice_key: str = "migration_notice"

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "TemplateLifecyclePolicy":
        states = _string_tuple(payload.get("states"))
        if not states:
            raise LifecycleError("Lifecycle policy requires at least one state")

        raw_compatibility = payload.get("compatibility_statuses", {})
        if not isinstance(raw_compatibility, Mapping):
            raise LifecycleError("compatibility_statuses must be an object")
        compatibility = {str(key): str(value) for key, value in raw_compatibility.items()}

        ignored_statuses = _string_tuple(payload.get("ignored_statuses"))

        raw_transitions = payload.get("transitions", {})
        if not isinstance(raw_transitions, Mapping):
            raise LifecycleError("transitions must be an object")
        transitions = {str(key): _string_tuple(value) for key, value in raw_transitions.items()}

        deprecation = payload.get("deprecation", {})
        if not isinstance(deprecation, Mapping):
            raise LifecycleError("deprecation must be an object")

        policy = cls(
            version=str(payload.get("version") or "unversioned"),
            states=states,
            compatibility_statuses=compatibility,
            ignored_statuses=ignored_statuses,
            transitions=transitions,
            grace_days=int(deprecation.get("grace_days", 30)),
            archive_after_days=int(deprecation.get("archive_after_days", 90)),
            deprecated_since_key=str(deprecation.get("deprecated_since_key", "deprecated_since")),
            replacement_key=str(deprecation.get("replacement_key", "replacement")),
            migration_notice_key=str(deprecation.get("migration_notice_key", "migration_notice")),
        )
        policy.validate()
        return policy

    @property
    def known_statuses(self) -> Tuple[str, ...]:
        return tuple(dict.fromkeys((*self.states, *self.compatibility_statuses.keys(), *self.ignored_statuses)))

    def canonical_status(self, status: object) -> Optional[str]:
        text = str(status or "").strip()
        if not text:
            return None
        if text in self.ignored_statuses:
            return None
        if text in self.states:
            return text
        return self.compatibility_statuses.get(text)

    def is_transition_allowed(self, current: str, target: str) -> bool:
        current_status = self.canonical_status(current)
        target_status = self.canonical_status(target)
        if not current_status or not target_status:
            return False
        return target_status in self.transitions.get(current_status, ())

    def validate(self) -> None:
        state_set = set(self.states)
        for compatibility, canonical in self.compatibility_statuses.items():
            if canonical not in state_set:
                raise LifecycleError(f"Compatibility status {compatibility!r} maps to unknown state {canonical!r}")
        for state, targets in self.transitions.items():
            if state not in state_set:
                raise LifecycleError(f"Transition source {state!r} is not a lifecycle state")
            for target in targets:
                if target not in state_set:
                    raise LifecycleError(f"Transition target {target!r} is not a lifecycle state")


@dataclass(frozen=True)
class LifecycleIssue:
    """Single lifecycle audit finding for a template record."""

    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class LifecycleAudit:
    """Lifecycle audit result for a template record or metadata block."""

    path: str
    status: Optional[str]
    canonical_status: Optional[str]
    issues: Tuple[LifecycleIssue, ...]

    @property
    def ok(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)


def load_lifecycle_policy(repo_root: Path | str | None = None) -> TemplateLifecyclePolicy:
    """Load the repo-local template lifecycle policy."""
    root = Path(repo_root or Path(__file__).resolve().parent.parent).resolve()
    structure = load_repo_structure(root)
    policy_path = structure.templates_root / POLICY_RELATIVE_PATH
    if not policy_path.exists():
        raise LifecycleError(f"Template lifecycle policy not found: {policy_path}")
    return TemplateLifecyclePolicy.from_mapping(json.loads(policy_path.read_text(encoding="utf-8")))


def bump_semver(version: str, level: str) -> str:
    """Return a major/minor/patch semver bump."""
    match = SEMVER_RE.match(version.strip())
    if not match:
        raise LifecycleError(f"Invalid semantic version: {version}")
    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch") or 0)

    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    if level == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise LifecycleError(f"Unknown version bump level: {level}")


def audit_metadata(
    path: str,
    metadata: Mapping[str, object],
    *,
    policy: TemplateLifecyclePolicy,
    today: Optional[date] = None,
) -> LifecycleAudit:
    """Audit a template metadata block against lifecycle policy without mutating files."""
    now = today or date.today()
    issues: list[LifecycleIssue] = []
    raw_status = _string_or_none(metadata.get("status"))
    canonical = policy.canonical_status(raw_status)

    if raw_status is None:
        issues.append(LifecycleIssue("error", "missing_status", "Template metadata is missing status"))
    elif raw_status not in policy.ignored_statuses and canonical is None:
        issues.append(
            LifecycleIssue(
                "error",
                "unknown_status",
                f"Template status {raw_status!r} is not in lifecycle policy known statuses",
            )
        )

    version = _string_or_none(metadata.get("version"))
    if version and not SEMVER_RE.match(version):
        issues.append(LifecycleIssue("error", "invalid_version", f"Template version {version!r} is not semver"))

    if canonical == "deprecated":
        issues.extend(_audit_deprecated_metadata(metadata, policy=policy, today=now))

    return LifecycleAudit(path=path, status=raw_status, canonical_status=canonical, issues=tuple(issues))


def audit_record(
    record: TemplateRecord,
    *,
    policy: TemplateLifecyclePolicy,
    today: Optional[date] = None,
) -> LifecycleAudit:
    """Audit a registry template record."""
    return audit_metadata(record.path, record.metadata, policy=policy, today=today)


def audit_registry(
    repo_root: Path | str | None = None,
    *,
    today: Optional[date] = None,
    include_missing: bool = False,
) -> Tuple[LifecycleAudit, ...]:
    """Audit template registry records, skipping metadata-free records by default."""
    root = Path(repo_root or Path(__file__).resolve().parent.parent).resolve()
    policy = load_lifecycle_policy(root)
    registry = TemplateRegistry(repo_root=root)
    audits: list[LifecycleAudit] = []
    for record in registry.records():
        if not include_missing and "status" not in record.metadata:
            continue
        audits.append(audit_record(record, policy=policy, today=today))
    return tuple(audits)


def parse_template_file(path: Path) -> Mapping[str, object]:
    """Parse template frontmatter from a single markdown file."""
    return parse_frontmatter(path.read_text(encoding="utf-8"))


def _audit_deprecated_metadata(
    metadata: Mapping[str, object],
    *,
    policy: TemplateLifecyclePolicy,
    today: date,
) -> Tuple[LifecycleIssue, ...]:
    issues: list[LifecycleIssue] = []
    deprecated_since = _string_or_none(metadata.get(policy.deprecated_since_key))
    replacement = _string_or_none(metadata.get(policy.replacement_key))
    migration_notice = _string_or_none(metadata.get(policy.migration_notice_key))

    if not replacement and not migration_notice:
        issues.append(
            LifecycleIssue(
                "warning",
                "missing_migration_notice",
                "Deprecated template should define replacement or migration_notice",
            )
        )

    if deprecated_since is None:
        issues.append(
            LifecycleIssue(
                "warning",
                "missing_deprecated_since",
                f"Deprecated template should define {policy.deprecated_since_key}",
            )
        )
        return tuple(issues)

    try:
        deprecated_date = date.fromisoformat(deprecated_since)
    except ValueError:
        issues.append(
            LifecycleIssue(
                "error",
                "invalid_deprecated_since",
                f"{policy.deprecated_since_key} must be ISO date YYYY-MM-DD",
            )
        )
        return tuple(issues)

    age_days = (today - deprecated_date).days
    if age_days < 0:
        issues.append(
            LifecycleIssue(
                "error",
                "future_deprecated_since",
                f"{policy.deprecated_since_key} cannot be in the future",
            )
        )
    if age_days >= policy.grace_days:
        issues.append(
            LifecycleIssue(
                "warning",
                "deprecation_grace_expired",
                f"Deprecated template is {age_days} days old; {policy.grace_days}-day grace period expired",
            )
        )
    if age_days >= policy.archive_after_days:
        issues.append(
            LifecycleIssue(
                "recommendation",
                "archive_recommended",
                f"Deprecated template is {age_days} days old; archive threshold is {policy.archive_after_days} days",
            )
        )
    return tuple(issues)


def _string_tuple(value: object) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return tuple(str(item) for item in value)
    raise LifecycleError(f"Expected string list, got {type(value).__name__}")


def _string_or_none(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _audit_to_dict(audit: LifecycleAudit) -> dict[str, object]:
    return {
        "path": audit.path,
        "status": audit.status,
        "canonical_status": audit.canonical_status,
        "ok": audit.ok,
        "issues": [asdict(issue) for issue in audit.issues],
    }


def _parse_today(value: Optional[str]) -> Optional[date]:
    return date.fromisoformat(value) if value else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit and manage template lifecycle metadata.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="Audit template lifecycle metadata")
    audit.add_argument("--repo-root", default=".", help="Repository root")
    audit.add_argument("--today", help="Override today's date as YYYY-MM-DD")
    audit.add_argument("--include-missing", action="store_true", help="Include records with no status metadata")
    audit.add_argument("--format", choices=("text", "json"), default="text")

    transition = subparsers.add_parser("transition", help="Validate a lifecycle transition")
    transition.add_argument("--from", dest="current", required=True)
    transition.add_argument("--to", dest="target", required=True)
    transition.add_argument("--repo-root", default=".", help="Repository root")

    bump = subparsers.add_parser("bump", help="Bump a semantic version")
    bump.add_argument("version")
    bump.add_argument("level", choices=("major", "minor", "patch"))

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "audit":
        audits = audit_registry(
            args.repo_root,
            today=_parse_today(args.today),
            include_missing=args.include_missing,
        )
        if args.format == "json":
            print(json.dumps([_audit_to_dict(audit) for audit in audits], indent=2))
        else:
            issue_count = sum(len(audit.issues) for audit in audits)
            print(f"Template lifecycle audit: {len(audits)} records, {issue_count} issue(s)")
            for audit in audits:
                for issue in audit.issues:
                    print(f"{issue.severity}: {audit.path}: {issue.code}: {issue.message}")
        return 0 if all(audit.ok for audit in audits) else 1

    if args.command == "transition":
        policy = load_lifecycle_policy(args.repo_root)
        allowed = policy.is_transition_allowed(args.current, args.target)
        print("allowed" if allowed else "blocked")
        return 0 if allowed else 1

    if args.command == "bump":
        print(bump_semver(args.version, args.level))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
