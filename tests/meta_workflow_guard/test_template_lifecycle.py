from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from template_lifecycle import (
    LifecycleError,
    TemplateLifecyclePolicy,
    audit_metadata,
    audit_registry,
    bump_semver,
    load_lifecycle_policy,
)


def _write_repo_config(repo: Path, templates_root: str = "custom_templates") -> None:
    config_dir = repo / ".codex"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        "[repo_structure]\n"
        f'templates_root = "{templates_root}"\n'
        'sessions_root = "sessions"\n'
        'plans_root = "plans"\n'
        'plan_state_dir = ".plan_state"\n'
        'taskmaster_root = ".taskmaster"\n'
        'work_tracking_root = "docs/ai/work-tracking"\n'
        'reports_root = "reports"\n',
        encoding="utf-8",
    )


def _policy_payload() -> dict[str, object]:
    return {
        "version": "test",
        "states": ["draft", "review", "stable", "deprecated", "archived"],
        "compatibility_statuses": {"experimental": "draft", "beta": "review"},
        "ignored_statuses": ["modular"],
        "transitions": {
            "draft": ["review", "archived"],
            "review": ["draft", "stable", "archived"],
            "stable": ["deprecated", "archived"],
            "deprecated": ["stable", "archived"],
            "archived": [],
        },
        "deprecation": {
            "grace_days": 30,
            "archive_after_days": 90,
            "deprecated_since_key": "deprecated_since",
            "replacement_key": "replacement",
            "migration_notice_key": "migration_notice",
        },
    }


def _write_lifecycle_policy(repo: Path, templates_root: str = "custom_templates") -> None:
    policy_path = repo / templates_root / "metadata" / "template-lifecycle-policy.json"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(json.dumps(_policy_payload(), indent=2) + "\n", encoding="utf-8")


def test_lifecycle_policy_loads_from_configured_templates_root(tmp_path: Path) -> None:
    _write_repo_config(tmp_path)
    _write_lifecycle_policy(tmp_path)

    policy = load_lifecycle_policy(tmp_path)

    assert policy.version == "test"
    assert policy.grace_days == 30
    assert policy.archive_after_days == 90
    assert policy.canonical_status("beta") == "review"
    assert "modular" in policy.known_statuses


def test_lifecycle_policy_validates_compatibility_targets() -> None:
    payload = _policy_payload()
    payload["compatibility_statuses"] = {"beta": "missing"}

    with pytest.raises(LifecycleError, match="maps to unknown state"):
        TemplateLifecyclePolicy.from_mapping(payload)


def test_lifecycle_transition_rules_support_canonical_and_compatibility_statuses() -> None:
    policy = TemplateLifecyclePolicy.from_mapping(_policy_payload())

    assert policy.is_transition_allowed("draft", "review") is True
    assert policy.is_transition_allowed("beta", "stable") is True
    assert policy.is_transition_allowed("stable", "deprecated") is True
    assert policy.is_transition_allowed("stable", "draft") is False
    assert policy.is_transition_allowed("archived", "stable") is False
    assert policy.is_transition_allowed("unknown", "stable") is False


def test_bump_semver_handles_major_minor_and_patch() -> None:
    assert bump_semver("1.2.3", "patch") == "1.2.4"
    assert bump_semver("1.2.3", "minor") == "1.3.0"
    assert bump_semver("1.2.3", "major") == "2.0.0"
    assert bump_semver("1.2", "patch") == "1.2.1"

    with pytest.raises(LifecycleError, match="Invalid semantic version"):
        bump_semver("version-one", "patch")


def test_audit_deprecated_template_reports_grace_and_archive_thresholds() -> None:
    policy = TemplateLifecyclePolicy.from_mapping(_policy_payload())
    audit = audit_metadata(
        "templates/example.md",
        {
            "status": "deprecated",
            "version": "1.0.0",
            "deprecated_since": "2026-01-01",
            "replacement": "templates/replacement.md",
        },
        policy=policy,
        today=date(2026, 4, 5),
    )

    codes = {issue.code for issue in audit.issues}
    assert audit.ok is True
    assert audit.canonical_status == "deprecated"
    assert "deprecation_grace_expired" in codes
    assert "archive_recommended" in codes


def test_audit_deprecated_template_requires_migration_notice_or_replacement() -> None:
    policy = TemplateLifecyclePolicy.from_mapping(_policy_payload())
    audit = audit_metadata(
        "templates/example.md",
        {
            "status": "deprecated",
            "version": "1.0.0",
            "deprecated_since": "2026-04-20",
        },
        policy=policy,
        today=date(2026, 5, 8),
    )

    assert any(issue.code == "missing_migration_notice" for issue in audit.issues)
    assert not any(issue.code == "archive_recommended" for issue in audit.issues)


def test_audit_flags_unknown_status_and_invalid_version() -> None:
    policy = TemplateLifecyclePolicy.from_mapping(_policy_payload())
    audit = audit_metadata(
        "templates/example.md",
        {"status": "unknown", "version": "one.two.three"},
        policy=policy,
        today=date(2026, 5, 8),
    )

    codes = {issue.code for issue in audit.issues}
    assert audit.ok is False
    assert codes == {"unknown_status", "invalid_version"}


def test_audit_ignores_aggregate_non_lifecycle_statuses() -> None:
    policy = TemplateLifecyclePolicy.from_mapping(_policy_payload())
    audit = audit_metadata(
        "templates/registry/index.md",
        {"status": "modular"},
        policy=policy,
        today=date(2026, 5, 8),
    )

    assert audit.ok is True
    assert audit.issues == ()
    assert audit.canonical_status is None


def test_frontmatter_schema_accepts_lifecycle_states_and_fields() -> None:
    schema = json.loads((REPO_ROOT / "templates" / "metadata" / "template-frontmatter.schema.json").read_text())
    validator = Draft202012Validator(schema)

    errors = list(
        validator.iter_errors(
            {
                "title": "Lifecycle Example",
                "type": "guide",
                "status": "archived",
                "version": "1.2.3",
                "deprecated_since": "2026-01-01",
                "archive_after": "2026-04-01",
                "replacement": "templates/new.md",
                "migration_notice": "Use templates/new.md instead.",
            }
        )
    )

    assert errors == []


def test_real_lifecycle_policy_and_registry_have_no_unknown_status_errors() -> None:
    audits = audit_registry(REPO_ROOT, today=date(2026, 5, 8))

    assert audits
    assert not [
        issue
        for audit in audits
        for issue in audit.issues
        if issue.code == "unknown_status"
    ]
