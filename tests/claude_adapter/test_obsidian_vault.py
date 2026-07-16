from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

import pytest

from aegis_foundation import cli as aegis_cli
from aegis_foundation import obsidian_vault

SOURCE_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _fake_read_only_bd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Expose a deterministic bd executable that enforces the production argv."""

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    executable = bin_dir / "bd"
    executable.write_text(
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\n"
        "import hashlib, json, sys\n"
        "if sys.argv[1:] == ['--version']:\n"
        "    print('bd version 1.1.0 (8e4e59d39)')\n"
        "    raise SystemExit(0)\n"
        "if len(sys.argv) >= 5 and '-C' in sys.argv:\n"
        "    root = Path(sys.argv[sys.argv.index('-C') + 1])\n"
        "else:\n"
        "    print('missing repository', file=sys.stderr)\n"
        "    raise SystemExit(8)\n"
        "source = root / '.beads' / 'test-export.jsonl'\n"
        "if not source.is_file():\n"
        "    print('authoritative Beads export unavailable', file=sys.stderr)\n"
        "    raise SystemExit(9)\n"
        "if sys.argv[1:] == ['--readonly', '-C', str(root), 'export']:\n"
        "    sys.stdout.write(source.read_text(encoding='utf-8'))\n"
        "    raise SystemExit(0)\n"
        "if sys.argv[1:5] == ['--json', '--readonly', '-C', str(root)] and sys.argv[5] == 'sql':\n"
        "    head = hashlib.sha256(source.read_bytes()).hexdigest()[:32]\n"
        "    print(json.dumps({'rows': [{'head': head}]}))\n"
        "    raise SystemExit(0)\n"
        "print('unexpected bd invocation: ' + ' '.join(sys.argv[1:]), file=sys.stderr)\n"
        "raise SystemExit(8)\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")


def _run(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        list(args),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result.stdout.strip()


def _bead_issue(
    issue_id: str,
    *,
    title: str | None = None,
    external_ref: str | None = None,
    status: str = "open",
    priority: int = 1,
    issue_type: str = "task",
    dependencies: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    return {
        "_type": "issue",
        "id": issue_id,
        "title": title or f"Bead {issue_id} title",
        "description": f"Bounded description for {issue_id}",
        "status": status,
        "priority": priority,
        "issue_type": issue_type,
        "external_ref": external_ref,
        "dependencies": dependencies or [],
    }


def _relationship(source_id: str, target_id: str, relation_type: str) -> dict[str, str]:
    return {
        "issue_id": source_id,
        "depends_on_id": target_id,
        "type": relation_type,
    }


def _write_beads_export(root: Path, issues: list[dict[str, object]]) -> None:
    beads_dir = root / ".beads"
    beads_dir.mkdir(exist_ok=True)
    (beads_dir / "test-export.jsonl").write_text(
        "".join(json.dumps(issue, sort_keys=True) + "\n" for issue in issues),
        encoding="utf-8",
    )


def _fixture_issues(task_count: int) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for task_id in range(1, task_count + 1):
        issue_id = f"ags-{task_id}"
        dependencies: list[dict[str, str]] = []
        if task_id > 1:
            dependencies.append(_relationship(issue_id, f"ags-{task_id - 1}", "blocks"))
        if task_id == 2:
            dependencies.append(_relationship(issue_id, "ags-1", "parent-child"))
        issues.append(
            _bead_issue(
                issue_id,
                title=f"Task {task_id} title",
                external_ref=f"taskmaster:master:{task_id}",
                status="in-progress" if task_id == 1 else "open",
                issue_type="epic" if task_id == 1 else "task",
                dependencies=dependencies,
            )
        )
    return issues


def _repo(tmp_path: Path, *, task_count: int = 2) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    _run("git", "init", "-q", "-b", "main", cwd=root)
    _run("git", "config", "user.name", "Aegis Test", cwd=root)
    _run("git", "config", "user.email", "aegis@example.invalid", cwd=root)
    tasks = []
    for task_id in range(1, task_count + 1):
        tasks.append(
            {
                "id": task_id,
                "title": f"Task {task_id} title",
                "description": f"Bounded description for task {task_id}",
                "status": "in-progress" if task_id == 1 else "pending",
                "priority": "high",
                "dependencies": [] if task_id == 1 else [task_id - 1],
                "subtasks": [],
            }
        )
    task_dir = root / ".taskmaster" / "tasks"
    task_dir.mkdir(parents=True)
    (task_dir / "tasks.json").write_text(
        json.dumps({"master": {"tasks": tasks}}, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_beads_export(root, _fixture_issues(task_count))
    capsule_dir = root / ".aegis" / "capsule"
    capsule_dir.mkdir(parents=True)
    (capsule_dir / "current.json").write_text(
        json.dumps(
            {
                "active_task": {"id": "1", "title": "Task 1 title", "status": "in-progress"},
                "next_action": "continue_task_1",
                "orientation_source": "branch",
                "branch": "feat/task-1-vault",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    tracker = root / "docs" / "ai" / "work-tracking" / "active" / "task1" / "TRACKER.md"
    tracker.parent.mkdir(parents=True)
    tracker.write_text(
        "# Task 1 Tracker\n\n"
        "- [ ] Human decision that must remain preserved\n"
        "- [S:one|W:task-1|H:human|E:note] Human evidence\n\n"
        "<!-- AEGIS:BEGIN generated-sweh-projection -->\n"
        "- [S:auto|W:task-1|H:generated|E:ledger:event] Generated evidence\n"
        "<!-- AEGIS:END generated-sweh-projection -->\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("# Test repository\n", encoding="utf-8")
    _run("git", "add", ".", cwd=root)
    _run("git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "fixture", cwd=root)
    _run("git", "switch", "-q", "-c", "feat/task-1-vault", cwd=root)
    return root


def _events(root: Path) -> list[dict[str, object]]:
    head = _run("git", "rev-parse", "HEAD", cwd=root)
    base = {
        "repository_identity": "sha256:fixture",
        "worktree_root": root.as_posix(),
        "branch": "feat/task-1-vault",
        "head": head,
        "session_id": "session-one",
        "agent_id": "agent-child",
        "agent_type": "codex",
        "parent_agent_id": "agent-parent",
    }
    return [
        {
            **base,
            "event_id": "event-session",
            "ts": "2026-07-14T10:00:00Z",
            "event_type": "session_begin",
            "handler": "codex:sessionstart",
            "outcome": "pass",
            "paths": [],
            "extra": {"source": "resume"},
        },
        {
            **base,
            "event_id": "event-scope",
            "ts": "2026-07-14T10:01:00Z",
            "event_type": "scope",
            "handler": "codex:scope",
            "outcome": "pass",
            "paths": [],
            "extra": {"task_id": "1", "work_id": "task-1"},
        },
        {
            **base,
            "event_id": "event-verify",
            "ts": "2026-07-14T10:02:00Z",
            "event_type": "verification",
            "handler": "codex:verify",
            "outcome": "pass",
            "exit_class": "pass",
            "paths": ["reports/verification.json"],
            "extra": {"task_id": "1", "gate": "tests", "package": "app"},
        },
        {
            **base,
            "event_id": "event-witness",
            "ts": "2026-07-14T10:03:00Z",
            "event_type": "witness",
            "handler": "codex:witness",
            "outcome": "pass",
            "paths": [".aegis/reports/witness-report.json"],
            "extra": {
                "task_id": "1",
                "passed": True,
                "report_path": ".aegis/reports/witness-report.json",
            },
        },
        {
            **base,
            "event_id": "event-delivery",
            "ts": "2026-07-14T10:04:00Z",
            "event_type": "delivery",
            "handler": "github:delivery",
            "outcome": "pass",
            "paths": [],
            "extra": {"task_id": "ags-2", "pr_number": 42, "action": "merged"},
        },
        {
            **base,
            "agent_id": "agent-low-level-only",
            "event_id": "event-mutation",
            "ts": "2026-07-14T10:05:00Z",
            "event_type": "mutation",
            "tool_name": "Bash",
            "handler": "codex:bash",
            "outcome": "pass",
            "paths": ["src/example.py"],
            "extra": {"command": "curl -H 'Authorization: Bearer github_pat_secretvalue'"},
        },
        {
            **base,
            "event_id": "event-gate",
            "ts": "2026-07-14T10:06:00Z",
            "event_type": "gate_decision",
            "handler": "codex:pretooluse",
            "outcome": "pass",
            "paths": ["src/example.py"],
            "extra": {"reason": "allowed"},
        },
    ]


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _fake_bd_path() -> Path:
    return Path(os.environ["PATH"].split(os.pathsep, 1)[0]) / "bd"


def test_builds_deterministic_bounded_graph_and_preserves_legacy_context(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    events = _events(root)
    snapshot = obsidian_vault.collect_snapshot(root, events)
    output = tmp_path / "vault"

    first = obsidian_vault.build_vault(snapshot, output, target_dir=root)
    assert first["status"] == "built"
    assert first["changed"] is True
    before = _tree_digest(output)
    task_source = snapshot["task_source"]
    fake_bd = Path(task_source["binary"])
    assert task_source["binary_sha256"] == hashlib.sha256(fake_bd.read_bytes()).hexdigest()
    assert task_source["version"].startswith("bd version 1.1.0 (")
    assert task_source["raw_export_sha256"] == hashlib.sha256(
        (root / ".beads" / "test-export.jsonl").read_bytes()
    ).hexdigest()
    assert re.fullmatch(r"[0-9a-f]{32}", task_source["dolt_main_head"])
    manifest = json.loads((output / obsidian_vault.MANIFEST_NAME).read_text())
    assert manifest["task_bd_binary_sha256"] == task_source["binary_sha256"]
    assert manifest["task_raw_export_sha256"] == task_source["raw_export_sha256"]
    assert manifest["task_dolt_main_head"] == task_source["dolt_main_head"]

    assert (output / "Home.md").is_file()
    assert (output / "Tasks" / "task-ags-1.md").is_file()
    assert (output / "Tasks" / "task-ags-2.md").is_file()
    assert (output / "Views" / "Tasks.base").is_file()
    assert list((output / "Evidence" / "witness").glob("*.md"))
    assert list((output / "Evidence" / "verification").glob("*.md"))
    assert list((output / "Evidence" / "delivery").glob("*.md"))
    assert len(list((output / "Legacy").glob("*.md"))) == 1
    assert len(list((output / "Agents").glob("*.md"))) == 3

    all_text = "\n".join(
        path.read_text(encoding="utf-8") for path in output.rglob("*") if path.is_file()
    )
    assert "[[Tasks/task-ags-1|Bead ags-1 (Taskmaster 1)]]" in all_text
    assert "[[Tasks/task-ags-2|Bead ags-2]]" in all_text
    assert "taskmaster:master:1` (non-authoritative)" in all_text
    first_task = (output / "Tasks" / "task-ags-1.md").read_text(encoding="utf-8")
    second_task = (output / "Tasks" / "task-ags-2.md").read_text(encoding="utf-8")
    assert "## Blocks\n- [[Tasks/task-ags-2|Bead ags-2]]" in first_task
    assert "## Children\n- [[Tasks/task-ags-2|Bead ags-2]]" in first_task
    assert "## Blocked by\n- [[Tasks/task-ags-1|Bead ags-1]]" in second_task
    assert "## Parents\n- [[Tasks/task-ags-1|Bead ags-1]]" in second_task
    assert "Parent agent: agent-parent" in all_text
    assert "agent-low-level-only" in all_text
    assert "Human-authored nonblank lines: 3" in all_text
    assert "Generated Aegis blocks: 1" in all_text
    assert "event-mutation" not in all_text
    assert "event-gate" not in all_text
    assert "github_pat_secretvalue" not in all_text
    assert "curl -H" not in all_text

    second = obsidian_vault.build_vault(snapshot, output, target_dir=root)
    assert second["status"] == "current"
    assert second["changed"] is False
    assert _tree_digest(output) == before
    assert obsidian_vault.check_vault(output, expected_source_digest=snapshot["source_digest"])[
        "ok"
    ]

    # New low-level hook traffic must not churn the knowledge graph or freshness digest.
    more_low_level = [
        *events,
        {
            **events[-1],
            "event_id": "another-gate",
            "ts": "2026-07-14T10:07:00Z",
        },
    ]
    quiet_snapshot = obsidian_vault.collect_snapshot(root, more_low_level)
    assert quiet_snapshot["source_digest"] == snapshot["source_digest"]

    new_identity = [
        *events,
        {
            **events[-1],
            "agent_id": "new-agent",
            "event_id": "new-agent-gate",
            "ts": "2026-07-14T10:07:30Z",
        },
    ]
    identity_snapshot = obsidian_vault.collect_snapshot(root, new_identity)
    assert identity_snapshot["source_digest"] != snapshot["source_digest"]

    high_signal_change = [
        *events,
        {
            **events[2],
            "event_id": "new-verification",
            "ts": "2026-07-14T10:08:00Z",
        },
    ]
    changed_snapshot = obsidian_vault.collect_snapshot(root, high_signal_change)
    assert changed_snapshot["source_digest"] != snapshot["source_digest"]


def test_collection_rejects_wrong_or_mutable_beads_binary(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    with pytest.raises(obsidian_vault.VaultError, match="does not match the projection pin"):
        obsidian_vault.collect_snapshot(
            root,
            [],
            bd_executable=_fake_bd_path(),
            expected_bd_sha256="0" * 64,
        )

    _fake_bd_path().chmod(0o775)
    with pytest.raises(obsidian_vault.VaultError, match="group- or world-writable"):
        obsidian_vault.collect_snapshot(root, [], bd_executable=_fake_bd_path())


def test_collection_rejects_dolt_head_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _repo(tmp_path)
    heads = iter(("a" * 32, "b" * 32))
    monkeypatch.setattr(obsidian_vault, "_beads_head", lambda *args, **kwargs: next(heads))

    with pytest.raises(obsidian_vault.VaultError, match="main head changed"):
        obsidian_vault.collect_snapshot(root, [], bd_executable=_fake_bd_path())


def test_refuses_in_repo_unknown_or_tampered_destinations(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    snapshot = obsidian_vault.collect_snapshot(root, _events(root))

    with pytest.raises(obsidian_vault.VaultError, match="outside the source repository"):
        obsidian_vault.build_vault(snapshot, root / "vault", target_dir=root)

    unknown = tmp_path / "unknown"
    unknown.mkdir()
    (unknown / "my-note.md").write_text("manual\n", encoding="utf-8")
    with pytest.raises(obsidian_vault.VaultError, match="untrusted or modified vault"):
        obsidian_vault.build_vault(snapshot, unknown, target_dir=root)
    assert (unknown / "my-note.md").read_text(encoding="utf-8") == "manual\n"

    managed = tmp_path / "managed"
    obsidian_vault.build_vault(snapshot, managed, target_dir=root)
    (managed / "Home.md").write_text("tampered\n", encoding="utf-8")
    check = obsidian_vault.check_vault(managed)
    assert check["ok"] is False
    assert "hash mismatch: Home.md" in check["problems"]
    with pytest.raises(obsidian_vault.VaultError, match="hash mismatch"):
        obsidian_vault.build_vault(snapshot, managed, target_dir=root)

    symlink = tmp_path / "vault-symlink"
    symlink.symlink_to(unknown, target_is_directory=True)
    with pytest.raises(obsidian_vault.VaultError, match="must not be a symlink"):
        obsidian_vault.build_vault(snapshot, symlink, target_dir=root)
    assert obsidian_vault.check_vault(symlink)["ok"] is False


def test_atomic_replace_restores_previous_vault_when_publish_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repo(tmp_path)
    events = _events(root)
    first_snapshot = obsidian_vault.collect_snapshot(root, events)
    output = tmp_path / "atomic-vault"
    obsidian_vault.build_vault(first_snapshot, output, target_dir=root)
    original_digest = _tree_digest(output)

    changed_snapshot = obsidian_vault.collect_snapshot(
        root,
        [
            *events,
            {
                **events[2],
                "event_id": "later-verification",
                "ts": "2026-07-14T11:00:00Z",
            },
        ],
    )
    real_replace = obsidian_vault.os.replace
    calls = 0

    def fail_second_replace(source: object, destination: object) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated publish failure")
        real_replace(source, destination)

    monkeypatch.setattr(obsidian_vault.os, "replace", fail_second_replace)
    with pytest.raises(OSError, match="simulated publish failure"):
        obsidian_vault.build_vault(changed_snapshot, output, target_dir=root)

    assert output.is_dir()
    assert _tree_digest(output) == original_digest
    assert obsidian_vault.check_vault(
        output, expected_source_digest=first_snapshot["source_digest"]
    )["ok"]


def test_atomic_refresh_removes_deleted_bead_notes_and_keeps_exact_inventory(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    output = tmp_path / "deletion-vault"
    initial = obsidian_vault.collect_snapshot(root, _events(root))
    obsidian_vault.build_vault(initial, output, target_dir=root)
    assert (output / "Tasks" / "task-ags-2.md").is_file()

    _write_beads_export(root, _fixture_issues(1))
    refreshed = obsidian_vault.collect_snapshot(root, _events(root))
    result = obsidian_vault.build_vault(refreshed, output, target_dir=root)

    assert result["status"] == "built"
    assert not (output / "Tasks" / "task-ags-2.md").exists()
    assert obsidian_vault.check_vault(
        output, expected_source_digest=refreshed["source_digest"]
    )["ok"]


def test_limits_fail_closed_before_rendering_unbounded_task_graph(tmp_path: Path) -> None:
    root = _repo(tmp_path, task_count=2)
    with pytest.raises(obsidian_vault.VaultError, match="exceeds task limit"):
        obsidian_vault.collect_snapshot(
            root,
            [],
            limits=obsidian_vault.VaultLimits(max_tasks=1),
        )
    with pytest.raises(obsidian_vault.VaultError, match="agent_id limit"):
        obsidian_vault.collect_snapshot(
            root,
            _events(root),
            limits=obsidian_vault.VaultLimits(max_agents=1),
        )


def test_beads_is_the_only_task_authority_and_export_failures_stop_the_build(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    baseline = obsidian_vault.collect_snapshot(root, [])

    taskmaster = root / ".taskmaster" / "tasks" / "tasks.json"
    taskmaster.write_text(
        json.dumps(
            {
                "master": {
                    "tasks": [
                        {
                            "id": 999,
                            "title": "This decoy must never enter the vault",
                            "status": "pending",
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    after_taskmaster_change = obsidian_vault.collect_snapshot(root, [])
    assert after_taskmaster_change["tasks"] == baseline["tasks"]
    assert after_taskmaster_change["source_digest"] == baseline["source_digest"]
    assert all(task["id"] != "999" for task in after_taskmaster_change["tasks"])

    (root / ".beads" / "test-export.jsonl").unlink()
    with pytest.raises(obsidian_vault.VaultError, match="read-only Beads command failed"):
        obsidian_vault.collect_snapshot(root, [])


def test_beads_jsonl_validation_alias_rules_and_mixed_id_sort_are_fail_closed(
    tmp_path: Path,
) -> None:
    root = _repo(tmp_path)
    mixed = [
        _bead_issue("z-2", external_ref="taskmaster:master:7"),
        _bead_issue("10", external_ref="taskmaster:other:10"),
        _bead_issue("a-1", external_ref="https://example.invalid/issues/1"),
        _bead_issue("a-1.2", external_ref="taskmaster:master:7.1"),
        _bead_issue("2", external_ref=None),
    ]
    _write_beads_export(root, mixed)
    snapshot = obsidian_vault.collect_snapshot(root, [])

    assert [task["id"] for task in snapshot["tasks"]] == [
        "2",
        "10",
        "a-1",
        "a-1.2",
        "z-2",
    ]
    assert {
        task["id"]: task["taskmaster_alias"] for task in snapshot["tasks"]
    } == {"2": "", "10": "", "a-1": "", "a-1.2": "7.1", "z-2": "7"}

    export_path = root / ".beads" / "test-export.jsonl"
    export_path.write_text("{not-json}\n", encoding="utf-8")
    with pytest.raises(obsidian_vault.VaultError, match="invalid Beads export line 1"):
        obsidian_vault.collect_snapshot(root, [])

    export_path.write_text(
        '{"_type":"issue","id":"x-1","id":"x-2"}\n',
        encoding="utf-8",
    )
    with pytest.raises(obsidian_vault.VaultError, match="duplicate JSON object key 'id'"):
        obsidian_vault.collect_snapshot(root, [])

    export_path.write_text(
        '{"_type":"issue","id":"x-1","title":"X","status":"open",'
        '"priority":NaN,"dependencies":[]}\n',
        encoding="utf-8",
    )
    with pytest.raises(obsidian_vault.VaultError, match="non-finite JSON number"):
        obsidian_vault.collect_snapshot(root, [])

    _write_beads_export(root, [mixed[0], mixed[0]])
    with pytest.raises(obsidian_vault.VaultError, match="duplicate issue id z-2"):
        obsidian_vault.collect_snapshot(root, [])

    duplicate_alias = _bead_issue("x-1", external_ref="taskmaster:master:7")
    _write_beads_export(root, [mixed[0], duplicate_alias])
    with pytest.raises(obsidian_vault.VaultError, match="duplicate Taskmaster alias 7"):
        obsidian_vault.collect_snapshot(root, [])

    invalid_edge = _bead_issue(
        "x-2",
        dependencies=[_relationship("wrong-source", "x-1", "blocks")],
    )
    _write_beads_export(root, [invalid_edge])
    with pytest.raises(obsidian_vault.VaultError, match="issue_id does not match"):
        obsidian_vault.collect_snapshot(root, [])


def test_linked_worktree_uses_common_repository_name_and_identity(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    sibling = tmp_path / "agent-worktree"
    _run("git", "worktree", "add", "-q", "-b", "feat/task-2-agent", str(sibling), cwd=root)

    root_snapshot = obsidian_vault.collect_snapshot(root, [])
    sibling_snapshot = obsidian_vault.collect_snapshot(sibling, [])

    assert root_snapshot["repository"]["name"] == "project"
    assert sibling_snapshot["repository"]["name"] == "project"
    assert root_snapshot["repository"]["identity"] == sibling_snapshot["repository"]["identity"]
    assert sibling_snapshot["repository"]["branch"] == "feat/task-2-agent"


def test_cli_build_and_check_use_explicit_out_of_repo_destination(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _repo(tmp_path)
    output = tmp_path / "cli-vault"
    fake_bd = _fake_bd_path()
    fake_bd_sha256 = hashlib.sha256(fake_bd.read_bytes()).hexdigest()
    args = [
        "--source-root",
        str(SOURCE_ROOT),
        "vault",
        "build",
        "--target-dir",
        str(root),
        "--output",
        str(output),
        "--bd-executable",
        str(fake_bd),
        "--expected-bd-sha256",
        fake_bd_sha256,
    ]
    assert aegis_cli.main(args) == 0
    built = json.loads(capsys.readouterr().out)
    assert built["status"] == "built"
    assert built["authority"] == "derived-read-only"
    assert built["ledger"] == "absent"

    check_args = [
        "--source-root",
        str(SOURCE_ROOT),
        "vault",
        "check",
        "--target-dir",
        str(root),
        "--output",
        str(output),
        "--bd-executable",
        str(fake_bd),
        "--expected-bd-sha256",
        fake_bd_sha256,
    ]
    assert aegis_cli.main(check_args) == 0
    checked = json.loads(capsys.readouterr().out)
    assert checked["ok"] is True
    assert checked["fresh"] is True

    inside_args = [
        "--source-root",
        str(SOURCE_ROOT),
        "vault",
        "build",
        "--target-dir",
        str(root),
        "--output",
        str(root / "forbidden-vault"),
    ]
    assert aegis_cli.main(inside_args) == 1
    assert "outside the source repository" in capsys.readouterr().err
