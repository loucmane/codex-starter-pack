from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from template_versioning import (
    TemplateVersioningPolicy,
    VersioningError,
    assess_version_change,
    build_history_entry,
    classify_version_change,
    compare_versions,
    history_entry_to_dict,
    load_versioning_policy,
    main,
    parse_version,
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
        "compatible_changes": ["same", "patch", "minor", "release"],
        "migration_required_changes": ["major", "downgrade"],
        "warning_changes": ["prerelease"],
        "history": {
            "schema": "template-version-history.test",
            "required_fields": ["path", "previous_version", "current_version", "change_type", "changed_at"],
        },
    }


def _write_versioning_policy(repo: Path, templates_root: str = "custom_templates") -> None:
    policy_path = repo / templates_root / "metadata" / "template-versioning-policy.json"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(json.dumps(_policy_payload(), indent=2) + "\n", encoding="utf-8")


def test_versioning_policy_loads_from_configured_templates_root(tmp_path: Path) -> None:
    _write_repo_config(tmp_path)
    _write_versioning_policy(tmp_path)

    policy = load_versioning_policy(tmp_path)

    assert policy.version == "test"
    assert policy.compatible_changes == ("same", "patch", "minor", "release")
    assert policy.migration_required_changes == ("major", "downgrade")
    assert policy.warning_changes == ("prerelease",)
    assert policy.history_schema == "template-version-history.test"
    assert "changed_at" in policy.required_history_fields


def test_versioning_policy_validates_unknown_change_types() -> None:
    payload = _policy_payload()
    payload["compatible_changes"] = ["patch", "surprise"]

    with pytest.raises(VersioningError, match="unknown change type"):
        TemplateVersioningPolicy.from_mapping(payload)


def test_parse_version_normalizes_missing_patch_and_preserves_metadata() -> None:
    version = parse_version("1.2-alpha.1+build.7")

    assert version.major == 1
    assert version.minor == 2
    assert version.patch == 0
    assert version.prerelease == ("alpha", "1")
    assert version.build == ("build", "7")
    assert version.normalized == "1.2.0-alpha.1+build.7"
    assert version.comparable == "1.2.0-alpha.1"


def test_compare_versions_handles_prerelease_and_build_metadata() -> None:
    assert compare_versions("1.2", "1.2.0+build.9") == 0
    assert compare_versions("1.2.0-alpha.1", "1.2.0-alpha.2") < 0
    assert compare_versions("1.2.0-alpha.2", "1.2.0-alpha.10") < 0
    assert compare_versions("1.2.0-alpha.10", "1.2.0-alpha.beta") < 0
    assert compare_versions("1.2.0-rc.1", "1.2.0") < 0
    assert compare_versions("2.0.0", "1.9.9") > 0


def test_parse_version_rejects_invalid_versions() -> None:
    with pytest.raises(VersioningError, match="Invalid semantic version"):
        parse_version("version-one")
    with pytest.raises(VersioningError, match="leading zeroes"):
        parse_version("1.2.3-alpha.01")


def test_classify_version_change_covers_supported_transition_types() -> None:
    assert classify_version_change("1.2.3", "1.2.3+build.2") == "same"
    assert classify_version_change("1.2.3", "1.2.4") == "patch"
    assert classify_version_change("1.2.3", "1.3.0") == "minor"
    assert classify_version_change("1.2.3", "2.0.0") == "major"
    assert classify_version_change("1.2.3", "1.2.2") == "downgrade"
    assert classify_version_change("1.2.3-rc.1", "1.2.3") == "release"
    assert classify_version_change("1.2.3", "1.3.0-rc.1") == "prerelease"


def test_assess_version_change_applies_policy_and_rollback_target() -> None:
    policy = TemplateVersioningPolicy.from_mapping(_policy_payload())

    minor = assess_version_change("1.2.3", "1.3.0", policy=policy, path="templates/example.md")
    assert minor.compatible is True
    assert minor.migration_required is False
    assert minor.rollback_version == "1.2.3"
    assert minor.issues == ()

    major = assess_version_change("1.2.3", "2.0.0", policy=policy, path="templates/example.md")
    assert major.compatible is False
    assert major.migration_required is True
    assert major.rollback_version == "1.2.3"
    assert [issue.code for issue in major.issues] == ["migration_required"]

    prerelease = assess_version_change("1.2.3", "1.3.0-rc.1", policy=policy)
    assert prerelease.compatible is False
    assert prerelease.migration_required is False
    assert [issue.code for issue in prerelease.issues] == ["prerelease_version"]


def test_build_history_entry_is_deterministic_and_non_mutating() -> None:
    policy = TemplateVersioningPolicy.from_mapping(_policy_payload())

    entry = build_history_entry(
        path="templates/example.md",
        previous="1.2.3",
        current="2.0.0",
        changed_at="2026-05-08T20:45:00+02:00",
        note="Breaking metadata contract change.",
        policy=policy,
    )

    assert history_entry_to_dict(entry) == {
        "schema": "template-version-history.test",
        "path": "templates/example.md",
        "previous_version": "1.2.3",
        "current_version": "2.0.0",
        "change_type": "major",
        "changed_at": "2026-05-08T20:45:00+02:00",
        "compatible": False,
        "migration_required": True,
        "rollback_version": "1.2.3",
        "issues": [
            {
                "severity": "error",
                "code": "migration_required",
                "message": "Version change 1.2.3 -> 2.0.0 requires migration review",
            }
        ],
        "note": "Breaking metadata contract change.",
    }


def test_history_entry_requires_path_and_changed_at() -> None:
    policy = TemplateVersioningPolicy.from_mapping(_policy_payload())

    with pytest.raises(VersioningError, match="requires path"):
        build_history_entry(path="", previous="1.0.0", current="1.0.1", changed_at="2026-05-08", policy=policy)
    with pytest.raises(VersioningError, match="requires changed_at"):
        build_history_entry(path="templates/example.md", previous="1.0.0", current="1.0.1", changed_at="", policy=policy)


def test_cli_compare_assess_and_history_entry(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_repo_config(tmp_path)
    _write_versioning_policy(tmp_path)

    assert main(["compare", "1.2.0-alpha.1", "1.2.0"]) == 0
    assert capsys.readouterr().out.strip() == "1.2.0-alpha.1 < 1.2.0"

    assert main(["assess", "1.2.3", "2.0.0", "--repo-root", str(tmp_path), "--format", "json"]) == 0
    assessment = json.loads(capsys.readouterr().out)
    assert assessment["change_type"] == "major"
    assert assessment["migration_required"] is True
    assert assessment["rollback_version"] == "1.2.3"

    assert (
        main(
            [
                "history-entry",
                "1.2.3",
                "1.2.4",
                "--repo-root",
                str(tmp_path),
                "--path",
                "templates/example.md",
                "--changed-at",
                "2026-05-08T20:45:00+02:00",
                "--note",
                "Patch wording update.",
            ]
        )
        == 0
    )
    text = capsys.readouterr().out
    assert "template-version-history.test: templates/example.md: 1.2.3 -> 1.2.4 (patch)" in text
    assert "rollback_version: 1.2.3" in text


def test_real_versioning_policy_loads() -> None:
    policy = load_versioning_policy(REPO_ROOT)

    assert policy.version == "1.0.0"
    assert "minor" in policy.compatible_changes
    assert "downgrade" in policy.migration_required_changes
    assert policy.history_schema == "template-version-history.v1"
