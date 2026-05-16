"""Tests for the Aegis MCP server scaffold."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from aegis_mcp.server import AegisMCPConfig, SERVER_NAME, V1_TOOL_NAMES, create_server


REPO_ROOT = Path(__file__).resolve().parents[2]


def list_tools(server: FastMCP):
    return asyncio.run(server.list_tools())


def tool_by_name(server: FastMCP, name: str):
    tools = {tool.name: tool for tool in list_tools(server)}
    return tools[name]


def test_config_defaults_to_repo_root() -> None:
    config = AegisMCPConfig.from_paths()

    assert config.source_root == REPO_ROOT
    assert config.default_target_dir == REPO_ROOT


def test_config_accepts_explicit_paths(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    config = AegisMCPConfig.from_paths(source_root=source, default_target_dir=target)

    assert config.source_root == source.resolve()
    assert config.default_target_dir == target.resolve()
    assert config.to_dict() == {
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
        "aegis.plan_install",
        "aegis.install",
        "aegis.verify",
        "aegis.list_profiles",
        "aegis.explain_profile",
    }
    assert {
        "aegis.status",
        "aegis.plan_update",
        "aegis.update",
        "aegis.rollback",
    }.isdisjoint({tool.name for tool in tools})


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


def test_verify_schema_requires_acknowledged_report_write(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)
    schema = tool_by_name(server, "aegis.verify").inputSchema

    assert set(schema["required"]) == {"target_dir", "acknowledge_report_write"}
    assert schema["properties"]["acknowledge_report_write"]["type"] == "boolean"


def test_valid_tool_call_is_validated_but_deferred_to_handler_wiring(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    content, structured_payload = asyncio.run(
        server.call_tool(
            "aegis.plan_install",
            {
                "target_dir": tmp_path.as_posix(),
                "primary_agent": "claude",
                "agents": ["claude"],
            },
        )
    )

    assert len(content) == 1
    payload = json.loads(content[0].text)
    assert structured_payload == payload
    assert payload["tool"] == "aegis.plan_install"
    assert payload["status"] == "handler_deferred"
    assert payload["validated_arguments"] == {
        "target_dir": tmp_path.as_posix(),
        "profile": "generic",
        "primary_agent": "claude",
        "agents": ["claude"],
    }


def test_invalid_or_omitted_agent_selection_is_rejected_before_core_call(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    invalid_calls = [
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
        try:
            asyncio.run(server.call_tool(tool_name, arguments))
        except ToolError as exc:
            assert expected_message in str(exc)
        else:
            raise AssertionError(f"{tool_name} unexpectedly accepted {arguments}")


def test_install_requires_apply_true_before_core_mutation(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    with pytest.raises(ToolError, match="apply must be true"):
        asyncio.run(
            server.call_tool(
                "aegis.install",
                {
                    "target_dir": tmp_path.as_posix(),
                    "profile": "generic",
                    "primary_agent": "claude",
                    "agents": ["claude"],
                    "apply": False,
                },
            )
        )

    with pytest.raises(ToolError, match="apply"):
        asyncio.run(
            server.call_tool(
                "aegis.install",
                {
                    "target_dir": tmp_path.as_posix(),
                    "profile": "generic",
                    "primary_agent": "claude",
                    "agents": ["claude"],
                },
            )
        )


def test_verify_requires_acknowledgement_true_before_report_write(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    with pytest.raises(ToolError, match="acknowledge_report_write must be true"):
        asyncio.run(
            server.call_tool(
                "aegis.verify",
                {
                    "target_dir": tmp_path.as_posix(),
                    "acknowledge_report_write": False,
                },
            )
        )

    with pytest.raises(ToolError, match="acknowledge_report_write"):
        asyncio.run(
            server.call_tool(
                "aegis.verify",
                {
                    "target_dir": tmp_path.as_posix(),
                },
            )
        )


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
        "source_root": REPO_ROOT.as_posix(),
        "default_target_dir": target.resolve().as_posix(),
    }
