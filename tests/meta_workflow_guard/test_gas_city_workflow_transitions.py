"""Transactional Gas City workflow begin/resume tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "plugins" / "gas-city-workflow" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import workflow_common  # noqa: E402
from scripts import _aegis_installer as aegis_installer  # noqa: E402
from aegis_foundation.gate.render import next_command  # noqa: E402
from workflow import _verify, parse_args  # noqa: E402
from workflow_begin import _kickoff_command, begin  # noqa: E402
from workflow_common import (  # noqa: E402
    BeginSpec,
    CommandRunner,
    WorkflowError,
    record_lifecycle_event,
)


class FixtureRunner(CommandRunner):
    def __init__(self, bead: dict[str, object]) -> None:
        self.bead = bead
        self.calls: list[list[str]] = []

    def run(
        self,
        argv,
        *,
        cwd: Path | None = None,
        env=None,
        check: bool = True,
    ):
        args = list(argv)
        self.calls.append(args)
        if args and args[0].endswith("/gc") and "bd" in args:
            if "show" in args:
                return subprocess.CompletedProcess(args, 0, json.dumps([self.bead]), "")
            if "update" in args and "--claim" in args:
                self.bead["status"] = "in_progress"
                self.bead["assignee"] = "fixture"
                return subprocess.CompletedProcess(args, 0, "claimed\n", "")
        if "aegis" in args and "verify" in args and "--strict" in args:
            return subprocess.CompletedProcess(args, 0, '{"status":"passed"}\n', "")
        if "plan" in args and "sync" in args:
            return subprocess.CompletedProcess(args, 0, "Plan and tracker are synchronized.\n", "")
        if "work-tracking" in args and "audit" in args:
            return subprocess.CompletedProcess(args, 0, "Audit passed: no issues found.\n", "")
        return super().run(args, cwd=cwd, env=env, check=check)


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def _write(path: Path, content: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if executable:
        path.chmod(0o755)


def _fixture_project(tmp_path: Path, *, descriptor: bool = True) -> tuple[Path, Path]:
    root = tmp_path / "future-project"
    root.mkdir()
    _write(root / "AGENTS.md", "# Agents\n")
    _write(root / "CLAUDE.md", "# Claude\n")
    if descriptor:
        _write(
            root / ".gas-city-workflow.json",
            json.dumps(
                {
                    "schema": "gas-city-workflow.project.v1",
                    "id": "future-project",
                    "repository": "fixture/future-project",
                    "rig": "future-project",
                    "workflow_authority": "beads",
                    "workflow_profile": "beads-with-aegis-evidence",
                },
                indent=2,
            )
            + "\n",
        )
    _write(
        root / "scripts" / "codex-task",
        """#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

