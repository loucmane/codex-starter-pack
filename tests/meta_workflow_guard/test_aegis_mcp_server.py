"""Tests for the Aegis MCP server scaffold."""

from __future__ import annotations

import asyncio
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

import pytest
from mcp import types as mcp_types
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from aegis_foundation import (
    DISTRIBUTION_NAME,
    FOUNDATION_VERSION,
    INSTALLER_VERSION,
    SCHEMA_VERSION,
)
from aegis_mcp.server import (
    AegisMCPConfig,
    PROMPT_NAMES,
    RESOURCE_URIS,
    SERVER_NAME,
    V1_TOOL_NAMES,
    create_server,
)
from scripts._aegis_installer import (
    AEGIS_CLIENT_RELOAD_REL,
    AEGIS_CLOSEOUT_REPORT_REL,
    AEGIS_MANIFEST_REL,
    AEGIS_PENDING_TRACKING_REL,
    AEGIS_REPAIR_REPORT_REL,
    AEGIS_RUNTIME_ENV_REL,
    AEGIS_UPDATE_REPORT_REL,
    AEGIS_VERIFY_REPORT_REL,
    closeout,
    install,
    kickoff,
    log_work,
    verify,
)
from scripts._aegis_installer import _content_checksum

REPO_ROOT = Path(__file__).resolve().parents[2]
RECONCILE_MUTATION_PARAMETER_NAMES = {
    "apply",
    "auto",
    "auto_fix",
    "fix",
    "set_status",
    "status",
    "done",
    "closeout",
    "mutate",
    "write",
    "push",
}
FORBIDDEN_AGENT_TARGET_SELECTOR_NAMES = {
    "cwd",
    "dir",
    "directory",
    "file_path",
    "path",
    "project_dir",
    "project_root",
    "relative_path",
    "repo_dir",
    "repo_root",
    "repository_dir",
    "root",
    "source_root",
    "target_root",
    "work_dir",
    "workdir",
    "worktree",
    "worktree_dir",
}


def list_tools(server: FastMCP):
    return asyncio.run(server.list_tools())


def tool_by_name(server: FastMCP, name: str):
    tools = {tool.name: tool for tool in list_tools(server)}
    return tools[name]


def forbidden_target_selector_names(schema: dict) -> list[str]:
    properties = schema.get("properties", {})
    assert isinstance(properties, dict)
    return sorted(name for name in properties if name in FORBIDDEN_AGENT_TARGET_SELECTOR_NAMES)


def call_tool_payload(server: FastMCP, name: str, arguments: dict | None = None) -> dict:
    content, structured_payload = asyncio.run(server.call_tool(name, arguments or {}))
    assert len(content) == 1
    payload = json.loads(content[0].text)
    assert structured_payload == payload
    return payload


def assert_client_reload_blocked(payload: dict, *, tool: str, report_status: str) -> dict:
    assert payload["ok"] is False
    assert payload["tool"] == tool
    assert payload["error"]["code"] == "client_reload_required"
    assert payload["error"]["status"] == "blocked"
    assert payload["error"]["details"]["must_stop"] is True
    assert "source edits" in payload["error"]["details"]["forbidden_until_reload"]
    report = payload["error"]["details"]["report"]
    assert report["status"] == report_status
    return report


def simulate_claude_reload(target: Path) -> None:
    result = subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "pretooluse-gate.sh")],
        cwd=target,
        input=json.dumps(
            {
                "tool_name": "mcp__aegis__aegis_next",
                "tool_input": {"target_dir": target.as_posix()},
            }
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "CLAUDE_PROJECT_DIR": target.as_posix()},
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert not (target / AEGIS_CLIENT_RELOAD_REL).exists()


def read_resource_payload(server: FastMCP, uri: str) -> dict:
    contents = asyncio.run(server.read_resource(uri))
    assert len(contents) == 1
    return json.loads(contents[0].content)


def get_prompt_text(server: FastMCP, name: str, arguments: dict | None = None) -> str:
    prompt = asyncio.run(server.get_prompt(name, arguments or {}))
    assert len(prompt.messages) == 1
    return prompt.messages[0].content.text


