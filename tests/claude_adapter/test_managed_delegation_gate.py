"""Managed-project provider-native delegation policy regressions."""

from __future__ import annotations

import json
import os
import subprocess
from hashlib import sha256
from pathlib import Path

import pytest

from aegis_foundation.gate.hooks.pretool import pretooluse_gate


DESCRIPTOR = {
    "schema": "gas-city-workflow.project.v1",
    "id": "fixture-project",
    "repository": "example/fixture-project",
    "rig": "fixture",
    "workflow_authority": "beads",
    "workflow_profile": "beads-with-aegis-evidence",
}


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _repo(tmp_path: Path, *, managed: bool = True) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert _git(repo, "init", "-q", "-b", "codex/ga-test").returncode == 0
    assert _git(repo, "config", "user.email", "test@example.invalid").returncode == 0
    assert _git(repo, "config", "user.name", "Test").returncode == 0
    (repo / ".gitignore").write_text(".aegis/reports/\n", encoding="utf-8")
    (repo / "README.md").write_text("fixture\n", encoding="utf-8")
    if managed:
        (repo / ".gas-city-workflow.json").write_text(
            json.dumps(DESCRIPTOR, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    assert _git(repo, "add", ".").returncode == 0
    assert _git(repo, "commit", "-q", "-m", "fixture").returncode == 0
    return repo


def _event(tool_name: str, tool_input: dict[str, object], *, session: str = "session-a") -> dict[str, object]:
    return {
        "hook_event_name": "PreToolUse",
        "session_id": session,
        "cwd": "/caller/namespace/is/not/authority",
        "tool_name": tool_name,
        "tool_input": tool_input,
    }


def _request_digest(event: dict[str, object]) -> str:
    encoded = json.dumps(
        {"tool_name": event["tool_name"], "tool_input": event["tool_input"]},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _run(
    monkeypatch: pytest.MonkeyPatch,
    repo: Path,
    event: dict[str, object],
    *,
    adapter: str,
) -> int:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", repo.as_posix())
    monkeypatch.setenv("AEGIS_INVOKING_AGENT", adapter)
    return pretooluse_gate(json.dumps(event))


@pytest.mark.parametrize(
    ("adapter", "tool_name", "tool_input"),
    [
        ("claude", "Agent", {"description": "review", "prompt": "do work", "subagent_type": "worker"}),
        ("claude", "Task", {"description": "review", "prompt": "do work", "subagent_type": "worker"}),
        ("codex", "spawn_agent", {"task_name": "worker", "message": "do work", "fork_turns": "all"}),
        ("codex", "collaboration.spawn_agent", {"task_name": "worker", "message": "do work"}),
        ("codex", "assign_agent_task", {"target": "worker", "message": "continue work"}),
        ("codex", "followup_task", {"target": "worker", "message": "continue work"}),
        ("codex", "resume_agent", {"target": "worker"}),
    ],
)
def test_managed_project_hard_blocks_provider_native_delegation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    adapter: str,
    tool_name: str,
    tool_input: dict[str, object],
) -> None:
    repo = _repo(tmp_path)
    result = _run(monkeypatch, repo, _event(tool_name, tool_input), adapter=adapter)

    assert result == 2
    decision = json.loads(
        (repo / ".aegis/reports/gate-decisions.jsonl").read_text(encoding="utf-8").splitlines()[-1]
    )
    assert decision["verdict"] == "block"
    assert decision["reason"] == "native_delegation_requires_gas_city"
    assert decision["tool_name"] == tool_name


def test_advisory_mode_cannot_relax_managed_delegation_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path)
    state = repo / ".aegis/state"
    state.mkdir(parents=True)
    (state / "enforcement.json").write_text('{"mode":"advisory"}\n', encoding="utf-8")

    result = _run(
        monkeypatch,
        repo,
        _event("Agent", {"description": "review", "prompt": "do work"}),
        adapter="claude",
    )

    assert result == 2


def test_invalid_managed_descriptor_fails_closed_for_delegation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path)
    (repo / ".gas-city-workflow.json").write_text('{"schema":"wrong"}\n', encoding="utf-8")

    result = _run(
        monkeypatch,
        repo,
        _event("spawn_agent", {"task_name": "worker", "message": "do work"}),
        adapter="codex",
    )

    assert result == 2
    decision = json.loads(
        (repo / ".aegis/reports/gate-decisions.jsonl").read_text(encoding="utf-8").splitlines()[-1]
    )
    assert decision["reason"] == "managed_project_context_invalid"


