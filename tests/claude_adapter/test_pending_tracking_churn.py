"""TM #216: kill the pending-tracking churn engine (HP-Coach closeout report).

Two churn sources made closeout unreachable: (1) read-only inspection commands (jq,
column, …) misclassified as mutations and enqueued, so even LOOKING at state grew the
queue; (2) this repo's own logging/workflow commands (codex-task work-tracking update,
sessions update, plan sync) armed the queue against themselves — the codex-task analog
of `aegis log`, which was already excluded.

The core invariant must hold: every real source mutation (including in-place edits and
non-logging codex-task subcommands) STILL enqueues. These tests pin both sides.
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
    spec = importlib.util.spec_from_file_location("gate_lib_churn", GATE_LIB)
    module = importlib.util.module_from_spec(spec)
    sys.modules["gate_lib_churn"] = module
    spec.loader.exec_module(module)
    return module


gate_lib = load_gate_lib()


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
        json.dumps(
            {"schema_version": "1", "status": "in-progress", "task": {"id": "9", "slug": "x", "status": "in-progress"}}
        ),
        encoding="utf-8",
    )
    return repo


def enqueue_count(repo: Path, tool: str, **tool_input: object) -> int:
    pending = repo / ".aegis" / "state" / "pending-tracking.json"
    if pending.exists():
        pending.unlink()
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = repo.as_posix()
    subprocess.run(
        ["bash", POSTTOOLUSE.as_posix()],
        cwd=repo,
        input=json.dumps({"tool_name": tool, "tool_input": tool_input}),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    if not pending.is_file():
        return 0
    return len(json.loads(pending.read_text(encoding="utf-8")).get("events", []))


# --- read-only classification (Bug A) ---------------------------------------------

READ_ONLY_INSPECTORS = [
    "jq . tasks.json",
    "jq -c '.master' tasks.json",
    "column -t data.tsv",
    "comm -12 a.txt b.txt",
    "cut -d, -f1 data.csv",
    "diff a.txt b.txt",
    "cmp a.bin b.bin",
    "nl file.txt",
    "realpath .aegis/state",
    "basename /a/b/c",
    "sort in.txt",
    "yq '.x' config.yaml",
]


@pytest.mark.parametrize("command", READ_ONLY_INSPECTORS)
def test_read_only_inspectors_are_read_only(command: str) -> None:
    assert gate_lib.bash_is_read_only(command) is True, command
    assert gate_lib.payload_is_read_only(gate_lib.Payload("Bash", {"command": command})) is True


@pytest.mark.parametrize("command", READ_ONLY_INSPECTORS)
def test_read_only_inspectors_do_not_enqueue(tmp_path_factory: pytest.TempPathFactory, command: str) -> None:
    repo = make_in_progress_repo(tmp_path_factory.mktemp("ro"))
    assert enqueue_count(repo, "Bash", command=command) == 0, command


# --- in-place write guards: these MUST stay mutations ------------------------------

IN_PLACE_WRITES = [
    "sed -i 's/a/b/' src/main.py",
    "sed -i.bak 's/a/b/' src/main.py",
    "sed -ni 's/a/b/' src/main.py",  # bundled short cluster -n -i
    "sed --in-place 's/a/b/' src/main.py",  # GNU long form
    "sed --in-place=.bak 's/a/b/' src/main.py",  # long form with attached value
    "yq -i '.x=1' config.yaml",
    "yq --inplace '.x=1' config.yaml",
    "yq -Pi '.x=1' config.yaml",  # bundled -P -i
    "yq -iP '.x=1' config.yaml",
    "sort -o out.txt in.txt",
    "sort -uo out.txt in.txt",  # bundled -u -o
    "sort --output out.txt in.txt",  # GNU long form
    "sort --output=out.txt in.txt",  # long form with attached value
    "uniq input.txt output.txt",  # positional output arg (no flag guard can catch)
    "xxd -r dump.hex out.bin",  # reverse mode positional output
    "jq '.' a.json > b.json",
]


# These look flag-adjacent to the guarded writers but only write to stdout — must stay read-only.
READ_ONLY_WRITER_VARIANTS = [
    "sed -n 'p' file.txt",
    "sed -E 's/a/b/' file.txt",
    "sort -r in.txt",
    "sort -u in.txt",
    "sort --ignore-case in.txt",
    "yq -P '.x' config.yaml",
]


@pytest.mark.parametrize("command", READ_ONLY_WRITER_VARIANTS)
def test_stdout_only_writer_variants_stay_read_only(command: str) -> None:
    assert gate_lib.bash_is_read_only(command) is True, command


@pytest.mark.parametrize("command", IN_PLACE_WRITES)
def test_in_place_writes_stay_mutations(command: str) -> None:
    assert gate_lib.bash_is_read_only(command) is False, command


@pytest.mark.parametrize("command", IN_PLACE_WRITES)
def test_in_place_writes_still_enqueue(tmp_path_factory: pytest.TempPathFactory, command: str) -> None:
    repo = make_in_progress_repo(tmp_path_factory.mktemp("wr"))
    assert enqueue_count(repo, "Bash", command=command) == 1, command


# --- codex-task logging exclusion (Bug B) -----------------------------------------

CODEX_TASK_LOGGING = [
    "python3 scripts/codex-task work-tracking update --work x --handler h --evidence e --note n",
    "python3 scripts/codex-task sessions update --work x --handler h --evidence e --note n",
    "python3 scripts/codex-task plan sync",
    "python3 scripts/codex-task work-tracking audit",
    "python3 scripts/codex-task scanner run",
]


@pytest.mark.parametrize("command", CODEX_TASK_LOGGING)
def test_codex_task_logging_is_excluded(command: str) -> None:
    assert gate_lib.payload_is_codex_task_logging(gate_lib.Payload("Bash", {"command": command})) is True


@pytest.mark.parametrize("command", CODEX_TASK_LOGGING)
def test_codex_task_logging_does_not_enqueue(tmp_path_factory: pytest.TempPathFactory, command: str) -> None:
    repo = make_in_progress_repo(tmp_path_factory.mktemp("ct"))
    assert enqueue_count(repo, "Bash", command=command) == 0, command


def test_aegis_log_both_forms_still_excluded() -> None:
    for command in (
        "./.aegis/bin/aegis log --handler h --evidence e --note n",
        "python3 -m aegis_foundation.cli log --handler h --evidence e --note n",
    ):
        assert gate_lib.payload_is_aegis_log(gate_lib.Payload("Bash", {"command": command})) is True


def test_pending_tracking_gate_output_is_bounded_without_hiding_total() -> None:
    events = [
        {
            "id": f"strict-{index:03d}",
            "handler": "codex:apply_patch",
            "evidence": f"src/fixture-{index}.tsx",
            "mode": "strict",
        }
        for index in range(97)
    ]

    rendered = gate_lib.format_pending_tracking(events)

    assert rendered.count("repair: ./.aegis/bin/aegis log") == 5
    assert "strict-000" in rendered
    assert "strict-004" in rendered
    assert "strict-005" not in rendered
    assert (
        "... 92 more pending events; inspect .aegis/state/pending-tracking.json for all 97."
        in rendered
    )
    assert len(rendered.splitlines()) == 11


def test_logging_chained_with_read_only_stays_excluded() -> None:
    # A sanctioned logging command plus a genuinely read-only companion is still pure
    # logging and must remain excluded (whole-payload-AND, not single-segment-only).
    for command in (
        "git status --short && python3 scripts/codex-task plan sync",
        "python3 scripts/codex-task work-tracking update --work x --handler h --evidence e --note n; git diff",
        "git status && ./.aegis/bin/aegis log --handler h --evidence e --note n",
    ):
        payload = gate_lib.Payload("Bash", {"command": command})
        assert (
            gate_lib.payload_is_codex_task_logging(payload) or gate_lib.payload_is_aegis_log(payload)
        ), command


# CORE INVARIANT: a real mutation chained with a sanctioned command must NOT be excluded.
COMPOUND_BYPASS_ATTEMPTS = [
    "python3 scripts/codex-task plan sync; rm -rf src",
    "python3 scripts/codex-task plan sync && rm -rf src/foo.py",
    "rm -rf src && python3 scripts/codex-task plan sync",
    "python3 scripts/codex-task scanner run; echo pwned > src/evil.py",
    "python3 scripts/codex-task work-tracking update --work x --handler h --evidence e --note n && git commit -am x",
    "python3 scripts/codex-task plan sync | tee src/evil.py",
    "python3 scripts/codex-task sessions update --work x --handler h --evidence e --note n; sed -i 's/a/b/' CODEX.md",
    "./.aegis/bin/aegis log --handler h --evidence e --note n && rm -rf src",
    "./.aegis/bin/aegis kickoff --task 1 --slug x --title y && rm -rf src",
]


@pytest.mark.parametrize("command", COMPOUND_BYPASS_ATTEMPTS)
def test_compound_logging_plus_mutation_is_not_excluded(command: str) -> None:
    payload = gate_lib.Payload("Bash", {"command": command})
    assert gate_lib.payload_is_codex_task_logging(payload) is False, command
    assert gate_lib.payload_is_aegis_log(payload) is False, command
    assert gate_lib.payload_is_aegis_bootstrap(payload) is False, command


@pytest.mark.parametrize("command", COMPOUND_BYPASS_ATTEMPTS)
def test_compound_logging_plus_mutation_still_enqueues(tmp_path_factory: pytest.TempPathFactory, command: str) -> None:
    repo = make_in_progress_repo(tmp_path_factory.mktemp("cb"))
    assert enqueue_count(repo, "Bash", command=command) == 1, command


# --- CORE INVARIANT: real mutations still tracked ---------------------------------


def test_source_write_still_enqueues(tmp_path: Path) -> None:
    repo = make_in_progress_repo(tmp_path)
    assert enqueue_count(repo, "Write", file_path="src/main.py", content="x") == 1


def test_non_logging_codex_task_still_enqueues(tmp_path: Path) -> None:
    repo = make_in_progress_repo(tmp_path)
    # A codex-task subcommand that is NOT an evidence/workflow write must still track.
    assert (
        gate_lib.payload_is_codex_task_logging(
            gate_lib.Payload("Bash", {"command": "python3 scripts/codex-task scanner notreal"})
        )
        is False
    )
    assert enqueue_count(repo, "Bash", command="python3 scripts/codex-task scanner notreal") == 1


def test_git_commit_still_enqueues(tmp_path: Path) -> None:
    repo = make_in_progress_repo(tmp_path)
    assert enqueue_count(repo, "Bash", command="git commit -m x") == 1


def test_redirect_to_file_still_enqueues(tmp_path: Path) -> None:
    repo = make_in_progress_repo(tmp_path)
    assert enqueue_count(repo, "Bash", command="jq . a.json > out.json") == 1


def test_assets_and_live_gate_lib_identical() -> None:
    live = (REPO_ROOT / ".claude" / "scripts" / "gate_lib.py").read_bytes()
    asset = (REPO_ROOT / "aegis_foundation" / "assets" / ".claude" / "scripts" / "gate_lib.py").read_bytes()
    assert live == asset
