from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = REPO_ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from template_testing import TemplateFixture, TemplateTestCase, render_template_text


def test_template_test_case_writes_portable_fixtures_and_asserts_registry_behavior(tmp_path: Path) -> None:
    case = TemplateTestCase(tmp_path, templates_root="custom_templates")
    alpha = TemplateFixture(
        id="alpha",
        path="guides/alpha.md",
        title="Alpha Guide",
        type="guide",
        status="stable",
        category="docs",
        version="1.0.0",
        tags=("docs", "onboarding"),
        dependencies=("beta",),
        body="Hello {{ user }} from {{ project }}.",
    )
    beta = TemplateFixture(
        id="beta",
        path="guides/beta.md",
        title="Beta Guide",
        type="guide",
        status="stable",
        category="docs",
        tags=("docs", "support"),
    )

    case.write_template(alpha)
    case.write_template(beta)
    case.write_registry([alpha, beta])
    case.write_compatibility_map(
        [
            {
                "legacy": "templates/legacy-alpha.md",
                "current": "templates/guides/alpha.md",
                "reason": "portable compatibility redirect",
            }
        ]
    )

    record = case.assert_template_registered("alpha", expected_path="custom_templates/guides/alpha.md")
    assert record.title == "Alpha Guide"
    assert case.assert_template_metadata_contains("alpha", {"category": "docs", "version": "1.0.0"})["id"] == "alpha"
    assert [item["id"] for item in case.assert_template_search_ids(["alpha", "beta"], category="docs", tags=["docs"])] == [
        "alpha",
        "beta",
    ]
    dependency_report = case.assert_template_dependencies_resolve("alpha")
    assert dependency_report["missing"] == []
    assert [item["id"] for item in dependency_report["resolved"]] == ["beta"]

    redirect = case.assert_template_resolves(
        "templates/legacy-alpha.md",
        expected_status="redirect",
        expected_path="custom_templates/guides/alpha.md",
    )
    assert redirect.source == "compatibility"

    rendered = case.render_template("alpha", {"user": "Lou", "project": "Codex"})
    assert rendered.ok is True
    assert "Hello Lou from Codex." in rendered.rendered


def test_template_coverage_report_flags_unregistered_and_missing_registry_paths(tmp_path: Path) -> None:
    case = TemplateTestCase(tmp_path, templates_root="ops/templates")
    alpha = TemplateFixture(id="alpha", path="guides/alpha.md", title="Alpha")
    beta = TemplateFixture(id="beta", path="guides/beta.md", title="Beta")
    case.write_template(alpha)
    case.write_template(beta)
    case.write_registry([alpha])

    report = case.coverage_report()

    assert report.ok is False
    assert report.coverage_pct == 50.0
    assert report.unregistered_paths == ("ops/templates/guides/beta.md",)
    assert report.missing_registry_paths == ()

    case.write_registry(
        [alpha, beta],
        entries=[{"id": "missing", "path": "ops/templates/guides/missing.md", "tags": []}],
    )
    missing_report = case.coverage_report()

    assert missing_report.ok is False
    assert missing_report.unregistered_paths == ()
    assert missing_report.missing_registry_paths == ("ops/templates/guides/missing.md",)
    assert missing_report.to_dict()["ok"] is False


def test_template_registry_coverage_assertion_passes_when_registry_and_markdown_match(tmp_path: Path) -> None:
    case = TemplateTestCase(tmp_path, templates_root="docs/templates")
    template = TemplateFixture(id="session-start", path="docs/templates/handlers/session-start.md", title="Session Start")
    case.write_template(template)
    case.write_registry([template])

    report = case.assert_registry_covers_templates()

    assert report.ok is True
    assert report.coverage_pct == 100.0
    assert report.markdown_paths == ("docs/templates/handlers/session-start.md",)


def test_template_assertions_raise_clear_failures(tmp_path: Path) -> None:
    case = TemplateTestCase(tmp_path, templates_root="templates")
    template = TemplateFixture(id="alpha", path="guides/alpha.md", title="Alpha", dependencies=("missing",))
    case.write_template(template)
    case.write_registry([template])

    with pytest.raises(AssertionError, match="Template id is not registered"):
        case.assert_template_registered("missing")

    with pytest.raises(AssertionError, match="missing dependencies"):
        case.assert_template_dependencies_resolve("alpha")

    with pytest.raises(AssertionError, match="Template search ids mismatch"):
        case.assert_template_search_ids(["beta"], category="guides")


def test_render_template_text_reports_unresolved_placeholders() -> None:
    rendered, unresolved = render_template_text("Hello {{ user }} from {{ project }} and {{ project }}.", {"user": "Lou"})

    assert rendered == "Hello Lou from {{ project }} and {{ project }}."
    assert unresolved == ("project",)

    with pytest.raises(AssertionError, match="Unresolved template placeholders"):
        render_template_text("Hello {{ user }}", {}, strict=True)
