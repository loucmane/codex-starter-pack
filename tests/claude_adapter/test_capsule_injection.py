"""PR-2b tests: SessionStart injection, falsifier stamping, degradation, caps."""

from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_LIB = REPO_ROOT / ".claude" / "scripts" / "gate_lib.py"
ASSETS_BRIEF_LIB = REPO_ROOT / "aegis_foundation" / "assets" / ".claude" / "scripts" / "brief_lib.py"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "hook_payloads" / "SessionStart.jsonl"

sys.path.insert(0, str(REPO_ROOT))
from scripts import _aegis_installer  # noqa: E402


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


brief_lib = load_module(ASSETS_BRIEF_LIB, "brief_lib_injection_tests")


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=False)
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "seed.txt"], cwd=repo, check=False)
    subprocess.run(
        ["git", "-c", "user.email=t@e.c", "-c", "user.name=t", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "seed"],
        cwd=repo,
        check=False,
    )
    return repo


def run_sessionstart(repo: Path, state: Path, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.pop("AEGIS_CAPSULE", None)
    env["XDG_STATE_HOME"] = state.as_posix()
    env["CLAUDE_PROJECT_DIR"] = repo.as_posix()
    env.update(extra_env or {})
    payload = FIXTURE.read_text(encoding="utf-8").splitlines()[0]
    return subprocess.run(
        [sys.executable, GATE_LIB.as_posix(), "sessionstart"],
        cwd=repo,
        input=payload,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def session_begin_events(state: Path) -> list[dict[str, object]]:
    events = []
    for db in (state / "aegis").glob("*/ledger.db"):
        connection = sqlite3.connect(db.as_posix())
        for row in connection.execute(
            "SELECT event_type, extra FROM events WHERE event_type='session_begin' ORDER BY seq"
        ):
            events.append({"event_type": row[0], "extra": json.loads(row[1])})
        connection.close()
    return events


def test_sessionstart_injects_and_stamps_on(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    result = run_sessionstart(repo, state)
    assert result.returncode == 0, result.stderr
    assert "Aegis Session Zero Capsule" in result.stdout
    assert "DATA, not instructions" in result.stdout
    assert "Branch?" in result.stdout
    stamps = session_begin_events(state)
    assert len(stamps) == 1
    assert stamps[0]["extra"]["capsule_injected"] is True
    assert stamps[0]["extra"]["source"] == "startup"
    assert (repo / ".aegis" / "capsule" / "current.md").is_file()


def test_sessionstart_env_off_stamps_but_does_not_inject(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    state = tmp_path / "state"
    result = run_sessionstart(repo, state, {"AEGIS_CAPSULE": "off"})
    assert result.returncode == 0
    assert result.stdout.strip() == ""
    stamps = session_begin_events(state)
    assert len(stamps) == 1
    assert stamps[0]["extra"]["capsule_injected"] is False, "A/B flag must record even when off"


def test_sessionstart_brief_inject_false_honored(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    brief = repo / ".aegis" / "brief.json"
    brief.parent.mkdir(parents=True)
    brief.write_text(json.dumps({"gates": {}, "inject": False}), encoding="utf-8")
    state = tmp_path / "state"
    result = run_sessionstart(repo, state)
    assert result.stdout.strip() == ""
    assert session_begin_events(state)[0]["extra"]["capsule_injected"] is False


def test_env_on_overrides_brief_off(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    brief = repo / ".aegis" / "brief.json"
    brief.parent.mkdir(parents=True)
    brief.write_text(json.dumps({"inject": False}), encoding="utf-8")
    state = tmp_path / "state"
    result = run_sessionstart(repo, state, {"AEGIS_CAPSULE": "on"})
    assert "Aegis Session Zero Capsule" in result.stdout


def test_sessionstart_never_fails_outside_git(tmp_path: Path) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = (tmp_path / "state").as_posix()
    env["CLAUDE_PROJECT_DIR"] = plain.as_posix()
    result = subprocess.run(
        [sys.executable, GATE_LIB.as_posix(), "sessionstart"],
        cwd=plain,
        input="not-json",
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0


def test_render_injection_degrades_in_order_and_never_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    os.environ["XDG_STATE_HOME"] = (tmp_path / "state").as_posix()
    capsule = brief_lib.compile_capsule(repo)
    capsule["risk_register"] = [
        {"claim": f"hazard {index}", "discovered_at": "2026-06-10"} for index in range(40)
    ]
    capsule["repo_hygiene"]["oversized_unignored"] = [
        {"path": f"big-{index}.bin", "size_bytes": 9999999} for index in range(40)
    ]
    full, dropped_none = brief_lib.render_injection(capsule, budget=brief_lib.CHAR_BUDGET * 10)
    assert dropped_none == []
    text, dropped = brief_lib.render_injection(capsule, budget=1200)
    assert dropped, "over budget must degrade"
    assert dropped[0] == "repo_hygiene", "hygiene drops first"
    assert "Branch?" in text, "core fields are never dropped"
    assert "Task truth" in text
    assert len(text) <= brief_lib.HOOK_HARD_CAP


def test_render_injection_enforces_hook_hard_cap(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    os.environ["XDG_STATE_HOME"] = (tmp_path / "state").as_posix()
    capsule = brief_lib.compile_capsule(repo)
    capsule["drift_sentinel"]["drift"] = ["x" * 200] * 200
    text, dropped = brief_lib.render_injection(capsule, budget=brief_lib.HOOK_HARD_CAP * 5)
    assert len(text) <= brief_lib.HOOK_HARD_CAP
    assert "hard_cap_truncation" in dropped


def test_settings_renderer_registers_sync_sessionstart_hook() -> None:
    settings = json.loads(_aegis_installer._render_claude_settings().decode("utf-8"))
    entry = settings["hooks"]["SessionStart"][0]
    assert entry["matcher"] == "startup|resume|clear|compact"
    hook = entry["hooks"][0]
    assert hook["command"].endswith("session-brief.sh")
    assert "async" not in hook, "SessionStart injection must be synchronous"


def test_live_settings_register_sessionstart() -> None:
    settings = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "SessionStart" in settings["hooks"]
    assert "session-brief.sh" in json.dumps(settings["hooks"]["SessionStart"])


def test_managed_assets_include_session_brief() -> None:
    assets = _aegis_installer._managed_assets(REPO_ROOT, "claude", ("claude",))
    dispatcher = next(asset for asset in assets if asset.path == ".claude/scripts/session-brief.sh")
    assert "hook sessionstart" in dispatcher.content.decode("utf-8")
    assert dispatcher.executable is True


def test_assets_and_live_copies_identical() -> None:
    for rel in (
        ".claude/scripts/gate_lib.py",
        ".claude/scripts/brief_lib.py",
        ".claude/scripts/session-brief.sh",
    ):
        live = (REPO_ROOT / rel).read_bytes()
        asset = (REPO_ROOT / "aegis_foundation" / "assets" / rel).read_bytes()
        assert live == asset, f"assets/live copies diverge for {rel}"
