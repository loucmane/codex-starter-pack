#!/usr/bin/env python3
"""Portable template registry discovery and lookup utilities."""

from __future__ import annotations

import json
import sys
import threading
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from _repo_structure import load_repo_structure


DEFAULT_COMPATIBILITY_MAP: Mapping[str, str] = {
    "templates/REGISTRY.md": "templates/registry/index.md",
    "templates/WORKFLOWS.md": "templates/workflows/",
    "templates/PATTERNS.md": "templates/patterns/",
    "templates/HANDLERS.md": "templates/handlers/",
    "templates/CONVENTIONS.md": "templates/conventions/",
    "templates/BEHAVIORS.md": "templates/behaviors/",
    "templates/MATRICES.md": "templates/matrices/",
    "templates/TOOLS.md": "templates/tools/",
    "templates/BUILDING-BETTER.md": "templates/integration/best-practices/",
}
COMPATIBILITY_MAP_RELATIVE_PATH = Path("registry") / "compatibility-map.json"


class TemplateNotFound(LookupError):
    """Raised when a template cannot be resolved and strict mode is enabled."""


class CompatibilityMapError(ValueError):
    """Raised when compatibility mapping data is invalid."""


@dataclass(frozen=True)
class CompatibilityEntry:
    """A versioned legacy-to-current template path mapping."""

    legacy: str
    current: str
    reason: str = ""


@dataclass(frozen=True)
class TemplateRecord:
    """A discoverable template or registry entry."""

    id: str
    path: str
    absolute_path: Path
    source: str
    tags: Tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)
    title: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    good_first_handler: bool = False
    good_first_workflow: bool = False


@dataclass(frozen=True)
class ResolutionResult:
    """Result returned by TemplateRegistry.resolve."""

    query: str
    status: str
    source: str
    record: Optional[TemplateRecord] = None
    path: Optional[str] = None
    fallback_action: Optional[str] = None
    message: str = ""

    @property
    def ok(self) -> bool:
        return self.status in {"found", "redirect", "fallback"}


class CompatibilityMap:
    """Bidirectional compatibility lookup table for legacy template paths."""

    def __init__(self, entries: Iterable[CompatibilityEntry], *, version: str = "unversioned") -> None:
        self.version = version
        self.entries = tuple(entries)
        forward: Dict[str, CompatibilityEntry] = {}
        reverse: Dict[str, CompatibilityEntry] = {}
        for entry in self.entries:
            legacy_key = _normal_key(entry.legacy)
            current_key = _normal_key(entry.current)
            if legacy_key in forward:
                raise CompatibilityMapError(f"Duplicate legacy compatibility key: {entry.legacy}")
            if current_key in reverse:
                existing = reverse[current_key]
                raise CompatibilityMapError(
                    f"Duplicate current compatibility target: {entry.current} "
                    f"({existing.legacy} and {entry.legacy})"
                )
            forward[legacy_key] = entry
            reverse[current_key] = entry
        self._forward = forward
        self._reverse = reverse

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, str], *, version: str = "mapping") -> "CompatibilityMap":
        return cls(
            (CompatibilityEntry(legacy=str(legacy), current=str(current)) for legacy, current in mapping.items()),
            version=version,
        )

    @classmethod
    def from_json_path(cls, path: Path) -> "CompatibilityMap":
        payload = json.loads(path.read_text(encoding="utf-8"))
        mappings = payload.get("mappings")
        if not isinstance(mappings, list):
            raise CompatibilityMapError(f"Compatibility map missing mappings list: {path}")
        entries: List[CompatibilityEntry] = []
        for index, raw_entry in enumerate(mappings, start=1):
            if not isinstance(raw_entry, dict):
                raise CompatibilityMapError(f"Compatibility map entry {index} is not an object")
            legacy = str(raw_entry.get("legacy") or "").strip()
            current = str(raw_entry.get("current") or "").strip()
            if not legacy or not current:
                raise CompatibilityMapError(f"Compatibility map entry {index} requires legacy and current")
            entries.append(
                CompatibilityEntry(
                    legacy=legacy,
                    current=current,
                    reason=str(raw_entry.get("reason") or ""),
                )
            )
        return cls(entries, version=str(payload.get("version") or "unversioned"))

    def target_for(self, legacy_path: str) -> Optional[str]:
        entry = self._forward.get(_normal_key(legacy_path))
        return entry.current if entry else None

    def legacy_for(self, current_path: str) -> Optional[str]:
        entry = self._reverse.get(_normal_key(current_path))
        return entry.legacy if entry else None

    def validate_targets(self, repo_root: Path) -> List[str]:
        issues: List[str] = []
        for entry in self.entries:
            target = repo_root / entry.current.rstrip("/")
            if not target.exists():
                issues.append(f"{entry.legacy} maps to missing target {entry.current}")
        return issues


