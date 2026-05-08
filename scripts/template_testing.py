#!/usr/bin/env python3
"""Portable test helpers for Markdown template fixtures and registry assertions."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _repo_structure import DEFAULT_REPO_STRUCTURE, load_repo_structure
from template_registry import ResolutionResult, TemplateDiscoveryAPI, TemplateRecord, TemplateRegistry, parse_frontmatter


PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")


@dataclass(frozen=True)
class TemplateFixture:
    """A Markdown template fixture with registry-ready metadata."""

    id: str
    path: str
    title: Optional[str] = None
    type: str = "guide"
    status: str = "draft"
    category: Optional[str] = None
    version: Optional[str] = None
    tags: Sequence[str] = ()
    dependencies: Sequence[str] = ()
    body: str = ""
    extra_metadata: Mapping[str, object] = field(default_factory=dict)
    good_first_handler: bool = False
    good_first_workflow: bool = False

    def metadata(self) -> dict[str, object]:
        data: dict[str, object] = {
            "id": self.id,
            "title": self.title or self.id,
            "type": self.type,
            "status": self.status,
        }
        if self.category is not None:
            data["category"] = self.category
        if self.version is not None:
            data["version"] = self.version
        if self.tags:
            data["tags"] = list(self.tags)
        if self.dependencies:
            data["dependencies"] = list(self.dependencies)
        data.update(self.extra_metadata)
        return data

    def registry_entry(self, templates_root: str) -> dict[str, object]:
        relative_path = _strip_templates_root(self.path, templates_root).as_posix()
        entry: dict[str, object] = {
            "id": self.id,
            "path": f"{templates_root.rstrip('/')}/{relative_path}",
            "tags": list(self.tags),
        }
        if self.good_first_handler:
            entry["goodFirstHandler"] = True
        if self.good_first_workflow:
            entry["goodFirstWorkflow"] = True
        return entry


@dataclass(frozen=True)
class TemplateRenderResult:
    """Result from lightweight placeholder rendering used in tests."""

    template_id: Optional[str]
    path: Optional[str]
    rendered: str
    context: Mapping[str, object]
    unresolved_placeholders: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.unresolved_placeholders


@dataclass(frozen=True)
class TemplateCoverageReport:
    """Registry coverage summary for Markdown template fixtures."""

    templates_root: str
    markdown_paths: tuple[str, ...]
    registry_paths: tuple[str, ...]
    unregistered_paths: tuple[str, ...]
    missing_registry_paths: tuple[str, ...]
    coverage_pct: float

    @property
    def ok(self) -> bool:
        return not self.unregistered_paths and not self.missing_registry_paths

    def to_dict(self) -> dict[str, object]:
        return {
            "templates_root": self.templates_root,
            "markdown_paths": list(self.markdown_paths),
            "registry_paths": list(self.registry_paths),
            "unregistered_paths": list(self.unregistered_paths),
            "missing_registry_paths": list(self.missing_registry_paths),
            "coverage_pct": self.coverage_pct,
            "ok": self.ok,
        }


class TemplateTestCase:
    """Reusable fixture and assertion helper for template tests."""

    def __init__(self, repo_root: Path | str, *, templates_root: str | None = None) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.repo_root.mkdir(parents=True, exist_ok=True)
        if templates_root is not None:
            self.write_repo_config(templates_root=templates_root)

    @property
    def structure(self):
        return load_repo_structure(self.repo_root)

    @property
    def templates_root(self) -> Path:
        return self.structure.templates_root

    @property
    def templates_root_relative(self) -> str:
        try:
            return self.templates_root.relative_to(self.repo_root).as_posix()
        except ValueError:
            return self.templates_root.as_posix()

    def write_repo_config(self, **overrides: str) -> Path:
        values = dict(DEFAULT_REPO_STRUCTURE)
        values.update({key: str(value) for key, value in overrides.items()})
        config_path = self.repo_root / ".codex" / "config.toml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["[repo_structure]"]
        for key in DEFAULT_REPO_STRUCTURE:
            lines.append(f'{key} = "{values[key]}"')
        config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return config_path

    def write_template(self, fixture: TemplateFixture) -> Path:
        path = self.templates_root / _strip_templates_root(fixture.path, self.templates_root_relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        heading = fixture.title or fixture.id
        body = fixture.body.strip() or f"# {heading}\n"
        if not body.startswith("#"):
            body = f"# {heading}\n\n{body}\n"
        text = "---\n" + _metadata_to_frontmatter(fixture.metadata()) + "---\n\n" + body.rstrip() + "\n"
        path.write_text(text, encoding="utf-8")
        return path

    def write_registry(
        self,
        fixtures: Iterable[TemplateFixture] = (),
        *,
        entries: Iterable[Mapping[str, object]] = (),
    ) -> Path:
        payload = [fixture.registry_entry(self.templates_root_relative) for fixture in fixtures]
        payload.extend(dict(entry) for entry in entries)
        registry_path = self.templates_root / "registry" / "index.json"
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return registry_path

    def write_compatibility_map(self, mappings: Iterable[Mapping[str, str]], *, version: str = "test") -> Path:
        compatibility_path = self.templates_root / "registry" / "compatibility-map.json"
        compatibility_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "template-compatibility-map.v1",
            "version": version,
            "mappings": [dict(mapping) for mapping in mappings],
        }
        compatibility_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return compatibility_path

    def registry(self, **kwargs: Any) -> TemplateRegistry:
        return TemplateRegistry(repo_root=self.repo_root, **kwargs)

    def discovery_api(self, **kwargs: Any) -> TemplateDiscoveryAPI:
        return TemplateDiscoveryAPI(registry=self.registry(**kwargs))

    def assert_template_registered(self, template_id: str, *, expected_path: str | None = None) -> TemplateRecord:
        record = self.registry().get(template_id)
        if record is None:
            raise AssertionError(f"Template id is not registered: {template_id}")
        if expected_path is not None and record.path != expected_path:
            raise AssertionError(
                f"Template {template_id} path mismatch: expected {expected_path!r}, got {record.path!r}"
            )
        return record

    def assert_template_resolves(
        self,
        query: str,
        *,
        expected_status: str = "found",
        expected_path: str | None = None,
        allow_serena: bool = False,
    ) -> ResolutionResult:
        result = self.registry().resolve(query, allow_serena=allow_serena)
        if result.status != expected_status:
            raise AssertionError(
                f"Template query {query!r} resolved with status {result.status!r}, expected {expected_status!r}"
            )
        if expected_path is not None and result.path != expected_path:
            raise AssertionError(f"Template query {query!r} path mismatch: expected {expected_path!r}, got {result.path!r}")
        return result

    def assert_template_search_ids(self, expected_ids: Sequence[str], **filters: Any) -> list[dict[str, object]]:
        result = self.discovery_api().search_templates(**filters)
        items = list(result["items"])
        actual_ids = [str(item["id"]) for item in items]
        if actual_ids != list(expected_ids):
            raise AssertionError(f"Template search ids mismatch: expected {list(expected_ids)!r}, got {actual_ids!r}")
        return items

    def assert_template_dependencies_resolve(self, template_id: str) -> dict[str, object]:
        dependency_report = self.discovery_api().get_dependencies(template_id)
        if dependency_report is None:
            raise AssertionError(f"Template id not found for dependency check: {template_id}")
        missing = list(dependency_report.get("missing") or [])
        if missing:
            raise AssertionError(f"Template {template_id} has missing dependencies: {missing}")
        return dependency_report

    def assert_template_metadata_contains(
        self,
        template_id: str,
        expected: Mapping[str, object],
    ) -> Mapping[str, object]:
        record = self.assert_template_registered(template_id)
        for key, wanted in expected.items():
            actual = record.metadata.get(key)
            if actual != wanted:
                raise AssertionError(
                    f"Template {template_id} metadata[{key!r}] mismatch: expected {wanted!r}, got {actual!r}"
                )
        return record.metadata

    def render_template(
        self,
        template_id: str,
        context: Mapping[str, object],
        *,
        strict: bool = False,
    ) -> TemplateRenderResult:
        record = self.assert_template_registered(template_id)
        text = record.absolute_path.read_text(encoding="utf-8")
        rendered, unresolved = render_template_text(text, context, strict=strict)
        return TemplateRenderResult(
            template_id=record.id,
            path=record.path,
            rendered=rendered,
            context=dict(context),
            unresolved_placeholders=unresolved,
        )

    def coverage_report(self) -> TemplateCoverageReport:
        markdown_paths = _repo_relative_markdown_paths(self.repo_root, self.templates_root)
        registry_paths = _registry_paths(self.repo_root, self.templates_root, self.templates_root_relative)
        markdown_set = set(markdown_paths)
        registry_set = set(registry_paths)
        unregistered = tuple(path for path in markdown_paths if path not in registry_set)
        missing = tuple(path for path in registry_paths if path not in markdown_set)
        registered_count = len(markdown_set - set(unregistered))
        coverage_pct = 100.0 if not markdown_paths else round((registered_count / len(markdown_paths)) * 100.0, 2)
        return TemplateCoverageReport(
            templates_root=self.templates_root_relative,
            markdown_paths=markdown_paths,
            registry_paths=registry_paths,
            unregistered_paths=unregistered,
            missing_registry_paths=missing,
            coverage_pct=coverage_pct,
        )

    def assert_registry_covers_templates(self) -> TemplateCoverageReport:
        report = self.coverage_report()
        if not report.ok:
            raise AssertionError(
                "Template registry coverage failed: "
                f"unregistered={list(report.unregistered_paths)!r}, missing={list(report.missing_registry_paths)!r}"
            )
        return report


def render_template_text(text: str, context: Mapping[str, object], *, strict: bool = False) -> tuple[str, tuple[str, ...]]:
    """Render simple `{{ name }}` placeholders for deterministic tests."""

    unresolved: list[str] = []

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in context:
            unresolved.append(key)
            return match.group(0)
        return str(context[key])

    rendered = PLACEHOLDER_PATTERN.sub(replace, text)
    unresolved_tuple = tuple(dict.fromkeys(unresolved))
    if strict and unresolved_tuple:
        raise AssertionError(f"Unresolved template placeholders: {list(unresolved_tuple)}")
    return rendered, unresolved_tuple


def _metadata_to_frontmatter(metadata: Mapping[str, object]) -> str:
    lines: list[str] = []
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            values = list(value)
            if not values:
                lines.append(f"{key}: []")
                continue
            lines.append(f"{key}:")
            for item in values:
                lines.append(f"  - {_yaml_scalar(item)}")
            continue
        lines.append(f"{key}: {_yaml_scalar(value)}")
    return "\n".join(lines) + "\n"


def _yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if not text or text.startswith(("{", "[", "-", "#")) or ":" in text:
        return json.dumps(text)
    return text


def _strip_templates_root(path: str, templates_root: str) -> Path:
    normalized = Path(path).as_posix().lstrip("./")
    prefix = templates_root.rstrip("/") + "/"
    if normalized.startswith(prefix):
        normalized = normalized[len(prefix) :]
    return Path(normalized)


def _repo_relative_markdown_paths(repo_root: Path, templates_root: Path) -> tuple[str, ...]:
    if not templates_root.exists():
        return ()
    paths = [
        path.resolve().relative_to(repo_root).as_posix()
        for path in templates_root.rglob("*.md")
        if path.is_file()
    ]
    return tuple(sorted(paths))


def _registry_paths(repo_root: Path, templates_root: Path, templates_root_relative: str) -> tuple[str, ...]:
    registry_path = templates_root / "registry" / "index.json"
    if not registry_path.exists():
        return ()
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        return ()
    paths: list[str] = []
    for entry in payload:
        if not isinstance(entry, dict) or not entry.get("path"):
            continue
        absolute = _registry_entry_absolute(repo_root, templates_root, templates_root_relative, str(entry["path"]))
        try:
            paths.append(absolute.resolve().relative_to(repo_root).as_posix())
        except ValueError:
            paths.append(absolute.as_posix())
    return tuple(sorted(dict.fromkeys(paths)))


def _registry_entry_absolute(repo_root: Path, templates_root: Path, templates_root_relative: str, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    normalized = candidate.as_posix().lstrip("./")
    if normalized.startswith(templates_root_relative.rstrip("/") + "/"):
        return repo_root / normalized
    return templates_root / normalized


__all__ = [
    "TemplateCoverageReport",
    "TemplateFixture",
    "TemplateRenderResult",
    "TemplateTestCase",
    "render_template_text",
    "parse_frontmatter",
]