def test_registry_fallback_blocks_descriptorless_managed_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, managed=False)
    source = tmp_path / "source"
    registry = source / "plugins/gas-city-workflow/config/projects.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        json.dumps(
            {
                "schema": "gas-city-workflow.project-registry.v1",
                "projects": [
                    {
                        **{key: value for key, value in DESCRIPTOR.items() if key != "schema"},
                        "root": repo.as_posix(),
                        "rig_root": repo.as_posix(),
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    runtime = repo / ".aegis/runtime.env"
    runtime.parent.mkdir(parents=True)
    runtime.write_text(f"AEGIS_SOURCE_ROOT={source.as_posix()}\n", encoding="utf-8")

    result = _run(
        monkeypatch,
        repo,
        _event("Agent", {"description": "review", "prompt": "do work"}),
        adapter="claude",
    )

    assert result == 2


def test_unmanaged_project_keeps_provider_native_delegation_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, managed=False)

    result = _run(
        monkeypatch,
        repo,
        _event("spawn_agent", {"task_name": "worker", "message": "do work"}),
        adapter="codex",
    )

    assert result == 0
    assert not (repo / ".aegis/reports/gate-decisions.jsonl").exists()


def test_exact_tracked_exception_is_request_bound_not_caller_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path)
    event = _event("spawn_agent", {"task_name": "worker", "message": "review exact artifact"})
    exception = {
        "schema": "gas-city.delegation-exceptions.v1",
        "exceptions": [
            {
                "project_id": DESCRIPTOR["id"],
                "adapter": "codex",
                "tool_name": "spawn_agent",
                "request_sha256": _request_digest(event),
                "branch": "codex/ga-test",
                "bead_id": "ga-test",
                "review_evidence": "bead:ga-test#reviewed-native-exception",
            }
        ],
    }
    path = repo / ".gas-city-delegation-exceptions.json"
    path.write_text(json.dumps(exception, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    assert _git(repo, "add", path.name).returncode == 0
    assert _git(repo, "commit", "-q", "-m", "review exception").returncode == 0

    assert _run(monkeypatch, repo, event, adapter="codex") == 0
    second = {**event, "session_id": "different-session", "cwd": "/different/caller"}
    assert _run(monkeypatch, repo, second, adapter="codex") == 0
    decisions = [
        json.loads(line)
        for line in (repo / ".aegis/reports/gate-decisions.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert [decision["reason"] for decision in decisions] == [
        "reviewed_native_delegation_exception",
        "reviewed_native_delegation_exception",
    ]
    assert decisions[0]["payload_digest"] == decisions[1]["payload_digest"]


@pytest.mark.parametrize("mutation", ["request", "branch", "exception_bytes"])
def test_exception_mismatch_or_dirty_bytes_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    repo = _repo(tmp_path)
    event = _event("spawn_agent", {"task_name": "worker", "message": "review exact artifact"})
    record = {
        "project_id": DESCRIPTOR["id"],
        "adapter": "codex",
        "tool_name": "spawn_agent",
        "request_sha256": _request_digest(event),
        "branch": "codex/ga-test",
        "bead_id": "ga-test",
        "review_evidence": "bead:ga-test#reviewed-native-exception",
    }
    path = repo / ".gas-city-delegation-exceptions.json"
    path.write_text(
        json.dumps({"schema": "gas-city.delegation-exceptions.v1", "exceptions": [record]}, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    assert _git(repo, "add", path.name).returncode == 0
    assert _git(repo, "commit", "-q", "-m", "review exception").returncode == 0
    if mutation == "request":
        event = _event("spawn_agent", {"task_name": "worker", "message": "different request"})
    elif mutation == "branch":
        assert _git(repo, "switch", "-q", "-c", "codex/different").returncode == 0
    else:
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    assert _run(monkeypatch, repo, event, adapter="codex") == 2


def test_local_coordinator_bash_is_not_reclassified_as_delegation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path)
    result = _run(monkeypatch, repo, _event("Bash", {"command": "git status --short"}), adapter="codex")
    assert result == 0
