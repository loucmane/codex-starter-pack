#!/usr/bin/env python3
"""Validate the portable Codex plugin contract used by this repository."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


PLUGIN_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
TOP_LEVEL_FIELDS = {
    "id",
    "name",
    "version",
    "description",
    "skills",
    "apps",
    "mcpServers",
    "interface",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
}
INTERFACE_FIELDS = {
    "displayName",
    "shortDescription",
    "longDescription",
    "developerName",
    "category",
    "capabilities",
    "websiteURL",
    "privacyPolicyURL",
    "termsOfServiceURL",
    "brandColor",
    "composerIcon",
    "logo",
    "logoDark",
    "screenshots",
    "defaultPrompt",
    "default_prompt",
}


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _safe_relative_path(value: Any) -> PurePosixPath | None:
    if not _non_empty_string(value):
        return None
    path = PurePosixPath(str(value))
    if path.is_absolute() or ".." in path.parts:
        return None
    return path


def _load_json_object(path: Path, errors: list[str]) -> dict[str, Any] | None:
    if not path.is_file():
        errors.append("missing `.codex-plugin/plugin.json`")
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid `.codex-plugin/plugin.json`: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append("`.codex-plugin/plugin.json` must contain an object")
        return None
    return value


def _reject_todo_markers(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, str) and "[TODO:" in value:
        errors.append(f"{path} contains an unresolved `[TODO: ...]` marker")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_todo_markers(item, f"{path}[{index}]", errors)
    elif isinstance(value, dict):
        for key, item in value.items():
            _reject_todo_markers(item, f"{path}.{key}", errors)


def _skill_frontmatter(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"unable to read `{path}`: {exc}")
        return None
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        errors.append(f"`{path}` must start with YAML frontmatter")
        return None
    try:
        end = next(
            index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"
        )
    except StopIteration:
        errors.append(f"`{path}` has unterminated YAML frontmatter")
        return None
    try:
        value = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as exc:
        errors.append(f"invalid YAML frontmatter in `{path}`: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"`{path}` frontmatter must contain a mapping")
        return None
    return value


def validate_plugin(plugin_root: Path) -> list[str]:
    errors: list[str] = []
    manifest = _load_json_object(plugin_root / ".codex-plugin" / "plugin.json", errors)
    if manifest is None:
        return errors

    _reject_todo_markers(manifest, "$", errors)
    unknown = sorted(set(manifest) - TOP_LEVEL_FIELDS)
    if unknown:
        errors.append(f"unsupported plugin.json field(s): {', '.join(unknown)}")

    name = manifest.get("name")
    if not _non_empty_string(name) or PLUGIN_NAME_RE.fullmatch(str(name)) is None:
        errors.append("plugin.json `name` must be a lowercase kebab-case identifier")
    version = manifest.get("version")
    if not _non_empty_string(version) or SEMVER_RE.fullmatch(str(version)) is None:
        errors.append("plugin.json `version` must be strict semantic versioning")
    if not _non_empty_string(manifest.get("description")):
        errors.append("plugin.json `description` must be a non-empty string")

    author = manifest.get("author")
    if not isinstance(author, dict) or not _non_empty_string(author.get("name")):
        errors.append("plugin.json `author.name` must be a non-empty string")

    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("plugin.json `interface` must be an object")
    else:
        interface_unknown = sorted(set(interface) - INTERFACE_FIELDS)
        if interface_unknown:
            errors.append(f"unsupported interface field(s): {', '.join(interface_unknown)}")
        for field in (
            "displayName",
            "shortDescription",
            "longDescription",
            "developerName",
            "category",
        ):
            if not _non_empty_string(interface.get(field)):
                errors.append(f"plugin.json `interface.{field}` must be a non-empty string")
        capabilities = interface.get("capabilities")
        if not isinstance(capabilities, list) or not capabilities or not all(
            _non_empty_string(item) for item in capabilities
        ):
            errors.append("plugin.json `interface.capabilities` must be a non-empty string array")
        prompts = interface.get("defaultPrompt", interface.get("default_prompt"))
        if not isinstance(prompts, list) or not prompts or not all(
            _non_empty_string(item) for item in prompts
        ):
            errors.append("plugin.json interface must declare a non-empty default prompt array")

    skills_rel = _safe_relative_path(manifest.get("skills"))
    if skills_rel is None:
        errors.append("plugin.json `skills` must be a safe relative path")
        return errors
    skills_root = plugin_root.joinpath(*skills_rel.parts)
    if not skills_root.is_dir():
        errors.append(f"skills directory does not exist: `{skills_rel}`")
        return errors

    skill_files = sorted(skills_root.glob("*/SKILL.md"))
    if not skill_files:
        errors.append("skills directory must contain at least one `<skill>/SKILL.md`")
    for skill_file in skill_files:
        metadata = _skill_frontmatter(skill_file, errors)
        if metadata is None:
            continue
        expected_name = skill_file.parent.name
        if metadata.get("name") != expected_name:
            errors.append(f"`{skill_file}` name must equal directory `{expected_name}`")
        if not _non_empty_string(metadata.get("description")):
            errors.append(f"`{skill_file}` description must be a non-empty string")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin", type=Path)
    args = parser.parse_args()
    plugin_root = args.plugin.expanduser().resolve()
    errors = validate_plugin(plugin_root)
    if errors:
        print("Codex plugin validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Codex plugin validation passed: {plugin_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
