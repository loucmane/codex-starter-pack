"""Tests for the Aegis MCP server scaffold."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from aegis_mcp.server import AegisMCPConfig, SERVER_NAME, create_server


REPO_ROOT = Path(__file__).resolve().parents[2]


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


def test_scaffold_registers_no_production_tools_yet(tmp_path: Path) -> None:
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=tmp_path)
    server = create_server(config)

    tools = asyncio.run(server.list_tools())

    assert tools == []


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
