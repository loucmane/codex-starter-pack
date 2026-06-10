"""TM #200: MCP/CLI version handshake — stale long-running servers must self-detect.

Reproduces the HP-Coach friction-13 class: the MCP server kept serving stale logic
after mid-session upstream bumps (empty repair plans while the fresh-reading CLI had
the fix). The handshake fingerprints the runtime-bearing source files at startup and
re-checks on every tool call: state-mutating tools are REFUSED when stale (mismatch
detected BEFORE action decisions); read-only tools answer but carry a runtime_stale
warning; aegis.runtime_status exposes both fingerprints.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from aegis_mcp.server import (  # noqa: E402
    AegisMCPConfig,
    RUNTIME_FINGERPRINT_FILES,
    create_server,
    runtime_fingerprint,
)


def call_tool_payload(server, name: str, arguments: dict | None = None) -> dict:
    content, structured = asyncio.run(server.call_tool(name, arguments or {}))
    payload = json.loads(content[0].text)
    assert structured == payload
    return payload


def make_source_copy(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    for rel in RUNTIME_FINGERPRINT_FILES:
        target = source / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / rel, target)
    return source


def make_target(tmp_path: Path) -> Path:
    target = tmp_path / "target"
    target.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=target, check=False)
    return target


def test_runtime_fingerprint_covers_runtime_files(tmp_path: Path) -> None:
    fingerprint = runtime_fingerprint(REPO_ROOT)
    assert set(fingerprint["files"]) == set(RUNTIME_FINGERPRINT_FILES)
    assert all(isinstance(value, str) for value in fingerprint["files"].values())
    missing = runtime_fingerprint(tmp_path / "nowhere")
    assert all(value is None for value in missing["files"].values())


def test_fresh_server_reports_not_stale(tmp_path: Path) -> None:
    target = make_target(tmp_path)
    config = AegisMCPConfig.from_paths(source_root=REPO_ROOT, default_target_dir=target)
    server = create_server(config)
    payload = call_tool_payload(server, "aegis.runtime_status", {"target_dir": str(target)})
    assert payload["ok"] is True
    assert "runtime_stale" not in payload
    assert payload["result"]["mcp_server"]["stale"] is False
    assert payload["result"]["mcp_server"]["started_fingerprint"]["files"]


def test_stale_server_refuses_mutating_tools(tmp_path: Path) -> None:
    source = make_source_copy(tmp_path)
    target = make_target(tmp_path)
    config = AegisMCPConfig.from_paths(source_root=source, default_target_dir=target)
    server = create_server(config)
    # Simulate the mid-session upstream bump: the source changes under the server.
    installer_copy = source / "scripts" / "_aegis_installer.py"
    installer_copy.write_text(installer_copy.read_text(encoding="utf-8") + "\n# bumped\n", encoding="utf-8")
    payload = call_tool_payload(
        server,
        "aegis.kickoff",
        {"target_dir": str(target), "task": "9", "slug": "x", "title": "X", "apply": True},
    )
    assert payload["ok"] is False
    assert payload["error"]["code"] == "runtime_stale_reload_required"
    assert payload["error"]["status"] == "blocked"
    details = payload["error"]["details"]
    assert details["started_with"]["files"] != details["on_disk"]["files"]
    assert "Restart the Aegis MCP server" in details["guidance"]


def test_stale_server_refuses_repair_before_producing_a_plan(tmp_path: Path) -> None:
    # The HP-Coach acceptance case: a stale server must never emit an (empty/stale)
    # repair decision — the mismatch is detected BEFORE the action decision.
    source = make_source_copy(tmp_path)
    target = make_target(tmp_path)
    config = AegisMCPConfig.from_paths(source_root=source, default_target_dir=target)
    server = create_server(config)
    gate_copy = source / ".claude" / "scripts" / "gate_lib.py"
    gate_copy.write_text(gate_copy.read_text(encoding="utf-8") + "\n# bumped\n", encoding="utf-8")
    payload = call_tool_payload(server, "aegis.repair", {"target_dir": str(target), "apply": True})
    assert payload["ok"] is False
    assert payload["error"]["code"] == "runtime_stale_reload_required"


def test_stale_server_answers_read_only_with_warning(tmp_path: Path) -> None:
    source = make_source_copy(tmp_path)
    target = make_target(tmp_path)
    config = AegisMCPConfig.from_paths(source_root=source, default_target_dir=target)
    server = create_server(config)
    ledger_copy = source / ".claude" / "scripts" / "ledger_lib.py"
    ledger_copy.write_text(ledger_copy.read_text(encoding="utf-8") + "\n# bumped\n", encoding="utf-8")
    payload = call_tool_payload(server, "aegis.runtime_status", {"target_dir": str(target)})
    assert payload["ok"] is True, "read-only tools keep answering when stale"
    assert payload["runtime_stale"]["started_with"]["files"] != payload["runtime_stale"]["on_disk"]["files"]
    assert payload["result"]["mcp_server"]["stale"] is True
