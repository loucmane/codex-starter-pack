from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from template_governance import (
    GovernanceError,
    TemplateGovernancePolicy,
    assess_governance,
    assessment_to_dict,
    load_governance_policy,
    main,
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
        "schema": "template-governance-review.test",
        "default_review_class": "routine",
        "emergency_review_class": "emergency",
        "roles": {
            "template_owner": "Owns the changed template.",
            "foundation_maintainer": "Owns the portable foundation.",
            "compatibility_reviewer": "Reviews migration impact.",
            "emergency_approver": "Approves emergency changes.",
        },
        "review_classes": {
            "routine": {
                "priority": 10,
                "required_roles": ["template_owner"],
                "approval": "Owner approval.",
                "escalation": "No escalation.",
                "notification_audiences": ["tracker"],
                "required_evidence": ["decision note"],
            },
            "coordinated": {
                "priority": 20,
                "required_roles": ["template_owner", "foundation_maintainer"],
                "approval": "Two-role acknowledgement.",
                "escalation": "Escalate if compatibility risk appears.",
                "notification_audiences": ["tracker", "handoff"],
                "required_evidence": ["findings", "tests"],
            },
            "breaking": {
                "priority": 30,
                "required_roles": ["template_owner", "foundation_maintainer", "compatibility_reviewer"],
                "approval": "All listed roles.",
                "escalation": "Migration and rollback notes.",
                "notification_audiences": ["tracker", "handoff", "migration notes"],
                "required_evidence": ["compatibility impact", "guard"],
            },
            "emergency": {
                "priority": 40,
                "required_roles": ["foundation_maintainer", "emergency_approver"],
                "approval": "Explicit user approval.",
                "escalation": "Emergency response policy.",
                "notification_audiences": ["session", "handoff"],
                "required_evidence": ["emergency reason", "follow-up plan"],
            },
        },
        "version_change_review": {
            "same": "routine",
            "patch": "routine",
            "minor": "routine",
            "release": "routine",
            "prerelease": "coordinated",
            "major": "breaking",
            "downgrade": "breaking",
        },
        "lifecycle_transition_review": {
            "review->stable": "coordinated",
            "stable->deprecated": "breaking",
            "deprecated->archived": "coordinated",
        },
        "notification_mode": "evidence-only",
    }


def _write_governance_policy(repo: Path, templates_root: str = "custom_templates") -> None:
    policy_path = repo / templates_root / "metadata" / "template-governance-policy.json"
    policy_path.parent.mkdir(parents=True)
    policy_path.write_text(json.dumps(_policy_payload(), indent=2) + "\n", encoding="utf-8")


def test_governance_policy_loads_from_configured_templates_root(tmp_path: Path) -> None:
    _write_repo_config(tmp_path)
    _write_governance_policy(tmp_path)

    policy = load_governance_policy(tmp_path)

    assert policy.version == "test"
    assert policy.schema == "template-governance-review.test"
    assert policy.notification_mode == "evidence-only"
    assert policy.review_class("breaking").required_roles == (
        "template_owner",
        "foundation_maintainer",
        "compatibility_reviewer",
    )


def test_governance_policy_validates_unknown_roles_and_classes() -> None:
    payload = _policy_payload()
    payload["review_classes"]["routine"]["required_roles"] = ["missing_role"]  # type: ignore[index]

    with pytest.raises(GovernanceError, match="unknown role"):
        TemplateGovernancePolicy.from_mapping(payload)

    payload = _policy_payload()
    payload["version_change_review"]["major"] = "missing_class"  # type: ignore[index]

    with pytest.raises(GovernanceError, match="unknown review class"):
        TemplateGovernancePolicy.from_mapping(payload)


