"""Documentation checks for the Aegis MCP wrapper contract."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _task110_contract_path() -> Path:
    candidates = (
        REPO_ROOT
        / "docs"
        / "ai"
        / "work-tracking"
        / "archive"
        / "20260516-task110-aegis-mcp-installer-server-COMPLETED"
        / "designs"
        / "aegis-mcp-implementation-guide.md",
        REPO_ROOT
        / "docs"
        / "ai"
        / "work-tracking"
        / "active"
        / "20260516-task110-aegis-mcp-installer-server-ACTIVE"
        / "designs"
        / "aegis-mcp-implementation-guide.md",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise AssertionError(
        "Task 110 Aegis MCP contract doc was not found in archive or active work tracking"
    )


CONTRACT = _task110_contract_path()


def test_aegis_mcp_contract_uses_aegis_namespace_and_expected_surfaces() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    for name in (
        "aegis.inspect",
        "aegis.plan_install",
        "aegis.install",
        "aegis.verify",
        "aegis.list_profiles",
        "aegis.explain_profile",
    ):
        assert name in text

    for deferred_name in (
        "aegis.status",
        "aegis.plan_update",
        "aegis.update",
        "aegis.rollback",
    ):
        assert deferred_name in text

    for uri in (
        "aegis://manifest/current",
        "aegis://contract/current",
        "aegis://schemas/foundation-manifest",
        "aegis://schemas/profile",
        "aegis://schemas/install-plan",
        "aegis://profiles",
        "aegis://profiles/{name}",
        "aegis://install-plan/latest",
        "aegis://verification/latest",
        "aegis://limitations",
        "aegis://managed-files",
    ):
        assert uri in text

    for prompt in (
        "aegis.bootstrap_new_project",
        "aegis.migrate_existing_project",
        "aegis.verify_runtime",
        "aegis.prepare_agent_session",
        "aegis.close_agent_session",
    ):
        assert prompt in text

    assert "foundation.*" not in text
    assert "foundation://" not in text


def test_aegis_mcp_contract_documents_wrapper_boundary_and_schema_alignment() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    assert "scripts/_aegis_installer.py" in text
    assert "scripts/aegis-mcp-server" in text
    assert "Task 110 ships the first production Aegis MCP server" in text
    assert "must not duplicate installer logic" in text
    assert "apply=true" in text
    assert "acknowledge_report_write=true" in text
    assert "V1-backed tools" in text
    assert "Deferred tools" in text
    assert '"ok": false' in text
    assert '"error": {' in text

    for schema_path in (
        "schemas/aegis/foundation-manifest.schema.json",
        "schemas/aegis/profile.schema.json",
        "schemas/aegis/install-plan.schema.json",
    ):
        assert schema_path in text

    assert "Direct stdio MCP smoke test" in text
    assert "Prompts and memories are continuity aids, not evidence" in text


def test_project_mcp_config_includes_aegis_without_removing_existing_servers() -> None:
    payload = json.loads((REPO_ROOT / ".mcp.json").read_text(encoding="utf-8"))
    servers = payload["mcpServers"]

    assert {"task-master-ai", "serena", "aegis"} <= set(servers)
    assert servers["aegis"] == {
        "type": "stdio",
        "command": "python3",
        "args": ["scripts/aegis-mcp-server"],
    }
