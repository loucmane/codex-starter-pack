"""Tests for the Aegis MCP server scaffold."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from aegis_foundation import DISTRIBUTION_NAME, FOUNDATION_VERSION, INSTALLER_VERSION, SCHEMA_VERSION
from aegis_mcp.server import (
    AegisMCPConfig,
    PROMPT_NAMES,
    RESOURCE_URIS,
    SERVER_NAME,
    V1_TOOL_NAMES,
    create_server,
)
from scripts._aegis_installer import AEGIS_MANIFEST_REL, AEGIS_PENDING_TRACKING_REL, install, kickoff


REPO_ROOT = Path(__file__).resolve().parents[2]


def list_tools(server: FastMCP):
    return asyncio.run(server.list_tools())


def tool_by_name(server: FastMCP, name: str):
    tools = {tool.name: tool for tool in list_tools(server)}
    return tools[name]


def call_tool_payload(server: FastMCP, name: str, arguments: dict | None = None) -> dict:
    content, structured_payload = asyncio.run(server.call_tool(name, arguments or {}))
    assert len(content) == 1
    payload = json.loads(content[0].text)
    assert structured_payload == payload
    return payload


def read_resource_payload(server: FastMCP, uri: str) -> dict:
    contents = asyncio.run(server.read_resource(uri))
    assert len(contents) == 1
    return json.loads(contents[0].content)


def get_prompt_text(server: FastMCP, name: str, arguments: dict | None = None) -> str:
    prompt = asyncio.run(server.get_prompt(name, arguments or {}))
    assert len(prompt.messages) == 1
    return prompt.messages[0].content.text


async def run_stdio_smoke(target: Path) -> tuple[set[str], set[str], set[str]]:
    params = StdioServerParameters(
        command=sys.executable,
        args=[
            "scripts/aegis-mcp-server",
            "--source-root",
            REPO_ROOT.as_posix(),
            "--default-target-dir",
            target.as_posix(),
        ],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            resources = await session.list_resources()
            prompts = await session.list_prompts()
    return (
        {tool.name for tool in tools.tools},
        {str(resource.uri) for resource in resources.resources},
        {prompt.name for prompt in prompts.prompts},
    )


def test_config_defaults_to_packaged_assets_and_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "external-project"
    target.mkdir()
    monkeypatch.chdir(target)

    config = AegisMCPConfig.from_paths()

    assert config.source_root == (REPO_ROOT / "aegis_foundation" / "assets").resolve()
    assert config.default_target_dir == target.resolve()
    assert config.asset_origin == "package"
    assert (config.source_root / "schemas" / "aegis" / "foundation-manifest.schema.json").is_file()


def test_config_accepts_explicit_paths(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    config = AegisMCPConfig.from_paths(source_root=source, default_target_dir=target)

    assert config.source_root == source.resolve()
    assert config.default_target_dir == target.resolve()
    assert config.asset_origin == "source"
    assert config.to_dict() == {
        "distribution_name": DISTRIBUTION_NAME,
        "asset_origin": "source",
        "foundation_version": FOUNDATION_VERSION,
        "installer_version": INSTALLER_VERSION,
        "schema_version": SCHEMA_VERSION,
        "source_root": source.resolve().as_posix(),
        "default_target_dir": target.resolve().as_posix(),
    }


def test_create_server_returns_fastmcp_with_aegis_context(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    assert isinstance(server, FastMCP)
    assert server.name == SERVER_NAME
    assert server.aegis_config == config
    assert server.aegis_installer.AEGIS_MANIFEST_REL == ".aegis/foundation-manifest.json"


def test_server_registers_exact_v1_tool_set(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    tools = list_tools(server)

    assert [tool.name for tool in tools] == list(V1_TOOL_NAMES)
    assert {tool.name for tool in tools} == {
        "aegis.inspect",
        "aegis.status",
        "aegis.next",
        "aegis.plan_install",
        "aegis.install",
        "aegis.init",
        "aegis.verify",
        "aegis.closeout_ready",
        "aegis.closeout",
        "aegis.start",
        "aegis.kickoff",
        "aegis.log",
        "aegis.list_profiles",
        "aegis.explain_profile",
    }
    assert {
        "aegis.plan_update",
        "aegis.update",
        "aegis.rollback",
    }.isdisjoint({tool.name for tool in tools})


def test_workflow_tools_describe_required_next_actions(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    status_description = tool_by_name(server, "aegis.status").description or ""
    next_description = tool_by_name(server, "aegis.next").description or ""
    init_description = tool_by_name(server, "aegis.init").description or ""
    start_description = tool_by_name(server, "aegis.start").description or ""
    kickoff_description = tool_by_name(server, "aegis.kickoff").description or ""
    log_description = tool_by_name(server, "aegis.log").description or ""
    verify_description = tool_by_name(server, "aegis.verify").description or ""
    closeout_ready_description = tool_by_name(server, "aegis.closeout_ready").description or ""
    closeout_description = tool_by_name(server, "aegis.closeout").description or ""

    assert "next workflow guidance" in status_description
    assert "next required Aegis workflow action" in next_description
    assert "read-only" in next_description
    assert "Public project setup" in init_description
    assert "Public local-task kickoff" in start_description
    assert "plan-step-scope before source edits" in kickoff_description
    assert "pending_event_id=current" in log_description
    assert "log its pending event before closeout" in verify_description
    assert "Read-only pre-closeout gate check" in closeout_ready_description
    assert "scope, implement, verify" in closeout_description


def test_server_registers_expected_resources_and_prompts(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    resources = asyncio.run(server.list_resources())
    templates = asyncio.run(server.list_resource_templates())
    prompts = asyncio.run(server.list_prompts())

    assert {str(resource.uri) for resource in resources} == set(RESOURCE_URIS)
    assert {template.uriTemplate for template in templates} == {"aegis://profiles/{name}"}
    assert {prompt.name for prompt in prompts} == set(PROMPT_NAMES)


def test_plan_install_schema_requires_explicit_agent_selection(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    schema = tool_by_name(server, "aegis.plan_install").inputSchema

    assert set(schema["required"]) == {"target_dir", "primary_agent", "agents"}
    assert schema["properties"]["profile"]["default"] == "generic"
    assert schema["properties"]["profile"]["const"] == "generic"
    assert schema["properties"]["primary_agent"]["enum"] == [
        "claude",
        "codex",
        "gemini",
        "multi",
        "none",
    ]
    assert schema["properties"]["agents"]["items"]["enum"] == [
        "claude",
        "codex",
        "gemini",
    ]
    assert schema["properties"]["agents"]["uniqueItems"] is True


def test_install_schema_requires_apply_and_full_selection(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    schema = tool_by_name(server, "aegis.install").inputSchema

    assert set(schema["required"]) == {
        "target_dir",
        "profile",
        "primary_agent",
        "agents",
        "apply",
    }
    assert schema["properties"]["profile"]["const"] == "generic"
    assert schema["properties"]["apply"]["type"] == "boolean"


def test_public_init_and_start_schemas_require_apply_confirmation(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    init_schema = tool_by_name(server, "aegis.init").inputSchema
    assert set(init_schema["required"]) == {"target_dir", "apply"}
    assert init_schema["properties"]["apply"]["type"] == "boolean"
    assert init_schema["properties"]["primary_agent"]["default"] == "claude"

    start_schema = tool_by_name(server, "aegis.start").inputSchema
    assert set(start_schema["required"]) == {"target_dir", "title"}
    assert start_schema["properties"]["apply"]["default"] is False
    assert start_schema["properties"]["create_branch"]["default"] is True


def test_verify_schema_requires_acknowledged_report_write(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    schema = tool_by_name(server, "aegis.verify").inputSchema

    assert set(schema["required"]) == {"target_dir", "acknowledge_report_write"}
    assert schema["properties"]["acknowledge_report_write"]["type"] == "boolean"
    assert schema["properties"]["strict"]["type"] == "boolean"
    assert schema["properties"]["strict"]["default"] is False


def test_kickoff_schema_requires_explicit_apply_and_task_inputs(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    schema = tool_by_name(server, "aegis.kickoff").inputSchema

    assert set(schema["required"]) == {"target_dir", "task", "slug", "title"}
    assert schema["properties"]["apply"]["default"] is False
    assert schema["properties"]["create_branch"]["default"] is True


def test_log_schema_requires_explicit_apply_and_tracking_inputs(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    schema = tool_by_name(server, "aegis.log").inputSchema

    assert set(schema["required"]) == {"target_dir", "note"}
    assert schema["properties"]["apply"]["default"] is False
    assert schema["properties"]["handler"]["default"] == ""
    assert schema["properties"]["evidence"]["default"] == ""
    assert schema["properties"]["plan_step"]["default"] == ""
    assert schema["properties"]["plan_status"]["default"] == "in-progress"
    assert schema["properties"]["surfaces"]["default"] is None
    assert schema["properties"]["event_class"]["default"] is None
    assert schema["properties"]["pending_event_id"]["default"] == ""


def test_log_tool_consumes_pending_event_id(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    kickoff(target, task_id="42", slug="mcp-pending-id", title="MCP Pending Id")
    current_work = json.loads((target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8"))
    evidence_rel = f"{current_work['paths']['reports']}/mcp-pending-id.txt"
    (target / evidence_rel).write_text("pending\n", encoding="utf-8")
    pending_path = target / AEGIS_PENDING_TRACKING_REL
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    pending_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "updated_at": "2026-05-23T12:00:00Z",
                "events": [
                    {
                        "id": "mcp123",
                        "handler": "claude:Write",
                        "evidence": evidence_rel,
                        "evidence_location": {
                            "path": evidence_rel,
                            "line_start": 1,
                            "line_end": 1,
                            "line_count": 1,
                            "source": "write_file_snapshot",
                            "confidence": "file_snapshot",
                            "display": f"{evidence_rel}:1",
                        },
                        "task": {"id": "42", "slug": "mcp-pending-id"},
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = call_tool_payload(
        server,
        "aegis.log",
        {
            "target_dir": target.as_posix(),
            "note": "Logged MCP pending event by id",
            "pending_event_id": "mcp123",
            "plan_step": "plan-step-implement",
            "plan_status": "completed",
            "apply": True,
        },
    )

    assert payload["ok"] is True
    assert payload["result"]["entry"]["h"] == "claude:Write"
    assert payload["result"]["entry"]["e"] == evidence_rel
    assert payload["result"]["entry"]["evidence_location"]["display"] == f"{evidence_rel}:1"
    assert payload["result"]["next_action"]["action"] == "run_task_specific_verification"
    assert payload["result"]["pending"]["cleared"] == 1
    assert not pending_path.exists()


def test_plan_install_calls_core_and_validates_schema(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    target.mkdir()

    payload = call_tool_payload(
        server,
        "aegis.plan_install",
        {
            "target_dir": target.as_posix(),
            "primary_agent": "claude",
            "agents": ["claude"],
        },
    )

    assert payload["ok"] is True
    assert payload["tool"] == "aegis.plan_install"
    assert payload["read_only"] is True
    assert payload["result"]["mode"] == "dry_run"
    assert payload["result"]["apply_confirmed"] is False
    assert payload["result"]["summary"]["creates"] > 0
    assert not (target / ".aegis").exists()


def test_invalid_agent_selection_returns_structured_error_before_core_call(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    invalid_calls = [
        (
            "aegis.plan_install",
            {
                "target_dir": tmp_path.as_posix(),
                "primary_agent": "claude",
                "agents": ["claude", "claude"],
            },
            "agents must be unique",
        ),
        (
            "aegis.plan_install",
            {
                "target_dir": tmp_path.as_posix(),
                "primary_agent": "multi",
                "agents": ["claude"],
            },
            "primary_agent=multi requires at least two enabled agents",
        ),
        (
            "aegis.plan_install",
            {
                "target_dir": tmp_path.as_posix(),
                "primary_agent": "codex",
                "agents": ["claude"],
            },
            "primary_agent=codex must also be listed in agents",
        ),
    ]

    for tool_name, arguments, expected_message in invalid_calls:
        payload = call_tool_payload(server, tool_name, arguments)

        assert payload["ok"] is False
        assert payload["error"]["code"] == "invalid_input"
        assert payload["error"]["status"] == "invalid_request"
        assert expected_message in payload["error"]["message"]


def test_missing_required_fields_are_rejected_by_schema(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    missing_required_calls = [
        ("aegis.plan_install", {"target_dir": tmp_path.as_posix(), "agents": ["claude"]}, "primary_agent"),
        ("aegis.plan_install", {"target_dir": tmp_path.as_posix(), "primary_agent": "claude"}, "agents"),
        (
            "aegis.install",
            {
                "target_dir": tmp_path.as_posix(),
                "profile": "generic",
                "primary_agent": "claude",
                "agents": ["claude"],
            },
            "apply",
        ),
        ("aegis.verify", {"target_dir": tmp_path.as_posix()}, "acknowledge_report_write"),
        (
            "aegis.kickoff",
            {"target_dir": tmp_path.as_posix(), "task": "1", "slug": "smoke"},
            "title",
        ),
        (
            "aegis.log",
            {"target_dir": tmp_path.as_posix(), "handler": "claude-test", "evidence": "reports/example.txt"},
            "note",
        ),
    ]

    for tool_name, arguments, expected_message in missing_required_calls:
        with pytest.raises(ToolError, match=expected_message):
            asyncio.run(server.call_tool(tool_name, arguments))


def test_install_requires_apply_true_before_core_mutation(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    target.mkdir()

    payload = call_tool_payload(
        server,
        "aegis.install",
        {
            "target_dir": target.as_posix(),
            "profile": "generic",
            "primary_agent": "claude",
            "agents": ["claude"],
            "apply": False,
        },
    )

    assert payload["ok"] is False
    assert payload["error"]["code"] == "apply_required"
    assert payload["error"]["status"] == "refused"


def test_public_init_and_start_require_apply_true_before_core_mutation(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    target.mkdir()

    init_payload = call_tool_payload(
        server,
        "aegis.init",
        {
            "target_dir": target.as_posix(),
            "apply": False,
        },
    )
    assert init_payload["ok"] is False
    assert init_payload["error"]["code"] == "apply_required"
    assert not (target / ".aegis").exists()

    start_payload = call_tool_payload(
        server,
        "aegis.start",
        {
            "target_dir": target.as_posix(),
            "title": "Improve BrandMark accessibility",
            "apply": False,
        },
    )
    assert start_payload["ok"] is False
    assert start_payload["error"]["code"] == "apply_required"
    assert not (target / ".aegis" / "state" / "current-work.json").exists()


def test_kickoff_requires_apply_true_before_core_mutation(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    target.mkdir()

    payload = call_tool_payload(
        server,
        "aegis.kickoff",
        {
            "target_dir": target.as_posix(),
            "task": "1",
            "slug": "smoke",
            "title": "Smoke",
            "apply": False,
        },
    )

    assert payload["ok"] is False
    assert payload["error"]["code"] == "apply_required"
    assert payload["error"]["status"] == "refused"
    assert not (target / ".aegis" / "state" / "current-work.json").exists()
    assert not (target / ".aegis").exists()


def test_log_requires_apply_true_before_core_mutation(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    target.mkdir()

    payload = call_tool_payload(
        server,
        "aegis.log",
        {
            "target_dir": target.as_posix(),
            "handler": "claude-test",
            "evidence": "reports/example.txt",
            "note": "Recorded example evidence",
            "apply": False,
        },
    )

    assert payload["ok"] is False
    assert payload["error"]["code"] == "apply_required"
    assert payload["error"]["status"] == "refused"
    assert not (target / ".aegis").exists()


def test_install_apply_true_writes_aegis_foundation_to_temp_target(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    target.mkdir()

    payload = call_tool_payload(
        server,
        "aegis.install",
        {
            "target_dir": target.as_posix(),
            "profile": "generic",
            "primary_agent": "claude",
            "agents": ["claude"],
            "apply": True,
        },
    )

    assert payload["ok"] is True
    assert payload["tool"] == "aegis.install"
    assert payload["read_only"] is False
    assert payload["result"]["status"] == "applied"
    assert (target / AEGIS_MANIFEST_REL).exists()


def test_install_refused_conflict_is_structured_error(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    (target / ".aegis").mkdir(parents=True)
    (target / AEGIS_MANIFEST_REL).write_text('{"foundation_name": "Other Foundation"}\n', encoding="utf-8")

    payload = call_tool_payload(
        server,
        "aegis.install",
        {
            "target_dir": target.as_posix(),
            "profile": "generic",
            "primary_agent": "claude",
            "agents": ["claude"],
            "apply": True,
        },
    )

    assert payload["ok"] is False
    assert payload["error"]["code"] == "install_refused"
    assert payload["error"]["status"] == "refused"
    assert payload["error"]["details"]["report"]["status"] == "refused"
    assert (target / AEGIS_MANIFEST_REL).read_text(encoding="utf-8") == '{"foundation_name": "Other Foundation"}\n'


def test_verify_requires_acknowledgement_true_before_report_write(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    target.mkdir()

    payload = call_tool_payload(
        server,
        "aegis.verify",
        {
            "target_dir": target.as_posix(),
            "acknowledge_report_write": False,
        },
    )

    assert payload["ok"] is False
    assert payload["error"]["code"] == "acknowledgement_required"
    assert payload["error"]["status"] == "refused"
    assert not (target / ".aegis" / "reports" / "verification-report.json").exists()


def test_verify_success_and_failure_details_are_structured(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    target.mkdir()

    install_payload = call_tool_payload(
        server,
        "aegis.install",
        {
            "target_dir": target.as_posix(),
            "profile": "generic",
            "primary_agent": "claude",
            "agents": ["claude"],
            "apply": True,
        },
    )
    assert install_payload["ok"] is True

    verify_payload = call_tool_payload(
        server,
        "aegis.verify",
        {
            "target_dir": target.as_posix(),
            "acknowledge_report_write": True,
        },
    )
    assert verify_payload["ok"] is True
    assert verify_payload["result"]["status"] == "passed"

    (target / ".claude" / "scripts" / "readiness.sh").unlink()
    failed_payload = call_tool_payload(
        server,
        "aegis.verify",
        {
            "target_dir": target.as_posix(),
            "acknowledge_report_write": True,
        },
    )

    assert failed_payload["ok"] is False
    assert failed_payload["error"]["code"] == "verification_failed"
    assert failed_payload["error"]["status"] == "failed"
    assert failed_payload["error"]["details"]["report"]["status"] == "failed"


def test_verify_strict_flag_passes_through_to_core_report(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr

    install_payload = call_tool_payload(
        server,
        "aegis.install",
        {
            "target_dir": target.as_posix(),
            "profile": "generic",
            "primary_agent": "claude",
            "agents": ["claude"],
            "apply": True,
        },
    )
    assert install_payload["ok"] is True
    kickoff_payload = call_tool_payload(
        server,
        "aegis.kickoff",
        {
            "target_dir": target.as_posix(),
            "task": "42",
            "slug": "strict-verify",
            "title": "Strict Verify",
            "apply": True,
        },
    )
    assert kickoff_payload["ok"] is True
    assert kickoff_payload["result"]["next_action"]["action"] == "log_scope_before_edit"

    verify_payload = call_tool_payload(
        server,
        "aegis.verify",
        {
            "target_dir": target.as_posix(),
            "acknowledge_report_write": True,
            "strict": True,
        },
    )

    assert verify_payload["ok"] is True
    assert verify_payload["result"]["mode"] == "strict"
    assert verify_payload["result"]["status"] == "passed"
    assert verify_payload["result"]["next_action"]["action"] == "log_strict_verification_before_closeout"
    assert any(
        check["gate_id"] == "workflow.current_work"
        for check in verify_payload["result"]["checks"]
    )


def test_status_reports_current_install_without_mutation(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    target.mkdir()

    install_payload = call_tool_payload(
        server,
        "aegis.install",
        {
            "target_dir": target.as_posix(),
            "profile": "generic",
            "primary_agent": "claude",
            "agents": ["claude"],
            "apply": True,
        },
    )
    assert install_payload["ok"] is True
    before = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in sorted(target.rglob("*"))
        if path.is_file()
    }

    payload = call_tool_payload(server, "aegis.status", {"target_dir": target.as_posix()})

    after = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in sorted(target.rglob("*"))
        if path.is_file()
    }
    assert after == before
    assert payload["ok"] is True
    assert payload["tool"] == "aegis.status"
    assert payload["read_only"] is True
    assert payload["result"]["status"] == "current"
    assert payload["result"]["migration_required"] is False
    assert payload["result"]["workflow_guidance"]["read_only"] is True
    assert payload["result"]["workflow_guidance"]["state"] == "installed_no_current_work"


def test_next_reports_guidance_without_mutation(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    target.mkdir()
    before = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in sorted(target.rglob("*"))
        if path.is_file()
    }

    payload = call_tool_payload(server, "aegis.next", {"target_dir": target.as_posix()})

    after = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in sorted(target.rglob("*"))
        if path.is_file()
    }
    assert after == before
    assert payload["ok"] is True
    assert payload["tool"] == "aegis.next"
    assert payload["read_only"] is True
    assert payload["result"]["phase"] == "bootstrap"
    assert payload["result"]["state"] == "not_installed"
    assert payload["result"]["suggested_mcp_call"]["tool"] == "aegis.plan_install"


def test_closeout_ready_reports_without_mutation(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    target.mkdir()
    before = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in sorted(target.rglob("*"))
        if path.is_file()
    }

    payload = call_tool_payload(server, "aegis.closeout_ready", {"target_dir": target.as_posix()})

    after = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in sorted(target.rglob("*"))
        if path.is_file()
    }
    assert after == before
    assert payload["ok"] is True
    assert payload["tool"] == "aegis.closeout_ready"
    assert payload["read_only"] is True
    assert payload["result"]["status"] == "failed"
    assert payload["result"]["dry_run"] is True
    assert payload["result"]["report_written"] is False
    assert payload["result"]["state_updated"] is False


def test_profile_tools_call_core_and_validate_payloads(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    list_payload = call_tool_payload(server, "aegis.list_profiles")
    assert list_payload["ok"] is True
    assert list_payload["read_only"] is True
    assert list_payload["result"]["profiles"][0]["name"] == "generic"

    explain_payload = call_tool_payload(server, "aegis.explain_profile", {"profile": "generic"})
    assert explain_payload["ok"] is True
    assert explain_payload["result"]["name"] == "generic"


def test_core_aegis_error_maps_to_structured_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    def fail_inspect(*_args, **_kwargs):
        raise server.aegis_installer.AegisError("controlled core failure")

    monkeypatch.setattr(server.aegis_installer, "inspect_project", fail_inspect)

    payload = call_tool_payload(server, "aegis.inspect", {"target_dir": tmp_path.as_posix()})

    assert payload["ok"] is False
    assert payload["error"]["code"] == "aegis_error"
    assert payload["error"]["status"] == "invalid_request"
    assert payload["error"]["message"] == "controlled core failure"


def test_schema_validation_failure_maps_to_structured_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    def invalid_plan(*_args, **_kwargs):
        return {"schema_version": "1.0.0"}

    monkeypatch.setattr(server.aegis_installer, "plan_install", invalid_plan)

    payload = call_tool_payload(
        server,
        "aegis.plan_install",
        {
            "target_dir": tmp_path.as_posix(),
            "primary_agent": "claude",
            "agents": ["claude"],
        },
    )

    assert payload["ok"] is False
    assert payload["error"]["code"] == "schema_validation_failed"
    assert payload["error"]["status"] == "invalid_response"


def test_failed_install_report_preserves_cleanup_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    def failed_install(*_args, **_kwargs):
        return {
            "schema_version": "1.0.0",
            "status": "failed",
            "reason": "write failure",
            "cleanup": {"status": "completed", "removed_paths": ["CLAUDE.md"]},
        }

    monkeypatch.setattr(server.aegis_installer, "install", failed_install)

    payload = call_tool_payload(
        server,
        "aegis.install",
        {
            "target_dir": tmp_path.as_posix(),
            "profile": "generic",
            "primary_agent": "claude",
            "agents": ["claude"],
            "apply": True,
        },
    )

    assert payload["ok"] is False
    assert payload["error"]["code"] == "install_failed"
    assert payload["error"]["status"] == "failed"
    assert payload["error"]["details"]["report"]["cleanup"]["removed_paths"] == ["CLAUDE.md"]


def test_not_installed_resources_return_structured_payloads(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    manifest = read_resource_payload(server, "aegis://manifest/current")
    contract = read_resource_payload(server, "aegis://contract/current")
    managed_files = read_resource_payload(server, "aegis://managed-files")
    latest_plan = read_resource_payload(server, "aegis://install-plan/latest")

    assert manifest["ok"] is False
    assert manifest["error"]["code"] == "not_installed"
    assert contract["ok"] is False
    assert contract["error"]["code"] == "not_installed"
    assert managed_files["ok"] is False
    assert managed_files["error"]["code"] == "not_installed"
    assert latest_plan["ok"] is False
    assert latest_plan["error"]["code"] == "not_available"


def test_schema_and_profile_resources_are_read_only_source_payloads(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    foundation_schema = read_resource_payload(server, "aegis://schemas/foundation-manifest")
    profile_schema = read_resource_payload(server, "aegis://schemas/profile")
    install_plan_schema = read_resource_payload(server, "aegis://schemas/install-plan")
    profiles = read_resource_payload(server, "aegis://profiles")
    profile = read_resource_payload(server, "aegis://profiles/generic")

    assert foundation_schema["ok"] is True
    assert foundation_schema["source"] == "source"
    assert foundation_schema["result"]["title"] == "Aegis Foundation Manifest"
    assert profile_schema["result"]["title"] == "Aegis Project Profile"
    assert install_plan_schema["result"]["title"] == "Aegis Install Plan"
    assert profiles["result"]["profiles"][0]["name"] == "generic"
    assert profile["result"]["name"] == "generic"


def test_install_plan_resource_prefers_session_cache_then_report(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=target)
    server = create_server(config)

    call_tool_payload(
        server,
        "aegis.plan_install",
        {
            "target_dir": target.as_posix(),
            "primary_agent": "claude",
            "agents": ["claude"],
        },
    )
    cached = read_resource_payload(server, "aegis://install-plan/latest")
    assert cached["ok"] is True
    assert cached["source"] == "session_cache"
    assert cached["result"]["mode"] == "dry_run"

    second_server = create_server(config)
    call_tool_payload(
        second_server,
        "aegis.install",
        {
            "target_dir": target.as_posix(),
            "profile": "generic",
            "primary_agent": "claude",
            "agents": ["claude"],
            "apply": True,
        },
    )
    report_backed = read_resource_payload(second_server, "aegis://install-plan/latest")
    assert report_backed["ok"] is True
    assert report_backed["source"] == "target_report"
    assert report_backed["result"]["mode"] == "apply"


def test_installed_target_resources_and_latest_verification(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=target)
    server = create_server(config)

    install_payload = call_tool_payload(
        server,
        "aegis.install",
        {
            "target_dir": target.as_posix(),
            "profile": "generic",
            "primary_agent": "claude",
            "agents": ["claude"],
            "apply": True,
        },
    )
    assert install_payload["ok"] is True
    verify_payload = call_tool_payload(
        server,
        "aegis.verify",
        {
            "target_dir": target.as_posix(),
            "acknowledge_report_write": True,
        },
    )
    assert verify_payload["ok"] is True

    manifest = read_resource_payload(server, "aegis://manifest/current")
    contract = read_resource_payload(server, "aegis://contract/current")
    managed_files = read_resource_payload(server, "aegis://managed-files")
    verification = read_resource_payload(server, "aegis://verification/latest")

    assert manifest["ok"] is True
    assert manifest["result"]["payload"]["primary_agent"] == "claude"
    assert contract["ok"] is True
    assert "Aegis Foundation Contract" in contract["result"]["content"]
    assert managed_files["ok"] is True
    assert any(item["path"] == "CLAUDE.md" for item in managed_files["result"]["managed_files"])
    assert verification["ok"] is True
    assert verification["result"]["payload"]["status"] == "passed"


def test_limitations_resource_includes_policy_and_deferred_tool_notes(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    payload = read_resource_payload(server, "aegis://limitations")

    assert payload["ok"] is True
    assert any(
        gate["id"] == "mcp.memory_write"
        for gate in payload["result"]["policy_only_gates"]
    )
    assert "aegis.status" not in payload["result"]["deferred_tools"]
    assert "aegis.update" in payload["result"]["deferred_tools"]
    assert any("Prompts are guidance only" in note for note in payload["result"]["prompt_limitations"])


def test_prompts_preserve_workflow_and_evidence_invariants(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    for prompt_name in PROMPT_NAMES:
        text = get_prompt_text(server, prompt_name)

        assert "Do not write `.aegis/` directly" in text
        assert "Aegis prompts are advisory" in text
        assert "prompt text" in text
        assert "aegis://limitations" in text or prompt_name == "aegis.close_agent_session"
        assert "policy-only" in text or "policy" in text

    bootstrap = get_prompt_text(server, "aegis.bootstrap_new_project")
    assert "aegis.inspect" in bootstrap
    assert "aegis.plan_install" in bootstrap
    assert "user" in bootstrap and "approval" in bootstrap
    assert "aegis.install" in bootstrap
    assert "aegis.verify" in bootstrap
    assert "mechanical gates" in bootstrap

    start_task = get_prompt_text(server, "aegis.start_task")
    assert "aegis.status" in start_task
    assert "aegis.next" in start_task
    assert "aegis.kickoff" in start_task
    assert "plan_step=auto" in start_task

    implement_task = get_prompt_text(server, "aegis.implement_task")
    assert "native agent tools" in implement_task
    assert "pending_event_id=current" in implement_task
    assert "plan_step=auto" in implement_task

    closeout_task = get_prompt_text(server, "aegis.closeout_task")
    assert "aegis.closeout_ready" in closeout_task
    assert "aegis.verify" in closeout_task
    assert "Only report completion after closeout writes a passing report" in closeout_task


def test_entrypoint_describe_config_does_not_start_server(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "scripts/aegis-mcp-server",
            "--source-root",
            str(REPO_ROOT),
            "--default-target-dir",
            str(target),
            "--describe-config",
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "distribution_name": DISTRIBUTION_NAME,
        "asset_origin": "source",
        "foundation_version": FOUNDATION_VERSION,
        "installer_version": INSTALLER_VERSION,
        "schema_version": SCHEMA_VERSION,
        "source_root": REPO_ROOT.as_posix(),
        "default_target_dir": target.resolve().as_posix(),
    }


def test_direct_stdio_mcp_smoke_lists_aegis_surfaces(tmp_path: Path) -> None:
    tools, resources, prompts = asyncio.run(run_stdio_smoke(tmp_path))

    assert tools == set(V1_TOOL_NAMES)
    assert resources == set(RESOURCE_URIS)
    assert prompts == set(PROMPT_NAMES)
