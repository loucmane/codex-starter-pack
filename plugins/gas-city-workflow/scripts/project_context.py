#!/usr/bin/env python3
"""Render a deterministic, read-only Gas City project context capsule."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = PLUGIN_ROOT / "config" / "projects.json"
DESCRIPTOR_NAME = ".gas-city-workflow.json"
REGISTRY_SCHEMA = "gas-city-workflow.project-registry.v1"
DESCRIPTOR_SCHEMA = "gas-city-workflow.project.v1"
CONTEXT_SCHEMA = "gas-city-workflow.project-context.v1"
PLUGIN_VERSION = "0.1.0"
CITY = "/home/loucmane/gascity/city"
GC = "/home/loucmane/gascity/bin/gc"
BD = "/home/loucmane/gascity/bin/bd"
ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class ContextError(RuntimeError):
    """Raised when project identity cannot be derived without guessing."""


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ContextError(f"{label} must be a regular file: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContextError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ContextError(f"{label} must contain a JSON object")
    return payload


def _validate_project(project: dict[str, Any], *, allow_root: bool) -> dict[str, str]:
    expected = {
        "id",
        "repository",
        "rig",
        "workflow_authority",
        "workflow_profile",
    }
    if allow_root:
        expected.add("root")
    if set(project) != expected:
        raise ContextError(f"project keys must be exactly {sorted(expected)}")
    project_id = project.get("id")
    rig = project.get("rig")
    repository = project.get("repository")
    if not isinstance(project_id, str) or not ID_PATTERN.fullmatch(project_id):
        raise ContextError("project id is invalid")
    if not isinstance(rig, str) or not ID_PATTERN.fullmatch(rig):
        raise ContextError("project rig is invalid")
    if not isinstance(repository, str) or not REPOSITORY_PATTERN.fullmatch(repository):
        raise ContextError("project repository is invalid")
    if project.get("workflow_authority") != "beads":
        raise ContextError("workflow_authority must be beads")
    profile = project.get("workflow_profile")
    if profile not in {
        "beads-with-aegis-evidence",
        "beads-with-frozen-legacy-evidence",
    }:
        raise ContextError("workflow_profile is invalid")
    result = {key: str(value) for key, value in project.items()}
    if allow_root:
        root_value = project.get("root")
        if not isinstance(root_value, str) or not Path(root_value).is_absolute():
            raise ContextError("registered project root must be absolute")
    return result


def _load_registry(path: Path) -> list[dict[str, str]]:
    payload = _read_json_object(path, "project registry")
    if set(payload) != {"schema", "projects"} or payload.get("schema") != REGISTRY_SCHEMA:
        raise ContextError("project registry schema is invalid")
    projects = payload.get("projects")
    if not isinstance(projects, list):
        raise ContextError("project registry projects must be a list")
    validated = [
        _validate_project(project, allow_root=True)
        for project in projects
        if isinstance(project, dict)
    ]
    if len(validated) != len(projects):
        raise ContextError("project registry contains a non-object entry")
    roots = [project["root"] for project in validated]
    ids = [project["id"] for project in validated]
    if len(set(roots)) != len(roots) or len(set(ids)) != len(ids):
        raise ContextError("project registry roots and ids must be unique")
    return validated


def _git(root: Path, *args: str) -> tuple[int, str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip()


def _resolve_git_root(requested: Path) -> Path:
    root = requested.expanduser().resolve()
    if not root.is_dir():
        raise ContextError(f"project root is not a directory: {root}")
    code, top = _git(root, "rev-parse", "--show-toplevel")
    if code != 0 or not top:
        raise ContextError(f"project root is not inside a Git worktree: {root}")
    resolved = Path(top).resolve()
    if resolved != root:
        raise ContextError(f"--root must name the Git worktree root exactly: {resolved}")
    return root


def _resolve_project(root: Path, registry_path: Path) -> tuple[dict[str, str], str]:
    descriptor_path = root / DESCRIPTOR_NAME
    descriptor: dict[str, str] | None = None
    if descriptor_path.exists():
        payload = _read_json_object(descriptor_path, "project descriptor")
        if payload.pop("schema", None) != DESCRIPTOR_SCHEMA:
            raise ContextError("project descriptor schema is invalid")
        descriptor = _validate_project(payload, allow_root=False)

    registered = next(
        (
            project
            for project in _load_registry(registry_path)
            if Path(project["root"]).resolve() == root
        ),
        None,
    )
    if descriptor is not None and registered is not None:
        comparable = {key: value for key, value in registered.items() if key != "root"}
        if descriptor != comparable:
            raise ContextError("project descriptor disagrees with the central registry")
        return descriptor, "descriptor+registry"
    if descriptor is not None:
        return descriptor, "descriptor"
    if registered is not None:
        return {key: value for key, value in registered.items() if key != "root"}, "registry"
    raise ContextError(
        f"project is not registered and has no {DESCRIPTOR_NAME}; onboard it before work"
    )


def _pointer_target(root: Path, relative: str) -> str | None:
    pointer = root / relative
    if not pointer.is_symlink():
        return None
    try:
        target = pointer.resolve(strict=True)
    except OSError:
        return "<broken>"
    try:
        return target.relative_to(root).as_posix()
    except ValueError:
        return "<outside-root>"


def build_context(root: Path, registry_path: Path) -> dict[str, Any]:
    root = _resolve_git_root(root)
    project, identity_source = _resolve_project(root, registry_path.resolve())
    branch_code, branch = _git(root, "branch", "--show-current")
    head_code, head = _git(root, "rev-parse", "HEAD")
    status_code, status = _git(root, "status", "--porcelain=v1")
    if branch_code != 0 or head_code != 0 or status_code != 0:
        raise ContextError("could not read Git branch, head, or worktree status")
    active_root = root / "docs" / "ai" / "work-tracking" / "active"
    active = (
        sorted(
            path.name
            for path in active_root.iterdir()
            if path.is_dir() and path.name.endswith("-ACTIVE")
        )
        if active_root.is_dir()
        else []
    )
    readiness_candidates = (
        ".aegis/bin/aegis",
        ".claude/scripts/readiness.sh",
    )
    readiness = next(
        (candidate for candidate in readiness_candidates if (root / candidate).is_file()),
        None,
    )
    rig = project["rig"]
    return {
        "schema": CONTEXT_SCHEMA,
        "plugin_version": PLUGIN_VERSION,
        "project": {
            **project,
            "root": root.as_posix(),
            "identity_source": identity_source,
        },
        "git": {
            "branch": branch or None,
            "head": head,
            "clean": not bool(status),
            "status_entries": len(status.splitlines()) if status else 0,
        },
        "workflow": {
            "authority": "beads",
            "city": CITY,
            "gc": GC,
            "bd": BD,
            "rig": rig,
            "readiness_entrypoint": readiness,
            "plan_current": _pointer_target(root, "plans/current"),
            "session_current": _pointer_target(root, "sessions/current"),
            "active_trackers": active,
            "commands": {
                "ready": [GC, "--city", CITY, "--rig", rig, "bd", "ready"],
                "show": [GC, "--city", CITY, "--rig", rig, "bd", "show", "<bead-id>"],
            },
        },
        "adapters": {
            "codex": {"instructions": "AGENTS.md", "present": (root / "AGENTS.md").is_file()},
            "fable": {"instructions": "CLAUDE.md", "present": (root / "CLAUDE.md").is_file()},
        },
        "permissions": {
            "mutates_project": False,
            "widens_permissions": False,
            "note": "Context generation performs only filesystem reads and read-only Git queries.",
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Exact Git worktree root")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="Project registry JSON")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate and emit a compact PASS line",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        context = build_context(Path(args.root), Path(args.registry))
    except ContextError as exc:
        print(f"gas-city-workflow: BLOCKED: {exc}", file=sys.stderr)
        return 2
    if args.check:
        project = context["project"]
        print(
            "gas-city-workflow: PASS "
            f"project={project['id']} rig={project['rig']} "
            f"authority={project['workflow_authority']} permissions=unchanged"
        )
    else:
        print(json.dumps(context, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
