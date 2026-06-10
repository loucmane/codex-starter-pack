"""PR-3.5 tests: delivery witness v0 — deterministic boundary checks, CI-mode split."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS_WITNESS_LIB = REPO_ROOT / "aegis_foundation" / "assets" / ".claude" / "scripts" / "witness_lib.py"
LEDGER_LIB = REPO_ROOT / ".claude" / "scripts" / "ledger_lib.py"

sys.path.insert(0, str(REPO_ROOT))
from scripts import _aegis_installer  # noqa: E402


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


witness_lib = load_module(ASSETS_WITNESS_LIB, "witness_lib_under_test")
ledger_lib = load_module(LEDGER_LIB, "ledger_lib_for_witness_tests")


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "user.email=t@e.c", "-c", "user.name=t", "-c", "commit.gpgsign=false", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture()
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_STATE_HOME", (tmp_path / "state").as_posix())
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    (repo / "app").mkdir()
    (repo / "app" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_main.py").write_text("def test_ok(): pass\n", encoding="utf-8")
    brief = repo / ".aegis" / "brief.json"
    brief.parent.mkdir(parents=True)
    brief.write_text(
        json.dumps(
            {
                "gates": {"app": {"test": ["pytest -q"]}},
                "source_roots": ["app/"],
                "witness": {"always_in_scope": ["docs/", ".aegis/"]},
            }
        ),
        encoding="utf-8",
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "seed")
    git(repo, "checkout", "-q", "-b", "feat/task-31-widget")
    return repo


def head_short(repo: Path) -> str:
    return git(repo, "rev-parse", "--short", "HEAD").stdout.strip()


def commit_change(repo: Path, rel: str, content: str = "x\n") -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"change {rel}")


def seed_verification(repo: Path, commit: str, ts: str | None = None) -> None:
    ledger = ledger_lib.open_ledger(cwd=repo)
    try:
        event = {
            "event_type": "verification",
            "exit_class": "pass",
            "outcome": "pass",
            "extra": {"package": "app", "gate": "test", "commit": commit},
        }
        if ts:
            event["ts"] = ts
        ledger.append(event)
    finally:
        ledger.close()


def test_in_scope_diff_with_verification_at_head_passes(repo: Path) -> None:
    commit_change(repo, "app/feature.py")
    seed_verification(repo, head_short(repo))
    report = witness_lib.run_witness(repo, base="main")
    assert report["checks"]["scope_mapping"]["passed"] is True
    assert report["checks"]["scope_mapping"]["task_id"] == "31"
    assert report["checks"]["diff_accounting"]["passed"] is True
    assert report["checks"]["verification_at_head"]["passed"] is True
    assert report["passed"] is True
    assert (repo / ".aegis" / "reports" / "witness-report.json").is_file()


def test_out_of_scope_file_fails_diff_accounting(repo: Path) -> None:
    commit_change(repo, "rogue/sneaky.txt")
    seed_verification(repo, head_short(repo))
    report = witness_lib.run_witness(repo, base="main")
    assert report["checks"]["diff_accounting"]["passed"] is False
    assert "rogue/sneaky.txt" in report["checks"]["diff_accounting"]["unaccounted"]
    assert report["passed"] is False


def test_deleted_test_escalates(repo: Path) -> None:
    git(repo, "rm", "-q", "tests/test_main.py")
    git(repo, "commit", "-q", "-m", "delete test")
    seed_verification(repo, head_short(repo))
    report = witness_lib.run_witness(repo, base="main")
    assert report["checks"]["diff_accounting"]["passed"] is False
    assert "tests/test_main.py" in report["checks"]["diff_accounting"]["deleted_tests_escalated"]
    assert report["escalations"], "test deletion must escalate to human review"


def test_stale_verification_fails_and_after_head_passes(repo: Path) -> None:
    old_head = head_short(repo)
    seed_verification(repo, old_head)
    commit_change(repo, "app/feature.py")
    report = witness_lib.run_witness(repo, base="main")
    assert report["checks"]["verification_at_head"]["passed"] is False, "old-commit run with old ts is stale"
    seed_verification(repo, "unrelated", ts="2099-01-01T00:00:00Z")
    report = witness_lib.run_witness(repo, base="main")
    assert report["checks"]["verification_at_head"]["passed"] is True, "pass recorded after head counts"


def test_confirmed_scope_record_beats_branch_convention(repo: Path) -> None:
    ledger = ledger_lib.open_ledger(cwd=repo)
    try:
        ledger.append(
            {
                "event_type": "scope",
                "branch": "feat/task-31-widget",
                "extra": {"task_id": "99", "path_globs": ["app/", "docs/"], "confirmed": True},
            }
        )
    finally:
        ledger.close()
    commit_change(repo, "app/feature.py")
    seed_verification(repo, head_short(repo))
    report = witness_lib.run_witness(repo, base="main")
    assert report["checks"]["scope_mapping"]["task_id"] == "99"
    assert report["checks"]["scope_mapping"]["source"] == "scope_record_confirmed"


def test_uncommitted_done_flip_fails_containment(repo: Path) -> None:
    tasks = repo / ".taskmaster" / "tasks" / "tasks.json"
    tasks.parent.mkdir(parents=True)
    tasks.write_text(json.dumps({"master": {"tasks": [{"id": 31, "status": "pending"}]}}), encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "tasks")
    tasks.write_text(json.dumps({"master": {"tasks": [{"id": 31, "status": "done"}]}}, indent=1), encoding="utf-8")
    seed_verification(repo, head_short(repo))
    report = witness_lib.run_witness(repo, base="main")
    assert report["checks"]["done_flip_containment"]["passed"] is False
    assert report["passed"] is False


def test_ci_mode_skips_ledger_checks_honestly(repo: Path) -> None:
    commit_change(repo, "app/feature.py")
    report = witness_lib.run_witness(repo, base="main", ci_mode=True)
    verification = report["checks"]["verification_at_head"]
    assert verification["passed"] is True
    assert verification["status"] == "not_derivable_in_ci"
    assert report["mode"] == "ci"
    assert report["passed"] is True


def test_cli_exit_codes_and_render(repo: Path, tmp_path: Path) -> None:
    commit_change(repo, "rogue/out.txt")
    env = dict(os.environ)
    env["XDG_STATE_HOME"] = os.environ["XDG_STATE_HOME"]
    result = subprocess.run(
        [sys.executable, "-m", "aegis_foundation.cli", "witness", "--target-dir", repo.as_posix(), "--base", "main"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 1
    assert "diff_accounting: FAIL" in result.stdout
    assert "Result: FAIL" in result.stdout


def test_ci_greenness_is_delegated_never_reimplemented(repo: Path) -> None:
    report = witness_lib.run_witness(repo, base="main")
    assert report["checks"]["ci_greenness"]["status"] == "delegated"


def test_gate_classifies_witness_read_only() -> None:
    gate_lib = load_module(REPO_ROOT / ".claude" / "scripts" / "gate_lib.py", "gate_lib_for_witness")
    assert gate_lib.bash_is_read_only("python3 -m aegis_foundation.cli witness --ci") is True


def test_support_files_include_witness_lib() -> None:
    assert ".claude/scripts/witness_lib.py" in _aegis_installer.CLAUDE_SUPPORT_FILES
    assets = _aegis_installer._managed_assets(REPO_ROOT, "claude", ("claude",))
    assert any(asset.path == ".claude/scripts/witness_lib.py" for asset in assets)


def test_assets_and_live_witness_copies_identical() -> None:
    live = (REPO_ROOT / ".claude" / "scripts" / "witness_lib.py").read_bytes()
    assert ASSETS_WITNESS_LIB.read_bytes() == live