@dataclass
class _RegistryIndex:
    records: Tuple[TemplateRecord, ...]
    by_id: Dict[str, TemplateRecord]
    by_path: Dict[str, TemplateRecord]


def parse_frontmatter(text: str) -> Dict[str, object]:
    """Parse a small YAML-frontmatter subset used by template docs."""
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}

    metadata: Dict[str, object] = {}
    current_list_key: Optional[str] = None
    for raw_line in parts[1].splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")) and current_list_key:
            stripped = line.strip()
            if stripped.startswith("-"):
                value = _strip_scalar(stripped[1:].strip())
                current = metadata.setdefault(current_list_key, [])
                if isinstance(current, list):
                    current.append(value)
            continue
        current_list_key = None
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not raw_value:
            metadata[key] = []
            current_list_key = key
            continue
        metadata[key] = _strip_scalar(raw_value)
    return metadata


def _strip_scalar(value: str) -> object:
    value = value.strip()
    if not value:
        return ""
    if value in {"true", "false"}:
        return value == "true"
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_strip_scalar(part.strip()) for part in inner.split(",")]
    return value


def _string_list(value: object) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),)


def _path_id(path: str) -> str:
    without_suffix = path[:-3] if path.endswith(".md") else path
    return without_suffix.replace("/", "-").replace("_", "-")


def _normal_key(value: str) -> str:
    return value.strip().lstrip("./").replace("\\", "/").lower()


@lru_cache(maxsize=512)
def _read_text_cached(path: str, mtime_ns: int) -> str:
    del mtime_ns
    return Path(path).read_text(encoding="utf-8")