root = Path.cwd()
bead = sys.argv[sys.argv.index("--bead") + 1]
slug = sys.argv[sys.argv.index("--slug") + 1]
branch = subprocess.run(
    ["git", "branch", "--show-current"], check=True, capture_output=True, text=True
).stdout.strip()
active = root / "docs" / "ai" / "work-tracking" / "active" / f"20300101-{bead}-{slug}-ACTIVE"
active.mkdir(parents=True)
(active / "TRACKER.md").write_text(f"# {bead} tracker\\n", encoding="utf-8")
session = root / "sessions" / "2030" / "01" / f"2030-01-01-001-{bead}-{slug}.md"
session.parent.mkdir(parents=True, exist_ok=True)
session.write_text(f"**Bead**: `{bead}`\\n", encoding="utf-8")
(root / "sessions" / "current").symlink_to(session.relative_to(root / "sessions"))
(root / "sessions" / "state.json").write_text(
    json.dumps(
        {"current": session.name, "paused": [], "updated_at": "2030-01-01T00:00:00Z"}
    )
    + "\\n",
    encoding="utf-8",
)
plan = root / "plans" / f"2030-01-01-{bead}-{slug}.md"
plan.parent.mkdir(parents=True, exist_ok=True)
plan.write_text(
    f"bead_ids: [{bead}]\\nbranch_policy: {branch}\\n", encoding="utf-8"
)
(root / "plans" / "current").symlink_to(plan.name)
""",
        executable=True,
    )
    _write(
        root / ".claude" / "scripts" / "readiness.sh",
        "#!/usr/bin/env bash\nset -euo pipefail\necho 'STATE: READY'\n",
        executable=True,
    )
    registry = tmp_path / "projects.json"
    projects = []
    if not descriptor:
        projects.append(
            {
                "id": "future-project",
                "root": root.as_posix(),
                "repository": "fixture/future-project",
                "rig": "future-project",
                "workflow_authority": "beads",
                "workflow_profile": "beads-with-aegis-evidence",
            }
        )
    _write(
        registry,
        json.dumps(
            {"schema": "gas-city-workflow.project-registry.v1", "projects": projects},
            indent=2,
        )
        + "\n",
    )
    _run(root, "git", "init", "-b", "main")
    _run(root, "git", "add", ".")
    _run(
        root,
        "git",
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.test",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-m",
        "fixture",
    )
    return root, registry


def _bead(*, status: str = "open", dependency_status: str | None = None):
    dependencies = []
    if dependency_status is not None:
        dependencies.append({"id": "ga-parent", "status": dependency_status})
    return {
        "id": "ga-test",
        "title": "Fixture transition",
        "status": status,
        "dependencies": dependencies,
    }


def test_begin_creates_descriptor_project_worktree_and_replays_exactly(tmp_path: Path) -> None:
    root, registry = _fixture_project(tmp_path)
    runner = FixtureRunner(_bead())

    first = begin(
        root,
        "ga-test",
        slug="fixture",
        goals=["Prove fixture transition"],
        registry=registry,
        runner=runner,
    )
    second = begin(
        root,
        "ga-test",
        slug="fixture",
        goals=["Prove fixture transition"],
        registry=registry,
        runner=runner,
    )

    worktree = tmp_path / "future-project-worktrees" / "ga-test-fixture"
    assert first["status"] == second["status"] == "ready"
    assert first["context"]["workspace"]["location"] == "linked-worktree"
    assert first["spec"]["worktree"] == worktree.as_posix()
    assert runner.bead["status"] == "in_progress"
    assert len(list((worktree / "docs" / "ai" / "work-tracking" / "active").iterdir())) == 1
    journal = json.loads(Path(first["journal"]).read_text(encoding="utf-8"))
    assert journal["phase"] == "ready"
    assert [item["phase"] for item in journal["history"]] == [
        "planned",
        "worktree-created",
        "scaffolded",
        "claimed",
        "ready",
    ]


def test_begin_adopts_exact_precreated_worktree_as_partial_outer_transition(
    tmp_path: Path,
) -> None:
    root, registry = _fixture_project(tmp_path)
    worktree = tmp_path / "future-project-worktrees" / "ga-test-fixture"
    worktree.parent.mkdir()
    _run(root, "git", "worktree", "add", "-b", "codex/ga-test-fixture", str(worktree))
    runner = FixtureRunner(_bead())

    result = begin(
        root,
        "ga-test",
        slug="fixture",
        goals=[],
        registry=registry,
        runner=runner,
    )

    assert result["status"] == "ready"
    assert result["spec"]["base_commit"] == _run(root, "git", "rev-parse", "HEAD").stdout.strip()


def test_begin_safely_fast_forwards_clean_precreated_worktree(tmp_path: Path) -> None:
    root, registry = _fixture_project(tmp_path)
    worktree = tmp_path / "future-project-worktrees" / "ga-test-fixture"
    worktree.parent.mkdir()
    _run(root, "git", "worktree", "add", "-b", "codex/ga-test-fixture", str(worktree))
    (root / "new-base.txt").write_text("new base\n", encoding="utf-8")
    _run(root, "git", "add", "new-base.txt")
    _run(
        root,
        "git",
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.test",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-m",
        "advance base",
    )

    result = begin(
        root,
        "ga-test",
        slug="fixture",
        goals=[],
        registry=registry,
        runner=FixtureRunner(_bead()),
    )

    assert (
        _run(worktree, "git", "rev-parse", "HEAD").stdout.strip() == result["spec"]["base_commit"]
    )
    assert (worktree / "new-base.txt").read_text(encoding="utf-8") == "new base\n"


def test_ready_replay_keeps_original_base_after_canonical_checkout_advances(
    tmp_path: Path,
) -> None:
    root, registry = _fixture_project(tmp_path)
    runner = FixtureRunner(_bead())
    first = begin(root, "ga-test", slug="fixture", goals=[], registry=registry, runner=runner)
    (root / "later.txt").write_text("later\n", encoding="utf-8")
    _run(root, "git", "add", "later.txt")
    _run(
        root,
        "git",
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.test",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-m",
        "later canonical change",
    )

    second = begin(root, "ga-test", slug="fixture", goals=[], registry=registry, runner=runner)

    assert second["spec"]["base_commit"] == first["spec"]["base_commit"]
    assert not (Path(first["spec"]["worktree"]) / "later.txt").exists()


def test_begin_recovers_from_a_pre_scaffold_failure(tmp_path: Path) -> None:
    root, registry = _fixture_project(tmp_path)

    class FailOnceRunner(FixtureRunner):
        failed = False

        def run(self, argv, *, cwd=None, env=None, check=True):
            args = list(argv)
            if not self.failed and any(part.endswith("/scripts/codex-task") for part in args):
                self.failed = True
                raise WorkflowError("fixture pre-scaffold failure")
            return super().run(args, cwd=cwd, env=env, check=check)

    runner = FailOnceRunner(_bead())
    with pytest.raises(WorkflowError, match="pre-scaffold failure"):
        begin(root, "ga-test", slug="fixture", goals=[], registry=registry, runner=runner)

    journal_path = root / ".git" / "gas-city-workflow" / "transactions" / "ga-test.json"
    assert json.loads(journal_path.read_text(encoding="utf-8"))["phase"] == "worktree-created"

    result = begin(root, "ga-test", slug="fixture", goals=[], registry=registry, runner=runner)
    assert result["phase"] == "ready"


def test_registered_project_uses_the_selected_registry_for_claim_and_replay(
    tmp_path: Path,
) -> None:
    root, registry = _fixture_project(tmp_path, descriptor=False)
    result = begin(
        root,
        "ga-test",
        slug="fixture",
        goals=[],
        registry=registry,
        runner=FixtureRunner(_bead()),
    )
    assert result["context"]["project"]["identity_source"] == "registry"


def test_lifecycle_events_append_to_the_bound_journal(tmp_path: Path) -> None:
    root, registry = _fixture_project(tmp_path)
    runner = FixtureRunner(_bead())
    result = begin(root, "ga-test", slug="fixture", goals=[], registry=registry, runner=runner)
    worktree = Path(result["spec"]["worktree"])

    record_lifecycle_event(runner, worktree, "checkpoint", "ready")

    journal = json.loads(Path(result["journal"]).read_text(encoding="utf-8"))
    assert journal["events"][-1]["action"] == "checkpoint"
    assert journal["events"][-1]["status"] == "ready"

    verified = _verify(worktree, runner)
    assert "source-work-tracking-audit" in verified["checks"]
    journal = json.loads(Path(result["journal"]).read_text(encoding="utf-8"))
    assert journal["events"][-1]["action"] == "verify"

    (worktree / "scripts" / "codex-task").unlink()
    _write(worktree / ".aegis" / "foundation-manifest.json", "{}\n")
    installed_verify = _verify(worktree, runner)
    assert "aegis-strict" in installed_verify["checks"]


def test_frozen_verification_does_not_append_plan_sync_state(tmp_path: Path) -> None:
    root, registry = _fixture_project(tmp_path)
    runner = FixtureRunner(_bead())
    result = begin(root, "ga-test", slug="fixture", goals=[], registry=registry, runner=runner)
    runner.calls.clear()

    verified = _verify(Path(result["spec"]["worktree"]), runner, synchronize=False)

    assert "plan-sync" not in verified["checks"]
    assert not any("plan" in call and "sync" in call for call in runner.calls)


def test_resume_can_derive_the_active_bead_from_session_state() -> None:
    args = parse_args(["resume", "--root", "/tmp/project"])
    assert args.bead is None


def test_installed_project_kickoff_uses_registry_bound_canonical_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "consumer"
    (target / ".aegis").mkdir(parents=True)
    (target / ".aegis" / "foundation-manifest.json").write_text("{}\n", encoding="utf-8")
    runtime = tmp_path / "gas-city-ops"
    _write(runtime / "scripts" / "codex-task", "#!/usr/bin/env python3\n", executable=True)
    registry = tmp_path / "projects.json"
    _write(
        registry,
        json.dumps(
            {
                "schema": "gas-city-workflow.project-registry.v1",
                "projects": [
                    {
                        "id": "gas-city-operations",
                        "root": runtime.as_posix(),
                        "repository": "fixture/gas-city-operations",
                        "rig": "gascity",
                        "workflow_authority": "beads",
                        "workflow_profile": "beads-with-aegis-evidence",
                    }
                ],
            }
        )
        + "\n",
    )
    monkeypatch.setattr(workflow_common, "SOURCE_ROOT", tmp_path / "plugin-cache")
    spec = BeginSpec(
        project_id="consumer",
        rig="consumer",
        workflow_profile="beads-with-aegis-evidence",
        canonical_root=target.as_posix(),
        worktree_root=(tmp_path / "consumer-worktrees").as_posix(),
        bead_id="ga-test",
        title="Installed transition",
        slug="installed-transition",
        branch="codex/ga-test-installed-transition",
        worktree=target.as_posix(),
        base_commit="a" * 40,
    )

    argv, cwd = _kickoff_command(spec, ["Prove installed kickoff"], registry)

    assert cwd == runtime
    assert argv[1] == (runtime / "scripts" / "codex-task").as_posix()
    assert argv[2:4] == ["aegis", "kickoff"]
    assert argv[argv.index("--target-dir") + 1] == target.as_posix()


def test_router_skill_delegates_transitions_without_copying_mutation_sequences() -> None:
    skill = (
        REPO_ROOT / "plugins" / "gas-city-workflow" / "skills" / "gas-city-workflow" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "scripts/workflow.py begin" in skill
    assert "workflow.py resume" in skill
    assert "git worktree add" not in skill
    assert "bd update" not in skill
    assert "wizard kickoff" not in skill


def test_aegis_guidance_selects_an_entrypoint_that_exists_for_each_target(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    _write(source / "scripts" / "codex-task", "#!/usr/bin/env python3\n", executable=True)
    installed = tmp_path / "installed"
    _write(installed / ".aegis" / "bin" / "aegis", "#!/bin/sh\n", executable=True)
    packaged = tmp_path / "packaged"
    packaged.mkdir()

    source_command = aegis_installer._workflow_cli_command(source)
    assert source_command.endswith("scripts/codex-task aegis")
    assert ".aegis/bin/aegis" not in source_command
    assert aegis_installer._workflow_cli_command(installed) == "./.aegis/bin/aegis"
    assert aegis_installer._workflow_cli_command(packaged) == "aegis"

    assert "scripts/codex-task aegis next" in next_command(source)
    assert next_command(installed) == "./.aegis/bin/aegis next --target-dir ."
    assert next_command(packaged) == "aegis next --target-dir ."


def test_begin_refuses_branch_registered_at_a_different_worktree(tmp_path: Path) -> None:
    root, registry = _fixture_project(tmp_path)
    wrong = tmp_path / "wrong-root" / "ga-test-fixture"
    wrong.parent.mkdir()
    _run(root, "git", "worktree", "add", "-b", "codex/ga-test-fixture", str(wrong))

    with pytest.raises(WorkflowError, match="disagrees with the derived target"):
        begin(
            root,
            "ga-test",
            slug="fixture",
            goals=[],
            registry=registry,
            runner=FixtureRunner(_bead()),
        )


def test_begin_refuses_unresolved_dependencies_before_creating_state(tmp_path: Path) -> None:
    root, registry = _fixture_project(tmp_path)

    with pytest.raises(WorkflowError, match="unresolved dependencies: ga-parent"):
        begin(
            root,
            "ga-test",
            slug="fixture",
            goals=[],
            registry=registry,
            runner=FixtureRunner(_bead(dependency_status="open")),
        )

    assert not (tmp_path / "future-project-worktrees").exists()
