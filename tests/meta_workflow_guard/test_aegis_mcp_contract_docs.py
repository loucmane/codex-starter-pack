"""Documentation checks for the Aegis MCP wrapper contract."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    REPO_ROOT
    / "docs"
    / "ai"
    / "work-tracking"
    / "active"
    / "20260515-task109-foundation-installer-mcp-ACTIVE"
    / "designs"
    / "aegis-mcp-wrapper-contract.md"
)


def test_aegis_mcp_contract_uses_aegis_namespace_and_expected_surfaces() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    for name in (
        "aegis.inspect",
        "aegis.plan_install",
        "aegis.install",
        "aegis.verify",
        "aegis.status",
        "aegis.plan_update",
        "aegis.update",
        "aegis.rollback",
        "aegis.list_profiles",
        "aegis.explain_profile",
    ):
        assert name in text

    for uri in (
        "aegis://contract/current",
        "aegis://profiles",
        "aegis://profiles/{name}",
        "aegis://install-plan/latest",
        "aegis://verification/latest",
        "aegis://limitations",
        "aegis://managed-files",
        "aegis://project/status",
    ):
        assert uri in text

    for prompt in (
        "aegis.bootstrap_new_project",
        "aegis.migrate_existing_project",
        "aegis.verify_runtime",
        "aegis.prepare_agent_session",
        "aegis.close_agent_session",
        "aegis.install_claude_adapter",
        "aegis.install_codex_adapter",
    ):
        assert prompt in text

    assert "foundation.*" not in text
    assert "foundation://" not in text


def test_aegis_mcp_contract_documents_wrapper_boundary_and_schema_alignment() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    assert "scripts/_aegis_installer.py" in text
    assert "not ship a production MCP server" in text
    assert "must not duplicate installer logic" in text
    assert "explicit apply semantics" in text
    assert "V1-backed" in text
    assert "future/deferred" in text

    for schema_path in (
        "schemas/aegis/foundation-manifest.schema.json",
        "schemas/aegis/profile.schema.json",
        "schemas/aegis/install-plan.schema.json",
    ):
        assert schema_path in text

    for follow_up in (
        "Production Aegis MCP server wrapper",
        "Expanded profile implementation",
        "Full rollback checkpoint",
        "Packaging and distribution",
        "Cross-agent smoke automation",
    ):
        assert follow_up in text
