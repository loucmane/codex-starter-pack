"""TM #214: gate resilience when the home directory is unresolvable.

HP-Coach incident 2026-06-12: hooks executed in a sandboxed environment (no HOME, no
passwd entry for the uid) made ``Path.home()`` raise ``RuntimeError: Could not
determine home directory``, and the PreToolUse gate failed closed — hard-blocking a
mutation even though enforcement was advisory, with no traceback to diagnose from.

Contract under test:
- ``ledger_lib`` path resolution NEVER raises RuntimeError (fallback chain:
  XDG_STATE_HOME > HOME env > Path.home() > per-uid tmp store);
- gate path normalization survives unexpandable ``~`` paths;
- the degraded fallback honors the advisory contract (record + allow, loudly) and
  captures the traceback in both the strict block message and the degraded event.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import pathlib
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_LIB = REPO_ROOT / ".claude" / "scripts" / "gate_lib.py"
LEDGER_LIB = REPO_ROOT / ".claude" / "scripts" / "ledger_lib.py"

sys.path.insert(0, str(REPO_ROOT))


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


gate_lib = load_module(GATE_LIB, "gate_lib_home_resilience")
ledger_lib = load_module(LEDGER_LIB, "ledger_lib_home_resilience")


def payload(tool_name: str, **tool_input: object) -> str:
    return json.dumps({"tool_name": tool_name, "tool_input": tool_input})


def make_repo(tmp_path: Path, *, advisory: bool) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=False)
    subprocess.run(["git", "checkout", "-q", "-b", "feat/task-73-x"], cwd=repo, check=False)
    if advisory:
        state = repo / ".aegis" / "state"
        state.mkdir(parents=True)
        (state / "enforcement.json").write_text(
            json.dumps({"mode": "advisory", "set_by": "test", "reason": "resilience"}),
            encoding="utf-8",
        )
    return repo


def raise_home(*_args: object, **_kwargs: object) -> Path:
    raise RuntimeError("Could not determine home directory.")


# --- ledger path resolution -------------------------------------------------------


def test_state_base_prefers_xdg_then_home_env() -> None:
    assert ledger_lib._state_base({"XDG_STATE_HOME": "/var/state"}) == Path("/var/state")
    assert ledger_lib._state_base({"HOME": "/home/u"}) == Path("/home/u/.local/state")


def test_state_base_never_raises_without_home(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pathlib.Path, "home", classmethod(lambda cls: raise_home()))
    base = ledger_lib._state_base({})
    assert "aegis-state-" in base.name, "must fall back to a deterministic per-uid tmp store"


def test_open_ledger_survives_unresolvable_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = make_repo(tmp_path, advisory=False)
    monkeypatch.setattr(pathlib.Path, "home", classmethod(lambda cls: raise_home()))
    ledger = ledger_lib.open_ledger(cwd=repo, env={})
    try:
        ledger.append({"event_type": "verification", "extra": {"probe": True}})
        events = ledger.read(event_type="verification")
    finally:
        ledger.close()
    assert len(events) == 1


# --- gate path normalization ------------------------------------------------------


def test_safe_expanduser_keeps_literal_when_home_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    def raising_expanduser(self: Path) -> Path:
        raise RuntimeError("Could not determine home directory.")

    monkeypatch.setattr(pathlib.Path, "expanduser", raising_expanduser)
    assert gate_lib.safe_expanduser("~/notes.txt") == Path("~/notes.txt")
    assert gate_lib.normalize_path("~/notes.txt") == "~/notes.txt"
    assert gate_lib.is_protected_path("~/notes.txt") is False


# --- degraded fallback ------------------------------------------------------------


def run_degraded(repo: Path, monkeypatch: pytest.MonkeyPatch, raw: str) -> int:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo))

    def crash(_payload: object) -> bool:
        raise RuntimeError("Could not determine home directory.")

    monkeypatch.setattr(gate_lib, "payload_is_read_only", crash)
    return gate_lib.pretooluse_gate_with_degraded_fallback(raw)


def test_degraded_mutation_in_advisory_allows_and_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(tmp_path, advisory=True)
    raw = payload("Write", file_path="src/main.ts", content="x")
    assert run_degraded(repo, monkeypatch, raw) == 0, "advisory must never hard-block on infra failure"
    captured = capsys.readouterr()
    assert "DEGRADED-ADVISORY" in captured.err
    degraded = json.loads((repo / ".aegis" / "state" / "degraded-events.json").read_text(encoding="utf-8"))
    event = degraded["events"][0]
    assert event["mode"] == "degraded_advisory_allow"
    assert event["action_class"] == "mutation_or_unsafe"
    assert "Could not determine home directory" in event["traceback"]


def test_degraded_mutation_in_strict_blocks_with_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(tmp_path, advisory=False)
    raw = payload("Write", file_path="src/main.ts", content="x")
    assert run_degraded(repo, monkeypatch, raw) == 2, "strict mode keeps failing closed"
    captured = capsys.readouterr()
    assert "fails closed" in captured.err
    assert "Traceback (for diagnosis):" in captured.err
    assert "RuntimeError: Could not determine home directory." in captured.err


def test_degraded_read_only_still_allows_with_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = make_repo(tmp_path, advisory=False)
    raw = payload("Bash", command="git status --short")
    assert run_degraded(repo, monkeypatch, raw) == 0
    degraded = json.loads((repo / ".aegis" / "state" / "degraded-events.json").read_text(encoding="utf-8"))
    assert degraded["events"][0]["mode"] == "degraded_allow"


# --- end-to-end: sandboxed hook environment ---------------------------------------


def test_gate_subprocess_with_unresolvable_home_renders_policy_verdict(tmp_path: Path) -> None:
    """The full incident shape: gate subprocess, no HOME/XDG, Path.home() raising
    (via sitecustomize), a workflow-state mutation. The gate must render a POLICY
    verdict (advisory allow here), never the infra fail-closed wall."""

    repo = make_repo(tmp_path, advisory=True)
    sitepatch = tmp_path / "sitepatch"
    sitepatch.mkdir()
    (sitepatch / "sitecustomize.py").write_text(
        "import pathlib\n"
        "def _raise(*a, **k):\n"
        "    raise RuntimeError('Could not determine home directory.')\n"
        "pathlib.Path.home = classmethod(lambda cls: _raise())\n"
        "_orig = pathlib.Path.expanduser\n"
        "def _exp(self):\n"
        "    if str(self).startswith('~'):\n"
        "        raise RuntimeError('Could not determine home directory.')\n"
        "    return self\n"
        "pathlib.Path.expanduser = _exp\n",
        encoding="utf-8",
    )
    env = dict(os.environ)
    env.pop("HOME", None)
    env.pop("XDG_STATE_HOME", None)
    env["CLAUDE_PROJECT_DIR"] = str(repo)
    env["PYTHONPATH"] = str(sitepatch)
    raw = payload(
        "Bash",
        command='python3 - <<EOF\nimport json\njson.dump({}, open(".taskmaster/tasks/tasks.json","w"))\nEOF',
    )
    result = subprocess.run(
        [sys.executable, GATE_LIB.as_posix(), "pretooluse"],
        cwd=repo,
        input=raw,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "infrastructure failed" not in result.stderr, "infra wall must not appear in advisory mode"


def test_assets_and_live_copies_identical() -> None:
    for rel in (".claude/scripts/gate_lib.py", ".claude/scripts/ledger_lib.py"):
        live = (REPO_ROOT / rel).read_bytes()
        asset = (REPO_ROOT / "aegis_foundation" / "assets" / rel).read_bytes()
        assert live == asset, f"assets/live copies diverge for {rel}"
