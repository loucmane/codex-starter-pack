"""PR-1c tests: advisory gate decisions dual-written to the ledger with JSONL parity.

Parity key: payload_digest. The JSONL at .aegis/reports/gate-decisions.jsonl stays the
primary surface; the ledger twin is best-effort and must never break a gate decision.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_LIB = REPO_ROOT / ".claude" / "scripts" / "gate_lib.py"


def load_gate_lib():
    spec = importlib.util.spec_from_file_location("gate_lib_dualwrite_tests", GATE_LIB)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["gate_lib_dualwrite_tests"] = module
    spec.loader.exec_module(module)
    return module


gate_lib = load_gate_lib()


def make_advisory_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert subprocess.run(["git", "init", "-q"], cwd=repo, check=False).returncode == 0
    state = repo / ".aegis" / "state"
    state.mkdir(parents=True)
    (state / "enforcement.json").write_text(
        json.dumps({"mode": "advisory", "set_at": "2026-06-10T00:00:00Z", "set_by": "test", "reason": "test"}),
        encoding="utf-8",
    )
    return repo


def read_jsonl(repo: Path) -> list[dict[str, object]]:
    path = repo / ".aegis" / "reports" / "gate-decisions.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_ledger_events(state_home: Path) -> list[dict[str, object]]:
    events = []
    for db in (state_home / "aegis").glob("*/ledger.db"):
        connection = sqlite3.connect(db.as_posix())
        for row in connection.execute(
            "SELECT event_type, tool_name, payload_digest, session_id, extra FROM events ORDER BY seq"
        ):
            events.append(
                {
                    "event_type": row[0],
                    "tool_name": row[1],
                    "payload_digest": row[2],
                    "session_id": row[3],
                    "extra": json.loads(row[4]),
                }
            )
        connection.close()
    return events


def run_pretooluse(repo: Path, state_home: Path, payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = state_home.as_posix()
    env["CLAUDE_PROJECT_DIR"] = repo.as_posix()
    return subprocess.run(
        [sys.executable, GATE_LIB.as_posix(), "pretooluse"],
        cwd=repo,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def test_payload_carries_session_attribution() -> None:
    payload = gate_lib.parse_payload(
        json.dumps(
            {
                "session_id": "sess-42",
                "cwd": "/tmp/x",
                "tool_name": "Bash",
                "tool_input": {"command": "echo hi"},
            }
        )
    )
    assert isinstance(payload, gate_lib.Payload)
    assert payload.session_id == "sess-42"
    assert payload.cwd == "/tmp/x"
    bare = gate_lib.Payload("Bash", {"command": "x"})
    assert bare.session_id is None and bare.cwd is None


def test_payload_digest_ignores_attribution_fields() -> None:
    with_attribution = gate_lib.Payload("Bash", {"command": "x"}, session_id="s", cwd="/c")
    without = gate_lib.Payload("Bash", {"command": "x"})
    assert gate_lib.payload_digest(with_attribution) == gate_lib.payload_digest(without)


def test_advisory_decision_dual_written_with_parity(tmp_path: Path) -> None:
    repo = make_advisory_repo(tmp_path)
    state = tmp_path / "state"
    payload = {
        "session_id": "sess-dualwrite",
        "cwd": repo.as_posix(),
        "tool_name": "Bash",
        "tool_input": {"command": "task-master add-task --title=x"},
    }
    result = run_pretooluse(repo, state, payload)
    assert result.returncode == 0, result.stderr
    jsonl = read_jsonl(repo)
    assert jsonl, "advisory mode must write the JSONL decision"
    ledger_events = [event for event in read_ledger_events(state) if event["event_type"] == "gate_decision"]
    assert len(ledger_events) == len(jsonl), "every JSONL decision needs a ledger twin"
    for record, event in zip(jsonl, ledger_events):
        assert event["payload_digest"] == record["payload_digest"], "parity key mismatch"
        assert event["extra"]["verdict"] == record["verdict"]
        assert event["extra"]["reason"] == record["reason"]
        assert event["extra"]["mode"] == record["mode"] == "advisory"
        assert event["extra"]["hook"] == record["hook"]
    assert ledger_events[0]["session_id"] == "sess-dualwrite"


def test_jsonl_survives_when_ledger_unavailable(tmp_path: Path) -> None:
    repo = make_advisory_repo(tmp_path)
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    (isolated / "gate_lib.py").write_text(GATE_LIB.read_text(encoding="utf-8"), encoding="utf-8")
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = (tmp_path / "state").as_posix()
    env["CLAUDE_PROJECT_DIR"] = repo.as_posix()
    result = subprocess.run(
        [sys.executable, (isolated / "gate_lib.py").as_posix(), "pretooluse"],
        cwd=repo,
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "git checkout -b x"}}),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert read_jsonl(repo), "JSONL write must not depend on the ledger"
    assert read_ledger_events(tmp_path / "state") == []


def test_strict_mode_still_blocks_and_records_nothing(tmp_path: Path) -> None:
    repo = make_advisory_repo(tmp_path)
    (repo / ".aegis" / "state" / "enforcement.json").write_text(
        json.dumps({"mode": "strict"}), encoding="utf-8"
    )
    state = tmp_path / "state"
    result = run_pretooluse(
        repo,
        state,
        {"tool_name": "Bash", "tool_input": {"command": "git checkout -b nope"}},
    )
    assert result.returncode == 2
    assert read_jsonl(repo) == []
    assert read_ledger_events(state) == []