def run_stdio_smoke(target: Path) -> tuple[set[str], set[str], set[str]]:
    """Exercise the real stdio entrypoint with bounded newline-JSON RPC frames.

    The Python `mcp.client.stdio_client` currently hangs in this environment after the
    initialize exchange. This smoke keeps the coverage on the server entrypoint and
    transport without letting a client-side transport regression hang pytest forever.
    """

    server_env = {
        key: value for key, value in os.environ.items() if not key.startswith("PYTEST_")
    }
    server_env["PYTHONUNBUFFERED"] = "1"

    process = subprocess.Popen(
        [
            sys.executable,
            "scripts/aegis-mcp-server",
            "--source-root",
            REPO_ROOT.as_posix(),
            "--default-target-dir",
            target.as_posix(),
        ],
        cwd=REPO_ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=server_env,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None
    stopped = False

    def stop_process() -> str:
        nonlocal stopped
        if stopped:
            return ""
        stopped = True
        try:
            if process.stdin is not None:
                process.stdin.close()
        except OSError:
            pass
        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        return process.stderr.read() if process.stderr is not None else ""

    frames = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": mcp_types.LATEST_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "aegis-stdio-smoke", "version": "0"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}},
        {"jsonrpc": "2.0", "id": 4, "method": "prompts/list", "params": {}},
    ]
    try:
        for frame in frames:
            process.stdin.write(json.dumps(frame) + "\n")
        process.stdin.flush()

        responses: dict[int, dict] = {}
        timeout = 120 if os.environ.get("PYTEST_XDIST_WORKER") else 30
        deadline = time.monotonic() + timeout
        while {1, 2, 3, 4} - set(responses):
            remaining = max(0, deadline - time.monotonic())
            if remaining == 0:
                returncode = process.poll()
                stderr = stop_process()
                raise AssertionError(
                    f"stdio smoke timed out after {timeout}s waiting for responses; "
                    f"got ids={sorted(responses)}; returncode={returncode}; stderr={stderr}"
                )
            ready, _, _ = select.select([process.stdout], [], [], remaining)
            if not ready:
                continue
            line = process.stdout.readline()
            if not line:
                stderr = stop_process()
                raise AssertionError(
                    f"stdio server exited before expected responses; got ids={sorted(responses)}; "
                    f"stderr={stderr}"
                )
            payload = json.loads(line)
            if "id" in payload:
                responses[int(payload["id"])] = payload
    finally:
        stop_process()

    return (
        {tool["name"] for tool in responses[2]["result"]["tools"]},
        {resource["uri"] for resource in responses[3]["result"]["resources"]},
        {prompt["name"] for prompt in responses[4]["result"]["prompts"]},
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
        "default_primary_agent": "claude",
        "default_agents": ["claude"],
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
        "aegis.update",
        "aegis.next",
        "aegis.doctor",
        "aegis.reconcile",
        "aegis.repair",
        "aegis.plan_install",
        "aegis.install",
        "aegis.init",
        "aegis.verify",
        "aegis.closeout_ready",
        "aegis.closeout",
        "aegis.handoff_repair",
        "aegis.start",
        "aegis.kickoff",
        "aegis.observe_start",
        "aegis.observe_stop",
        "aegis.runtime_status",
        "aegis.runtime_update",
        "aegis.log",
        "aegis.list_profiles",
        "aegis.explain_profile",
    }
    assert {
        "aegis.plan_update",
        "aegis.rollback",
    }.isdisjoint({tool.name for tool in tools})


