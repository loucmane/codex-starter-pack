"""TM 191: browser-observation MCP tools are read-only and must not arm pending-tracking.

chrome-devtools / playwright tools drive a live browser, not the project tree, so observation
calls (snapshot, click, navigate, console, evaluate) are read-only w.r.t. the repo and should
not enqueue pending-tracking. The one exception: a call that writes a repo path (e.g.
take_screenshot with a filePath) is still a mutation and stays tracked.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_LIB = REPO_ROOT / ".claude" / "scripts" / "gate_lib.py"
POSTTOOLUSE = REPO_ROOT / ".claude" / "scripts" / "posttooluse-tracking.sh"
sys.path.insert(0, str(REPO_ROOT))


def load_gate_lib():
    spec = importlib.util.spec_from_file_location("gate_lib_browser", GATE_LIB)
    module = importlib.util.module_from_spec(spec)
    sys.modules["gate_lib_browser"] = module
    spec.loader.exec_module(module)
    return module


gate_lib = load_gate_lib()


READ_ONLY_BROWSER = [
    ("mcp__playwright__browser_click", {"ref": "x"}),
    ("mcp__playwright__browser_snapshot", {}),
    ("mcp__playwright__browser_navigate", {"url": "http://localhost:3000"}),
    ("mcp__playwright__browser_evaluate", {"function": "() => 1"}),
    ("mcp__playwright__browser_file_upload", {"paths": ["src/x.ts"]}),  # reads a file -> read-only
    ("mcp__chrome-devtools__take_snapshot", {}),
    ("mcp__chrome-devtools__list_console_messages", {}),
    ("mcp__chrome-devtools__navigate_page", {"url": "http://localhost"}),
    ("mcp__chrome-devtools__performance_start_trace", {}),
]

WRITES_REPO_PATH = [
    ("mcp__chrome-devtools__take_screenshot", {"filePath": "src/shot.png"}),
    ("mcp__playwright__browser_take_screenshot", {"path": "out/a.png"}),
]


@pytest.mark.parametrize(("tool", "tool_input"), READ_ONLY_BROWSER)
def test_browser_observation_is_read_only(tool: str, tool_input: dict) -> None:
    payload = gate_lib.Payload(tool, tool_input)
    assert gate_lib.payload_is_read_only(payload) is True, tool
    assert gate_lib.mcp_is_mutation(payload) is False, tool


@pytest.mark.parametrize(("tool", "tool_input"), WRITES_REPO_PATH)
def test_browser_write_to_repo_path_stays_mutation(tool: str, tool_input: dict) -> None:
    payload = gate_lib.Payload(tool, tool_input)
    assert gate_lib.mcp_is_mutation(payload) is True, tool


def test_non_browser_mcp_classification_unchanged() -> None:
    assert gate_lib.mcp_is_mutation(gate_lib.Payload("mcp__aegis__aegis_repair", {"apply": True})) is True
    assert gate_lib.mcp_is_mutation(gate_lib.Payload("mcp__taskmaster_ai__set_task_status", {"id": "1", "status": "done"})) is True
    assert gate_lib.mcp_is_mutation(gate_lib.Payload("mcp__taskmaster_ai__get_tasks", {})) is False
    assert gate_lib.mcp_is_mutation(gate_lib.Payload("mcp__unknown__do_thing", {})) is True  # unknown stays conservative


def make_in_progress_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=False)
    subprocess.run(["git", "checkout", "-q", "-b", "feat/task-9-x"], cwd=repo, check=False)
    (repo / ".taskmaster" / "tasks").mkdir(parents=True)
    (repo / ".aegis" / "state").mkdir(parents=True)
    (repo / ".taskmaster" / "tasks" / "tasks.json").write_text(
        json.dumps({"master": {"tasks": [{"id": 9, "status": "in-progress"}]}}), encoding="utf-8"
    )
    (repo / ".aegis" / "state" / "enforcement.json").write_text(
        json.dumps({"mode": "advisory", "set_by": "t", "reason": "r"}), encoding="utf-8"
    )
    (repo / ".aegis" / "state" / "current-work.json").write_text(
        json.dumps({"schema_version": "1", "status": "in-progress", "task": {"id": "9", "slug": "x", "status": "in-progress"}}),
        encoding="utf-8",
    )
    return repo


def enqueue_count(repo: Path, tool: str, tool_input: dict) -> int:
    pending = repo / ".aegis" / "state" / "pending-tracking.json"
    if pending.exists():
        pending.unlink()
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = repo.as_posix()
    subprocess.run(
        ["bash", POSTTOOLUSE.as_posix()], cwd=repo,
        input=json.dumps({"tool_name": tool, "tool_input": tool_input}),
        text=True, capture_output=True, env=env, check=False,
    )
    return len(json.loads(pending.read_text(encoding="utf-8")).get("events", [])) if pending.is_file() else 0


def test_browser_observation_does_not_arm_pending_tracking(tmp_path: Path) -> None:
    repo = make_in_progress_repo(tmp_path)
    assert enqueue_count(repo, "mcp__playwright__browser_click", {"ref": "x"}) == 0
    assert enqueue_count(repo, "mcp__chrome-devtools__take_snapshot", {}) == 0


def test_browser_screenshot_to_repo_path_still_arms(tmp_path: Path) -> None:
    repo = make_in_progress_repo(tmp_path)
    assert enqueue_count(repo, "mcp__chrome-devtools__take_screenshot", {"filePath": "src/shot.png"}) == 1


def test_assets_and_live_gate_lib_identical() -> None:
    live = (REPO_ROOT / ".claude" / "scripts" / "gate_lib.py").read_bytes()
    asset = (REPO_ROOT / "aegis_foundation" / "assets" / ".claude" / "scripts" / "gate_lib.py").read_bytes()
    assert live == asset
