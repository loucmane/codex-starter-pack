"""Versioned Gas City workflow plugin and cold-start capsule tests."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
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


def _write_registry(path: Path, projects: list[dict[str, str]]) -> Path:
    path.write_text(
        json.dumps(
            {"schema": "gas-city-workflow.project-registry.v1", "projects": projects},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


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
    assert manifest["version"] == "0.1.0"
    assert manifest["interface"]["capabilities"] == ["Read"]
    assert not (PLUGIN / ".mcp.json").exists()
    assert not (PLUGIN / "hooks").exists()
    marketplace = json.loads((REPO_ROOT / "marketplace.json").read_text(encoding="utf-8"))
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
        assert context["workflow"]["authority"] == "beads"
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
    assert context["workflow"]["active_trackers"] == [
        "20300101-future-project-ACTIVE"
    ]


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


def test_codex_and_fable_adapters_share_one_context_and_keep_roles_bounded() -> None:
    skill = (PLUGIN / "skills" / "gas-city-workflow" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    codex = (PLUGIN / "adapters" / "codex.md").read_text(encoding="utf-8")
    fable = (PLUGIN / "adapters" / "fable.md").read_text(encoding="utf-8")

    assert "gas-city-workflow.project-context.v1" in codex
    assert "gas-city-workflow.project-context.v1" in fable
    assert "default executor" in codex
    assert "read-only reviewer" in fable
    assert "Fable is read-only" in skill
    assert "does not authorize" in skill