def test_mcp_tool_schemas_use_target_dir_as_sole_agent_target_selector(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    for tool in list_tools(server):
        schema = tool.inputSchema
        assert forbidden_target_selector_names(schema) == [], tool.name
        properties = schema.get("properties", {})
        assert isinstance(properties, dict)
        if "target_dir" in properties:
            assert properties["target_dir"]["type"] == "string"


def test_mcp_tool_schema_target_selector_scan_rejects_aliases() -> None:
    project_dir_schema = {"properties": {"project_dir": {"type": "string"}}}

    assert forbidden_target_selector_names(project_dir_schema) == ["project_dir"]
    assert forbidden_target_selector_names({"properties": {"cwd": {"type": "string"}}}) == ["cwd"]
    assert forbidden_target_selector_names({"properties": {"target_dir": {"type": "string"}}}) == []


def test_workflow_tools_describe_required_next_actions(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    status_description = tool_by_name(server, "aegis.status").description or ""
    next_description = tool_by_name(server, "aegis.next").description or ""
    doctor_description = tool_by_name(server, "aegis.doctor").description or ""
    reconcile_description = tool_by_name(server, "aegis.reconcile").description or ""
    repair_description = tool_by_name(server, "aegis.repair").description or ""
    init_description = tool_by_name(server, "aegis.init").description or ""
    start_description = tool_by_name(server, "aegis.start").description or ""
    kickoff_description = tool_by_name(server, "aegis.kickoff").description or ""
    observe_start_description = tool_by_name(server, "aegis.observe_start").description or ""
    observe_stop_description = tool_by_name(server, "aegis.observe_stop").description or ""
    log_description = tool_by_name(server, "aegis.log").description or ""
    verify_description = tool_by_name(server, "aegis.verify").description or ""
    closeout_ready_description = tool_by_name(server, "aegis.closeout_ready").description or ""
    closeout_description = tool_by_name(server, "aegis.closeout").description or ""
    handoff_repair_description = tool_by_name(server, "aegis.handoff_repair").description or ""

    assert "next workflow guidance" in status_description
    assert "next required Aegis workflow action" in next_description
    assert "read-only" in next_description
    assert "Read-only state diagnostic" in doctor_description
    assert "Read-only Taskmaster/Aegis/git/PR drift report" in reconcile_description
    assert "never auto-mutates status" in reconcile_description
    assert "Preview or apply safe Aegis state repairs" in repair_description
    assert "Public project setup" in init_description
    assert "Public local-task kickoff" in start_description
    assert "plan-step-scope before source edits" in kickoff_description
    assert "Start observation mode" in observe_start_description
    assert "Stop observation mode" in observe_stop_description
    assert "pending_event_id=current" in log_description
    assert "log its pending event before closeout" in verify_description
    assert "Read-only pre-closeout gate check" in closeout_ready_description
    assert "scope, implement, verify" in closeout_description
    assert "HANDOFF.md semantic-section repair" in handoff_repair_description


def test_reconcile_mcp_schema_keeps_report_only_contract(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    tool = tool_by_name(server, "aegis.reconcile")
    schema = tool.inputSchema
    description = tool.description or ""

    assert set(schema["required"]) == {"target_dir"}
    assert set(schema["properties"]) == {
        "target_dir",
        "base_ref",
        "use_github",
        "preview_candidates",
    }
    assert set(schema["properties"]).isdisjoint(RECONCILE_MUTATION_PARAMETER_NAMES)
    assert "Read-only Taskmaster/Aegis/git/PR drift report" in description
    assert "optional inert preview" in description
    assert "never auto-mutates status" in description


def test_reconcile_mcp_execution_is_report_only(tmp_path: Path) -> None:
    target = tmp_path / "reconcile-mcp-read-only"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    status_before = subprocess.run(
        ["git", "status", "--short"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=target)
    server = create_server(config)

    payload = call_tool_payload(
        server,
        "aegis.reconcile",
        {
            "target_dir": target.as_posix(),
            "base_ref": "main",
            "use_github": False,
            "preview_candidates": False,
        },
    )

    assert payload["ok"] is True
    assert payload["read_only"] is True
    assert payload["result"]["read_only"] is True
    assert payload["result"]["status"] == "clean"
    assert "never mutates Taskmaster" in "\n".join(payload["result"]["notes"])
    status_after = subprocess.run(
        ["git", "status", "--short"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout
    assert status_after == status_before


@pytest.mark.parametrize(
    "tool_name",
    [
        "aegis.inspect",
        "aegis.status",
        "aegis.doctor",
        "aegis.reconcile",
    ],
)
def test_read_only_mcp_tools_reject_target_dir_outside_configured_root(
    tmp_path: Path,
    tool_name: str,
) -> None:
    allowed = tmp_path / "allowed-target"
    outside = tmp_path / "outside-target"
    allowed.mkdir()
    outside.mkdir()
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=allowed)
    server = create_server(config)
    arguments: dict[str, object] = {"target_dir": outside.as_posix()}
    if tool_name == "aegis.reconcile":
        arguments.update({"base_ref": "main", "use_github": False})

    payload = call_tool_payload(server, tool_name, arguments)

    assert payload["ok"] is False
    assert payload["tool"] == tool_name
    assert payload["error"]["code"] == "invalid_target"
    assert payload["error"]["status"] == "invalid_request"
    assert payload["error"]["details"]["allowed_root"] == allowed.resolve().as_posix()
    assert payload["error"]["details"]["resolved_target_dir"] == outside.resolve().as_posix()


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
    assert init_schema["properties"]["primary_agent"]["default"] is None
    assert init_schema["properties"]["agents"]["default"] is None

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


def test_observe_schemas_require_explicit_apply(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    start_schema = tool_by_name(server, "aegis.observe_start").inputSchema
    assert set(start_schema["required"]) == {"target_dir", "title"}
    assert start_schema["properties"]["apply"]["default"] is False

    stop_schema = tool_by_name(server, "aegis.observe_stop").inputSchema
    assert set(stop_schema["required"]) == {"target_dir"}
    assert stop_schema["properties"]["apply"]["default"] is False
    assert stop_schema["properties"]["allow_dirty"]["default"] is False
    assert stop_schema["properties"]["collect_artifacts"]["default"] is False


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
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="mcp-pending-id", title="MCP Pending Id")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
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
        (
            "aegis.plan_install",
            {"target_dir": tmp_path.as_posix(), "agents": ["claude"]},
            "primary_agent",
        ),
        (
            "aegis.plan_install",
            {"target_dir": tmp_path.as_posix(), "primary_agent": "claude"},
            "agents",
        ),
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
            {
                "target_dir": tmp_path.as_posix(),
                "handler": "claude-test",
                "evidence": "reports/example.txt",
            },
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

    observe_start_payload = call_tool_payload(
        server,
        "aegis.observe_start",
        {
            "target_dir": target.as_posix(),
            "title": "Polish audit",
            "apply": False,
        },
    )
    assert observe_start_payload["ok"] is False
    assert observe_start_payload["error"]["code"] == "apply_required"
    assert not (target / ".aegis" / "state" / "current-work.json").exists()

    observe_stop_payload = call_tool_payload(
        server,
        "aegis.observe_stop",
        {
            "target_dir": target.as_posix(),
            "summary": "Observed nothing",
            "apply": False,
        },
    )
    assert observe_stop_payload["ok"] is False
    assert observe_stop_payload["error"]["code"] == "apply_required"

    runtime_update_payload = call_tool_payload(
        server,
        "aegis.runtime_update",
        {
            "target_dir": target.as_posix(),
            "apply": False,
        },
    )
    assert runtime_update_payload["ok"] is False
    assert runtime_update_payload["error"]["code"] == "apply_required"


def test_runtime_status_and_update_tools_do_not_reinstall_scaffold(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    target.mkdir()
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)

    bootstrap_before = {
        rel: (target / rel).read_text(encoding="utf-8")
        for rel in (
            ".aegis/bin/aegis",
            ".claude/settings.json",
            ".claude/scripts/pretooluse-gate.sh",
            ".claude/scripts/readiness.sh",
        )
    }
    status_payload = call_tool_payload(
        server,
        "aegis.runtime_status",
        {"target_dir": target.as_posix()},
    )
    assert status_payload["ok"] is True
    assert status_payload["read_only"] is True
    assert status_payload["result"]["active_source_root"] == REPO_ROOT.resolve().as_posix()
    assert status_payload["result"]["active_source_valid"] is True

    update_payload = call_tool_payload(
        server,
        "aegis.runtime_update",
        {"target_dir": target.as_posix(), "apply": True},
    )
    assert update_payload["ok"] is True
    assert update_payload["read_only"] is False
    assert update_payload["result"]["status"] == "applied"
    assert update_payload["result"]["reinstall_required"] is False
    assert (target / AEGIS_RUNTIME_ENV_REL).read_text(encoding="utf-8") == (
        "# Aegis runtime pointer. Managed by aegis runtime update.\n"
        f"AEGIS_SOURCE_ROOT={REPO_ROOT.resolve().as_posix()}\n"
    )
    assert bootstrap_before == {
        rel: (target / rel).read_text(encoding="utf-8") for rel in bootstrap_before
    }


def test_project_update_tool_refreshes_stale_managed_assets(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "project-update-target"
    target.mkdir()
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)

    stale_rel = ".claude/scripts/brief_lib.py"
    stale_content = b"# stale installed managed asset\n"
    (target / stale_rel).write_bytes(stale_content)
    manifest_path = target / AEGIS_MANIFEST_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    record = next(
        item
        for item in manifest["managed_files"]
        if isinstance(item, dict) and item.get("path") == stale_rel
    )
    record["checksum"] = _content_checksum(stale_content)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    preview_payload = call_tool_payload(
        server,
        "aegis.update",
        {"target_dir": target.as_posix(), "apply": False, "detail": "all"},
    )
    assert preview_payload["ok"] is True
    assert preview_payload["read_only"] is True
    assert preview_payload["result"]["status"] == "preview"
    preview_operations = {
        operation["path"]: operation
        for operation in preview_payload["result"]["install"]["plan"]["operations"]
    }
    assert preview_operations[stale_rel]["classification"] == "modify"
    assert (target / stale_rel).read_text(encoding="utf-8") == "# stale installed managed asset\n"

    apply_payload = call_tool_payload(
        server,
        "aegis.update",
        {"target_dir": target.as_posix(), "apply": True, "detail": "all"},
    )
    update_report = assert_client_reload_blocked(
        apply_payload,
        tool="aegis.update",
        report_status="applied",
    )
    assert (target / stale_rel).read_text(encoding="utf-8") == (REPO_ROOT / stale_rel).read_text(encoding="utf-8")
    assert update_report["status"] == "applied"
    assert (target / AEGIS_UPDATE_REPORT_REL).is_file()
    assert (target / ".aegis" / "capsule" / "current.json").is_file()


def test_project_update_tool_refuses_locally_diverged_managed_asset(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "project-update-diverged-target"
    target.mkdir()
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)

    diverged_rel = ".claude/scripts/brief_lib.py"
    diverged_content = "# locally hardened managed asset\n"
    (target / diverged_rel).write_text(diverged_content, encoding="utf-8")

    payload = call_tool_payload(
        server,
        "aegis.update",
        {"target_dir": target.as_posix(), "apply": False, "detail": "all"},
    )

    assert payload["ok"] is False
    assert payload["error"]["code"] == "update_refused"
    report = payload["error"]["details"]["report"]
    operations = {
        operation["path"]: operation for operation in report["install"]["plan"]["operations"]
    }
    assert report["status"] == "refused"
    assert operations[diverged_rel]["classification"] == "manual-review"
    assert (target / diverged_rel).read_text(encoding="utf-8") == diverged_content


def test_doctor_and_repair_tools_preserve_read_only_preview_contract(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "doctor-repair-target"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        profile="generic",
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    shim = target / ".aegis" / "bin" / "aegis"
    shim.unlink()

    doctor_payload = call_tool_payload(
        server,
        "aegis.doctor",
        {"target_dir": target.as_posix(), "detail": "all"},
    )

    assert doctor_payload["ok"] is True
    assert doctor_payload["read_only"] is True
    assert doctor_payload["result"]["repair_plan"]["safe"] >= 1

    preview_payload = call_tool_payload(
        server,
        "aegis.repair",
        {"target_dir": target.as_posix(), "apply": False},
    )

    assert preview_payload["ok"] is True
    assert preview_payload["read_only"] is True
    assert preview_payload["result"]["status"] == "preview"
    assert not shim.exists()
    assert not (target / AEGIS_REPAIR_REPORT_REL).exists()

    applied_payload = call_tool_payload(
        server,
        "aegis.repair",
        {"target_dir": target.as_posix(), "apply": True},
    )

    assert applied_payload["ok"] is True
    assert applied_payload["read_only"] is False
    assert applied_payload["result"]["status"] == "applied"
    assert shim.is_file()
    assert (target / AEGIS_REPAIR_REPORT_REL).is_file()


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

    report = assert_client_reload_blocked(payload, tool="aegis.install", report_status="applied")
    assert report["client_reload"]["must_stop"] is True
    assert report["client_reload"]["severity"] == "hard_stop"
    assert (target / AEGIS_MANIFEST_REL).exists()


def test_public_init_returns_hard_stop_when_claude_reload_is_required(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    target.mkdir()

    payload = call_tool_payload(
        server,
        "aegis.init",
        {
            "target_dir": target.as_posix(),
            "apply": True,
        },
    )

    report = assert_client_reload_blocked(payload, tool="aegis.init", report_status="initialized")
    assert report["next_action"]["action"] == "restart_claude_before_mutation"
    assert report["next_action"]["details"]["must_stop"] is True
    assert "Taskmaster mutations" in report["install"]["client_reload"]["forbidden_until_reload"]
    assert (target / AEGIS_CLIENT_RELOAD_REL).exists()


def test_install_refused_conflict_is_structured_error(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    (target / ".aegis").mkdir(parents=True)
    (target / AEGIS_MANIFEST_REL).write_text(
        '{"foundation_name": "Other Foundation"}\n', encoding="utf-8"
    )

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
    assert (target / AEGIS_MANIFEST_REL).read_text(
        encoding="utf-8"
    ) == '{"foundation_name": "Other Foundation"}\n'


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
    assert_client_reload_blocked(install_payload, tool="aegis.install", report_status="applied")

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
    assert_client_reload_blocked(install_payload, tool="aegis.install", report_status="applied")
    simulate_claude_reload(target)
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
            "detail": "all",
        },
    )

    assert verify_payload["ok"] is True
    assert verify_payload["result"]["mode"] == "strict"
    assert verify_payload["result"]["status"] == "passed"
    assert (
        verify_payload["result"]["next_action"]["action"]
        == "log_strict_verification_before_closeout"
    )
    assert any(
        check["gate_id"] == "workflow.current_work" for check in verify_payload["result"]["checks"]
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
    assert_client_reload_blocked(install_payload, tool="aegis.install", report_status="applied")
    before = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in sorted(target.rglob("*"))
        if path.is_file()
    }

    payload = call_tool_payload(
        server,
        "aegis.status",
        {"target_dir": target.as_posix(), "detail": "all"},
    )

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
    assert payload["result"]["workflow_guidance"]["state"] == "client_reload_required"
    assert payload["result"]["workflow_guidance"]["suggested_mcp_call"]["tool"] == "aegis.next"


def test_agent_facing_mcp_status_obeys_context_budget_and_explicit_all_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    event_count = 3_500

    def huge_status(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "schema_version": "1.0.0",
            "status": "current",
            "installed": True,
            "workflow_guidance": {
                "status": "blocked",
                "details": {
                    "pending_event_ids": [f"event-{index}" for index in range(event_count)]
                },
            },
        }

    monkeypatch.setattr(server.aegis_installer, "status", huge_status)  # type: ignore[attr-defined]

    content, structured = asyncio.run(
        server.call_tool("aegis.status", {"target_dir": tmp_path.as_posix()})
    )
    assert len(content) == 1
    default = json.loads(content[0].text)
    assert structured == default
    assert len(content[0].text.splitlines()) <= 60
    assert len(content[0].text.encode("utf-8")) <= 8 * 1024
    assert default["ok"] is True
    assert default["result"]["status"] == "current"
    metadata = default["_aegis_output"]
    assert (
        metadata["collection_counts"]["$.result.workflow_guidance.details.pending_event_ids"]
        == event_count
    )
    assert metadata["next_action"] == "./.aegis/bin/aegis next --target-dir ."
    assert metadata["actual"] == (
        f"lines={len(content[0].text.splitlines())}; bytes={len(content[0].text.encode('utf-8'))}"
    )

    verbose_content, _verbose_structured = asyncio.run(
        server.call_tool(
            "aegis.status",
            {"target_dir": tmp_path.as_posix(), "detail": "verbose"},
        )
    )
    verbose = json.loads(verbose_content[0].text)
    assert len(verbose_content[0].text.splitlines()) <= 120
    assert len(verbose_content[0].text.encode("utf-8")) <= 32 * 1024
    assert len(verbose["result"]["workflow_guidance"]["details"]["pending_event_ids"]) == 20

    complete = call_tool_payload(
        server,
        "aegis.status",
        {"target_dir": tmp_path.as_posix(), "detail": "all"},
    )
    assert "_aegis_output" not in complete
    assert (
        len(complete["result"]["workflow_guidance"]["details"]["pending_event_ids"]) == event_count
    )


def test_failed_mcp_report_is_bounded_but_explicit_all_retains_every_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    failure_count = 3_500

    def failed_verify(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "status": "failed",
            "passed": False,
            "checks": [
                {"status": "fail", "gate_id": f"fixture.gate.{index}"}
                for index in range(failure_count)
            ],
        }

    monkeypatch.setattr(server.aegis_installer, "verify", failed_verify)  # type: ignore[attr-defined]
    content, _structured = asyncio.run(
        server.call_tool(
            "aegis.verify",
            {
                "target_dir": tmp_path.as_posix(),
                "acknowledge_report_write": True,
            },
        )
    )
    bounded = json.loads(content[0].text)
    assert len(content[0].text.splitlines()) <= 60
    assert len(content[0].text.encode("utf-8")) <= 8 * 1024
    assert bounded["ok"] is False
    assert bounded["error"]["code"] == "verification_failed"
    assert bounded["error"]["details"]["report"]["status"] == "failed"
    assert (
        bounded["_aegis_output"]["collection_counts"]["$.error.details.report.checks"]
        == failure_count
    )

    complete = call_tool_payload(
        server,
        "aegis.verify",
        {
            "target_dir": tmp_path.as_posix(),
            "acknowledge_report_write": True,
            "detail": "all",
        },
    )
    assert len(complete["error"]["details"]["report"]["checks"]) == failure_count


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

    payload = call_tool_payload(
        server,
        "aegis.next",
        {"target_dir": target.as_posix(), "detail": "all"},
    )

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
    assert payload["result"]["suggested_mcp_call"]["tool"] == "aegis.init"
    assert payload["result"]["suggested_mcp_call"]["arguments"]["apply"] is True
    assert payload["result"]["suggested_mcp_call"]["arguments"]["primary_agent"] == "claude"
    assert payload["result"]["suggested_mcp_call"]["arguments"]["agents"] == ["claude"]
    assert payload["result"]["details"]["must_initialize_before_source_edits"] is True
    assert "source edits" in payload["result"]["details"]["forbidden_until_init"]
    assert "Taskmaster mutations" in payload["result"]["details"]["forbidden_until_init"]


def test_inspect_reports_not_installed_hard_stop_guidance_without_mutation(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    target = tmp_path / "target"
    target.mkdir()
    before = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in sorted(target.rglob("*"))
        if path.is_file()
    }

    payload = call_tool_payload(server, "aegis.inspect", {"target_dir": target.as_posix()})

    after = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in sorted(target.rglob("*"))
        if path.is_file()
    }
    assert after == before
    assert payload["ok"] is True
    assert payload["tool"] == "aegis.inspect"
    assert payload["read_only"] is True
    assert payload["result"]["aegis"]["installed"] is False
    guidance = payload["result"]["workflow_guidance"]
    assert guidance["read_only"] is True
    assert guidance["phase"] == "bootstrap"
    assert guidance["state"] == "not_installed"
    assert guidance["suggested_mcp_call"]["tool"] == "aegis.init"
    assert guidance["suggested_mcp_call"]["arguments"]["apply"] is True
    assert guidance["suggested_mcp_call"]["arguments"]["primary_agent"] == "claude"
    assert guidance["suggested_mcp_call"]["arguments"]["agents"] == ["claude"]
    assert guidance["details"]["must_initialize_before_source_edits"] is True
    assert "source edits" in guidance["details"]["forbidden_until_init"]
    assert "project verification" in guidance["details"]["forbidden_until_init"]
    assert "Taskmaster mutations" in guidance["details"]["forbidden_until_init"]


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

    payload = call_tool_payload(
        server,
        "aegis.closeout_ready",
        {"target_dir": target.as_posix(), "detail": "all"},
    )

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


def test_handoff_repair_tool_previews_and_applies_without_closeout_report(tmp_path: Path) -> None:
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
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="handoff-repair", title="Handoff Repair")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    work_rel = current_work["paths"]["work_tracking"]
    evidence_rel = f"{current_work['paths']['reports']}/repair-evidence.txt"
    (target / evidence_rel).write_text("evidence\n", encoding="utf-8")

    log_work(
        target,
        handler="claude:scope",
        evidence=f"{work_rel}/FINDINGS.md",
        note="Confirmed MCP handoff repair scope",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    log_work(
        target,
        handler="claude:Write",
        evidence=evidence_rel,
        note="Captured MCP handoff repair implementation evidence",
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    log_work(
        target,
        handler="verify:inspection",
        evidence="cmd`test -f repair-evidence.txt`",
        note="Verified MCP handoff repair evidence exists",
        plan_step="plan-step-verify",
        plan_status="completed",
    )
    strict = verify(target, source_root=REPO_ROOT, strict=True)
    assert strict["status"] == "passed"
    log_work(
        target,
        handler="aegis:verify",
        evidence=AEGIS_VERIFY_REPORT_REL,
        note="Recorded strict verification evidence",
        plan_step="plan-step-verify",
        plan_status="completed",
    )
    handoff_path = target / work_rel / "HANDOFF.md"
    before = handoff_path.read_text(encoding="utf-8")

    preview = call_tool_payload(server, "aegis.handoff_repair", {"target_dir": target.as_posix()})

    assert preview["ok"] is True
    assert preview["read_only"] is True
    assert preview["result"]["status"] == "planned"
    assert preview["result"]["handoff"]["would_update"] is True
    assert handoff_path.read_text(encoding="utf-8") == before

    applied = call_tool_payload(
        server,
        "aegis.handoff_repair",
        {"target_dir": target.as_posix(), "apply": True},
    )

    assert applied["ok"] is True
    assert applied["read_only"] is False
    assert applied["result"]["status"] == "repaired"
    assert applied["result"]["handoff"]["updated"] is True
    assert applied["result"]["closeout_ready_after"]["status"] == "passed"
    assert not (target / AEGIS_CLOSEOUT_REPORT_REL).exists()
    assert closeout(target, source_root=REPO_ROOT, dry_run=True)["status"] == "passed"


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


def test_core_aegis_error_maps_to_structured_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
    assert_client_reload_blocked(install_payload, tool="aegis.install", report_status="applied")
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
    assert any(gate["id"] == "mcp.memory_write" for gate in payload["result"]["policy_only_gates"])
    assert "aegis.status" not in payload["result"]["deferred_tools"]
    assert "aegis.update" in payload["result"]["deferred_tools"]
    assert any(
        "Prompts are guidance only" in note for note in payload["result"]["prompt_limitations"]
    )


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
    assert "aegis.init apply=true" in bootstrap
    assert "aegis.plan_install" in bootstrap
    assert "aegis.install" in bootstrap
    assert "aegis.start apply=true" in bootstrap
    assert "aegis.next" in bootstrap
    assert "restart Claude" in bootstrap
    assert "client_reload.required" in bootstrap
    assert "mechanical gates" in bootstrap

    start_task = get_prompt_text(server, "aegis.start_task")
    assert "aegis.status" in start_task
    assert "aegis.next" in start_task
    assert "restart_claude_before_mutation" in start_task
    assert "task-master next" in start_task
    assert "task-master show <id>" in start_task
    assert "aegis.start apply=true" in start_task
    assert "aegis.kickoff" in start_task
    assert "Taskmaster numeric task id" in start_task
    assert "explicit external numeric task id" in start_task
    assert "plan_step=auto" in start_task

    implement_task = get_prompt_text(server, "aegis.implement_task")
    assert "native agent tools" in implement_task
    assert "pending_event_id=current" in implement_task
    assert "plan_step=auto" in implement_task

    closeout_task = get_prompt_text(server, "aegis.closeout_task")
    assert "aegis.closeout_ready" in closeout_task
    assert "aegis.handoff_repair" in closeout_task
    assert "Do not hand-edit HANDOFF.md" in closeout_task
    assert "aegis.verify" in closeout_task
    assert "aegis.doctor" in closeout_task
    assert "task-master generate" in closeout_task
    assert (
        "Only report completion after closeout passes and doctor reports the completed state"
        in closeout_task
    )


def test_tool_descriptions_make_aegis_discoverable_from_normal_task_requests(
    tmp_path: Path,
) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    inspect_description = tool_by_name(server, "aegis.inspect").description or ""
    init_description = tool_by_name(server, "aegis.init").description or ""
    next_description = tool_by_name(server, "aegis.next").description or ""
    kickoff_description = tool_by_name(server, "aegis.kickoff").description or ""

    assert "Use proactively" in inspect_description
    assert "normal coding task" in inspect_description
    assert "aegis.init" in inspect_description
    assert "before source edits" in inspect_description
    assert "CLI fallback only when aegis is on PATH" in inspect_description
    assert "project workflow" in init_description
    assert "default agent selection" in init_description
    assert "normal request" in next_description
    assert "Taskmaster" in kickoff_description


def test_codex_mcp_config_drives_not_installed_guidance_defaults(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    config = AegisMCPConfig.from_paths(
        source_root=REPO_ROOT,
        default_target_dir=target,
        default_primary_agent="codex",
        default_agents=["codex"],
    )
    server = create_server(config)

    payload = call_tool_payload(
        server,
        "aegis.next",
        {"target_dir": target.as_posix(), "detail": "all"},
    )

    guidance = payload["result"]
    assert guidance["suggested_cli"] == "aegis init --primary-agent codex --agent codex"
    assert "call suggested_mcp_call" in guidance["next_required_action"]
    assert "Use suggested_cli only as a CLI fallback" in guidance["next_required_action"]
    assert guidance["suggested_mcp_call"] == {
        "tool": "aegis.init",
        "arguments": {
            "target_dir": ".",
            "profile": "generic",
            "primary_agent": "codex",
            "agents": ["codex"],
            "apply": True,
            "verify_after_install": True,
        },
    }
    assert guidance["details"]["default_primary_agent"] == "codex"
    assert guidance["details"]["default_agents"] == ["codex"]
    assert guidance["details"]["preferred_invocation"] == "mcp"
    assert guidance["details"]["mcp_preferred_when_available"] is True
    assert guidance["details"]["cli_requires_aegis_on_path"] is True


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
        "default_primary_agent": "claude",
        "default_agents": ["claude"],
    }


def test_direct_stdio_mcp_smoke_lists_aegis_surfaces(tmp_path: Path) -> None:
    tools, resources, prompts = run_stdio_smoke(tmp_path)

    assert tools == set(V1_TOOL_NAMES)
    assert resources == set(RESOURCE_URIS)
    assert prompts == set(PROMPT_NAMES)
