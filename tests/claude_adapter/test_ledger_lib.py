"""PR-1a ledger core tests (capsule program).

Runs the same suite against BOTH backends (spec section 2 fallback contract) and
covers: schema round-trip, concurrent writers, redaction, store-path resolution
including worktrees, rotation, and the CLI/status discoverability surfaces.
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
ASSETS_LEDGER_LIB = REPO_ROOT / "aegis_foundation" / "assets" / ".claude" / "scripts" / "ledger_lib.py"
LIVE_LEDGER_LIB = REPO_ROOT / ".claude" / "scripts" / "ledger_lib.py"
LIVE_GATE_LIB = REPO_ROOT / ".claude" / "scripts" / "gate_lib.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ledger_lib = load_module(ASSETS_LEDGER_LIB, "ledger_lib_under_test")


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env, check=False)


def make_git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    assert run(["git", "init", "-q"], path).returncode == 0
    return path


def commit_something(repo: Path) -> None:
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    assert run(["git", "add", "README.md"], repo).returncode == 0
    result = run(
        [
            "git",
            "-c", "user.email=test@example.com",
            "-c", "user.name=test",
            "-c", "commit.gpgsign=false",
            "commit", "-q", "-m", "seed",
        ],
        repo,
    )
    assert result.returncode == 0, result.stderr


@pytest.fixture(params=["sqlite", "jsonl"])
def ledger(request, tmp_path: Path):
    if request.param == "sqlite":
        instance = ledger_lib.SQLiteLedger(tmp_path / "ledger.db")
    else:
        instance = ledger_lib.JsonlLedger(tmp_path / "shards")
    yield instance
    instance.close()


def test_assets_and_live_ledger_lib_copies_identical() -> None:
    assert LIVE_LEDGER_LIB.is_file(), "live .claude/scripts/ledger_lib.py mirror missing"
    assert ASSETS_LEDGER_LIB.read_bytes() == LIVE_LEDGER_LIB.read_bytes()


def test_ledger_lib_is_stdlib_only() -> None:
    import ast

    tree = ast.parse(ASSETS_LEDGER_LIB.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots = {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            roots = {(node.module or "").split(".")[0]}
        else:
            continue
        assert "aegis_foundation" not in roots, "ledger_lib.py must not import aegis_foundation"
        assert "scripts" not in roots, "ledger_lib.py must not import the installer"


def test_schema_round_trip(ledger) -> None:
    appended = ledger.append(
        {
            "event_type": "mutation",
            "session_id": "sess-1",
            "branch": "feat/task-202-capsule-ledger-core",
            "cwd": "/tmp/repo",
            "tool_name": "Edit",
            "handler": "claude:Edit",
            "paths": ["app/src/main.ts"],
            "outcome": "pass",
            "duration_ms": "42",
            "agent_id": "agent-7",
            "agent_type": "explore",
            "payload_digest": "abc123",
            "unknown_key": "kept",
            "extra": {"detail": "x"},
        }
    )
    events = ledger.read()
    assert len(events) == 1
    event = events[0]
    for field in ledger_lib.EVENT_FIELDS:
        assert field in event
    assert event["schema_version"] == ledger_lib.SCHEMA_VERSION
    assert event["event_id"] == appended["event_id"]
    assert event["ts"].endswith("Z")
    assert event["session_id"] == "sess-1"
    assert event["event_type"] == "mutation"
    assert event["paths"] == ["app/src/main.ts"]
    assert event["outcome"] == "pass"
    assert event["exit_class"] == "pass"
    assert event["duration_ms"] == 42
    assert event["agent_id"] == "agent-7"
    assert event["extra"]["detail"] == "x"
    assert event["extra"]["unknown_key"] == "kept", "unknown top-level keys must fold into extra"


def test_missing_fields_degrade_to_null_never_crash(ledger) -> None:
    event = ledger.append({})
    assert event["event_type"] == "unknown"
    assert event["session_id"] is None
    assert event["duration_ms"] is None
    assert event["outcome"] == "unknown"
    garbage = ledger.append({"duration_ms": "not-a-number", "outcome": "exploded", "paths": 7})
    assert garbage["duration_ms"] is None
    assert garbage["outcome"] == "unknown"
    assert garbage["paths"] == ["7"]
    assert len(ledger.read()) == 2


@pytest.mark.parametrize(
    ("secret", "must_not_contain"),
    [
        ("wrangler secret put API_KEY hunter2-value", "hunter2-value"),
        ("curl -H 'Authorization: Basic dXNlcjpwYXNz'", "dXNlcjpwYXNz"),
        ("curl -H 'Authorization: Bearer abc.def.ghi'", "abc.def.ghi"),
        ("token sk_live_1234567890abcdef done", "sk_live_1234567890abcdef"),
        ("jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.sig123", "eyJhbGciOiJIUzI1NiJ9"),
    ],
)
def test_default_redaction_patterns(ledger, secret: str, must_not_contain: str) -> None:
    ledger.append({"event_type": "mutation", "extra": {"command": secret}})
    stored = ledger.read()[-1]["extra"]["command"]
    assert must_not_contain not in stored
    assert ledger_lib.REDACTED in stored or "Bearer " + ledger_lib.REDACTED in stored


def test_redact_extra_patterns(tmp_path: Path) -> None:
    ledger = ledger_lib.SQLiteLedger(tmp_path / "ledger.db", redact_patterns=[r"hp-coach-[0-9]+"])
    ledger.append({"event_type": "mutation", "extra": {"command": "deploy hp-coach-12345 now"}})
    stored = ledger.read()[0]["extra"]["command"]
    ledger.close()
    assert "hp-coach-12345" not in stored
    assert ledger_lib.REDACTED in stored


def test_read_filters_and_limit(ledger) -> None:
    for index in range(5):
        ledger.append(
            {
                "event_type": "mutation" if index % 2 == 0 else "delivery",
                "session_id": "sess-a" if index < 3 else "sess-b",
                "agent_id": "agent-1" if index == 0 else None,
                "ts": f"2026-06-10T10:0{index}:00Z",
            }
        )
    assert len(ledger.read(session_id="sess-a")) == 3
    assert len(ledger.read(event_type="delivery")) == 2
    assert len(ledger.read(agent_id="agent-1")) == 1
    assert len(ledger.read(since_ts="2026-06-10T10:03:00Z")) == 2
    recent = ledger.read(limit=2)
    assert [event["ts"] for event in recent] == ["2026-06-10T10:03:00Z", "2026-06-10T10:04:00Z"]


def test_jsonl_shards_merge_ordered(tmp_path: Path) -> None:
    ledger = ledger_lib.JsonlLedger(tmp_path / "shards")
    ledger.append({"event_type": "mutation", "session_id": "s2", "ts": "2026-06-10T10:02:00Z"})
    ledger.append({"event_type": "mutation", "session_id": "s1", "ts": "2026-06-10T10:01:00Z"})
    ledger.append({"event_type": "mutation", "session_id": "s2", "ts": "2026-06-10T10:00:00Z"})
    assert len(list((tmp_path / "shards").glob("*.jsonl"))) == 2, "per-session shards expected"
    timestamps = [event["ts"] for event in ledger.read()]
    assert timestamps == sorted(timestamps)


def test_concurrent_writers_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "ledger.db"
    writer = tmp_path / "writer.py"
    writer.write_text(
        f"""
