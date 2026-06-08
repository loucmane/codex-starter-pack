"""Tests for the Aegis Foundation installer CLI/core prototype."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from aegis_foundation import cli as aegis_cli
from scripts import _aegis_installer as aegis_installer
from scripts._aegis_installer import (
    AEGIS_MANIFEST_REL,
    AEGIS_CLOSEOUT_REPORT_REL,
    AEGIS_CURRENT_WORK_REL,
    AEGIS_CLIENT_RELOAD_REL,
    AEGIS_DEGRADED_EVENTS_REL,
    AEGIS_LOCAL_TASKS_REL,
    AEGIS_RUNTIME_ENV_REL,
    AEGIS_PENDING_TRACKING_REL,
    AEGIS_RELEASE_CERT_REPORT_REL,
    AEGIS_REPAIR_REPORT_REL,
    AEGIS_VERIFY_REPORT_REL,
    AegisError,
    certify_release_candidate,
    closeout,
    doctor,
    initialize_project,
    install,
    inspect_project,
    kickoff,
    log_work,
    next_action,
    plan_install,
    reconcile,
    repair,
    repair_handoff,
    runtime_status,
    runtime_update,
    status,
    start_observation,
    start_local_work,
    stop_observation,
    uninstall,
    verify,
)
from tests.meta_workflow_guard.reconcile_side_effect_oracle import snapshot_whole_tree

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPO_ROOT / "schemas" / "aegis"
RECONCILE_MUTATION_FLAGS = (
    "--apply",
    "--auto",
    "--auto-fix",
    "--fix",
    "--set-status",
    "--status",
    "--done",
    "--closeout",
    "--mutate",
    "--write",
    "--push",
)


def load_task_module():
    name = "codex_task_aegis_test_module"
    if name in sys.modules:
        del sys.modules[name]
    path = Path("scripts/codex-task")
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


def validate_schema(schema_name: str, payload: dict) -> None:
    schema = json.loads((SCHEMA_ROOT / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)


def run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "scripts/codex-task", *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def run_target_readiness(target: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "bash",
            str(target / ".claude" / "scripts" / "readiness.sh"),
            "--quick",
            "--root",
            str(target),
        ],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def run_target_pretooluse(target: Path, payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "pretooluse-gate.sh")],
        cwd=target,
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "CLAUDE_PROJECT_DIR": target.as_posix()},
        check=False,
    )


def run_target_pretooluse_raw(target: Path, payload: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "pretooluse-gate.sh")],
        cwd=target,
        input=payload,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "CLAUDE_PROJECT_DIR": target.as_posix()},
        check=False,
    )


def simulate_claude_reload(target: Path) -> None:
    """Run an installed PreToolUse hook once to prove Claude hooks are active."""
    result = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__aegis__aegis_next",
            "tool_input": {"target_dir": target.as_posix()},
        },
    )
    assert result.returncode == 0, result.stderr
    assert not (target / AEGIS_CLIENT_RELOAD_REL).exists()


def run_target_posttooluse(target: Path, payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "posttooluse-tracking.sh")],
        cwd=target,
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "CLAUDE_PROJECT_DIR": target.as_posix()},
        check=False,
    )


def run_target_stop_gate(target: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "tracking-stop-gate.sh")],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "CLAUDE_PROJECT_DIR": target.as_posix()},
        check=False,
    )


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", repo.as_posix(), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check:
        assert result.returncode == 0, result.stderr or result.stdout
    return result


def init_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "aegis@example.invalid")
    git(repo, "config", "user.name", "Aegis Test")
    git(repo, "config", "commit.gpgsign", "false")
    (repo / "README.md").write_text("# target\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "initial")


def write_taskmaster_tasks(repo: Path, tasks: list[dict[str, Any]]) -> None:
    task_dir = repo / ".taskmaster" / "tasks"
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "tasks.json").write_text(
        json.dumps({"master": {"tasks": tasks}}, indent=2) + "\n", encoding="utf-8"
    )


def write_taskmaster_payload(repo: Path, payload: object | str) -> None:
    task_dir = repo / ".taskmaster" / "tasks"
    task_dir.mkdir(parents=True, exist_ok=True)
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2) + "\n"
    (task_dir / "tasks.json").write_text(text, encoding="utf-8")


def commit_file(repo: Path, rel_path: str, content: str, message: str) -> None:
    path = repo / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    git(repo, "add", rel_path)
    git(repo, "commit", "-m", message)


def assert_reconcile_preserved_whole_tree(target: Path, before) -> None:
    before.assert_matches(snapshot_whole_tree(target))


def test_build_parser_accepts_aegis_commands() -> None:
    module = load_task_module()
    parser = module.build_parser()

    inspect_args = parser.parse_args(["aegis", "inspect", "--target-dir", "/tmp/example"])
    assert inspect_args.command == "aegis"
    assert inspect_args.subcommand == "inspect"
    assert inspect_args.target_dir == "/tmp/example"

    plan_args = parser.parse_args(
        [
            "aegis",
            "plan-install",
            "--target-dir",
            "/tmp/example",
            "--primary-agent",
            "claude",
            "--agent",
            "claude",
        ]
    )
    assert plan_args.primary_agent == "claude"
    assert plan_args.agent == ["claude"]

    init_args = parser.parse_args(["aegis", "init", "--target-dir", "/tmp/example"])
    assert init_args.subcommand == "init"
    assert init_args.primary_agent == "claude"
    assert init_args.agent is None

    start_args = parser.parse_args(["aegis", "start", "Improve BrandMark accessibility"])
    assert start_args.subcommand == "start"
    assert start_args.title == "Improve BrandMark accessibility"

    observe_start_args = parser.parse_args(
        ["aegis", "observe", "start", "Polish audit", "--slug", "polish-audit"]
    )
    assert observe_start_args.subcommand == "observe"
    assert observe_start_args.observe_subcommand == "start"
    assert observe_start_args.title == "Polish audit"
    assert observe_start_args.slug == "polish-audit"

    observe_stop_args = parser.parse_args(
        ["aegis", "observe", "stop", "--summary", "Observed app shell", "--allow-dirty"]
    )
    assert observe_stop_args.subcommand == "observe"
    assert observe_stop_args.observe_subcommand == "stop"
    assert observe_stop_args.summary == "Observed app shell"
    assert observe_stop_args.allow_dirty is True

    install_args = parser.parse_args(
        [
            "aegis",
            "install",
            "--target-dir",
            "/tmp/example",
            "--primary-agent",
            "multi",
            "--agent",
            "claude",
            "--agent",
            "codex",
            "--apply",
        ]
    )
    assert install_args.apply is True
    assert install_args.agent == ["claude", "codex"]

    verify_args = parser.parse_args(["aegis", "verify", "--target-dir", "/tmp/example", "--strict"])
    assert verify_args.subcommand == "verify"
    assert verify_args.strict is True

    next_args = parser.parse_args(["aegis", "next", "--target-dir", "/tmp/example"])
    assert next_args.subcommand == "next"
    assert next_args.target_dir == "/tmp/example"

    doctor_args = parser.parse_args(["aegis", "doctor", "--target-dir", "/tmp/example", "--json"])
    assert doctor_args.subcommand == "doctor"
    assert doctor_args.target_dir == "/tmp/example"
    assert doctor_args.json is True

    reconcile_args = parser.parse_args(
        [
            "aegis",
            "reconcile",
            "--target-dir",
            "/tmp/example",
            "--base-ref",
            "main",
            "--no-github",
            "--json",
            "--preview-candidates",
        ]
    )
    assert reconcile_args.subcommand == "reconcile"
    assert reconcile_args.target_dir == "/tmp/example"
    assert reconcile_args.base_ref == "main"
    assert reconcile_args.no_github is True
    assert reconcile_args.json is True
    assert reconcile_args.preview_candidates is True

    repair_args = parser.parse_args(
        ["aegis", "repair", "--target-dir", "/tmp/example", "--apply", "--json"]
    )
    assert repair_args.subcommand == "repair"
    assert repair_args.target_dir == "/tmp/example"
    assert repair_args.apply is True
    assert repair_args.json is True

    uninstall_args = parser.parse_args(
        [
            "aegis",
            "uninstall",
            "--target-dir",
            "/tmp/example",
            "--apply",
            "--remove-hook-scripts",
            "--json",
        ]
    )
    assert uninstall_args.subcommand == "uninstall"
    assert uninstall_args.target_dir == "/tmp/example"
    assert uninstall_args.apply is True
    assert uninstall_args.remove_hook_scripts is True
    assert uninstall_args.json is True

    closeout_args = parser.parse_args(
        [
            "aegis",
            "closeout",
            "--target-dir",
            "/tmp/example",
            "--update-handoff",
            "--dry-run",
            "--json",
        ]
    )
    assert closeout_args.subcommand == "closeout"
    assert closeout_args.update_handoff is True
    assert closeout_args.dry_run is True
    assert closeout_args.json is True

    handoff_repair_args = parser.parse_args(
        [
            "aegis",
            "handoff",
            "repair",
            "--target-dir",
            "/tmp/example",
            "--dry-run",
        ]
    )
    assert handoff_repair_args.subcommand == "handoff"
    assert handoff_repair_args.handoff_subcommand == "repair"
    assert handoff_repair_args.target_dir == "/tmp/example"
    assert handoff_repair_args.dry_run is True

    certify_args = parser.parse_args(
        [
            "aegis",
            "certify-release",
            "--source-dir",
            "/tmp/source",
            "--dist-dir",
            "/tmp/dist",
            "--skip-build",
            "--skip-smoke",
        ]
    )
    assert certify_args.subcommand == "certify-release"
    assert certify_args.skip_build is True
    assert certify_args.skip_smoke is True

    kickoff_args = parser.parse_args(
        [
            "aegis",
            "kickoff",
            "--target-dir",
            "/tmp/example",
            "--task",
            "1",
            "--slug",
            "portable-smoke",
            "--title",
            "Portable Smoke",
        ]
    )
    assert kickoff_args.subcommand == "kickoff"
    assert kickoff_args.task == "1"

    kickoff_local_args = parser.parse_args(
        [
            "aegis",
            "kickoff",
            "--target-dir",
            "/tmp/example",
            "--local",
            "--title",
            "Improve BrandMark accessibility",
        ]
    )
    assert kickoff_local_args.local is True
    assert kickoff_local_args.title == "Improve BrandMark accessibility"

    log_args = parser.parse_args(
        [
            "aegis",
            "log",
            "--target-dir",
            "/tmp/example",
            "--handler",
            "claude-test",
            "--evidence",
            "reports/example.txt",
            "--note",
            "Recorded example evidence",
        ]
    )
    assert log_args.subcommand == "log"
    assert log_args.handler == "claude-test"
    assert log_args.plan_step == ""

    profile_args = parser.parse_args(["aegis", "explain-profile"])
    assert profile_args.profile == "generic"


def test_reconcile_cli_parsers_reject_mutation_flags() -> None:
    module = load_task_module()
    codex_parser = module.build_parser()
    package_parser = aegis_cli.build_arg_parser()

    codex_allowed = codex_parser.parse_args(
        [
            "aegis",
            "reconcile",
            "--target-dir",
            "/tmp/example",
            "--base-ref",
            "main",
            "--no-github",
            "--json",
            "--preview-candidates",
        ]
    )
    assert codex_allowed.subcommand == "reconcile"
    assert codex_allowed.target_dir == "/tmp/example"
    assert codex_allowed.base_ref == "main"
    assert codex_allowed.no_github is True
    assert codex_allowed.json is True
    assert codex_allowed.preview_candidates is True

    package_allowed = package_parser.parse_args(
        [
            "reconcile",
            "--target-dir",
            "/tmp/example",
            "--base-ref",
            "main",
            "--no-github",
            "--json",
            "--preview-candidates",
        ]
    )
    assert package_allowed.subcommand == "reconcile"
    assert package_allowed.target_dir == "/tmp/example"
    assert package_allowed.base_ref == "main"
    assert package_allowed.no_github is True
    assert package_allowed.json is True
    assert package_allowed.preview_candidates is True

    for flag in RECONCILE_MUTATION_FLAGS:
        with pytest.raises(SystemExit):
            codex_parser.parse_args(["aegis", "reconcile", flag])
        with pytest.raises(SystemExit):
            package_parser.parse_args(["reconcile", flag])


def test_reconcile_rejects_option_shaped_base_ref(tmp_path: Path) -> None:
    target = tmp_path / "reconcile-invalid-base-ref"
    init_git_repo(target)
    write_taskmaster_tasks(
        target, [{"id": 42, "title": "Cart Button", "status": "pending", "dependencies": []}]
    )

    with pytest.raises(AegisError, match="invalid reconcile base_ref"):
        reconcile(target, source_root=REPO_ROOT, base_ref="--git-dir=/tmp/other", use_github=False)


def test_reconcile_reports_git_merged_task_that_taskmaster_has_not_marked_done(
    tmp_path: Path,
) -> None:
    target = tmp_path / "reconcile-merged-not-done"
    init_git_repo(target)
    write_taskmaster_tasks(
        target, [{"id": 42, "title": "Cart Button", "status": "pending", "dependencies": []}]
    )
    git(target, "switch", "-c", "feat/task-42-cart-button")
    commit_file(target, "feature.txt", "cart\n", "task 42")
    git(target, "switch", "main")
    git(target, "merge", "--no-ff", "feat/task-42-cart-button", "-m", "merge task 42")
    status_before = git(target, "status", "--short").stdout
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=False)

    assert report["read_only"] is True
    assert git(target, "status", "--short").stdout == status_before
    assert_reconcile_preserved_whole_tree(target, tree_before)
    assert report["status"] == "drift"
    assert report["summary"]["errors"] == 1
    finding = report["findings"][0]
    assert finding["kind"] == "merged_but_not_done"
    assert finding["task_id"] == "42"
    assert finding["evidence"]["merge_truth"]["proof"] == "git_ancestor"
    assert "Aegis reconcile: DRIFT" in aegis_installer.format_reconcile_summary(report)


def test_reconcile_uses_github_merged_pr_to_handle_squash_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "reconcile-squash-gh"
    init_git_repo(target)
    write_taskmaster_tasks(
        target, [{"id": 43, "title": "Squashed Feature", "status": "pending", "dependencies": []}]
    )
    git(target, "switch", "-c", "feat/task-43-squashed-feature")
    commit_file(target, "feature.txt", "squash\n", "task 43")
    git(target, "switch", "main")
    git(target, "merge", "--squash", "feat/task-43-squashed-feature")
    git(target, "commit", "-m", "squash task 43")
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {
            "available": True,
            "reason": "",
            "prs": [
                {
                    "number": 43,
                    "state": "MERGED",
                    "title": "Task 43 squashed feature",
                    "headRefName": "feat/task-43-squashed-feature",
                    "baseRefName": "main",
                    "mergedAt": "2026-06-02T10:00:00Z",
                    "url": "https://example.invalid/pr/43",
                    "isDraft": False,
                }
            ],
        },
    )
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=True)

    assert_reconcile_preserved_whole_tree(target, tree_before)
    finding = next(item for item in report["findings"] if item["kind"] == "merged_but_not_done")
    assert finding["evidence"]["merge_truth"]["proof"] == "github_pr_merged"
    task = next(item for item in report["tasks"] if item["task_id"] == "43")
    assert task["merge_truth"]["branches"][0]["proof"] == "git_non_ancestor"


def test_reconcile_keeps_squash_ambiguous_git_only_case_unknown(tmp_path: Path) -> None:
    target = tmp_path / "reconcile-squash-offline"
    init_git_repo(target)
    write_taskmaster_tasks(
        target, [{"id": 44, "title": "Offline Squash", "status": "pending", "dependencies": []}]
    )
    git(target, "switch", "-c", "feat/task-44-offline-squash")
    commit_file(target, "feature.txt", "offline\n", "task 44")
    git(target, "switch", "main")
    git(target, "merge", "--squash", "feat/task-44-offline-squash")
    git(target, "commit", "-m", "squash task 44")
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=False)

    assert_reconcile_preserved_whole_tree(target, tree_before)
    assert report["status"] == "clean"
    assert not [
        finding for finding in report["findings"] if finding["kind"] == "merged_but_not_done"
    ]
    task = next(item for item in report["tasks"] if item["task_id"] == "44")
    assert task["merge_truth"]["status"] == "unknown"
    assert task["merge_truth"]["proof"] == "git_only_non_ancestor_or_missing_base"


def test_reconcile_keeps_done_git_only_unknown_as_task_detail_not_finding(tmp_path: Path) -> None:
    target = tmp_path / "reconcile-done-offline-unknown"
    init_git_repo(target)
    write_taskmaster_tasks(
        target, [{"id": 441, "title": "Done Offline", "status": "done", "dependencies": []}]
    )
    git(target, "switch", "-c", "feat/task-441-stale-local-branch")
    commit_file(target, "feature.txt", "offline done\n", "task 441")
    git(target, "switch", "main")
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=False)

    assert_reconcile_preserved_whole_tree(target, tree_before)
    assert report["status"] == "clean"
    assert not report["findings"]
    task = next(item for item in report["tasks"] if item["task_id"] == "441")
    assert task["merge_truth"]["status"] == "unknown"
    assert task["merge_truth"]["proof"] == "git_only_non_ancestor_or_missing_base"


def test_reconcile_reports_done_task_with_open_pr_as_not_merged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "reconcile-done-open-pr"
    init_git_repo(target)
    write_taskmaster_tasks(
        target, [{"id": 45, "title": "Open PR", "status": "done", "dependencies": []}]
    )
    git(target, "switch", "-c", "feat/task-45-open-pr")
    commit_file(target, "feature.txt", "open\n", "task 45")
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {
            "available": True,
            "reason": "",
            "prs": [
                {
                    "number": 45,
                    "state": "OPEN",
                    "title": "Task 45 open PR",
                    "headRefName": "feat/task-45-open-pr",
                    "baseRefName": "main",
                    "mergedAt": None,
                    "url": "https://example.invalid/pr/45",
                    "isDraft": False,
                }
            ],
        },
    )
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=True)

    assert_reconcile_preserved_whole_tree(target, tree_before)
    finding = next(item for item in report["findings"] if item["kind"] == "done_but_not_merged")
    assert finding["task_id"] == "45"
    assert finding["evidence"]["merge_truth"]["proof"] == "github_pr_open"


def test_reconcile_reports_abandoned_branches_stubs_and_multi_pr_ambiguity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "reconcile-stubs"
    init_git_repo(target)
    write_taskmaster_tasks(
        target,
        [
            {"id": 46, "title": "In Progress", "status": "in-progress", "dependencies": []},
            {"id": 47, "title": "Ambiguous Epic", "status": "pending", "dependencies": []},
        ],
    )
    git(target, "switch", "-c", "feat/task-46-abandoned")
    commit_file(target, "task46.txt", "abandoned\n", "task 46")
    git(target, "switch", "main")
    git(target, "switch", "-c", "feat/task-999-local-stub")
    commit_file(target, "stub.txt", "stub\n", "task 999")
    git(target, "switch", "main")
    (target / ".aegis" / "state").mkdir(parents=True)
    (target / ".aegis" / "state" / "local-tasks.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "tasks": [
                    {
                        "id": "1000",
                        "title": "Ad hoc local task",
                        "status": "in-progress",
                        "slug": "ad-hoc",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {
            "available": True,
            "reason": "",
            "prs": [
                {
                    "number": 470,
                    "state": "OPEN",
                    "title": "Task 47 part A",
                    "headRefName": "feat/task-47-part-a",
                    "baseRefName": "main",
                    "mergedAt": None,
                    "url": "https://example.invalid/pr/470",
                    "isDraft": False,
                },
                {
                    "number": 471,
                    "state": "OPEN",
                    "title": "Task 47 part B",
                    "headRefName": "feat/task-47-part-b",
                    "baseRefName": "main",
                    "mergedAt": None,
                    "url": "https://example.invalid/pr/471",
                    "isDraft": False,
                },
            ],
        },
    )
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=True)
    assert_reconcile_preserved_whole_tree(target, tree_before)
    kinds = {finding["kind"] for finding in report["findings"]}

    assert "abandoned_in_progress_branch" in kinds
    assert "stale_local_stub" in kinds
    assert "local_ad_hoc_stub" in kinds
    assert "multi_pr_epic_ambiguity" in kinds


def test_reconcile_preserves_whole_tree_with_malformed_taskmaster_state(tmp_path: Path) -> None:
    target = tmp_path / "reconcile-malformed-taskmaster"
    init_git_repo(target)
    task_dir = target / ".taskmaster" / "tasks"
    task_dir.mkdir(parents=True)
    (task_dir / "tasks.json").write_text("{not json\n", encoding="utf-8")
    git(target, "switch", "-c", "feat/task-77-malformed-taskmaster")
    commit_file(target, "task77.txt", "malformed taskmaster\n", "task 77")
    git(target, "switch", "main")
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=False)

    assert_reconcile_preserved_whole_tree(target, tree_before)
    assert report["read_only"] is True
    assert report["taskmaster"]["state"] == "invalid"
    assert report["taskmaster"]["present"] is True
    assert report["taskmaster"]["valid"] is False
    assert report["taskmaster"]["reason"] == "json_decode_error"
    assert {finding["kind"] for finding in report["findings"]} == {"taskmaster_invalid"}


def test_reconcile_preserves_whole_tree_when_github_metadata_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "reconcile-github-unavailable"
    init_git_repo(target)
    write_taskmaster_tasks(
        target, [{"id": 78, "title": "GitHub Unavailable", "status": "pending", "dependencies": []}]
    )
    git(target, "switch", "-c", "feat/task-78-github-unavailable")
    commit_file(target, "feature.txt", "github unavailable\n", "task 78")
    git(target, "switch", "main")
    monkeypatch.setattr(
        aegis_installer,
        "_run_gh_pr_list",
        lambda _target: {"available": False, "reason": "gh unavailable", "prs": []},
    )
    tree_before = snapshot_whole_tree(target)

    report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=True)

    assert_reconcile_preserved_whole_tree(target, tree_before)
    assert report["read_only"] is True
    assert report["github"]["enabled"] is True
    assert report["github"]["available"] is False
    assert report["github"]["reason"] == "gh unavailable"
    task = next(item for item in report["tasks"] if item["task_id"] == "78")
    assert task["merge_truth"]["status"] == "unknown"


def test_public_init_installs_with_default_claude_adapter(tmp_path: Path) -> None:
    target = tmp_path / "public-init"
    target.mkdir()

    payload = initialize_project(target, source_root=REPO_ROOT)

    assert payload["status"] == "initialized"
    assert payload["agent_selection"] == {
        "source": "public_defaults",
        "primary_agent": "claude",
        "enabled_agents": ["claude"],
    }
    assert payload["install"]["status"] == "applied"
    assert payload["verification"]["status"] == "passed"
    assert payload["public_commands"]["start"] == 'aegis start "<task title>"'
    assert (target / AEGIS_MANIFEST_REL).exists()
    assert (target / ".claude" / "settings.json").exists()
    assert (target / AEGIS_VERIFY_REPORT_REL).exists()


def test_doctor_reports_installed_no_current_work_without_mutating(tmp_path: Path) -> None:
    target = tmp_path / "doctor-installed"
    target.mkdir()
    initialize_project(target, source_root=REPO_ROOT)
    repair_report = target / AEGIS_REPAIR_REPORT_REL

    payload = doctor(target, source_root=REPO_ROOT)

    assert payload["read_only"] is True
    assert payload["current_state"] == "installed_no_current_work"
    assert payload["status"] == "healthy"
    assert payload["summary"]["failed_required"] == 0
    assert payload["repair_plan"]["available"] is False
    assert not repair_report.exists()


def test_repair_preview_is_read_only_and_apply_restores_safe_managed_file(tmp_path: Path) -> None:
    target = tmp_path / "repair-missing-shim"
    target.mkdir()
    initialize_project(target, source_root=REPO_ROOT)
    shim = target / ".aegis" / "bin" / "aegis"
    shim.unlink()

    preview = repair(target, source_root=REPO_ROOT)

    assert preview["read_only"] is True
    assert preview["status"] == "preview"
    assert preview["repair_plan"]["safe"] >= 1
    assert any(
        action["kind"] == "restore_managed_file" and action["path"] == ".aegis/bin/aegis"
        for action in preview["repair_plan"]["actions"]
    )
    assert not shim.exists()
    assert not (target / AEGIS_REPAIR_REPORT_REL).exists()

    applied = repair(target, source_root=REPO_ROOT, apply=True)

    assert applied["read_only"] is False
    assert applied["status"] == "applied"
    assert shim.is_file()
    assert os.access(shim, os.X_OK)
    assert (target / AEGIS_REPAIR_REPORT_REL).is_file()
    assert applied["postflight"]["summary"]["failed_required"] == 0


def test_repair_recreates_current_symlinks_and_does_not_delete_stale_active_folders(
    tmp_path: Path,
) -> None:
    target = tmp_path / "repair-current-links"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="pointer-repair", title="Pointer Repair")
    stale = target / "docs/ai/work-tracking/active/20990101-task99-stale-ACTIVE"
    stale.mkdir(parents=True)
    (target / "sessions/current").unlink()
    (target / "plans/current").unlink()

    diagnosis = doctor(target, source_root=REPO_ROOT)
    preview = repair(target, source_root=REPO_ROOT)

    assert diagnosis["status"] == "repairable"
    assert any(action["kind"] == "recreate_symlink" for action in preview["repair_plan"]["actions"])
    assert any(check["id"] == "workflow.stale_active_folders" for check in diagnosis["checks"])
    assert stale.is_dir()

    applied = repair(target, source_root=REPO_ROOT, apply=True)

    assert applied["status"] == "applied"
    assert (target / "sessions/current").is_symlink()
    assert (target / "plans/current").is_symlink()
    assert stale.is_dir()


def test_repair_normalizes_malformed_current_plan_table(tmp_path: Path) -> None:
    target = tmp_path / "repair-plan-table"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="plan-table-repair", title="Plan Table Repair")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    plan_path = target / current_work["paths"]["plan"]
    plan_lines = plan_path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(plan_lines):
        if line.startswith("| plan-step-scope |"):
            plan_lines[index] = line.replace(
                " | in-progress |",
                "; cmd`python - <<'PY'\nprint('scope | evidence')\nPY` | completed |",
            )
        if line.startswith("| plan-step-verify |"):
            plan_lines[index] = line.replace(
                " | pending |",
                "; cmd`pytest -q\nuv run | tee verification.txt` | completed |",
            )
    plan_path.write_text("\n".join(plan_lines).rstrip() + "\n", encoding="utf-8")

    diagnosis = doctor(target, source_root=REPO_ROOT)
    preview = repair(target, source_root=REPO_ROOT)

    assert diagnosis["status"] == "repairable"
    assert any(
        check["id"] == "workflow.plan_table" and check["status"] == "fail"
        for check in diagnosis["checks"]
    )
    assert any(
        action["kind"] == "normalize_plan_table" and action["path"] == current_work["paths"]["plan"]
        for action in preview["repair_plan"]["actions"]
    )
    assert "print('scope | evidence')" in plan_path.read_text(encoding="utf-8")

    applied = repair(target, source_root=REPO_ROOT, apply=True)

    assert applied["status"] == "applied"
    assert any(
        item["id"] == "workflow.normalize_plan_table" and item["status"] == "applied"
        for item in applied["applied"]
    )
    repaired_text = plan_path.read_text(encoding="utf-8")
    assert "scope &#124; evidence" in repaired_text
    assert "uv run &#124; tee verification.txt" in repaired_text
    assert "print('scope | evidence')" not in repaired_text
    rows = aegis_installer._parse_plan_rows(plan_path)
    assert rows["plan-step-scope"]["malformed"] is False
    assert rows["plan-step-scope"]["status"] == "completed"
    assert rows["plan-step-verify"]["malformed"] is False
    assert rows["plan-step-verify"]["status"] == "completed"
    assert doctor(target, source_root=REPO_ROOT)["status"] == "healthy"


def test_repair_apply_is_blocked_while_pending_tracking_exists(tmp_path: Path) -> None:
    target = tmp_path / "repair-pending"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="pending-repair", title="Pending Repair")
    pending_path = target / AEGIS_PENDING_TRACKING_REL
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    pending_path.write_text(
        json.dumps(
            {
                "events": [
                    {
                        "id": "abc123def456",
                        "handler": "claude:Write",
                        "evidence": "src/main.ts",
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    diagnosis = doctor(target, source_root=REPO_ROOT)
    applied = repair(target, source_root=REPO_ROOT, apply=True)

    assert diagnosis["current_state"] == "pending_tracking"
    assert applied["status"] == "blocked"
    assert applied["applied"] == []
    assert pending_path.exists()
    assert not (target / AEGIS_REPAIR_REPORT_REL).exists()


def test_public_start_allocates_local_task_without_taskmaster_or_serena(tmp_path: Path) -> None:
    target = tmp_path / "local-start"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    initialize_project(target, source_root=REPO_ROOT)
    next_before_start = next_action(target, source_root=REPO_ROOT)
    assert next_before_start["state"] == "client_reload_required"
    assert next_before_start["suggested_mcp_call"]["tool"] == "aegis.next"
    simulate_claude_reload(target)
    next_before_start = next_action(target, source_root=REPO_ROOT)
    assert next_before_start["state"] == "installed_no_current_work"
    assert next_before_start["suggested_mcp_call"]["tool"] == "aegis.start"
    assert next_before_start["suggested_mcp_call"]["arguments"]["apply"] is True

    bash_start_payload = {
        "tool_name": "Bash",
        "tool_input": {"command": './.aegis/bin/aegis start "Improve BrandMark accessibility"'},
    }
    mcp_start_payload = {
        "tool_name": "mcp__aegis__aegis_start",
        "tool_input": {
            "target_dir": target.as_posix(),
            "title": "Improve BrandMark accessibility",
            "apply": True,
        },
    }
    bash_start_gate = run_target_pretooluse(target, bash_start_payload)
    assert bash_start_gate.returncode == 0, bash_start_gate.stderr
    mcp_start_gate = run_target_pretooluse(target, mcp_start_payload)
    assert mcp_start_gate.returncode == 0, mcp_start_gate.stderr

    payload = start_local_work(
        target, title="Improve BrandMark accessibility", source_root=REPO_ROOT
    )

    assert payload["status"] == "started"
    assert payload["local_task"]["id"] == "1"
    assert payload["task"]["id"] == "1"
    assert payload["task"]["slug"] == "improve-brandmark-accessibility"
    assert payload["branch"]["current"] == "feat/task-1-improve-brandmark-accessibility"
    local_tasks = json.loads((target / AEGIS_LOCAL_TASKS_REL).read_text(encoding="utf-8"))
    assert local_tasks["next_id"] == 2
    assert local_tasks["tasks"][0]["source"] == "aegis-local"
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    assert current_work["task"]["source"] == "aegis-local"
    assert current_work["integrations"]["taskmaster"]["required"] is False
    assert current_work["integrations"]["taskmaster"]["detected"] is False
    assert current_work["integrations"]["serena"]["required"] is False
    assert current_work["integrations"]["serena"]["detected"] is False
    readiness = run_target_readiness(target)
    assert readiness.returncode == 0
    assert "READY | task=1" in readiness.stdout
    assert run_target_posttooluse(target, bash_start_payload).returncode == 0
    assert run_target_posttooluse(target, mcp_start_payload).returncode == 0
    assert not (target / AEGIS_PENDING_TRACKING_REL).exists()


def test_observation_mode_allows_pre_task_app_audit_without_task_branch(
    tmp_path: Path,
) -> None:
    target = tmp_path / "observe-taskmaster"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    write_taskmaster_tasks(
        target,
        [{"id": 18, "title": "Mock exam modes", "status": "pending"}],
    )
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)

    before = next_action(target, source_root=REPO_ROOT)
    assert before["state"] == "installed_taskmaster_present"
    assert any("observe start" in repair for repair in before["copyable_repairs"])

    observe_payload = {
        "tool_name": "Bash",
        "tool_input": {"command": './.aegis/bin/aegis observe start --target-dir . "Polish audit"'},
    }
    observe_gate = run_target_pretooluse(target, observe_payload)
    assert observe_gate.returncode == 0, observe_gate.stderr

    started = start_observation(target, title="Polish audit", source_root=REPO_ROOT)
    assert started["status"] == "started"
    assert started["mode"] == "observation"
    assert started["branch"]["current"] == "main"
    current_work = json.loads((target / AEGIS_CURRENT_WORK_REL).read_text(encoding="utf-8"))
    assert current_work["mode"] == "observation"
    assert current_work["branch"]["requires_task_id"] is False

    readiness = run_target_readiness(target)
    assert readiness.returncode == 0, readiness.stdout + readiness.stderr
    assert readiness.stdout.startswith("READY | task=obs-")

    dev_gate = run_target_pretooluse(target, {"tool_name": "Bash", "tool_input": {"command": "pnpm -C app dev"}})
    assert dev_gate.returncode == 0, dev_gate.stderr
    browser_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__playwright__browser_navigate",
            "tool_input": {"url": "http://localhost:5173"},
        },
    )
    assert browser_gate.returncode == 0, browser_gate.stderr
    chrome_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__chrome-devtools__take_screenshot",
            "tool_input": {},
        },
    )
    assert chrome_gate.returncode == 0, chrome_gate.stderr

    curl_stdout_gate = run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "curl http://localhost:5173/health"}},
    )
    assert curl_stdout_gate.returncode == 0, curl_stdout_gate.stderr
    wget_stdout_gate = run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "wget -O- http://localhost:5173/health"}},
    )
    assert wget_stdout_gate.returncode == 0, wget_stdout_gate.stderr
    curl_output_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "curl -o .claude/settings.json http://localhost:5173/health"},
        },
    )
    assert curl_output_gate.returncode == 2
    assert "observation mode only permits observation tooling" in curl_output_gate.stderr
    wget_file_gate = run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "wget http://localhost:5173/health"}},
    )
    assert wget_file_gate.returncode == 2
    assert "observation mode only permits observation tooling" in wget_file_gate.stderr

    edit_gate = run_target_pretooluse(
        target,
        {"tool_name": "Write", "tool_input": {"file_path": "app/src/routes/audit.tsx", "content": "x"}},
    )
    assert edit_gate.returncode == 2
    assert "observation mode only permits observation tooling" in edit_gate.stderr
    taskmaster_gate = run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": 'task-master add-task --title "Audit finding"'}},
    )
    assert taskmaster_gate.returncode == 2
    assert "observation mode only permits observation tooling" in taskmaster_gate.stderr

    post = run_target_posttooluse(target, {"tool_name": "Bash", "tool_input": {"command": "pnpm -C app dev"}})
    assert post.returncode == 0, post.stderr
    assert not (target / AEGIS_PENDING_TRACKING_REL).exists()

    stopped = stop_observation(target, summary="Observed app shell", source_root=REPO_ROOT)
    assert stopped["status"] == "completed"
    assert stopped["unexpected_changes"] == []
    diagnosis = doctor(target, source_root=REPO_ROOT)
    assert diagnosis["current_state"] == "observation_completed"
    assert diagnosis["status"] == "healthy"


def test_observation_stop_blocks_unexpected_delta_and_allow_dirty_overrides(
    tmp_path: Path,
) -> None:
    target = tmp_path / "observe-dirty"
    init_git_repo(target)
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    start_observation(target, title="Dirty audit", source_root=REPO_ROOT)

    (target / "src" / "audit.ts").parent.mkdir(parents=True, exist_ok=True)
    (target / "src" / "audit.ts").write_text("export const audit = true;\n", encoding="utf-8")
    blocked = stop_observation(target, summary="Unexpected source file", source_root=REPO_ROOT)
    assert blocked["status"] == "blocked"
    assert "?? src/audit.ts" in blocked["unexpected_changes"]

    completed = stop_observation(
        target,
        summary="Accepted dirty audit",
        allow_dirty=True,
        source_root=REPO_ROOT,
    )
    assert completed["status"] == "completed"
    assert "?? src/audit.ts" in completed["unexpected_changes"]


def test_observation_stop_blocks_tracked_and_ignored_deltas(tmp_path: Path) -> None:
    target = tmp_path / "observe-ignored"
    init_git_repo(target)
    (target / ".gitignore").write_text(".ignored/\n", encoding="utf-8")
    git(target, "add", ".gitignore")
    git(target, "commit", "-m", "ignore observation cache")
    ignored_file = target / ".ignored" / "cache.txt"
    ignored_file.parent.mkdir(parents=True, exist_ok=True)
    ignored_file.write_text("before\n", encoding="utf-8")

    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)
    start_observation(target, title="Ignored audit", source_root=REPO_ROOT)

    (target / "README.md").write_text("# target\nchanged\n", encoding="utf-8")
    ignored_file.write_text("after\n", encoding="utf-8")
    blocked = stop_observation(target, summary="Unexpected edits", source_root=REPO_ROOT)

    assert blocked["status"] == "blocked"
    assert " M README.md" in blocked["unexpected_changes"]
    assert any(
        entry.startswith("changed status-visible path: .ignored")
        for entry in blocked["unexpected_changes"]
    )


def test_start_local_work_replay_is_noop_and_different_work_is_refused(tmp_path: Path) -> None:
    target = tmp_path / "local-start-replay"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    initialize_project(target, source_root=REPO_ROOT)
    simulate_claude_reload(target)

    first = start_local_work(target, title="Improve BrandMark accessibility", source_root=REPO_ROOT)
    replay = start_local_work(
        target, title="Improve BrandMark accessibility", source_root=REPO_ROOT
    )

    assert replay["status"] == "already_started"
    assert replay["idempotent"] is True
    assert replay["task"]["id"] == first["task"]["id"]
    assert replay["paths"] == first["paths"]
    local_tasks = json.loads((target / AEGIS_LOCAL_TASKS_REL).read_text(encoding="utf-8"))
    assert local_tasks["next_id"] == 2
    assert len(local_tasks["tasks"]) == 1

    with pytest.raises(AegisError, match="current work is already in progress"):
        start_local_work(target, title="Add checkout screen", source_root=REPO_ROOT)


def test_plan_install_is_dry_run_and_schema_valid(tmp_path: Path) -> None:
    target = tmp_path / "empty-repo"
    target.mkdir()

    payload = plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
    )

    validate_schema("install-plan.schema.json", payload)
    assert payload["mode"] == "dry_run"
    assert payload["apply_confirmed"] is False
    assert payload["summary"]["creates"] > 0
    assert payload["summary"]["manual_reviews"] == 0
    assert not (target / ".aegis").exists()


def test_install_verify_and_second_plan_are_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "empty-repo"
    target.mkdir()

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    assert report["status"] == "applied"
    assert (target / AEGIS_MANIFEST_REL).exists()
    assert (target / ".aegis" / "contract.md").exists()
    assert (target / "AGENTS.md").exists()
    assert (target / "CLAUDE.md").exists()
    assert (target / ".claude" / "settings.json").exists()
    assert (target / ".claude" / "scripts" / "gate_lib.py").exists()
    assert (target / ".claude" / "scripts" / "readiness.sh").exists()
    assert (target / "schemas" / "aegis" / "foundation-manifest.schema.json").exists()

    manifest = json.loads((target / AEGIS_MANIFEST_REL).read_text(encoding="utf-8"))
    validate_schema("foundation-manifest.schema.json", manifest)
    assert manifest["primary_agent"] == "claude"
    assert manifest["agents"]["claude"]["enabled"] is True
    assert {gate["id"] for gate in manifest["gates"] if gate["required"]} >= {
        "claude.readiness",
        "claude.pretooluse",
        "claude.posttooluse_tracking",
        "claude.stop_tracking",
        "claude.bash_command",
        "claude.protected_path",
    }

    verification = verify(target, source_root=REPO_ROOT)
    assert verification["status"] == "passed"
    assert verification["mode"] == "standard"
    assert verification["summary"]["failed_required"] == 0
    assert (target / ".aegis" / "reports" / "verification-report.json").exists()

    second_plan = plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
    )
    assert second_plan["summary"]["creates"] == 0
    assert second_plan["summary"]["manual_reviews"] == 0
    assert second_plan["summary"]["conflicts"] == 0
    assert {operation["classification"] for operation in second_plan["operations"]} == {"skip"}


def test_install_uses_runtime_dispatchers_and_update_without_reinstall(tmp_path: Path) -> None:
    target = tmp_path / "runtime-update-target"
    target.mkdir()
    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert report["status"] == "applied"

    pretooluse = (target / ".claude" / "scripts" / "pretooluse-gate.sh").read_text(encoding="utf-8")
    readiness = (target / ".claude" / "scripts" / "readiness.sh").read_text(encoding="utf-8")
    assert 'exec "$AEGIS_BIN" hook pretooluse "$@"' in pretooluse
    assert 'exec "$AEGIS_BIN" hook readiness "$@"' in readiness
    assert (target / AEGIS_RUNTIME_ENV_REL).read_text(encoding="utf-8") == (
        "# Aegis runtime pointer. Managed by aegis runtime update.\n"
        f"AEGIS_SOURCE_ROOT={REPO_ROOT.resolve().as_posix()}\n"
    )

    manifest = json.loads((target / AEGIS_MANIFEST_REL).read_text(encoding="utf-8"))
    validate_schema("foundation-manifest.schema.json", manifest)
    assert manifest["runtime"]["source_root"] == REPO_ROOT.resolve().as_posix()
    assert manifest["runtime"]["pointer"] == AEGIS_RUNTIME_ENV_REL
    assert {item["path"] for item in manifest["managed_files"]} >= {AEGIS_RUNTIME_ENV_REL}

    bootstrap_before = {
        rel: (target / rel).read_text(encoding="utf-8")
        for rel in (
            ".aegis/bin/aegis",
            ".claude/settings.json",
            ".claude/scripts/pretooluse-gate.sh",
            ".claude/scripts/readiness.sh",
        )
    }
    preview = runtime_update(target, source_root=REPO_ROOT, apply=False)
    assert preview["status"] == "preview"
    assert preview["reinstall_required"] is False
    assert bootstrap_before == {
        rel: (target / rel).read_text(encoding="utf-8") for rel in bootstrap_before
    }

    applied = runtime_update(target, source_root=REPO_ROOT, apply=True)
    assert applied["status"] == "applied"
    assert applied["reinstall_required"] is False
    assert bootstrap_before == {
        rel: (target / rel).read_text(encoding="utf-8") for rel in bootstrap_before
    }
    runtime = runtime_status(target, source_root=REPO_ROOT)
    assert runtime["status"] == "installed"
    assert runtime["runtime_env_present"] is True
    assert runtime["active_source_root"] == REPO_ROOT.resolve().as_posix()
    assert runtime["active_source_valid"] is True

    second_plan = plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
    )
    assert {operation["classification"] for operation in second_plan["operations"]} == {"skip"}


def test_install_upgrades_existing_manifest_owned_bootstrap_files(tmp_path: Path) -> None:
    target = tmp_path / "managed-upgrade-target"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    stale_paths = [
        ".aegis/bin/aegis",
        ".claude/scripts/pretooluse-gate.sh",
        ".claude/scripts/gate_lib.py",
        "schemas/aegis/foundation-manifest.schema.json",
    ]
    for rel_path in stale_paths:
        path = target / rel_path
        path.write_text("# old Aegis-managed bootstrap content\n", encoding="utf-8")

    plan = plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
    )
    operations = {operation["path"]: operation for operation in plan["operations"]}

    assert plan["summary"]["manual_reviews"] == 0
    for rel_path in stale_paths:
        assert operations[rel_path]["classification"] == "modify"
        assert operations[rel_path]["safe_to_apply"] is True
        assert operations[rel_path]["managed"] is True

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert report["status"] == "applied"
    assert 'exec "$AEGIS_BIN" hook pretooluse "$@"' in (
        target / ".claude" / "scripts" / "pretooluse-gate.sh"
    ).read_text(encoding="utf-8")


def test_install_refuses_to_overwrite_customized_bootstrap_files(tmp_path: Path) -> None:
    target = tmp_path / "customized-upgrade-target"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    customized_path = ".claude/scripts/pretooluse-gate.sh"
    (target / customized_path).write_text("# user customized hook\n", encoding="utf-8")
    manifest_path = target / AEGIS_MANIFEST_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["customized_files"] = [{"path": customized_path, "kind": "adapter"}]
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    plan = plan_install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
    )
    operations = {operation["path"]: operation for operation in plan["operations"]}

    assert operations[customized_path]["classification"] == "manual-review"
    assert operations[customized_path]["safe_to_apply"] is False
    assert plan["summary"]["manual_reviews"] == 1


def test_next_action_guides_not_installed_and_installed_states(tmp_path: Path) -> None:
    target = tmp_path / "guided-repo"
    target.mkdir()

    initial = next_action(target, source_root=REPO_ROOT)
    assert initial["read_only"] is True
    assert initial["phase"] == "bootstrap"
    assert initial["state"] == "not_installed"
    assert initial["suggested_mcp_call"]["tool"] == "aegis.init"
    assert initial["suggested_mcp_call"]["arguments"]["apply"] is True
    assert initial["details"]["must_initialize_before_source_edits"] is True
    assert "source edits" in initial["details"]["forbidden_until_init"]
    assert "Taskmaster mutations" in initial["details"]["forbidden_until_init"]
    assert "aegis.inspect" in initial["details"]["allowed_until_init"]

    install_report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert install_report["status"] == "applied"

    installed = next_action(target, source_root=REPO_ROOT)
    assert installed["phase"] == "bootstrap"
    assert installed["state"] == "client_reload_required"
    assert installed["suggested_mcp_call"]["tool"] == "aegis.next"

    simulate_claude_reload(target)
    installed = next_action(target, source_root=REPO_ROOT)
    assert installed["phase"] == "start"
    assert installed["state"] == "installed_no_current_work"
    assert installed["suggested_mcp_call"]["tool"] == "aegis.start"
    assert installed["suggested_mcp_call"]["arguments"]["apply"] is True


def test_next_action_defers_task_selection_to_taskmaster_when_tasks_json_is_present(
    tmp_path: Path,
) -> None:
    target = tmp_path / "guided-taskmaster-repo"
    target.mkdir()
    write_taskmaster_tasks(
        target,
        [
            {
                "id": 6,
                "title": "Heuristic would pick this first",
                "description": "Aegis must not present this as the next task.",
                "status": "pending",
                "priority": "medium",
                "dependencies": [],
                "subtasks": [],
            },
            {
                "id": 31,
                "title": "Prerequisite",
                "status": "done",
                "dependencies": [],
                "subtasks": [],
            },
            {
                "id": 32,
                "title": "Taskmaster CLI may choose this instead",
                "description": "Only Taskmaster is allowed to decide that.",
                "status": "pending",
                "priority": "high",
                "dependencies": [31],
                "subtasks": [],
            },
        ],
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)

    guided = next_action(target, source_root=REPO_ROOT)

    assert guided["phase"] == "start"
    assert guided["state"] == "installed_taskmaster_present"
    assert "Taskmaster" in guided["next_required_action"]
    assert guided["suggested_mcp_call"] is None
    assert "task-master next" in guided["suggested_cli"]
    assert "--task <id>" in guided["suggested_cli"]
    assert "--task 6" not in guided["suggested_cli"]
    assert "--task 32" not in guided["suggested_cli"]
    repairs = "\n".join(guided["copyable_repairs"])
    assert "task-master next" in repairs
    assert "task-master show <id>" in repairs
    assert "aegis kickoff --target-dir . --task <id>" in repairs
    assert "aegis start '<task title>'" not in repairs
    taskmaster = guided["details"]["taskmaster"]
    assert taskmaster["source"] == ".taskmaster/tasks/tasks.json"
    assert taskmaster["state"] == "valid"
    assert taskmaster["present"] is True
    assert taskmaster["valid"] is True
    assert taskmaster["task_count"] == 3
    assert taskmaster["task_selection_authority"] == "taskmaster"
    assert taskmaster["aegis_task_selection"] == "suppressed"
    assert taskmaster["kickoff_requires_explicit_taskmaster_id"] is True
    assert taskmaster["local_fallback_allowed"] is False
    assert "task" not in taskmaster
    assert guided["details"]["taskmaster"]["ordering"] == [
        "task-master next/show",
        "aegis.kickoff",
        "native source edit",
        "aegis.verify",
        "aegis.closeout",
        "aegis.doctor",
        "task-master set-status --status=done",
    ]
    claude_entry = (target / "CLAUDE.md").read_text(encoding="utf-8")
    assert "task-master next" in claude_entry
    assert "task-master show <id>" in claude_entry
    assert "Taskmaster done only after Aegis closeout and doctor pass" in claude_entry

    for report in (
        inspect_project(target, source_root=REPO_ROOT),
        status(target, source_root=REPO_ROOT),
        doctor(target, source_root=REPO_ROOT),
    ):
        guidance = report["workflow_guidance"] if "workflow_guidance" in report else report["next_action"]
        assert guidance["state"] == "installed_taskmaster_present"
        assert guidance["details"]["taskmaster"]["aegis_task_selection"] == "suppressed"
        assert "task" not in guidance["details"]["taskmaster"]
    assert "task-master generate" in claude_entry
    claude_settings = json.loads((target / ".claude" / "settings.json").read_text(encoding="utf-8"))
    allowed = claude_settings["permissions"]["allow"]
    assert "Bash(task-master *)" in allowed


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        ("{not json\n", "json_decode_error"),
        ([], "non_object_payload"),
        ({}, "missing_task_container"),
        ({"master": {"tasks": []}}, "empty_taskmaster_tasks"),
        ({"master": {"tasks": {}}}, "malformed_task_container"),
        ({"master": {"tasks": ["not-an-object"]}}, "malformed_task"),
        (
            {"master": {"tasks": [{"id": "abc", "title": "Bad", "status": "pending"}]}},
            "invalid_task_id",
        ),
        (
            {"master": {"tasks": [{"id": 42, "title": "Bad", "status": 7}]}},
            "invalid_task_status",
        ),
        (
            {
                "master": {
                    "tasks": [
                        {
                            "id": 42,
                            "title": "Bad",
                            "status": "pending",
                            "dependencies": "1",
                        }
                    ]
                }
            },
            "invalid_task_dependencies",
        ),
        (
            {
                "master": {
                    "tasks": [
                        {
                            "id": 42,
                            "title": "Bad",
                            "status": "pending",
                            "dependencies": ["x"],
                        }
                    ]
                }
            },
            "invalid_task_dependency",
        ),
    ],
)
def test_taskmaster_present_invalid_blocks_task_selection_across_surfaces(
    tmp_path: Path, payload: object | str, reason: str
) -> None:
    target = tmp_path / f"invalid-taskmaster-{reason}"
    init_git_repo(target)
    write_taskmaster_payload(target, payload)
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)

    guided = next_action(target, source_root=REPO_ROOT)

    assert guided["phase"] == "start"
    assert guided["state"] == "installed_taskmaster_invalid"
    assert guided["suggested_mcp_call"] is None
    assert "aegis start" not in guided["suggested_cli"]
    assert "aegis kickoff" not in guided["suggested_cli"]
    assert "taskmaster.tasks_json_valid" in guided["missing_gates"]
    taskmaster = guided["details"]["taskmaster"]
    assert taskmaster["source"] == ".taskmaster/tasks/tasks.json"
    assert taskmaster["state"] == "invalid"
    assert taskmaster["present"] is True
    assert taskmaster["valid"] is False
    assert taskmaster["reason"] == reason
    assert taskmaster["task_selection_authority"] == "taskmaster"
    assert taskmaster["aegis_task_selection"] == "suppressed"
    assert taskmaster["local_fallback_allowed"] is False
    assert "task" not in taskmaster
    repairs = "\n".join(guided["copyable_repairs"])
    assert "taskmaster health" in repairs
    assert "task-master validate-dependencies" in repairs

    for report in (
        inspect_project(target, source_root=REPO_ROOT),
        status(target, source_root=REPO_ROOT),
        doctor(target, source_root=REPO_ROOT),
    ):
        guidance = report["workflow_guidance"] if "workflow_guidance" in report else report["next_action"]
        assert guidance["state"] == "installed_taskmaster_invalid"
        assert guidance["details"]["taskmaster"]["reason"] == reason
        assert "task" not in guidance["details"]["taskmaster"]

    with pytest.raises(AegisError, match="Taskmaster task state is present but invalid"):
        start_local_work(target, title="Local fallback must not happen", source_root=REPO_ROOT)

    tree_before = snapshot_whole_tree(target)
    reconcile_report = reconcile(target, source_root=REPO_ROOT, base_ref="main", use_github=False)

    assert_reconcile_preserved_whole_tree(target, tree_before)
    assert reconcile_report["read_only"] is True
    assert reconcile_report["taskmaster"]["state"] == "invalid"
    assert reconcile_report["taskmaster"]["present"] is True
    assert reconcile_report["taskmaster"]["valid"] is False
    assert reconcile_report["taskmaster"]["reason"] == reason
    assert reconcile_report["taskmaster"]["available"] is False
    assert reconcile_report["summary"]["findings"] == 1
    assert reconcile_report["findings"][0]["kind"] == "taskmaster_invalid"
    assert reconcile_report["findings"][0]["evidence"]["reason"] == reason
    assert not (target / AEGIS_LOCAL_TASKS_REL).exists()
    assert not (target / AEGIS_CURRENT_WORK_REL).exists()


@pytest.mark.skipif(
    hasattr(os, "geteuid") and os.geteuid() == 0,
    reason="root can read chmod 000 files, so unreadable-file behavior is not observable",
)
def test_taskmaster_present_unreadable_blocks_task_selection(tmp_path: Path) -> None:
    target = tmp_path / "unreadable-taskmaster"
    init_git_repo(target)
    write_taskmaster_tasks(
        target,
        [{"id": 42, "title": "Unreadable", "status": "pending", "dependencies": []}],
    )
    tasks_path = target / ".taskmaster" / "tasks" / "tasks.json"
    tasks_path.chmod(0)
    try:
        install(
            target,
            source_root=REPO_ROOT,
            primary_agent="claude",
            agents=["claude"],
            apply=True,
        )
        simulate_claude_reload(target)

        guided = next_action(target, source_root=REPO_ROOT)

        assert guided["state"] == "installed_taskmaster_invalid"
        assert guided["details"]["taskmaster"]["reason"] == "unreadable"
        assert "task" not in guided["details"]["taskmaster"]
    finally:
        tasks_path.chmod(0o644)


def test_install_report_flags_claude_reload_when_adapter_hooks_change(tmp_path: Path) -> None:
    target = tmp_path / "claude-reload-required"
    target.mkdir()

    install_report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    assert install_report["status"] == "applied"
    reload_guidance = install_report["client_reload"]
    assert reload_guidance["required"] is True
    assert reload_guidance["agent"] == "claude"
    assert ".claude/settings.json" in reload_guidance["changed_paths"]
    assert any(path.startswith(".claude/scripts/") for path in reload_guidance["changed_paths"])
    assert "restart Claude" in reload_guidance["instructions"]
    assert (target / AEGIS_CLIENT_RELOAD_REL).is_file()

    second = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    assert second["status"] == "applied"
    assert second["client_reload"]["required"] is True
    assert second["client_reload"]["pending_marker"] is True
    assert second["client_reload"]["changed_paths"] == reload_guidance["changed_paths"]

    hook_probe = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__aegis__aegis_next",
            "tool_input": {"target_dir": target.as_posix()},
        },
    )
    assert hook_probe.returncode == 0, hook_probe.stderr
    assert not (target / AEGIS_CLIENT_RELOAD_REL).exists()

    third = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    assert third["status"] == "applied"
    assert third["client_reload"]["required"] is False
    assert third["client_reload"]["changed_paths"] == []


def test_installed_pretooluse_blocks_unclassifiable_payload(tmp_path: Path) -> None:
    target = tmp_path / "unclassifiable-pretooluse"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    malformed = run_target_pretooluse_raw(target, '{"tool_name": "Write",')
    missing_tool_name = run_target_pretooluse_raw(
        target, '{"tool_input": {"file_path": "src/main.ts"}}'
    )

    assert malformed.returncode == 2
    assert "could not be parsed or classified safely" in malformed.stderr
    assert "invalid JSON" in malformed.stderr
    assert missing_tool_name.returncode == 2
    assert "missing required field 'tool_name'" in missing_tool_name.stderr
    assert (target / AEGIS_CLIENT_RELOAD_REL).is_file()


def test_installed_pretooluse_short_circuits_read_only_before_readiness(tmp_path: Path) -> None:
    target = tmp_path / "read-only-without-readiness"
    target.mkdir()
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    (target / ".claude" / "scripts" / "readiness.sh").unlink()

    read_only = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git status --short"},
        },
    )
    mutating = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "npm run build"},
        },
    )

    assert read_only.returncode == 0, read_only.stderr
    assert mutating.returncode == 2
    assert "readiness is BLOCKED" in mutating.stderr


def test_installed_pretooluse_blocks_direct_workflow_edits_but_allows_aegis_handlers(
    tmp_path: Path,
) -> None:
    target = tmp_path / "workflow-surface-protection"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="42",
        slug="protect-workflow-surfaces",
        title="Protect Workflow Surfaces",
        source_root=REPO_ROOT,
    )

    current_work = json.loads((target / AEGIS_CURRENT_WORK_REL).read_text(encoding="utf-8"))
    handoff_rel = f"{current_work['paths']['work_tracking']}/HANDOFF.md"
    findings_rel = f"{current_work['paths']['work_tracking']}/FINDINGS.md"

    direct_write = run_target_pretooluse(
        target,
        {"tool_name": "Write", "tool_input": {"file_path": handoff_rel}},
    )
    bash_redirect = run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "printf forged > sessions/current"}},
    )
    mcp_direct = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__serena__create_text_file",
            "tool_input": {"relative_path": handoff_rel},
        },
    )
    aegis_cli_log = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {
                "command": (
                    f"./.aegis/bin/aegis log --target-dir . --handler test --evidence {findings_rel} "
                    "--note 'structured evidence'"
                )
            },
        },
    )
    aegis_mcp_log = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__aegis__aegis_log",
            "tool_input": {
                "target_dir": target.as_posix(),
                "path": findings_rel,
                "note": "structured evidence",
            },
        },
    )

    assert direct_write.returncode == 2
    assert "Workflow-owned path" in direct_write.stderr
    assert handoff_rel in direct_write.stderr
    assert bash_redirect.returncode == 2
    assert "redirection targets workflow-owned path sessions/current" in bash_redirect.stderr
    assert mcp_direct.returncode == 2
    assert "Workflow-owned path" in mcp_direct.stderr
    assert aegis_cli_log.returncode == 0, aegis_cli_log.stderr
    assert aegis_mcp_log.returncode == 0, aegis_mcp_log.stderr


def test_start_and_kickoff_are_blocked_until_claude_reload_hook_runs(tmp_path: Path) -> None:
    target = tmp_path / "reload-barrier"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    install_report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    assert install_report["client_reload"]["required"] is True
    assert (target / AEGIS_CLIENT_RELOAD_REL).is_file()
    guided = next_action(target, source_root=REPO_ROOT)
    assert guided["state"] == "client_reload_required"
    assert guided["suggested_mcp_call"]["tool"] == "aegis.next"

    with pytest.raises(AegisError, match="restart Claude"):
        start_local_work(target, title="Improve BrandMark accessibility", source_root=REPO_ROOT)
    with pytest.raises(AegisError, match="restart Claude"):
        kickoff(
            target,
            task_id="42",
            slug="add-to-cart-button",
            title="Add visible Add to cart button",
            source_root=REPO_ROOT,
        )

    hook_probe = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__aegis__aegis_next",
            "tool_input": {"target_dir": target.as_posix()},
        },
    )
    assert hook_probe.returncode == 0, hook_probe.stderr
    assert not (target / AEGIS_CLIENT_RELOAD_REL).exists()

    kickoff_report = kickoff(
        target,
        task_id="42",
        slug="add-to-cart-button",
        title="Add visible Add to cart button",
        source_root=REPO_ROOT,
    )

    assert kickoff_report["status"] == "started"
    assert kickoff_report["task"]["id"] == "42"


def test_codex_primary_guidance_uses_explicit_agent_logs_and_normalized_task_slug(
    tmp_path: Path,
) -> None:
    target = tmp_path / "codex-guided-workflow"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    (target / "src").mkdir()
    (target / "src" / "main.ts").write_text("export const ready = true;\n", encoding="utf-8")
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )

    kickoff_report = kickoff(
        target,
        task_id="42",
        slug="task-42-add-visible-add-to-cart-button",
        title="Add visible Add to cart button",
        source_root=REPO_ROOT,
    )

    assert kickoff_report["task"]["slug"] == "add-visible-add-to-cart-button"
    assert kickoff_report["branch"]["current"] == "feat/task-42-add-visible-add-to-cart-button"
    assert kickoff_report["next_action"]["suggested_mcp"]["arguments"]["handler"] == "codex:scope"

    current_work = json.loads((target / AEGIS_CURRENT_WORK_REL).read_text(encoding="utf-8"))
    scope_required = next_action(target, source_root=REPO_ROOT)
    assert scope_required["suggested_mcp_call"]["arguments"]["handler"] == "codex:scope"

    scope_logged = log_work(
        target,
        handler="codex:scope",
        evidence=f"{current_work['paths']['work_tracking']}/FINDINGS.md",
        note="Confirmed Codex scope before implementation",
        event_class="scope",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    after_scope_args = scope_logged["next_action"]["suggested_mcp"]["arguments"]
    assert after_scope_args["handler"] == "codex:implementation"
    assert "pending_event_id" not in after_scope_args
    assert scope_logged["next_action"]["details"]["pending_tracking_expected"] is False

    implementation_logged = log_work(
        target,
        handler="codex:implementation",
        evidence="src/main.ts",
        note="Recorded Codex implementation evidence",
        event_class="implementation",
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    after_implementation_args = implementation_logged["next_action"]["suggested_mcp"]["arguments"]
    assert after_implementation_args["handler"] == "codex:verification"
    assert after_implementation_args["evidence"].endswith("/task-verification.md")
    assert "pending_event_id" not in after_implementation_args

    verify_required = next_action(target, source_root=REPO_ROOT)
    assert verify_required["suggested_mcp_call"]["arguments"]["handler"] == "codex:verification"
    assert "pending_event_id" not in verify_required["suggested_mcp_call"]["arguments"]
    assert verify_required["details"]["pending_tracking_expected"] is False

    strict_report = verify(target, source_root=REPO_ROOT, strict=True)
    strict_args = strict_report["next_action"]["suggested_mcp"]["arguments"]
    assert strict_args["handler"] == "codex:verification"
    assert strict_args["evidence"] == AEGIS_VERIFY_REPORT_REL
    assert "pending_event_id" not in strict_args
    assert strict_report["next_action"]["details"]["pending_tracking_expected"] is False


def test_start_local_work_refuses_to_bypass_present_taskmaster(tmp_path: Path) -> None:
    target = tmp_path / "taskmaster-start-refusal"
    target.mkdir()
    taskmaster_tasks = target / ".taskmaster" / "tasks"
    taskmaster_tasks.mkdir(parents=True)
    (taskmaster_tasks / "tasks.json").write_text(
        json.dumps(
            {
                "master": {
                    "tasks": [
                        {
                            "id": 42,
                            "title": "Add visible Add to cart button",
                            "status": "pending",
                            "dependencies": [],
                            "subtasks": [],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)

    with pytest.raises(AegisError, match="Taskmaster is present"):
        start_local_work(target, title="Add visible Add to cart button", source_root=REPO_ROOT)

    assert not (target / AEGIS_LOCAL_TASKS_REL).exists()
    assert not (target / AEGIS_CURRENT_WORK_REL).exists()


def test_installed_gate_allows_taskmaster_completion_after_closeout(tmp_path: Path) -> None:
    target = tmp_path / "post-closeout-taskmaster"
    target.mkdir()
    taskmaster_tasks = target / ".taskmaster" / "tasks"
    taskmaster_tasks.mkdir(parents=True)
    (taskmaster_tasks / "tasks.json").write_text(
        json.dumps(
            {
                "master": {
                    "tasks": [
                        {
                            "id": 42,
                            "title": "Add visible Add to cart button",
                            "status": "pending",
                            "dependencies": [],
                            "subtasks": [],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="42",
        slug="add-visible-add-to-cart-button",
        title="Add visible Add to cart button",
        source_root=REPO_ROOT,
    )
    current_work_path = target / AEGIS_CURRENT_WORK_REL
    current_work = json.loads(current_work_path.read_text(encoding="utf-8"))
    current_work["status"] = "completed"
    current_work["closeout_passed_at"] = "2026-05-30T15:48:41Z"
    current_work["task"]["status"] = "completed"
    current_work_path.write_text(json.dumps(current_work, indent=2) + "\n", encoding="utf-8")

    done_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "task-master set-status --id=42 --status=done"},
        },
    )
    assert done_gate.returncode == 0, done_gate.stderr
    done_posttool = run_target_posttooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "task-master set-status --id=42 --status=done"},
        },
    )
    assert done_posttool.returncode == 0, done_posttool.stderr
    assert not (target / AEGIS_PENDING_TRACKING_REL).exists()

    generate_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "test -f scripts/codex-task; task-master generate"},
        },
    )
    assert generate_gate.returncode == 0, generate_gate.stderr

    wrong_task_gate = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "task-master set-status --id=99 --status=done"},
        },
    )
    assert wrong_task_gate.returncode == 2
    assert "readiness is BLOCKED" in wrong_task_gate.stderr

    source_edit_gate = run_target_pretooluse(
        target,
        {"tool_name": "Write", "tool_input": {"file_path": "src/main.ts"}},
    )
    assert source_edit_gate.returncode == 2
    assert "readiness is BLOCKED" in source_edit_gate.stderr


def test_public_init_requires_claude_reload_before_start_as_next_action(tmp_path: Path) -> None:
    target = tmp_path / "public-init-guided-repo"
    target.mkdir()

    initialized = initialize_project(target, source_root=REPO_ROOT)

    assert initialized["status"] == "initialized"
    assert initialized["install"]["client_reload"]["required"] is True
    assert initialized["next_action"]["action"] == "restart_claude_before_mutation"
    assert "restart Claude" in initialized["next_action"]["message"]
    assert initialized["next_action"]["suggested_mcp"]["tool"] == "aegis.next"
    assert initialized["next_action"]["details"]["client_reload_required"] is True
    assert ".claude/settings.json" in initialized["next_action"]["details"]["changed_paths"]
    assert (
        initialized["next_action"]["details"]["post_reload"]
        == "Run aegis.next, then start/kickoff tracked work before source edits."
    )


def test_next_action_guides_active_workflow_states(tmp_path: Path) -> None:
    target = tmp_path / "guided-workflow"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="42",
        slug="guided-task",
        title="Guided Task",
        goals=["Exercise next action guidance"],
    )
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )

    scope_required = next_action(target, source_root=REPO_ROOT)
    assert scope_required["phase"] == "scope"
    assert scope_required["state"] == "scope_required"
    assert scope_required["suggested_mcp_call"]["tool"] == "aegis.log"
    assert scope_required["suggested_mcp_call"]["arguments"]["plan_step"] == "auto"

    scope_logged = log_work(
        target,
        handler="claude:scope",
        evidence=f"{current_work['paths']['work_tracking']}/FINDINGS.md",
        note="Confirmed scope before implementation",
        event_class="scope",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    assert scope_logged["status"] == "logged"

    implement_required = next_action(target, source_root=REPO_ROOT)
    assert implement_required["phase"] == "implement"
    assert implement_required["state"] == "implementation_required"
    assert "native" in implement_required["architecture_notes"].lower()

    pending_payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": f"{current_work['paths']['reports']}/evidence.txt"},
    }
    evidence_file = target / current_work["paths"]["reports"] / "evidence.txt"
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    evidence_file.write_text("implementation evidence\n", encoding="utf-8")
    run_target_posttooluse(target, pending_payload)

    pending_required = next_action(target, source_root=REPO_ROOT)
    assert pending_required["phase"] == "track"
    assert pending_required["state"] == "pending_tracking"
    assert pending_required["suggested_mcp_call"]["arguments"]["pending_event_id"] == "current"

    implementation_logged = log_work(
        target,
        pending_event_id="current",
        note="Recorded implementation evidence",
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    assert implementation_logged["status"] == "logged"

    verify_required = next_action(target, source_root=REPO_ROOT)
    assert verify_required["phase"] == "verify"
    assert verify_required["state"] == "task_verification_required"

    verification_rel = f"{current_work['paths']['reports']}/task-verification.md"
    (target / verification_rel).write_text("verification passed\n", encoding="utf-8")
    log_work(
        target,
        handler="claude:verify",
        evidence=verification_rel,
        note="Recorded task verification evidence",
        event_class="verification",
        plan_step="plan-step-verify",
        plan_status="completed",
    )

    strict_required = next_action(target, source_root=REPO_ROOT)
    assert strict_required["state"] == "strict_verification_required"
    assert strict_required["suggested_mcp_call"]["tool"] == "aegis.verify"


def test_log_work_plan_step_auto_infers_scope_implementation_and_verify(tmp_path: Path) -> None:
    target = tmp_path / "auto-plan-step"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="42",
        slug="auto-step",
        title="Auto Step",
        goals=["Exercise deterministic plan step inference"],
    )
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )

    scope = log_work(
        target,
        handler="claude:scope",
        evidence=f"{current_work['paths']['work_tracking']}/FINDINGS.md",
        note="Confirmed scope before implementation",
        event_class="scope",
        plan_step="auto",
        plan_status="completed",
    )
    assert scope["plan"]["step"] == "plan-step-scope"
    assert scope["plan"]["inferred"] is True
    assert scope["plan"]["inference_reason"] == "event_class=scope"

    evidence_rel = f"{current_work['paths']['reports']}/implementation.txt"
    evidence_path = target / evidence_rel
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text("implementation evidence\n", encoding="utf-8")
    run_target_posttooluse(
        target,
        {"tool_name": "Write", "tool_input": {"file_path": evidence_rel}},
    )
    implementation = log_work(
        target,
        pending_event_id="current",
        note="Recorded implementation evidence",
        plan_step="auto",
        plan_status="completed",
    )
    assert implementation["plan"]["step"] == "plan-step-implement"
    assert implementation["plan"]["inferred"] is True
    assert implementation["plan"]["inference_reason"] == "event_class=implementation"

    verification_report = verify(target, source_root=REPO_ROOT, strict=True)
    assert verification_report["status"] == "passed"
    strict_log = log_work(
        target,
        handler="aegis:verify",
        evidence=AEGIS_VERIFY_REPORT_REL,
        note="Recorded strict verification evidence",
        plan_step="auto",
        plan_status="completed",
    )
    assert strict_log["plan"]["step"] == "plan-step-verify"
    assert strict_log["plan"]["inferred"] is True
    assert strict_log["plan"]["strict_verification_evidence"] is True


def test_log_work_plan_step_auto_does_not_infer_implementation_from_handler_text(
    tmp_path: Path,
) -> None:
    target = tmp_path / "auto-plan-step-no-handler-substring"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="42",
        slug="auto-step-neutral",
        title="Auto Step Neutral",
    )

    with pytest.raises(AegisError, match="plan-step auto could not infer"):
        log_work(
            target,
            handler="bash:jq-edit-output",
            evidence="docs/ai/work-tracking/active/example/reports/read-output.json",
            note="Read reconcile output without mutating source",
            plan_step="auto",
            plan_status="completed",
        )


def test_log_work_replay_does_not_duplicate_swhe_entries(tmp_path: Path) -> None:
    target = tmp_path / "log-replay"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="log-replay", title="Log Replay")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    evidence_rel = f"{current_work['paths']['work_tracking']}/FINDINGS.md"

    first = log_work(
        target,
        handler="claude:scope",
        evidence=evidence_rel,
        note="Confirmed scope before implementation",
        event_class="scope",
        plan_step="auto",
        plan_status="completed",
    )
    replay = log_work(
        target,
        handler="claude:scope",
        evidence=evidence_rel,
        note="Confirmed scope before implementation",
        event_class="scope",
        plan_step="auto",
        plan_status="completed",
    )

    assert first["status"] == "logged"
    assert replay["status"] == "already_logged"
    assert replay["idempotent"] is True
    swhe = f"[S:{first['entry']['s']}|W:{first['entry']['w']}|H:claude:scope|E:{evidence_rel}]"
    session_text = (target / current_work["paths"]["session"]).read_text(encoding="utf-8")
    tracker_text = (target / current_work["paths"]["work_tracking"] / "TRACKER.md").read_text(
        encoding="utf-8"
    )
    assert session_text.count(swhe) == 1
    assert tracker_text.count(swhe) == 1


def test_log_work_replay_can_backfill_missing_surfaces_without_duplicate_core_entries(
    tmp_path: Path,
) -> None:
    target = tmp_path / "log-replay-backfill"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="log-backfill", title="Log Backfill")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    evidence_rel = f"{current_work['paths']['reports']}/implementation.txt"
    (target / evidence_rel).parent.mkdir(parents=True, exist_ok=True)
    (target / evidence_rel).write_text("implementation\n", encoding="utf-8")

    first = log_work(
        target,
        handler="claude:Write",
        evidence=evidence_rel,
        note="Recorded implementation evidence",
        surfaces=["implementation"],
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    replay = log_work(
        target,
        handler="claude:Write",
        evidence=evidence_rel,
        note="Recorded implementation evidence",
        surfaces=["changelog"],
        plan_step="plan-step-implement",
        plan_status="completed",
    )

    assert first["status"] == "logged"
    assert replay["status"] == "logged"
    assert replay["replay_completed_missing_surfaces"] is True
    assert replay["paths"]["surfaces"] == {
        "changelog": f"{current_work['paths']['work_tracking']}/CHANGELOG.md"
    }
    swhe = f"[S:{first['entry']['s']}|W:{first['entry']['w']}|H:claude:Write|E:{evidence_rel}]"
    session_text = (target / current_work["paths"]["session"]).read_text(encoding="utf-8")
    tracker_text = (target / current_work["paths"]["work_tracking"] / "TRACKER.md").read_text(
        encoding="utf-8"
    )
    implementation_text = (
        target / current_work["paths"]["work_tracking"] / "IMPLEMENTATION.md"
    ).read_text(encoding="utf-8")
    changelog_text = (target / current_work["paths"]["work_tracking"] / "CHANGELOG.md").read_text(
        encoding="utf-8"
    )
    assert session_text.count(swhe) == 1
    assert tracker_text.count(swhe) == 1
    assert implementation_text.count(swhe) == 1
    assert changelog_text.count(swhe) == 1


def test_log_work_plan_step_auto_rejects_ambiguous_inference(tmp_path: Path) -> None:
    target = tmp_path / "ambiguous-auto-plan-step"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="42",
        slug="ambiguous-auto",
        title="Ambiguous Auto",
        goals=["Exercise ambiguous plan step inference"],
    )
    with pytest.raises(AegisError, match="plan-step auto is ambiguous"):
        log_work(
            target,
            handler="claude:scope",
            evidence=AEGIS_VERIFY_REPORT_REL,
            note="Attempted ambiguous auto plan step",
            plan_step="auto",
        )


def test_kickoff_creates_native_ready_state_without_taskmaster_or_serena(tmp_path: Path) -> None:
    target = tmp_path / "portable-repo"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert report["status"] == "applied"
    assert not (target / ".taskmaster").exists()
    assert not (target / ".serena").exists()

    blocked = run_target_readiness(target)
    assert blocked.returncode == 2
    assert "branch 'main' does not contain a task ID" in blocked.stdout

    blocked_verify = run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "aegis verify --target-dir ."}},
    )
    assert blocked_verify.returncode == 2
    assert "Claude readiness is BLOCKED" in blocked_verify.stderr

    blocked_mcp_verify = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__aegis__aegis_verify",
            "tool_input": {"target_dir": target.as_posix(), "strict": True},
        },
    )
    assert blocked_mcp_verify.returncode == 2
    assert "Claude readiness is BLOCKED" in blocked_mcp_verify.stderr

    bootstrap = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {
                "command": './.aegis/bin/aegis kickoff --task 1 --slug portable-smoke --title "Portable Smoke"'
            },
        },
    )
    assert bootstrap.returncode == 0, bootstrap.stderr

    start_bootstrap = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": './.aegis/bin/aegis start "Portable Smoke"'},
        },
    )
    assert start_bootstrap.returncode == 0, start_bootstrap.stderr

    mcp_start_bootstrap = run_target_pretooluse(
        target,
        {
            "tool_name": "mcp__aegis__aegis_start",
            "tool_input": {
                "target_dir": target.as_posix(),
                "title": "Portable Smoke",
                "apply": True,
            },
        },
    )
    assert mcp_start_bootstrap.returncode == 0, mcp_start_bootstrap.stderr

    kickoff_report = kickoff(
        target,
        task_id="1",
        slug="portable-smoke",
        title="Portable Smoke",
        goals=["Prove Aegis can reach READY without Taskmaster or Serena"],
    )
    assert kickoff_report["status"] == "started"
    assert kickoff_report["branch"]["current"] == "feat/task-1-portable-smoke"

    ready = run_target_readiness(target)
    assert ready.returncode == 0, ready.stdout + ready.stderr
    assert ready.stdout.strip().startswith("READY | task=1")
    assert (
        "Aegis current work Task 1 is in-progress"
        in subprocess.run(
            ["bash", str(target / ".claude" / "scripts" / "readiness.sh"), "--root", str(target)],
            cwd=target,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        ).stdout
    )

    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    assert current_work["task"]["id"] == "1"
    assert current_work["integrations"]["taskmaster"] == {"detected": False, "required": False}
    assert current_work["integrations"]["serena"] == {"detected": False, "required": False}
    assert (target / "sessions" / "current").is_symlink()
    assert (target / "plans" / "current").is_symlink()
    assert (target / ".aegis" / "bin" / "aegis").is_file()
    assert os.access(target / ".aegis" / "bin" / "aegis", os.X_OK)
    assert (target / current_work["paths"]["work_tracking"] / "TRACKER.md").is_file()

    evidence_path = "src/allowed-evidence.txt"
    allowed = run_target_pretooluse(
        target,
        {
            "tool_name": "Write",
            "tool_input": {"file_path": evidence_path},
        },
    )
    assert allowed.returncode == 0, allowed.stderr

    (target / evidence_path).parent.mkdir(parents=True, exist_ok=True)
    (target / evidence_path).write_text("allowed evidence\n", encoding="utf-8")
    tracked = run_target_posttooluse(
        target,
        {"tool_name": "Write", "tool_input": {"file_path": evidence_path}},
    )
    assert tracked.returncode == 0, tracked.stderr
    pending_payload = json.loads((target / AEGIS_PENDING_TRACKING_REL).read_text(encoding="utf-8"))
    pending_event = pending_payload["events"][0]
    assert pending_event["evidence_location"]["path"] == evidence_path
    assert pending_event["evidence_location"]["display"] == f"{evidence_path}:1"
    pending_next = run_target_pretooluse(
        target,
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "src/blocked-before-log.txt"},
        },
    )
    assert pending_next.returncode == 2
    assert "pending S:W:H:E tracking must be logged" in pending_next.stderr

    with pytest.raises(AegisError, match="does not match any pending S:W:H:E tracking event"):
        log_work(
            target,
            handler="claude-installer-test",
            evidence="src/wrong-evidence.txt",
            note="Tried to log the wrong evidence",
        )
    assert (target / AEGIS_PENDING_TRACKING_REL).is_file()

    logged = log_work(
        target,
        handler="claude-installer-test",
        evidence=evidence_path,
        note="Recorded installer test evidence",
        plan_step="plan-step-implement",
        plan_status="in-progress",
    )
    assert logged["status"] == "logged"
    assert logged["pending"]["cleared"] == 1
    assert logged["entry"]["evidence_location"]["display"] == f"{evidence_path}:1"
    session_text = (target / current_work["paths"]["session"]).read_text(encoding="utf-8")
    tracker_text = (target / current_work["paths"]["work_tracking"] / "TRACKER.md").read_text(
        encoding="utf-8"
    )
    plan_text = (target / current_work["paths"]["plan"]).read_text(encoding="utf-8")
    implementation_text = (
        target / current_work["paths"]["work_tracking"] / "IMPLEMENTATION.md"
    ).read_text(encoding="utf-8")
    changelog_text = (target / current_work["paths"]["work_tracking"] / "CHANGELOG.md").read_text(
        encoding="utf-8"
    )
    handoff_text = (target / current_work["paths"]["work_tracking"] / "HANDOFF.md").read_text(
        encoding="utf-8"
    )
    assert "|W:task1-portable-smoke|H:claude-installer-test|E:" in session_text
    assert "|W:task1-portable-smoke|H:claude-installer-test|E:" in tracker_text
    assert "|W:task1-portable-smoke|H:claude-installer-test|E:" in implementation_text
    assert "|W:task1-portable-smoke|H:claude-installer-test|E:" in changelog_text
    assert "|W:task1-portable-smoke|H:claude-installer-test|E:" in handoff_text
    assert (
        "| plan-step-implement | Make only task-scoped changes and record implementation notes |"
        in plan_text
    )
    assert f"; {evidence_path} | in-progress |" in plan_text
    assert logged["paths"]["surfaces"] == {
        "implementation": f"{current_work['paths']['work_tracking']}/IMPLEMENTATION.md",
        "changelog": f"{current_work['paths']['work_tracking']}/CHANGELOG.md",
        "handoff": f"{current_work['paths']['work_tracking']}/HANDOFF.md",
    }
    assert logged["plan"] == {
        "updated": True,
        "step": "plan-step-implement",
        "status": "in-progress",
        "evidence": evidence_path,
        "inferred": False,
        "inference_reason": None,
        "strict_verification_evidence": False,
    }

    generic_logged = log_work(
        target,
        handler="claude-note",
        evidence=f"{current_work['paths']['work_tracking']}/FINDINGS.md",
        note="Recorded generic workflow note without changing plan state",
        surfaces=["findings"],
    )
    assert generic_logged["status"] == "logged"
    assert generic_logged["plan"] == {
        "updated": False,
        "step": None,
        "status": None,
        "evidence": f"{current_work['paths']['work_tracking']}/FINDINGS.md",
        "inferred": False,
        "inference_reason": None,
        "strict_verification_evidence": False,
    }

    verify_loop_payload = {
        "tool_name": "Bash",
        "tool_input": {
            "command": (
                f"grep -q '{evidence_path}' sessions/current 2>/dev/null && "
                f"grep -q '{evidence_path}' plans/current 2>/dev/null"
            )
        },
    }
    read_only_verify = run_target_pretooluse(target, verify_loop_payload)
    assert read_only_verify.returncode == 0, read_only_verify.stderr
    tracked_verify = run_target_posttooluse(target, verify_loop_payload)
    assert tracked_verify.returncode == 0, tracked_verify.stderr
    assert not (target / AEGIS_PENDING_TRACKING_REL).exists()

    protected = run_target_pretooluse(
        target,
        {"tool_name": "Write", "tool_input": {"file_path": "CODEX.md"}},
    )
    assert protected.returncode == 2
    assert "Protected path(s):" in protected.stderr


def test_blocked_branch_deadlock_allows_pending_log_and_uninstall_recovery(tmp_path: Path) -> None:
    target = tmp_path / "blocked-branch-recovery"
    init_git_repo(target)
    install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="42",
        slug="blocked-recovery",
        title="Blocked Recovery",
        goals=["Exercise recovery from non-task branch deadlock"],
        source_root=REPO_ROOT,
    )

    git(target, "switch", "-c", "chore/taskmaster-ledger-reconciliation")
    post = run_target_posttooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git switch -c chore/taskmaster-ledger-reconciliation"},
        },
    )
    assert post.returncode == 0, post.stderr
    assert (target / AEGIS_PENDING_TRACKING_REL).is_file()

    blocked = run_target_readiness(target)
    assert blocked.returncode == 2
    assert "branch 'chore/taskmaster-ledger-reconciliation' does not contain a task ID" in blocked.stdout

    ordinary_write = run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "touch source.txt"}},
    )
    assert ordinary_write.returncode == 2
    assert "Claude readiness is BLOCKED" in ordinary_write.stderr

    blocked_verify = run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "./.aegis/bin/aegis verify --target-dir ."}},
    )
    assert blocked_verify.returncode == 2
    assert "Claude readiness is BLOCKED" in blocked_verify.stderr

    pending_log = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {
                "command": (
                    "./.aegis/bin/aegis log --target-dir . --pending-id current "
                    "--note 'Recorded non-task-branch recovery event' "
                    "--plan-step plan-step-emergency --plan-status completed"
                )
            },
        },
    )
    assert pending_log.returncode == 0, pending_log.stderr
    log_work(
        target,
        pending_event_id="current",
        note="Recorded non-task-branch recovery event",
        plan_step="plan-step-emergency",
        plan_status="completed",
    )
    assert not (target / AEGIS_PENDING_TRACKING_REL).exists()
    assert run_target_stop_gate(target).returncode == 0

    uninstall_preview = run_target_pretooluse(
        target,
        {"tool_name": "Bash", "tool_input": {"command": "./.aegis/bin/aegis uninstall --target-dir ."}},
    )
    assert uninstall_preview.returncode == 0, uninstall_preview.stderr

    uninstall_apply = run_target_pretooluse(
        target,
        {
            "tool_name": "Bash",
            "tool_input": {"command": "./.aegis/bin/aegis uninstall --target-dir . --apply"},
        },
    )
    assert uninstall_apply.returncode == 0, uninstall_apply.stderr
    report = uninstall(target, source_root=REPO_ROOT, apply=True)
    assert report["status"] == "applied"
    assert not (target / ".aegis").exists()
    assert not (target / ".claude" / "settings.json").exists()
    assert (target / ".claude" / "scripts" / "pretooluse-gate.sh").is_file()
    assert run_target_stop_gate(target).returncode == 0


def test_log_work_uses_event_aware_default_surfaces(tmp_path: Path) -> None:
    target = tmp_path / "event-aware-log-surfaces"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    started = kickoff(target, task_id="42", slug="surface-defaults", title="Surface Defaults")
    assert started["next_action"]["action"] == "log_scope_before_edit"
    assert started["next_action"]["suggested_mcp"]["tool"] == "aegis.log"
    assert started["next_action"]["suggested_mcp"]["arguments"]["plan_step"] == "auto"
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    current_work["branch"] = {
        "action": "created_branch",
        "before": "main",
        "created": True,
        "current": "feat/task-42-handoff-repair",
    }
    (target / ".aegis" / "state" / "current-work.json").write_text(
        json.dumps(current_work, indent=2) + "\n", encoding="utf-8"
    )
    work_rel = current_work["paths"]["work_tracking"]
    reports_rel = current_work["paths"]["reports"]
    implementation_evidence = f"{reports_rel}/implementation.txt"
    (target / implementation_evidence).write_text("implementation\n", encoding="utf-8")

    scope = log_work(
        target,
        handler="claude:scope",
        evidence=f"{work_rel}/FINDINGS.md",
        note="Confirmed event-aware logging scope",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    assert scope["entry"]["event_class"] == "scope"
    assert set(scope["paths"]["surfaces"]) == {"findings", "decisions", "handoff"}
    assert scope["next_action"]["action"] == "make_task_scoped_source_change"

    implementation = log_work(
        target,
        handler="claude:Write",
        evidence=implementation_evidence,
        note="Captured implementation evidence",
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    assert implementation["entry"]["event_class"] == "implementation"
    assert set(implementation["paths"]["surfaces"]) == {"implementation", "changelog", "handoff"}
    assert implementation["next_action"]["action"] == "run_task_specific_verification"

    verification = log_work(
        target,
        handler="aegis:verify",
        evidence=AEGIS_VERIFY_REPORT_REL,
        note="Recorded strict verification evidence",
        plan_step="plan-step-verify",
        plan_status="completed",
    )
    assert verification["entry"]["event_class"] == "verification"
    assert set(verification["paths"]["surfaces"]) == {"implementation", "changelog", "handoff"}
    assert verification["next_action"]["action"] == "run_closeout"

    explicit = log_work(
        target,
        handler="claude:scope",
        evidence=f"{work_rel}/DECISIONS.md",
        note="Recorded explicit surface override",
        surfaces=["decisions"],
    )
    assert explicit["entry"]["event_class"] == "scope"
    assert set(explicit["paths"]["surfaces"]) == {"decisions"}


def test_log_work_sanitizes_multiline_plan_table_evidence(tmp_path: Path) -> None:
    target = tmp_path / "multiline-plan-evidence"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="multiline-plan", title="Multiline Plan")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    plan_path = target / current_work["paths"]["plan"]

    scope_evidence = "cmd`python - <<'PY'\nprint('scope | evidence')\nPY`"
    scope = log_work(
        target,
        handler="claude:scope",
        evidence=scope_evidence,
        note="Recorded multiline scope evidence",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    assert scope["plan"]["evidence"] == scope_evidence
    plan_text = plan_path.read_text(encoding="utf-8")
    scope_row = next(line for line in plan_text.splitlines() if line.startswith("| plan-step-scope |"))
    assert scope_row.count("|") == 5
    assert "scope &#124; evidence" in scope_row
    assert "print('scope | evidence')" not in scope_row
    rows = aegis_installer._parse_plan_rows(plan_path)
    assert rows["plan-step-scope"]["malformed"] is False
    assert rows["plan-step-scope"]["status"] == "completed"

    verify_evidence = "cmd`pytest -q\nuv run | tee verification.txt`"
    verification = log_work(
        target,
        handler="aegis:verify",
        evidence=verify_evidence,
        note="Recorded multiline verification evidence",
        plan_step="plan-step-verify",
        plan_status="completed",
    )
    assert verification["status"] == "logged"
    assert verification["plan"]["evidence"] == verify_evidence
    plan_text = plan_path.read_text(encoding="utf-8")
    verify_row = next(line for line in plan_text.splitlines() if line.startswith("| plan-step-verify |"))
    assert verify_row.count("|") == 5
    assert "uv run &#124; tee verification.txt" in verify_row
    rows = aegis_installer._parse_plan_rows(plan_path)
    assert rows["plan-step-verify"]["malformed"] is False
    assert rows["plan-step-verify"]["status"] == "completed"


def test_log_work_keeps_pending_tracking_when_plan_table_update_fails(tmp_path: Path) -> None:
    target = tmp_path / "log-plan-failure-keeps-pending"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="atomic-log", title="Atomic Log")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    plan_path = target / current_work["paths"]["plan"]
    plan_lines = plan_path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(plan_lines):
        if line.startswith("| plan-step-implement |"):
            plan_lines[index] = line.replace("changed files", "src/a.ts | src/b.ts")
    plan_path.write_text("\n".join(plan_lines).rstrip() + "\n", encoding="utf-8")
    pending_path = target / AEGIS_PENDING_TRACKING_REL
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    pending_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "events": [
                    {
                        "id": "keepme123",
                        "handler": "claude:Write",
                        "evidence": "src/a.ts",
                        "task": {"id": "42", "slug": "atomic-log"},
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(AegisError, match="plan row for plan-step-implement is malformed"):
        log_work(
            target,
            pending_event_id="keepme123",
            note="Tried to log implementation evidence into a malformed plan row",
            plan_step="plan-step-implement",
            plan_status="completed",
        )

    pending_payload = json.loads(pending_path.read_text(encoding="utf-8"))
    assert [event["id"] for event in pending_payload["events"]] == ["keepme123"]


def test_log_work_consumes_pending_event_by_id(tmp_path: Path) -> None:
    target = tmp_path / "pending-id-log"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="pending-id", title="Pending Id")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    evidence_rel = f"{current_work['paths']['reports']}/pending-id.txt"
    (target / evidence_rel).write_text("pending\n", encoding="utf-8")
    pending_path = target / AEGIS_PENDING_TRACKING_REL
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    pending_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "updated_at": "2026-05-23T12:00:00Z",
                "events": [
                    {
                        "id": "abc123def456",
                        "created_at": "2026-05-23T12:00:00Z",
                        "updated_at": "2026-05-23T12:00:00Z",
                        "tool": "Write",
                        "handler": "claude:Write",
                        "evidence": evidence_rel,
                        "evidence_location": {
                            "path": evidence_rel,
                            "line_start": 1,
                            "line_end": 1,
                            "line_count": 1,
                            "source": "write_file_snapshot",
                            "confidence": "file_snapshot",
                            "display": f"{evidence_rel}:1",
                        },
                        "task": {"id": "42", "slug": "pending-id"},
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(AegisError, match="valid ids: abc123def456"):
        log_work(target, pending_event_id="missing", note="Tried missing pending id")

    logged = log_work(
        target,
        pending_event_id="abc123def456",
        note="Logged pending event by id",
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    assert logged["entry"]["h"] == "claude:Write"
    assert logged["entry"]["e"] == evidence_rel
    assert logged["entry"]["evidence_location"]["display"] == f"{evidence_rel}:1"
    assert logged["pending"]["cleared"] == 1
    assert logged["pending"]["pending_event_id"] == "abc123def456"
    assert not pending_path.exists()


def test_mcp_verify_pending_event_uses_strict_report_evidence(tmp_path: Path) -> None:
    target = tmp_path / "mcp-verify-pending"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="mcp-verify", title="MCP Verify")
    (target / AEGIS_VERIFY_REPORT_REL).parent.mkdir(parents=True, exist_ok=True)
    (target / AEGIS_VERIFY_REPORT_REL).write_text("{}\n", encoding="utf-8")

    tracked = run_target_posttooluse(
        target,
        {
            "tool_name": "mcp__aegis__aegis_verify",
            "tool_input": {
                "target_dir": target.as_posix(),
                "strict": True,
                "acknowledge_report_write": True,
            },
        },
    )

    assert tracked.returncode == 0, tracked.stderr
    pending_payload = json.loads((target / AEGIS_PENDING_TRACKING_REL).read_text(encoding="utf-8"))
    event = pending_payload["events"][0]
    assert event["handler"] == "aegis:verify"
    assert event["evidence"] == AEGIS_VERIFY_REPORT_REL
    assert event["evidence_location"]["path"] == AEGIS_VERIFY_REPORT_REL


def test_read_only_aegis_mcp_tools_do_not_create_pending_tracking(tmp_path: Path) -> None:
    target = tmp_path / "mcp-read-only-pending"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="mcp-read-only", title="MCP Read Only")

    for tool_name in (
        "mcp__aegis__aegis_inspect",
        "mcp__aegis__aegis_status",
        "mcp__aegis__aegis_next",
        "mcp__aegis__aegis_doctor",
        "mcp__aegis__aegis_repair",
        "mcp__aegis__aegis_plan_install",
        "mcp__aegis__aegis_closeout_ready",
        "mcp__aegis__aegis_handoff_repair",
        "mcp__aegis__aegis_list_profiles",
        "mcp__aegis__aegis_explain_profile",
    ):
        payload = {"tool_name": tool_name, "tool_input": {"target_dir": target.as_posix()}}
        pretool = run_target_pretooluse(target, payload)
        assert pretool.returncode == 0, pretool.stderr
        posttool = run_target_posttooluse(target, payload)
        assert posttool.returncode == 0, posttool.stderr
        assert not (target / AEGIS_PENDING_TRACKING_REL).exists(), tool_name


def test_read_only_aegis_cli_does_not_create_pending_tracking(tmp_path: Path) -> None:
    target = tmp_path / "cli-read-only-pending"
    target.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="cli-read-only", title="CLI Read Only")

    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "./.aegis/bin/aegis reconcile --target-dir . --preview-candidates"},
    }

    pretool = run_target_pretooluse(target, payload)
    assert pretool.returncode == 0, pretool.stderr
    posttool = run_target_posttooluse(target, payload)
    assert posttool.returncode == 0, posttool.stderr
    assert not (target / AEGIS_PENDING_TRACKING_REL).exists()


def test_installed_pretooluse_blocks_aegis_read_only_target_dir_outside_project(
    tmp_path: Path,
) -> None:
    target = tmp_path / "confined-target"
    target.mkdir()
    outside = tmp_path / "outside-project"
    outside.mkdir()
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)

    cli_payload = {
        "tool_name": "Bash",
        "tool_input": {"command": f"./.aegis/bin/aegis status --target-dir {outside.as_posix()}"},
    }
    mcp_payload = {
        "tool_name": "mcp__aegis__aegis_status",
        "tool_input": {"target_dir": outside.as_posix()},
    }

    cli_result = run_target_pretooluse(target, cli_payload)
    mcp_result = run_target_pretooluse(target, mcp_payload)

    assert cli_result.returncode == 2
    assert "target_dir escapes governed project root" in cli_result.stderr
    assert mcp_result.returncode == 2
    assert "target_dir escapes governed project root" in mcp_result.stderr


def test_closeout_reports_missing_evidence_repair_guidance(tmp_path: Path) -> None:
    target = tmp_path / "closeout-repair-guidance"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    simulate_claude_reload(target)
    kickoff(target, task_id="42", slug="repair-guidance", title="Repair Guidance")
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    work_rel = current_work["paths"]["work_tracking"]
    implementation_evidence = f"{current_work['paths']['reports']}/implementation.txt"
    (target / implementation_evidence).write_text("implementation\n", encoding="utf-8")

    log_work(
        target,
        handler="claude:scope",
        evidence=f"{work_rel}/FINDINGS.md",
        note="Confirmed repair guidance scope",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    log_work(
        target,
        handler="claude:Write",
        evidence=implementation_evidence,
        note="Captured implementation evidence with an intentionally missing changelog reference",
        surfaces=["implementation", "handoff"],
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    log_work(
        target,
        handler="aegis:verify",
        evidence=AEGIS_VERIFY_REPORT_REL,
        note="Recorded strict verification evidence with an intentionally missing changelog reference",
        surfaces=["implementation", "handoff"],
        plan_step="plan-step-verify",
        plan_status="completed",
    )

    failed = closeout(target, source_root=REPO_ROOT, update_handoff=True)

    assert failed["status"] == "failed"
    assert failed["next_action"]["action"] == "repair_closeout_gates_before_retry"
    assert failed["next_action"]["suggested_mcp"]["tool"] == "aegis.closeout"
    repair_items = failed["repair_guidance"]["items"]
    changelog_repairs = [
        item
        for item in repair_items
        if item["kind"] == "missing_evidence_reference"
        and item["surface"] == "changelog"
        and item["evidence"] == implementation_evidence
    ]
    assert changelog_repairs
    assert "--surface changelog" in changelog_repairs[0]["command"]
    assert implementation_evidence in changelog_repairs[0]["command"]


def test_kickoff_ready_state_does_not_depend_on_optional_stale_taskmaster(tmp_path: Path) -> None:
    target = tmp_path / "portable-repo-with-stale-taskmaster"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert report["status"] == "applied"
    simulate_claude_reload(target)

    kickoff_report = kickoff(
        target,
        task_id="1",
        slug="portable-smoke",
        title="Portable Smoke",
    )
    assert kickoff_report["status"] == "started"
    (target / ".taskmaster" / "tasks").mkdir(parents=True)
    (target / ".taskmaster" / "tasks" / "tasks.json").write_text(
        json.dumps(
            {
                "master": {
                    "tasks": [
                        {
                            "id": 1,
                            "title": "Portable Smoke",
                            "status": "done",
                            "subtasks": [],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    ready = run_target_readiness(target)

    assert ready.returncode == 0, ready.stdout + ready.stderr
    assert ready.stdout.strip().startswith("READY | task=1")
    full = subprocess.run(
        ["bash", str(target / ".claude" / "scripts" / "readiness.sh"), "--root", str(target)],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert full.returncode == 0, full.stdout + full.stderr
    assert "Aegis current work Task 1 is in-progress" in full.stdout
    assert "Taskmaster Task 1 is optional with status 'done'" in full.stdout


def test_strict_verify_requires_current_work_and_validates_runtime_surfaces(tmp_path: Path) -> None:
    target = tmp_path / "strict-repo"
    target.mkdir()
    install_report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert install_report["status"] == "applied"

    before_kickoff = verify(target, source_root=REPO_ROOT, strict=True)
    assert before_kickoff["mode"] == "strict"
    assert before_kickoff["status"] == "failed"
    assert any(
        check["gate_id"] == "workflow.current_work" and check["status"] == "fail"
        for check in before_kickoff["checks"]
    )

    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    simulate_claude_reload(target)

    kickoff_report = kickoff(
        target,
        task_id="42",
        slug="strict-verify",
        title="Strict Verify",
        goals=["Prove strict verification validates an installed workflow runtime"],
    )
    assert kickoff_report["status"] == "started"

    strict_report = verify(target, source_root=REPO_ROOT, strict=True)

    assert strict_report["mode"] == "strict"
    assert strict_report["status"] == "passed"
    check_ids = {check["gate_id"] for check in strict_report["checks"]}
    assert {
        "manifest.managed_files",
        "runtime.local_cli_shim",
        "runtime.workflow_templates",
        "workflow.current_work",
        "workflow.branch_task_alignment",
        "workflow.tracking_surfaces",
        "mutation.pending_tracking_empty",
        "claude.required_files",
        "claude.hooks_registered",
        "protection.codex_owned_paths",
        "integrations.taskmaster_optional",
        "integrations.serena_optional",
    }.issubset(check_ids)
    assert strict_report["summary"]["failed_required"] == 0
    assert strict_report["next_action"]["action"] == "log_strict_verification_before_closeout"
    assert strict_report["next_action"]["suggested_mcp"]["tool"] == "aegis.log"
    assert (
        strict_report["next_action"]["suggested_mcp"]["arguments"]["pending_event_id"] == "current"
    )


def test_local_cli_shim_resolves_packaged_asset_source_root(tmp_path: Path) -> None:
    target = tmp_path / "packaged-shim-repo"
    target.mkdir()
    package_asset_root = REPO_ROOT / "aegis_foundation" / "assets"

    install_report = install(
        target,
        source_root=package_asset_root,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert install_report["status"] == "applied"

    env = {**os.environ, "PATH": "/usr/bin:/bin"}
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [str(target / ".aegis" / "bin" / "aegis"), "status", "--target-dir", "."],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["installed"] is True
    assert payload["status"] == "current"


def test_closeout_requires_semantic_handoff_and_passes_with_update(tmp_path: Path) -> None:
    target = tmp_path / "closeout-repo"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install_report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert install_report["status"] == "applied"
    simulate_claude_reload(target)

    kickoff(
        target,
        task_id="42",
        slug="closeout-gate",
        title="Closeout Gate",
        goals=["Prove closeout validates semantic workflow completion"],
    )
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    work_rel = current_work["paths"]["work_tracking"]
    report_rel = f"{current_work['paths']['reports']}/closeout-evidence.txt"
    (target / report_rel).write_text("closeout evidence\n", encoding="utf-8")

    scope = log_work(
        target,
        handler="claude:scope",
        evidence=f"{work_rel}/FINDINGS.md",
        note="Confirmed closeout gate scope",
        surfaces=["findings", "decisions"],
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    assert scope["status"] == "logged"
    implementation = log_work(
        target,
        handler="claude:Write",
        evidence=report_rel,
        note="Recorded closeout implementation evidence",
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    assert implementation["status"] == "logged"
    verification = log_work(
        target,
        handler="verify:inspection",
        evidence="cmd`test -f closeout-evidence.txt`",
        note="Verified closeout evidence exists",
        plan_step="plan-step-verify",
        plan_status="completed",
    )
    assert verification["status"] == "logged"

    strict = verify(target, source_root=REPO_ROOT, strict=True)
    assert strict["status"] == "passed"
    strict_log = log_work(
        target,
        handler="aegis:verify",
        evidence=AEGIS_VERIFY_REPORT_REL,
        note="Recorded strict verification evidence",
        plan_step="plan-step-verify",
        plan_status="completed",
    )
    assert strict_log["status"] == "logged"

    manifest_before_dry_run = (target / AEGIS_MANIFEST_REL).read_text(encoding="utf-8")
    handoff_before_dry_run = (target / work_rel / "HANDOFF.md").read_text(encoding="utf-8")
    dry_failed = closeout(target, source_root=REPO_ROOT, update_handoff=True, dry_run=True)
    assert dry_failed["status"] == "failed"
    assert dry_failed["dry_run"] is True
    assert dry_failed["report_written"] is False
    assert dry_failed["state_updated"] is False
    assert dry_failed["handoff"]["updated"] is False
    assert dry_failed["handoff"]["would_update"] is True
    assert not (target / AEGIS_CLOSEOUT_REPORT_REL).exists()
    assert (target / AEGIS_MANIFEST_REL).read_text(encoding="utf-8") == manifest_before_dry_run
    assert (target / work_rel / "HANDOFF.md").read_text(encoding="utf-8") == handoff_before_dry_run
    concise_failed = run_cli(
        [
            "aegis",
            "closeout",
            "--target-dir",
            str(target),
            "--dry-run",
            "--update-handoff",
        ]
    )
    assert concise_failed.returncode == 1
    assert "Aegis closeout readiness: FAILED" in concise_failed.stdout
    assert "failed_required:" in concise_failed.stdout
    assert "failed_gates:" in concise_failed.stdout
    assert "closeout.handoff.current_state" in concise_failed.stdout
    assert not concise_failed.stdout.lstrip().startswith("{")
    json_failed = run_cli(
        [
            "aegis",
            "closeout",
            "--target-dir",
            str(target),
            "--dry-run",
            "--update-handoff",
            "--json",
        ]
    )
    assert json_failed.returncode == 1
    assert json.loads(json_failed.stdout)["status"] == "failed"

    failed = closeout(target, source_root=REPO_ROOT)
    assert failed["status"] == "failed"
    assert failed["next_action"]["action"] == "apply_handoff_repair_before_retry"
    assert failed["next_action"]["suggested_mcp"]["tool"] == "aegis.handoff_repair"
    assert failed["next_action"]["suggested_mcp"]["arguments"]["apply"] is True
    assert (
        "closeout.handoff.current_state"
        in failed["next_action"]["details"]["failed_required_gates"]
    )
    assert any(
        check["gate_id"] == "closeout.handoff.current_state" and check["status"] == "fail"
        for check in failed["checks"]
    )

    passed = closeout(target, source_root=REPO_ROOT, update_handoff=True)
    assert passed["status"] == "passed"
    assert passed["next_action"]["action"] == "run_post_closeout_doctor"
    assert passed["next_action"]["suggested_mcp"]["tool"] == "aegis.doctor"
    assert passed["summary"]["failed_required"] == 0
    assert passed["git"]["legacy_manual_only"] == ["gac"]
    assert 'git commit -m "<type(scope): summary>"' in passed["git"]["guidance"]
    concise_passed = aegis_installer.format_closeout_summary(passed)
    assert "Aegis closeout: PASSED" in concise_passed
    assert "closeout_report: .aegis/reports/closeout-report.json (written)" in concise_passed
    assert (target / AEGIS_CLOSEOUT_REPORT_REL).is_file()
    closeout_report = json.loads((target / AEGIS_CLOSEOUT_REPORT_REL).read_text(encoding="utf-8"))
    assert closeout_report["report_written"] is True
    assert closeout_report["state_updated"] is True
    refreshed_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    assert refreshed_work["status"] == "completed"
    assert refreshed_work["task"]["status"] == "completed"
    assert refreshed_work["closeout_report"] == AEGIS_CLOSEOUT_REPORT_REL
    degraded_event = {
        "id": "degraded123",
        "created_at": "2026-06-01T17:00:00Z",
        "gate": "pretooluse",
        "mode": "degraded_allow",
        "action_class": "non_destructive",
        "tool": "Bash",
        "reason": "RuntimeError: synthetic gate failure",
        "raw_preview": '{"tool_name":"Bash"}',
        "previous_event_hash": "",
        "event_hash": "synthetic",
    }
    (target / AEGIS_DEGRADED_EVENTS_REL).write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "updated_at": "2026-06-01T17:00:00Z",
                "events": [degraded_event],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    degraded_doctor = doctor(target, source_root=REPO_ROOT)
    assert degraded_doctor["status"] == "degraded"
    degraded_check = next(
        check
        for check in degraded_doctor["checks"]
        if check["id"] == "runtime.degraded_events_acknowledged"
    )
    assert degraded_check["status"] == "fail"
    degraded_closeout = closeout(target, source_root=REPO_ROOT, update_handoff=True, dry_run=True)
    assert degraded_closeout["status"] == "failed"
    assert "closeout.degraded_events_acknowledged" in [
        check["gate_id"] for check in degraded_closeout["checks"] if check["status"] == "fail"
    ]
    degraded_event["acknowledged_at"] = "2026-06-01T17:05:00Z"
    (target / AEGIS_DEGRADED_EVENTS_REL).write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "updated_at": "2026-06-01T17:05:00Z",
                "events": [degraded_event],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    acknowledged_doctor = doctor(target, source_root=REPO_ROOT)
    assert acknowledged_doctor["status"] == "healthy"
    idempotent_dry_run = closeout(target, source_root=REPO_ROOT, update_handoff=True, dry_run=True)
    assert idempotent_dry_run["status"] == "passed"
    assert idempotent_dry_run["readiness"]["status"] == "passed"
    assert idempotent_dry_run["readiness"]["stdout"] == "READY from completed closeout state"
    assert idempotent_dry_run["next_action"]["action"] == "task_complete"
    handoff = (target / work_rel / "HANDOFF.md").read_text(encoding="utf-8")
    assert AEGIS_CLOSEOUT_REPORT_REL in handoff
    assert AEGIS_VERIFY_REPORT_REL in handoff
    assert report_rel in handoff


def test_handoff_repair_fixes_placeholder_handoff_before_closeout(tmp_path: Path) -> None:
    target = tmp_path / "handoff-repair-repo"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install_report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert install_report["status"] == "applied"
    simulate_claude_reload(target)

    kickoff(
        target,
        task_id="42",
        slug="handoff-repair",
        title="Handoff Repair",
        goals=["Repair placeholder handoff before final closeout"],
    )
    current_work = json.loads(
        (target / ".aegis" / "state" / "current-work.json").read_text(encoding="utf-8")
    )
    work_rel = current_work["paths"]["work_tracking"]
    report_rel = f"{current_work['paths']['reports']}/handoff-repair-evidence.txt"
    (target / report_rel).write_text("handoff repair evidence\n", encoding="utf-8")

    log_work(
        target,
        handler="claude:scope",
        evidence=f"{work_rel}/FINDINGS.md",
        note="Confirmed handoff repair scope",
        plan_step="plan-step-scope",
        plan_status="completed",
    )
    log_work(
        target,
        handler="claude:Write",
        evidence=report_rel,
        note="Recorded handoff repair implementation evidence",
        plan_step="plan-step-implement",
        plan_status="completed",
    )
    log_work(
        target,
        handler="verify:inspection",
        evidence="cmd`test -f handoff-repair-evidence.txt`",
        note="Verified handoff repair evidence exists",
        plan_step="plan-step-verify",
        plan_status="completed",
    )
    strict = verify(target, source_root=REPO_ROOT, strict=True)
    assert strict["status"] == "passed"
    log_work(
        target,
        handler="aegis:verify",
        evidence=AEGIS_VERIFY_REPORT_REL,
        note="Recorded strict verification evidence",
        plan_step="plan-step-verify",
        plan_status="completed",
    )

    handoff_path = target / work_rel / "HANDOFF.md"
    handoff_before = handoff_path.read_text(encoding="utf-8")
    assert "has been kicked off through Aegis" in handoff_before
    assert closeout(target, source_root=REPO_ROOT, dry_run=True)["status"] == "failed"

    dry_run = repair_handoff(target, source_root=REPO_ROOT, dry_run=True)
    assert dry_run["status"] == "planned"
    assert dry_run["dry_run"] is True
    assert dry_run["handoff"]["would_update"] is True
    assert (
        "closeout.handoff.current_state"
        in dry_run["closeout_ready_before"]["failed_required_gates"]
    )
    assert "## Implementation Evidence" in dry_run["preview"]
    assert handoff_path.read_text(encoding="utf-8") == handoff_before
    assert not (target / AEGIS_CLOSEOUT_REPORT_REL).exists()

    repaired = repair_handoff(target, source_root=REPO_ROOT)
    assert repaired["status"] == "repaired"
    assert repaired["report_written"] is False
    assert repaired["state_updated"] is False
    assert repaired["handoff"]["updated"] is True
    assert repaired["closeout_ready_after"]["status"] == "passed"
    assert not (target / AEGIS_CLOSEOUT_REPORT_REL).exists()

    handoff = handoff_path.read_text(encoding="utf-8")
    semantic_handoff = handoff.split("## Progress Log", 1)[0]
    assert "## Implementation Evidence" in semantic_handoff
    assert "## Verification Evidence" in semantic_handoff
    assert "## Strict Verification Evidence" in semantic_handoff
    assert "Branch: `feat/task-42-handoff-repair`." in semantic_handoff
    assert "'action': 'created_branch'" not in semantic_handoff
    assert report_rel in semantic_handoff
    assert AEGIS_VERIFY_REPORT_REL in semantic_handoff
    assert "## Progress Log" in handoff
    assert "Handoff initialized by Aegis kickoff" in handoff

    closeout_ready = closeout(target, source_root=REPO_ROOT, dry_run=True)
    assert closeout_ready["status"] == "passed"
    assert closeout_ready["report_written"] is False
    assert closeout_ready["state_updated"] is False


def test_strict_verify_fails_when_workflow_template_is_missing(tmp_path: Path) -> None:
    target = tmp_path / "strict-missing-template"
    target.mkdir()
    git_init = subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=target,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert git_init.returncode == 0, git_init.stderr
    install_report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert install_report["status"] == "applied"
    simulate_claude_reload(target)
    kickoff(
        target,
        task_id="42",
        slug="strict-verify",
        title="Strict Verify",
    )

    (target / ".aegis" / "templates" / "workflow" / "session.md").unlink()

    strict_report = verify(target, source_root=REPO_ROOT, strict=True)

    assert strict_report["mode"] == "strict"
    assert strict_report["status"] == "failed"
    assert any(
        check["gate_id"] == "runtime.workflow_templates" and check["status"] == "fail"
        for check in strict_report["checks"]
    )


def _write_fake_wheel(path: Path, *, omit: str | None = None) -> None:
    members = [
        "aegis_foundation/cli.py",
        "aegis_mcp/server.py",
        "aegis_foundation/assets/.claude/scripts/pretooluse-gate.sh",
        "aegis_foundation/assets/.claude/scripts/posttooluse-tracking.sh",
        "aegis_foundation/assets/.claude/scripts/tracking-stop-gate.sh",
        "aegis_foundation/assets/scripts/_aegis_installer.py",
        "aegis_foundation/assets/scripts/codex-task",
        "aegis_foundation/assets/schemas/aegis/foundation-manifest.schema.json",
        "aegis_foundation/assets/templates/aegis/workflow/session.md",
        "aegis_foundation/assets/templates/aegis/workflow/tracker.md",
        "aegis_foundation-0.1.0.dist-info/entry_points.txt",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        for member in members:
            if omit and member.endswith(omit):
                continue
            archive.writestr(member, "x\n")


def _write_fake_sdist(path: Path) -> None:
    members = [
        "aegis_foundation-0.1.0/aegis_foundation/cli.py",
        "aegis_foundation-0.1.0/aegis_mcp/server.py",
        "aegis_foundation-0.1.0/aegis_foundation/assets/.claude/scripts/pretooluse-gate.sh",
        "aegis_foundation-0.1.0/aegis_foundation/assets/.claude/scripts/posttooluse-tracking.sh",
        "aegis_foundation-0.1.0/aegis_foundation/assets/.claude/scripts/tracking-stop-gate.sh",
        "aegis_foundation-0.1.0/aegis_foundation/assets/scripts/_aegis_installer.py",
        "aegis_foundation-0.1.0/aegis_foundation/assets/scripts/codex-task",
        "aegis_foundation-0.1.0/aegis_foundation/assets/schemas/aegis/foundation-manifest.schema.json",
        "aegis_foundation-0.1.0/aegis_foundation/assets/templates/aegis/workflow/session.md",
        "aegis_foundation-0.1.0/aegis_foundation/assets/templates/aegis/workflow/tracker.md",
        "aegis_foundation-0.1.0/pyproject.toml",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "w:gz") as archive:
        for member in members:
            data = b"x\n"
            info = tarfile.TarInfo(member)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))


def test_release_certification_inspects_artifacts_and_writes_report(tmp_path: Path) -> None:
    source = tmp_path / "source"
    dist = tmp_path / "dist"
    source.mkdir()
    _write_fake_wheel(dist / "aegis_foundation-0.1.0-py3-none-any.whl")
    _write_fake_sdist(dist / "aegis_foundation-0.1.0.tar.gz")

    report = certify_release_candidate(
        source,
        dist_dir=dist,
        report_file=AEGIS_RELEASE_CERT_REPORT_REL,
        build=False,
        run_smoke=False,
    )

    assert report["status"] == "passed"
    assert report["build"]["status"] == "skipped"
    assert report["smokes"]["clean_cli"]["status"] == "skipped"
    assert report["smokes"]["mcp_server_config"]["status"] == "skipped"
    assert report["smokes"]["mcp_stdio"]["status"] == "covered_by_focused_pytest"
    assert {artifact["kind"] for artifact in report["artifacts"]} == {"wheel", "sdist"}
    assert all(len(artifact["sha256"]) == 64 for artifact in report["artifacts"])
    assert (source / AEGIS_RELEASE_CERT_REPORT_REL).is_file()


def test_release_certification_fails_on_missing_required_artifact_member(tmp_path: Path) -> None:
    source = tmp_path / "source"
    dist = tmp_path / "dist"
    source.mkdir()
    _write_fake_wheel(
        dist / "aegis_foundation-0.1.0-py3-none-any.whl",
        omit="pretooluse-gate.sh",
    )
    _write_fake_sdist(dist / "aegis_foundation-0.1.0.tar.gz")

    report = certify_release_candidate(
        source,
        dist_dir=dist,
        report_file=AEGIS_RELEASE_CERT_REPORT_REL,
        build=False,
        run_smoke=False,
    )

    assert report["status"] == "failed"
    assert any(failure["stage"] == "artifact_inspection" for failure in report["failures"])
    wheel = next(artifact for artifact in report["artifacts"] if artifact["kind"] == "wheel")
    assert (
        "aegis_foundation/assets/.claude/scripts/pretooluse-gate.sh"
        in wheel["missing_required_suffixes"]
    )


def test_release_certification_runs_clean_smoke_when_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    dist = tmp_path / "dist"
    source.mkdir()
    wheel_path = dist / "aegis_foundation-0.1.0-py3-none-any.whl"
    _write_fake_wheel(wheel_path)
    _write_fake_sdist(dist / "aegis_foundation-0.1.0.tar.gz")
    called: list[str] = []

    def fake_clean_smoke(wheel: Path) -> dict:
        called.append(wheel.name)
        return {
            "status": "passed",
            "steps": [
                {
                    "name": "aegis_verify_strict",
                    "status": "passed",
                }
            ],
        }

    monkeypatch.setattr(aegis_installer, "_certify_clean_cli_smoke", fake_clean_smoke)
    monkeypatch.setattr(
        aegis_installer,
        "_certify_mcp_server_config_smoke",
        lambda wheel: {"status": "passed", "checks": [], "wheel": wheel.name},
    )

    report = certify_release_candidate(
        source,
        dist_dir=dist,
        report_file=AEGIS_RELEASE_CERT_REPORT_REL,
        build=False,
        run_smoke=True,
    )

    assert called == [wheel_path.name]
    assert report["status"] == "passed"
    assert report["smokes"]["clean_cli"]["status"] == "passed"
    assert report["smokes"]["mcp_server_config"]["status"] == "passed"
    assert report["smokes"]["clean_cli"]["steps"][0]["name"] == "aegis_verify_strict"


def test_release_certification_full_clean_smoke_when_enabled(tmp_path: Path) -> None:
    if os.environ.get("AEGIS_RUN_CERTIFICATION_SMOKE") != "1":
        pytest.skip(
            "Set AEGIS_RUN_CERTIFICATION_SMOKE=1 to run the full release certification smoke."
        )
    if shutil.which("uv") is None or shutil.which("uvx") is None:
        pytest.skip("uv and uvx are required for the full release certification smoke.")

    report = certify_release_candidate(
        REPO_ROOT,
        dist_dir=tmp_path / "dist",
        report_file=tmp_path / "certification-report.json",
        build=True,
        run_smoke=True,
    )

    assert report["status"] == "passed"
    assert report["build"]["status"] == "passed"
    assert report["smokes"]["clean_cli"]["status"] == "passed"
    assert report["smokes"]["mcp_server_config"]["status"] == "passed"
    assert any(
        step["name"] == "aegis_verify_strict" and step["status"] == "passed"
        for step in report["smokes"]["clean_cli"]["steps"]
    )


def test_install_merges_existing_claude_entrypoint_without_losing_project_context(
    tmp_path: Path,
) -> None:
    target = tmp_path / "existing-claude-project"
    target.mkdir()
    claude = target / "CLAUDE.md"
    claude.write_text("# Existing Claude instructions\n", encoding="utf-8")

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )

    assert report["status"] == "applied"
    text = claude.read_text(encoding="utf-8")
    assert aegis_installer.AEGIS_CLAUDE_BLOCK_BEGIN in text
    assert aegis_installer.AEGIS_CLAUDE_BLOCK_END in text
    assert "Before persistent mutation, Claude must be in a READY state" in text
    assert "## Existing Project Instructions" in text
    assert "# Existing Claude instructions" in text
    claude_operation = next(
        operation for operation in report["plan"]["operations"] if operation["path"] == "CLAUDE.md"
    )
    assert claude_operation["classification"] == "modify"
    assert claude_operation["safe_to_apply"] is True
    assert (target / AEGIS_MANIFEST_REL).exists()


def test_install_merges_existing_agents_entrypoint_without_losing_project_context(
    tmp_path: Path,
) -> None:
    target = tmp_path / "existing-agents-project"
    target.mkdir()
    agents = target / "AGENTS.md"
    agents.write_text("# Existing agent instructions\n", encoding="utf-8")

    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="codex",
        agents=["codex"],
        apply=True,
    )

    assert report["status"] == "applied"
    text = agents.read_text(encoding="utf-8")
    assert aegis_installer.AEGIS_AGENTS_BLOCK_BEGIN in text
    assert aegis_installer.AEGIS_AGENTS_BLOCK_END in text
    assert "Aegis Foundation" in text
    assert "## Existing Agent Instructions" in text
    assert "# Existing agent instructions" in text
    agents_operation = next(
        operation for operation in report["plan"]["operations"] if operation["path"] == "AGENTS.md"
    )
    assert agents_operation["classification"] == "modify"
    assert agents_operation["safe_to_apply"] is True
    assert (target / AEGIS_MANIFEST_REL).exists()


def test_verify_fails_when_required_claude_gate_file_is_missing(tmp_path: Path) -> None:
    target = tmp_path / "missing-hook"
    target.mkdir()
    report = install(
        target,
        source_root=REPO_ROOT,
        primary_agent="claude",
        agents=["claude"],
        apply=True,
    )
    assert report["status"] == "applied"

    (target / ".claude" / "scripts" / "readiness.sh").unlink()

    verification = verify(target, source_root=REPO_ROOT)
    assert verification["status"] == "failed"
    assert any(
        check["gate_id"] == "claude.readiness" and check["status"] == "fail"
        for check in verification["checks"]
    )


def test_agent_selection_is_explicit_and_consistent(tmp_path: Path) -> None:
    with pytest.raises(AegisError, match="at least one explicit --agent"):
        plan_install(tmp_path, source_root=REPO_ROOT, primary_agent="claude", agents=[])

    with pytest.raises(AegisError, match="must also be listed"):
        plan_install(tmp_path, source_root=REPO_ROOT, primary_agent="codex", agents=["claude"])

    with pytest.raises(AegisError, match="requires at least two"):
        plan_install(tmp_path, source_root=REPO_ROOT, primary_agent="multi", agents=["claude"])

    with pytest.raises(AegisError, match="cannot be combined"):
        plan_install(tmp_path, source_root=REPO_ROOT, primary_agent="none", agents=["claude"])


def test_inspect_reports_installed_aegis_state(tmp_path: Path) -> None:
    target = tmp_path / "repo"
    target.mkdir()
    before = inspect_project(target)
    assert before["aegis"]["installed"] is False
    assert before["detected_agents"]["claude"] is False
    assert before["workflow_guidance"]["phase"] == "bootstrap"
    assert before["workflow_guidance"]["state"] == "not_installed"
    assert before["workflow_guidance"]["suggested_mcp_call"]["tool"] == "aegis.init"
    assert before["workflow_guidance"]["details"]["must_initialize_before_source_edits"] is True
    assert "source edits" in before["workflow_guidance"]["details"]["forbidden_until_init"]
    assert "Taskmaster mutations" in before["workflow_guidance"]["details"]["forbidden_until_init"]

    install(target, source_root=REPO_ROOT, primary_agent="claude", agents=["claude"], apply=True)
    after = inspect_project(target)

    assert after["aegis"]["installed"] is True
    assert after["aegis"]["primary_agent"] == "claude"
    assert after["detected_agents"]["claude"] is True
    assert after["workflow_guidance"]["state"] == "client_reload_required"


def test_aegis_cli_smoke_installs_and_verifies_generic_claude_profile(tmp_path: Path) -> None:
    target = tmp_path / "cli-repo"
    target.mkdir()

    plan_result = run_cli(
        [
            "aegis",
            "plan-install",
            "--target-dir",
            str(target),
            "--primary-agent",
            "claude",
            "--agent",
            "claude",
        ]
    )
    assert plan_result.returncode == 0, plan_result.stderr
    plan = json.loads(plan_result.stdout)
    assert plan["mode"] == "dry_run"
    assert plan["summary"]["creates"] > 0

    install_result = run_cli(
        [
            "aegis",
            "install",
            "--target-dir",
            str(target),
            "--primary-agent",
            "claude",
            "--agent",
            "claude",
            "--apply",
        ]
    )
    assert install_result.returncode == 0, install_result.stderr
    install_report = json.loads(install_result.stdout)
    assert install_report["status"] == "applied"

    verify_result = run_cli(["aegis", "verify", "--target-dir", str(target)])
    assert verify_result.returncode == 0, verify_result.stderr
    verify_report = json.loads(verify_result.stdout)
    assert verify_report["status"] == "passed"

    second_plan_result = run_cli(
        [
            "aegis",
            "plan-install",
            "--target-dir",
            str(target),
            "--primary-agent",
            "claude",
            "--agent",
            "claude",
        ]
    )
    assert second_plan_result.returncode == 0, second_plan_result.stderr
    second_plan = json.loads(second_plan_result.stdout)
    assert second_plan["summary"]["creates"] == 0
    assert second_plan["summary"]["manual_reviews"] == 0
    assert {operation["classification"] for operation in second_plan["operations"]} == {"skip"}
