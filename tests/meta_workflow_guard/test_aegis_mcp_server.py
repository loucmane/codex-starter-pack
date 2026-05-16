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
from scripts._aegis_installer import AEGIS_MANIFEST_REL


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
    target.mkdir()
    (target / "CLAUDE.md").write_text("# Existing\n", encoding="utf-8")

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
    assert not (target / AEGIS_MANIFEST_REL).exists()


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
