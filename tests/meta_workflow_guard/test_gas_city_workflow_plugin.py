"""Versioned Gas City workflow plugin and cold-start capsule tests."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MARKETPLACE_ROOT = REPO_ROOT / ".agents" / "plugins"
PLUGIN = REPO_ROOT / "plugins" / "gas-city-workflow"
CONTEXT_SCRIPT = PLUGIN / "scripts" / "project_context.py"
PLUGIN_VALIDATOR = REPO_ROOT / "scripts" / "validate_codex_plugin.py"


def _load_context_module():
    name = "gas_city_workflow_project_context_test"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, CONTEXT_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def _init_project(root: Path, project_id: str, *, descriptor: bool = False) -> None:
    root.mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (root / "CLAUDE.md").write_text("# Claude\n", encoding="utf-8")
    active = root / "docs" / "ai" / "work-tracking" / "active" / f"20300101-{project_id}-ACTIVE"
    active.mkdir(parents=True)
    (active / "TRACKER.md").write_text("**Status**: ACTIVE\n", encoding="utf-8")
    plan = root / "plans" / f"2030-01-01-{project_id}.md"
    plan.parent.mkdir(parents=True)
    plan.write_text("# Plan\n", encoding="utf-8")
    (plan.parent / "current").symlink_to(plan.name)
    session = root / "sessions" / "2030" / "01" / f"2030-01-01-001-{project_id}.md"
    session.parent.mkdir(parents=True)
    session.write_text("# Session\n", encoding="utf-8")
    current = root / "sessions" / "current"
    current.parent.mkdir(parents=True, exist_ok=True)
    current.symlink_to(session.relative_to(current.parent))
    if descriptor:
        (root / ".gas-city-workflow.json").write_text(
            json.dumps(
                {
                    "schema": "gas-city-workflow.project.v1",
                    "id": project_id,
                    "repository": f"fixture/{project_id}",
                    "rig": project_id,
                    "workflow_authority": "beads",
                    "workflow_profile": "beads-with-aegis-evidence",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    subprocess.run(
        ["git", "init", "-b", f"codex/{project_id}-fixture"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(
        [
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
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def _write_registry(path: Path, projects: list[dict[str, object]]) -> Path:
    path.write_text(
        json.dumps(
            {"schema": "gas-city-workflow.project-registry.v1", "projects": projects},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _add_linked_worktree(root: Path, worktree: Path, branch: str) -> None:
    worktree.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "worktree", "add", "-b", branch, str(worktree)],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def test_plugin_manifest_and_router_skill_validate() -> None:
    result = subprocess.run(
        [sys.executable, str(PLUGIN_VALIDATOR), str(PLUGIN)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "gas-city-workflow"
    assert manifest["version"].startswith("0.5.0+codex.")
    assert manifest["interface"]["capabilities"] == ["Read"]
    assert not (PLUGIN / ".mcp.json").exists()
    assert not (PLUGIN / "hooks").exists()
    assert not (REPO_ROOT / "marketplace.json").exists()
    marketplace = json.loads((MARKETPLACE_ROOT / "marketplace.json").read_text(encoding="utf-8"))
    assert marketplace["name"] == "gas-city-operations"
    assert marketplace["plugins"] == [
        {
            "name": "gas-city-workflow",
            "source": {
                "source": "local",
                "path": "./plugins/gas-city-workflow",
            },
            "policy": {
                "installation": "AVAILABLE",
                "authentication": "ON_USE",
            },
            "category": "Developer Tools",
        }
    ]
    source = marketplace["plugins"][0]["source"]["path"]
    assert source.startswith("./")
    assert (REPO_ROOT / source.removeprefix("./")).resolve() == PLUGIN.resolve()
    assert PLUGIN.is_dir()


def test_context_capsule_supports_three_registered_projects_without_mutation(
    tmp_path: Path,
) -> None:
    module = _load_context_module()
    projects = []
    roots = {}
    for project_id in ("gas-city", "hpfetcher", "blog"):
        root = tmp_path / project_id
        _init_project(root, project_id)
        roots[project_id] = root
        projects.append(
            {
                "id": project_id,
                "root": str(root),
                "repository": f"fixture/{project_id}",
                "rig": project_id,
                "workflow_authority": "beads",
                "workflow_profile": "beads-with-aegis-evidence",
            }
        )
    registry = _write_registry(tmp_path / "projects.json", projects)

    for project_id, root in roots.items():
        before = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        context = module.build_context(root, registry)
        after = subprocess.run(
            ["git", "status", "--porcelain=v1"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout

        assert context["schema"] == "gas-city-workflow.project-context.v1"
        assert context["project"]["id"] == project_id
        assert context["project"]["rig"] == project_id
        assert context["project"]["identity_source"] == "registry"
        assert context["workspace"] == {
            "canonical_root": root.as_posix(),
            "worktree_root": root.with_name(f"{root.name}-worktrees").as_posix(),
            "location": "canonical",
            "policy_source": "derived",
            "enforced": True,
        }
        assert context["workflow"]["authority"] == "beads"
        assert context["plugin_version"] == module.PLUGIN_VERSION
        assert context["workflow"]["lifecycle_entrypoint"].endswith("/scripts/workflow.py")
        assert context["workflow"]["commands"]["begin"][-1] == "<bead-id>"
        assert context["workflow"]["commands"]["resume"][-1] == root.as_posix()
        assert context["workflow"]["commands"]["ready"][3:6] == [
            "--rig",
            project_id,
            "bd",
        ]
        assert context["adapters"]["codex"]["present"] is True
        assert context["adapters"]["fable"]["present"] is True
        assert context["permissions"]["widens_permissions"] is False
        assert before == after == ""


def test_future_project_onboards_with_local_descriptor(tmp_path: Path) -> None:
    module = _load_context_module()
    root = tmp_path / "future-project"
    _init_project(root, "future-project", descriptor=True)
    registry = _write_registry(tmp_path / "projects.json", [])

    context = module.build_context(root, registry)

    assert context["project"]["id"] == "future-project"
    assert context["project"]["identity_source"] == "descriptor"
    assert context["workflow"]["rig"] == "future-project"
    assert context["workflow"]["active_trackers"] == ["20300101-future-project-ACTIVE"]
    assert context["workspace"]["canonical_root"] == root.as_posix()
    assert (
        context["workspace"]["worktree_root"] == (tmp_path / "future-project-worktrees").as_posix()
    )
    assert context["workspace"]["location"] == "canonical"
    assert context["git"]["origin_status"] == "unconfigured"


@pytest.mark.parametrize(
    "remote",
    (
        "git@github.com:fixture/future-project.git",
        "https://github.com/fixture/future-project",
        "ssh://git@github.com/fixture/future-project.git",
    ),
)
def test_project_identity_matches_supported_origin_shapes(tmp_path: Path, remote: str) -> None:
    module = _load_context_module()
    root = tmp_path / "future-project"
    _init_project(root, "future-project", descriptor=True)
    subprocess.run(
        ["git", "remote", "add", "origin", remote],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    registry = _write_registry(tmp_path / "projects.json", [])

    context = module.build_context(root, registry)

    assert context["git"]["origin_repository"] == "fixture/future-project"
    assert context["git"]["origin_status"] == "exact"


def test_project_identity_blocks_declared_repository_origin_mismatch(tmp_path: Path) -> None:
    module = _load_context_module()
    root = tmp_path / "future-project"
    _init_project(root, "future-project", descriptor=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "git@github.com:fixture/renamed-project.git"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    registry = _write_registry(tmp_path / "projects.json", [])

    with pytest.raises(module.ContextError, match="disagrees with origin"):
        module.build_context(root, registry)


def test_descriptor_only_linked_worktree_uses_sibling_root_and_blocks_legacy_root(
    tmp_path: Path,
) -> None:
    module = _load_context_module()
    root = tmp_path / "future-project"
    _init_project(root, "future-project", descriptor=True)
    registry = _write_registry(tmp_path / "projects.json", [])
    approved = tmp_path / "future-project-worktrees" / "ga-approved"
    legacy = tmp_path / "codex" / "worktrees" / "ga-legacy"
    _add_linked_worktree(root, approved, "codex/ga-approved-fixture")
    _add_linked_worktree(root, legacy, "codex/ga-legacy-fixture")

    context = module.build_context(approved, registry)

    assert context["workspace"]["canonical_root"] == root.as_posix()
    assert context["workspace"]["worktree_root"] == approved.parent.as_posix()
    assert context["workspace"]["location"] == "linked-worktree"
    assert context["workspace"]["policy_source"] == "derived"
    with pytest.raises(module.ContextError, match="outside the approved worktree root"):
        module.build_context(legacy, registry)


def test_registry_can_override_the_derived_worktree_root(tmp_path: Path) -> None:
    module = _load_context_module()
    root = tmp_path / "special-project"
    _init_project(root, "special-project", descriptor=True)
    approved_root = tmp_path / "managed" / "special-worktrees"
    linked = approved_root / "ga-special"
    _add_linked_worktree(root, linked, "codex/ga-special-fixture")
    registry = _write_registry(
        tmp_path / "projects.json",
        [
            {
                "id": "special-project",
                "root": str(root),
                "worktree_root": str(approved_root),
                "repository": "fixture/special-project",
                "rig": "special-project",
                "workflow_authority": "beads",
                "workflow_profile": "beads-with-aegis-evidence",
            }
        ],
    )

    context = module.build_context(linked, registry)

    assert context["project"]["identity_source"] == "descriptor+registry"
    assert context["workspace"]["worktree_root"] == approved_root.as_posix()
    assert context["workspace"]["policy_source"] == "registry"


def test_gas_city_operations_identity_and_workspace_policy_are_registered() -> None:
    descriptor = json.loads((REPO_ROOT / ".gas-city-workflow.json").read_text(encoding="utf-8"))
    registry = json.loads((PLUGIN / "config" / "projects.json").read_text(encoding="utf-8"))[
        "projects"
    ]
    registered = next(project for project in registry if project["id"] == "gas-city-operations")

    assert descriptor == {
        "schema": "gas-city-workflow.project.v1",
        "id": "gas-city-operations",
        "repository": "loucmane/gas-city-operations",
        "rig": "gascity",
        "workflow_authority": "beads",
        "workflow_profile": "beads-with-aegis-evidence",
    }
    assert registered["root"] == "/home/loucmane/gas-city-ops"
    assert registered["worktree_root"] == "/home/loucmane/gas-city-ops-worktrees"
    assert {
        key: value for key, value in registered.items() if key not in {"root", "worktree_root"}
    } == {key: value for key, value in descriptor.items() if key != "schema"}


def test_descriptor_and_registry_disagreement_fails_closed(tmp_path: Path) -> None:
    module = _load_context_module()
    root = tmp_path / "future-project"
    _init_project(root, "future-project", descriptor=True)
    registry = _write_registry(
        tmp_path / "projects.json",
        [
            {
                "id": "different",
                "root": str(root),
                "repository": "fixture/different",
                "rig": "different",
                "workflow_authority": "beads",
                "workflow_profile": "beads-with-aegis-evidence",
            }
        ],
    )

    with pytest.raises(module.ContextError, match="disagrees with the central registry"):
        module.build_context(root, registry)


def test_hpfetcher_declares_a_stable_base_ref_for_dirty_canonical_checkout() -> None:
    registry = json.loads((PLUGIN / "config" / "projects.json").read_text(encoding="utf-8"))[
        "projects"
    ]
    hpfetcher = next(project for project in registry if project["id"] == "hpfetcher")

    assert hpfetcher["base_ref"] == "refs/remotes/origin/main"


def test_codex_and_fable_adapters_share_one_context_and_keep_roles_bounded() -> None:
    skill = (PLUGIN / "skills" / "gas-city-workflow" / "SKILL.md").read_text(encoding="utf-8")
    codex = (PLUGIN / "adapters" / "codex.md").read_text(encoding="utf-8")
    fable = (PLUGIN / "adapters" / "fable.md").read_text(encoding="utf-8")

    assert "gas-city-workflow.project-context.v1" in codex
    assert "gas-city-workflow.project-context.v1" in fable
    assert "default executor" in codex
    assert "read-only reviewer" in fable
    assert "Fable is read-only" in skill
    assert "does not authorize" in skill