import importlib.util, sys
spec = importlib.util.spec_from_file_location("ll", {str(ASSETS_LEDGER_LIB)!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ledger = module.SQLiteLedger({str(db_path)!r})
for index in range(25):
    ledger.append({{"event_type": "mutation", "session_id": sys.argv[1], "extra": {{"i": index}}}})
ledger.close()
""",
        encoding="utf-8",
    )
    processes = [
        subprocess.Popen([sys.executable, writer.as_posix(), f"writer-{n}"], cwd=tmp_path)
        for n in range(4)
    ]
    for process in processes:
        assert process.wait(timeout=60) == 0
    ledger = ledger_lib.SQLiteLedger(db_path)
    events = ledger.read()
    ledger.close()
    assert len(events) == 100
    assert {event["session_id"] for event in events} == {f"writer-{n}" for n in range(4)}


def test_store_path_keyed_on_git_common_dir_shared_across_worktrees(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path / "repo")
    commit_something(repo)
    worktree = tmp_path / "wt"
    assert run(["git", "worktree", "add", "-q", worktree.as_posix(), "-b", "wt-branch"], repo).returncode == 0
    env = {"XDG_STATE_HOME": (tmp_path / "state").as_posix()}
    repo_store = ledger_lib.store_path(cwd=repo, env=env)
    worktree_store = ledger_lib.store_path(cwd=worktree, env=env)
    assert repo_store == worktree_store, "worktrees must share one store (git common dir key)"
    assert repo_store.as_posix().startswith((tmp_path / "state").as_posix())
    assert repo_store.name == ledger_lib.LEDGER_FILENAME


def test_store_path_outside_git_raises(tmp_path: Path) -> None:
    with pytest.raises(ledger_lib.LedgerError):
        ledger_lib.store_path(cwd=tmp_path / "not-a-repo-anywhere", env={"XDG_STATE_HOME": "/tmp"})


def test_open_ledger_backend_selection(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path / "repo")
    env = {"XDG_STATE_HOME": (tmp_path / "state").as_posix()}
    sqlite_ledger = ledger_lib.open_ledger(cwd=repo, env=env)
    assert sqlite_ledger.backend == "sqlite"
    sqlite_ledger.close()
    jsonl_env = dict(env)
    jsonl_env[ledger_lib.BACKEND_ENV_VAR] = "jsonl"
    jsonl_ledger = ledger_lib.open_ledger(cwd=repo, env=jsonl_env)
    assert jsonl_ledger.backend == "jsonl"
    jsonl_ledger.close()
    with pytest.raises(ledger_lib.LedgerError):
        ledger_lib.open_ledger(cwd=repo, env=env, backend="postgres")


def test_rotate_if_needed(tmp_path: Path) -> None:
    db_path = tmp_path / "ledger.db"
    ledger = ledger_lib.SQLiteLedger(db_path)
    for index in range(5):
        ledger.append({"event_type": "mutation", "extra": {"i": index}})
    ledger.close()
    assert ledger_lib.rotate_if_needed(db_path, max_bytes=1024 * 1024 * 1024) is None
    rotated = ledger_lib.rotate_if_needed(db_path, max_bytes=1)
    assert rotated is not None and rotated.is_file()
    assert not db_path.exists()
    fresh = ledger_lib.SQLiteLedger(db_path)
    fresh.append({"event_type": "mutation"})
    assert len(fresh.read()) == 1
    fresh.close()
    archived = ledger_lib.SQLiteLedger(rotated)
    assert len(archived.read()) == 5
    archived.close()


def test_cli_ledger_path_prints_resolved_store(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path / "repo")
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = (tmp_path / "state").as_posix()
    result = run(
        [sys.executable, "-m", "aegis_foundation.cli", "ledger", "path", "--target-dir", repo.as_posix()],
        REPO_ROOT,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    printed = result.stdout.strip()
    assert printed == ledger_lib.store_path(cwd=repo, env=env).as_posix()


def test_cli_ledger_path_fails_cleanly_outside_git(tmp_path: Path) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = (tmp_path / "state").as_posix()
    result = run(
        [sys.executable, "-m", "aegis_foundation.cli", "ledger", "path", "--target-dir", plain.as_posix()],
        REPO_ROOT,
        env=env,
    )
    assert result.returncode == 1
    assert "not inside a git repository" in result.stderr


def test_status_includes_ledger_block(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path / "repo")
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = (tmp_path / "state").as_posix()
    result = run(
        [sys.executable, "-m", "aegis_foundation.cli", "status", "--target-dir", repo.as_posix()],
        REPO_ROOT,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    ledger_block = payload.get("ledger")
    assert isinstance(ledger_block, dict)
    assert ledger_block["store_path"] == ledger_lib.store_path(cwd=repo, env=env).as_posix()
    assert ledger_block["exists"] is False
    assert ledger_block["backend"] == "sqlite"


def test_gate_classifies_ledger_path_read_only() -> None:
    gate_lib = load_module(LIVE_GATE_LIB, "gate_lib_for_ledger_tests")
    assert gate_lib.read_only_aegis_remainder(["ledger", "path"]) is True
    assert gate_lib.read_only_aegis_remainder(["ledger"]) is False
    assert (
        gate_lib.bash_is_read_only("python3 -m aegis_foundation.cli ledger path --target-dir .")
        is True
    )