class TemplateRegistry:
    """Discover, cache, search, and resolve template registry entries."""

    def __init__(
        self,
        repo_root: Path | str | None = None,
        *,
        ttl_seconds: float = 60.0,
        glob_patterns: Sequence[str] = ("*.md", "**/*.md"),
        compatibility_map: Optional[Mapping[str, str] | CompatibilityMap] = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.repo_root = Path(repo_root or Path(__file__).resolve().parent.parent).resolve()
        self.structure = load_repo_structure(self.repo_root)
        self.templates_root = self.structure.templates_root
        self.registry_index_path = self.templates_root / "registry" / "index.json"
        self.ttl_seconds = ttl_seconds
        self.glob_patterns = tuple(glob_patterns)
        self.compatibility_map = self._load_compatibility_map(compatibility_map)
        self.clock = clock
        self._lock = threading.RLock()
        self._cache: Optional[_RegistryIndex] = None
        self._cache_built_at: float = 0.0

    def _load_compatibility_map(
        self,
        compatibility_map: Optional[Mapping[str, str] | CompatibilityMap],
    ) -> CompatibilityMap:
        if isinstance(compatibility_map, CompatibilityMap):
            return compatibility_map
        if compatibility_map is not None:
            return CompatibilityMap.from_mapping(compatibility_map, version="constructor")
        compatibility_path = self.templates_root / COMPATIBILITY_MAP_RELATIVE_PATH
        if compatibility_path.exists():
            return CompatibilityMap.from_json_path(compatibility_path)
        return CompatibilityMap.from_mapping(DEFAULT_COMPATIBILITY_MAP, version="default")

    def invalidate_cache(self) -> None:
        with self._lock:
            self._cache = None
            self._cache_built_at = 0.0

    def records(self) -> Tuple[TemplateRecord, ...]:
        return self._index().records

    def get(self, template_id: str) -> Optional[TemplateRecord]:
        return self._index().by_id.get(_normal_key(template_id))

    def read_text(self, template_id: str) -> str:
        record = self.get(template_id)
        if record is None:
            raise TemplateNotFound(f"Template id not found: {template_id}")
        stat = record.absolute_path.stat()
        return _read_text_cached(str(record.absolute_path), stat.st_mtime_ns)

    def search(
        self,
        *,
        id: Optional[str] = None,
        type: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        text: Optional[str] = None,
    ) -> List[TemplateRecord]:
        wanted_tags = {_normal_key(tag) for tag in tags or []}
        text_key = _normal_key(text) if text else None
        results: List[TemplateRecord] = []
        for record in self.records():
            if id and _normal_key(record.id) != _normal_key(id):
                continue
            if type and _normal_key(record.type or "") != _normal_key(type):
                continue
            if category and _normal_key(record.category or "") != _normal_key(category):
                continue
            if wanted_tags and not wanted_tags.issubset({_normal_key(tag) for tag in record.tags}):
                continue
            if text_key:
                haystack = " ".join(
                    [
                        record.id,
                        record.path,
                        record.title or "",
                        record.type or "",
                        record.category or "",
                        " ".join(record.tags),
                    ]
                )
                if text_key not in _normal_key(haystack):
                    continue
            results.append(record)
        return results

    def resolve(self, query: str, *, allow_serena: bool = True, strict: bool = False) -> ResolutionResult:
        index = self._index()
        key = _normal_key(query)
        if key in index.by_id:
            record = index.by_id[key]
            return ResolutionResult(query=query, status="found", source=record.source, record=record, path=record.path)
        path_record = index.by_path.get(key)
        if path_record and path_record.source == "modular":
            return ResolutionResult(
                query=query,
                status="found",
                source=path_record.source,
                record=path_record,
                path=path_record.path,
            )

        compatibility_target = self._compatibility_target(query)
        if compatibility_target:
            target_key = _normal_key(compatibility_target)
            record = index.by_path.get(target_key)
            return ResolutionResult(
                query=query,
                status="redirect",
                source="compatibility",
                record=record,
                path=compatibility_target,
                message=f"Use {compatibility_target} instead of {query}",
            )

        if path_record:
            source = "legacy" if path_record.source == "discovered" else path_record.source
            return ResolutionResult(
                query=query,
                status="found",
                source=source,
                record=path_record,
                path=path_record.path,
            )

        legacy_record = self._legacy_record(query)
        if legacy_record:
            return ResolutionResult(
                query=query,
                status="found",
                source="legacy",
                record=legacy_record,
                path=legacy_record.path,
            )

        if allow_serena:
            return ResolutionResult(
                query=query,
                status="fallback",
                source="serena",
                fallback_action="serena_search",
                message=f"Search Serena memories or semantic index for {query}",
            )

        if strict:
            raise TemplateNotFound(f"Template not found: {query}")
        return ResolutionResult(query=query, status="error", source="error", message=f"Template not found: {query}")

    def _index(self) -> _RegistryIndex:
        now = self.clock()
        with self._lock:
            if self._cache is not None and now - self._cache_built_at < self.ttl_seconds:
                return self._cache
            self._cache = self._build_index()
            self._cache_built_at = now
            return self._cache

    def _build_index(self) -> _RegistryIndex:
        records: List[TemplateRecord] = []
        by_path: Dict[str, TemplateRecord] = {}
        by_id: Dict[str, TemplateRecord] = {}

        for record in self._load_modular_records():
            self._add_record(record, records, by_id, by_path)

        for record in self._discover_markdown_records():
            self._add_record(record, records, by_id, by_path)

        return _RegistryIndex(tuple(records), by_id, by_path)

    def _add_record(
        self,
        record: TemplateRecord,
        records: List[TemplateRecord],
        by_id: Dict[str, TemplateRecord],
        by_path: Dict[str, TemplateRecord],
    ) -> None:
        path_key = _normal_key(record.path)
        id_key = _normal_key(record.id)
        if path_key in by_path:
            return
        records.append(record)
        by_path[path_key] = record
        by_id.setdefault(id_key, record)

    def _load_modular_records(self) -> Iterable[TemplateRecord]:
        if not self.registry_index_path.exists():
            return []
        payload = json.loads(self.registry_index_path.read_text(encoding="utf-8"))
        records: List[TemplateRecord] = []
        for raw_entry in payload:
            if not isinstance(raw_entry, dict) or not raw_entry.get("path"):
                continue
            path = str(raw_entry["path"])
            absolute_path = self._absolute_from_registry_path(path)
            metadata = self._frontmatter_for_path(absolute_path)
            tags = tuple(str(tag) for tag in raw_entry.get("tags", []) if str(tag))
            record = self._record_from_parts(
                template_id=str(raw_entry.get("id") or metadata.get("id") or _path_id(path)),
                path=self._repo_relative_path(absolute_path),
                absolute_path=absolute_path,
                source="modular",
                tags=tags or _string_list(metadata.get("tags")),
                metadata=metadata,
                good_first_handler=bool(raw_entry.get("goodFirstHandler", False)),
                good_first_workflow=bool(raw_entry.get("goodFirstWorkflow", False)),
            )
            records.append(record)
        return records

    def _discover_markdown_records(self) -> Iterable[TemplateRecord]:
        if not self.templates_root.exists():
            return []
        discovered: List[TemplateRecord] = []
        seen: set[Path] = set()
        for pattern in self.glob_patterns:
            for path in self.templates_root.glob(pattern):
                if not path.is_file() or path.suffix != ".md" or path in seen:
                    continue
                seen.add(path)
                metadata = self._frontmatter_for_path(path)
                repo_relative = self._repo_relative_path(path)
                discovered.append(
                    self._record_from_parts(
                        template_id=str(metadata.get("id") or _path_id(repo_relative)),
                        path=repo_relative,
                        absolute_path=path,
                        source="discovered",
                        tags=_string_list(metadata.get("tags")),
                        metadata=metadata,
                    )
                )
        return discovered

    def _record_from_parts(
        self,
        *,
        template_id: str,
        path: str,
        absolute_path: Path,
        source: str,
        tags: Tuple[str, ...],
        metadata: Mapping[str, object],
        good_first_handler: bool = False,
        good_first_workflow: bool = False,
    ) -> TemplateRecord:
        category = metadata.get("category")
        if not category:
            category = self._category_from_path(path)
        return TemplateRecord(
            id=template_id,
            path=path,
            absolute_path=absolute_path,
            source=source,
            tags=tags,
            metadata=metadata,
            title=_string_or_none(metadata.get("title") or metadata.get("name")),
            type=_string_or_none(metadata.get("type")),
            status=_string_or_none(metadata.get("status")),
            category=_string_or_none(category),
            good_first_handler=good_first_handler,
            good_first_workflow=good_first_workflow,
        )

    def _frontmatter_for_path(self, path: Path) -> Dict[str, object]:
        if not path.exists() or path.suffix != ".md":
            return {}
        return parse_frontmatter(path.read_text(encoding="utf-8"))

    def _absolute_from_registry_path(self, raw_path: str) -> Path:
        candidate = Path(raw_path)
        if candidate.is_absolute():
            return candidate.resolve()
        repo_candidate = (self.repo_root / candidate).resolve()
        if repo_candidate.exists() or raw_path.startswith(f"{self.templates_root.relative_to(self.repo_root).as_posix()}/"):
            return repo_candidate
        return (self.templates_root / candidate).resolve()

    def _repo_relative_path(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.repo_root).as_posix()
        except ValueError:
            return path.as_posix()

    def _category_from_path(self, path: str) -> Optional[str]:
        templates_rel = self.templates_root.relative_to(self.repo_root).as_posix()
        path_text = Path(path).as_posix()
        prefix = f"{templates_rel}/"
        if path_text.startswith(prefix):
            relative_parts = Path(path_text[len(prefix) :]).parts
            return relative_parts[0] if relative_parts else None
        parts = Path(path_text).parts
        if parts:
            return parts[0]
        return None

    def _compatibility_target(self, query: str) -> Optional[str]:
        candidates = [query]
        templates_rel = self.templates_root.relative_to(self.repo_root).as_posix()
        if not query.startswith("templates/"):
            candidates.append(f"templates/{query.lstrip('/')}")
        if templates_rel != "templates" and query.startswith(f"{templates_rel}/"):
            candidates.append(f"templates/{query[len(templates_rel) + 1:]}")
        for candidate in candidates:
            target = self.compatibility_map.target_for(candidate)
            if not target:
                continue
            if templates_rel != "templates" and target.startswith("templates/"):
                target = f"{templates_rel}/{target[len('templates/'):]}"
            return target
        return None

    def _legacy_record(self, query: str) -> Optional[TemplateRecord]:
        path = self._absolute_from_registry_path(query)
        if not path.exists() or not path.is_file():
            return None
        metadata = self._frontmatter_for_path(path)
        repo_relative = self._repo_relative_path(path)
        return self._record_from_parts(
            template_id=str(metadata.get("id") or _path_id(repo_relative)),
            path=repo_relative,
            absolute_path=path,
            source="legacy",
            tags=_string_list(metadata.get("tags")),
            metadata=metadata,
        )


def _string_or_none(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value)
    return text if text else None