def test_version_change_assessment_maps_major_and_prerelease_review_classes() -> None:
    policy = TemplateGovernancePolicy.from_mapping(_policy_payload())

    major = assess_governance(
        path="templates/example.md",
        previous_version="1.2.3",
        current_version="2.0.0",
        policy=policy,
    )
    assert major.review_class == "breaking"
    assert major.required_roles == ("template_owner", "foundation_maintainer", "compatibility_reviewer")
    assert major.reasons[0].signal == "version_change"
    assert major.reasons[0].value == "major"

    prerelease = assess_governance(
        previous_version="1.2.3",
        current_version="1.3.0-rc.1",
        policy=policy,
    )
    assert prerelease.review_class == "coordinated"
    assert prerelease.reasons[0].value == "prerelease"


def test_lifecycle_transition_assessment_and_precedence() -> None:
    policy = TemplateGovernancePolicy.from_mapping(_policy_payload())

    assessment = assess_governance(
        previous_version="1.2.3",
        current_version="1.2.4",
        lifecycle_from="stable",
        lifecycle_to="deprecated",
        policy=policy,
    )

    assert assessment.review_class == "breaking"
    assert [reason.signal for reason in assessment.reasons] == ["version_change", "lifecycle_transition"]
    assert assessment.reasons[1].value == "stable->deprecated"


def test_emergency_flag_overrides_lower_review_classes() -> None:
    policy = TemplateGovernancePolicy.from_mapping(_policy_payload())

    assessment = assess_governance(
        previous_version="1.2.3",
        current_version="1.2.4",
        emergency=True,
        policy=policy,
    )

    assert assessment.review_class == "emergency"
    assert assessment.required_roles == ("foundation_maintainer", "emergency_approver")
    assert assessment.reasons[-1].signal == "emergency"


def test_assessment_requires_complete_signal_pairs() -> None:
    policy = TemplateGovernancePolicy.from_mapping(_policy_payload())

    with pytest.raises(GovernanceError, match="previous_version and current_version"):
        assess_governance(previous_version="1.0.0", policy=policy)

    with pytest.raises(GovernanceError, match="lifecycle_from and lifecycle_to"):
        assess_governance(lifecycle_from="stable", policy=policy)


def test_assessment_to_dict_contains_reviewable_payload() -> None:
    policy = TemplateGovernancePolicy.from_mapping(_policy_payload())

    payload = assessment_to_dict(
        assess_governance(
            path="templates/example.md",
            previous_version="1.2.3",
            current_version="2.0.0",
            note="Breaking metadata contract.",
            policy=policy,
        )
    )

    assert payload["schema"] == "template-governance-review.test"
    assert payload["path"] == "templates/example.md"
    assert payload["review_class"] == "breaking"
    assert payload["notification_mode"] == "evidence-only"
    assert payload["note"] == "Breaking metadata contract."
    assert payload["reasons"][0]["value"] == "major"


def test_cli_assess_outputs_json_and_text(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_repo_config(tmp_path)
    _write_governance_policy(tmp_path)

    assert (
        main(
            [
                "assess",
                "--repo-root",
                str(tmp_path),
                "--path",
                "templates/example.md",
                "--previous-version",
                "1.2.3",
                "--current-version",
                "2.0.0",
                "--format",
                "json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["review_class"] == "breaking"
    assert payload["reasons"][0]["value"] == "major"

    assert (
        main(
            [
                "assess",
                "--repo-root",
                str(tmp_path),
                "--lifecycle-from",
                "review",
                "--lifecycle-to",
                "stable",
            ]
        )
        == 0
    )
    text = capsys.readouterr().out
    assert "coordinated" in text
    assert "required_roles: template_owner, foundation_maintainer" in text


def test_real_governance_policy_loads_and_assesses_breaking_change() -> None:
    policy = load_governance_policy(REPO_ROOT)

    assessment = assess_governance(
        path="templates/example.md",
        previous_version="1.0.0",
        current_version="2.0.0",
        policy=policy,
    )

    assert policy.version == "1.0.0"
    assert assessment.review_class == "breaking"
    assert "compatibility_reviewer" in assessment.required_roles
