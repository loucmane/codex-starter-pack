"""Strict project registry for automatic Aegis Obsidian reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

SCHEMA_VERSION = "1"
MAX_REGISTRY_BYTES = 256 * 1024
PROJECT_ID = re.compile(r"^[a-z][a-z0-9-]{0,63}$")


class RegistryError(RuntimeError):
    """Raised when a reconciliation registry is ambiguous or unsafe."""


@dataclass(frozen=True)
class ProjectConfig:
    id: str
    enabled: bool
    target_dir: Path
    output_dir: Path
    bead_export_argv: tuple[str, ...]
    include_bead_content: bool = False
    freshness_sla_seconds: int = 180
    min_interval_seconds: int = 10
    export_timeout_seconds: int = 30


@dataclass(frozen=True)
class Registry:
    path: Path
    digest: str
    projects: tuple[ProjectConfig, ...]


def _strict_json(content: str, path: Path) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise RegistryError(f"duplicate registry key {key!r}: {path}")
            result[key] = value
        return result

    try:
        return json.loads(content, object_pairs_hook=pairs)
    except RegistryError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise RegistryError(f"invalid registry JSON {path}: {exc}") from exc


def _integer(raw: Any, *, field: str, minimum: int, maximum: int) -> int:
    if isinstance(raw, bool) or not isinstance(raw, int) or not minimum <= raw <= maximum:
        raise RegistryError(f"{field} must be an integer in [{minimum}, {maximum}]")
    return raw


def _project(raw: Any, *, seen: set[str]) -> ProjectConfig:
    if not isinstance(raw, dict):
        raise RegistryError("every registry project must be an object")
    allowed = {
        "id",
        "enabled",
        "target_dir",
        "output_dir",
        "bead_export_argv",
        "include_bead_content",
        "freshness_sla_seconds",
        "min_interval_seconds",
        "export_timeout_seconds",
    }
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise RegistryError("unknown project fields: " + ", ".join(unknown))
    project_id = str(raw.get("id") or "")
    if not PROJECT_ID.fullmatch(project_id):
        raise RegistryError(f"unsafe project id: {project_id!r}")
    if project_id in seen:
        raise RegistryError(f"duplicate project id: {project_id}")
    seen.add(project_id)
    enabled = raw.get("enabled", True)
    if not isinstance(enabled, bool):
        raise RegistryError(f"project {project_id} enabled must be boolean")
    target_raw = str(raw.get("target_dir") or "")
    output_raw = str(raw.get("output_dir") or "")
    target = Path(target_raw).expanduser()
    output = Path(output_raw).expanduser()
    if not target.is_absolute() or not output.is_absolute():
        raise RegistryError(f"project {project_id} target_dir and output_dir must be absolute")
    target = target.resolve()
    output = output.resolve()
    if output == target or target in output.parents:
        raise RegistryError(f"project {project_id} output_dir must live outside target_dir")
    if output in target.parents:
        raise RegistryError(f"project {project_id} output_dir must not overlap target_dir")
    argv = raw.get("bead_export_argv")
    if (
        not isinstance(argv, list)
        or not argv
        or not all(isinstance(item, str) and item for item in argv)
    ):
        raise RegistryError(
            f"project {project_id} bead_export_argv must be a non-empty string array"
        )
    if not Path(argv[0]).is_absolute():
        raise RegistryError(
            f"project {project_id} bead_export_argv requires an absolute executable"
        )
    include_content = raw.get("include_bead_content", False)
    if not isinstance(include_content, bool):
        raise RegistryError(f"project {project_id} include_bead_content must be boolean")
    return ProjectConfig(
        id=project_id,
        enabled=enabled,
        target_dir=target,
        output_dir=output,
        bead_export_argv=tuple(argv),
        include_bead_content=include_content,
        freshness_sla_seconds=_integer(
            raw.get("freshness_sla_seconds", 180),
            field=f"project {project_id} freshness_sla_seconds",
            minimum=60,
            maximum=86_400,
        ),
        min_interval_seconds=_integer(
            raw.get("min_interval_seconds", 10),
            field=f"project {project_id} min_interval_seconds",
            minimum=0,
            maximum=300,
        ),
        export_timeout_seconds=_integer(
            raw.get("export_timeout_seconds", 30),
            field=f"project {project_id} export_timeout_seconds",
            minimum=5,
            maximum=120,
        ),
    )


def load_registry(path: str | Path) -> Registry:
    registry_path = Path(path).expanduser()
    if registry_path.is_symlink() or not registry_path.is_file():
        raise RegistryError(f"registry must be a regular non-symlink file: {registry_path}")
    content = registry_path.read_bytes()
    if len(content) > MAX_REGISTRY_BYTES:
        raise RegistryError(f"registry exceeds size limit ({len(content)} > {MAX_REGISTRY_BYTES})")
    payload = _strict_json(content.decode("utf-8"), registry_path)
    if not isinstance(payload, dict):
        raise RegistryError("registry root must be an object")
    if set(payload) != {"schema_version", "projects"}:
        raise RegistryError("registry root must contain only schema_version and projects")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise RegistryError(
            f"unsupported registry schema_version: {payload.get('schema_version')!r}"
        )
    projects_raw = payload.get("projects")
    if not isinstance(projects_raw, list) or not projects_raw:
        raise RegistryError("registry projects must be a non-empty array")
    seen: set[str] = set()
    projects = tuple(_project(item, seen=seen) for item in projects_raw)
    if not any(item.enabled for item in projects):
        raise RegistryError("registry must enable at least one project")
    return Registry(
        path=registry_path.resolve(),
        digest=hashlib.sha256(content).hexdigest(),
        projects=projects,
    )


__all__ = [
    "ProjectConfig",
    "Registry",
    "RegistryError",
    "SCHEMA_VERSION",
    "load_registry",
]
