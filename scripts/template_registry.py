#!/usr/bin/env python3
"""Portable template registry discovery and lookup utilities."""

from __future__ import annotations

import json
import sys
import threading
import time
from dataclasses import dataclass, field
from difflib import SequenceMatcher
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
DISCOVERY_METRIC_KEYS: Tuple[str, ...] = ("modular", "compatibility", "legacy", "serena", "error")


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
    aliases: Tuple[str, ...] = ()
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
    trace: Tuple[str, ...] = ()
    suggestions: Tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.status in {"found", "redirect", "fallback"}


@dataclass(frozen=True)
class CacheWarmEntry:
    """Single query result from TemplateRegistry.warm_cache."""

    query: str
    ok: bool
    status: str
    source: str
    path: Optional[str] = None
    message: str = ""


@dataclass(frozen=True)
class CacheWarmResult:
    """Summary returned by TemplateRegistry.warm_cache."""

    entries: Tuple[CacheWarmEntry, ...]

    @property
    def success_count(self) -> int:
        return sum(1 for entry in self.entries if entry.ok)

    @property
    def failure_count(self) -> int:
        return sum(1 for entry in self.entries if not entry.ok)


@dataclass(frozen=True)
class CacheStats:
    """Snapshot of TemplateRegistry cache diagnostics."""

    index: Mapping[str, object]
    read_text: Mapping[str, object]

    def as_dict(self) -> Dict[str, Mapping[str, object]]:
        return {"index": dict(self.index), "read_text": dict(self.read_text)}


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


def _aliases_for(primary_id: str, *values: object) -> Tuple[str, ...]:
    aliases: List[str] = []
    seen = {_normal_key(primary_id)}
    for value in values:
        for alias in _string_list(value):
            key = _normal_key(alias)
            if not key or key in seen:
                continue
            seen.add(key)
            aliases.append(alias)
    return tuple(aliases)


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
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_rebuilds = 0
        self._cache_invalidations = 0
        self._discovery_metrics: Dict[str, int] = {key: 0 for key in DISCOVERY_METRIC_KEYS}

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
            self._cache_invalidations += 1

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

    def discovery_metrics(self) -> Dict[str, int]:
        """Return a snapshot of resolve-path usage for this registry instance."""
        with self._lock:
            return dict(self._discovery_metrics)

    def reset_discovery_metrics(self) -> None:
        """Reset resolve-path usage metrics for this registry instance."""
        with self._lock:
            self._discovery_metrics = {key: 0 for key in DISCOVERY_METRIC_KEYS}

    def cache_stats(self) -> Dict[str, Mapping[str, object]]:
        """Return a copy-safe snapshot of registry index and text cache diagnostics."""
        text_cache = _read_text_cached.cache_info()
        with self._lock:
            cached = self._cache is not None
            now = self.clock()
            age_seconds: Optional[float] = None
            ttl_remaining_seconds: Optional[float] = None
            record_count = 0
            if cached:
                age_seconds = max(0.0, now - self._cache_built_at)
                ttl_remaining_seconds = max(0.0, self.ttl_seconds - age_seconds)
                record_count = len(self._cache.records) if self._cache is not None else 0
            stats = CacheStats(
                index={
                    "cached": cached,
                    "ttl_seconds": self.ttl_seconds,
                    "age_seconds": age_seconds,
                    "ttl_remaining_seconds": ttl_remaining_seconds,
                    "record_count": record_count,
                    "hits": self._cache_hits,
                    "misses": self._cache_misses,
                    "rebuilds": self._cache_rebuilds,
                    "invalidations": self._cache_invalidations,
                },
                read_text={
                    "hits": text_cache.hits,
                    "misses": text_cache.misses,
                    "maxsize": text_cache.maxsize,
                    "currsize": text_cache.currsize,
                },
            )
        return stats.as_dict()

    def reset_cache_stats(self, *, clear_text_cache: bool = False) -> None:
        """Reset cache counters while preserving the currently cached registry index."""
        with self._lock:
            self._cache_hits = 0
            self._cache_misses = 0
            self._cache_rebuilds = 0
            self._cache_invalidations = 0
        if clear_text_cache:
            _read_text_cached.cache_clear()

    def warm_cache(self, queries: Iterable[str], *, allow_serena: bool = False) -> CacheWarmResult:
        """Resolve common queries to build the index cache and report misses without raising."""
        entries: List[CacheWarmEntry] = []
        for query in queries:
            result = self.resolve(query, allow_serena=allow_serena, strict=False)
            entries.append(
                CacheWarmEntry(
                    query=query,
                    ok=result.ok,
                    status=result.status,
                    source=result.source,
                    path=result.path,
                    message=result.message,
                )
            )
        return CacheWarmResult(tuple(entries))

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
                        " ".join(record.aliases),
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
            return self._finish_resolution(
                ResolutionResult(
                    query=query,
                    status="found",
                    source=record.source,
                    record=record,
                    path=record.path,
                    trace=("modular_id:hit",),
                )
            )
        trace: List[str] = ["modular_id:miss"]
        path_record = index.by_path.get(key)
        if path_record and path_record.source == "modular":
            trace.append("modular_path:hit")
            return self._finish_resolution(
                ResolutionResult(
                    query=query,
                    status="found",
                    source=path_record.source,
                    record=path_record,
                    path=path_record.path,
                    trace=tuple(trace),
                )
            )
        trace.append("modular_path:miss")

        compatibility_target = self._compatibility_target(query)
        if compatibility_target:
            trace.append("compatibility:hit")
            target_key = _normal_key(compatibility_target)
            record = index.by_path.get(target_key)
            return self._finish_resolution(
                ResolutionResult(
                    query=query,
                    status="redirect",
                    source="compatibility",
                    record=record,
                    path=compatibility_target,
                    message=f"Use {compatibility_target} instead of {query}",
                    trace=tuple(trace),
                )
            )
        trace.append("compatibility:miss")

        if path_record:
            trace.append("legacy_index:hit")
            source = "legacy" if path_record.source == "discovered" else path_record.source
            return self._finish_resolution(
                ResolutionResult(
                    query=query,
                    status="found",
                    source=source,
                    record=path_record,
                    path=path_record.path,
                    trace=tuple(trace),
                )
            )
        trace.append("legacy_index:miss")

        legacy_record = self._legacy_record(query)
        if legacy_record:
            trace.append("legacy_file:hit")
            return self._finish_resolution(
                ResolutionResult(
                    query=query,
                    status="found",
                    source="legacy",
                    record=legacy_record,
                    path=legacy_record.path,
                    trace=tuple(trace),
                )
            )
        trace.append("legacy_file:miss")

        suggestions = self._suggestions_for(query, index)
        if allow_serena:
            trace.append("serena:fallback")
            message = f"Search Serena memories or semantic index for {query}"
            if suggestions:
                message = f"{message}. Local suggestions: {', '.join(suggestions)}"
            return self._finish_resolution(
                ResolutionResult(
                    query=query,
                    status="fallback",
                    source="serena",
                    fallback_action="serena_search",
                    message=message,
                    trace=tuple(trace),
                    suggestions=suggestions,
                )
            )
        trace.append("serena:disabled")

        message = f"Template not found: {query}"
        if suggestions:
            message = f"{message}. Suggestions: {', '.join(suggestions)}"
        if strict:
            self._record_discovery_metric("error")
            raise TemplateNotFound(message)
        trace.append("error:not_found")
        return self._finish_resolution(
            ResolutionResult(
                query=query,
                status="error",
                source="error",
                message=message,
                trace=tuple(trace),
                suggestions=suggestions,
            )
        )

    def _index(self) -> _RegistryIndex:
        now = self.clock()
        with self._lock:
            if self._cache is not None and now - self._cache_built_at < self.ttl_seconds:
                self._cache_hits += 1
                return self._cache
            self._cache_misses += 1
            self._cache = self._build_index()
            self._cache_built_at = now
            self._cache_rebuilds += 1
            return self._cache

    def _build_index(self) -> _RegistryIndex:
        records: List[TemplateRecord] = []
        by_path: Dict[str, TemplateRecord] = {}
        by_id: Dict[str, TemplateRecord] = {}

        for record in self._load_modular_records():
            self._add_record(record, records, by_id, by_path)

        for record in self._discover_markdown_records(excluded_paths=set(by_path)):
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
            existing = by_path[path_key]
            by_id.setdefault(id_key, existing)
            for alias in record.aliases:
                by_id.setdefault(_normal_key(alias), existing)
            return
        records.append(record)
        by_path[path_key] = record
        by_id.setdefault(id_key, record)
        for alias in record.aliases:
            by_id.setdefault(_normal_key(alias), record)

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
            template_id = str(raw_entry.get("id") or metadata.get("id") or _path_id(path))
            record = self._record_from_parts(
                template_id=template_id,
                path=self._repo_relative_path(absolute_path),
                absolute_path=absolute_path,
                source="modular",
                tags=tags or _string_list(metadata.get("tags")),
                metadata=metadata,
                aliases=_aliases_for(
                    template_id,
                    raw_entry.get("aliases"),
                    metadata.get("id"),
                    metadata.get("aliases"),
                ),
                good_first_handler=bool(raw_entry.get("goodFirstHandler", False)),
                good_first_workflow=bool(raw_entry.get("goodFirstWorkflow", False)),
            )
            records.append(record)
        return records

    def _discover_markdown_records(self, *, excluded_paths: Optional[set[str]] = None) -> Iterable[TemplateRecord]:
        if not self.templates_root.exists():
            return []
        discovered: List[TemplateRecord] = []
        excluded_paths = excluded_paths or set()
        seen: set[Path] = set()
        for pattern in self.glob_patterns:
            for path in self.templates_root.glob(pattern):
                if not path.is_file() or path.suffix != ".md" or path in seen:
                    continue
                seen.add(path)
                repo_relative = self._repo_relative_path(path)
                if _normal_key(repo_relative) in excluded_paths:
                    continue
                metadata = self._frontmatter_for_path(path)
                discovered.append(
                    self._record_from_parts(
                        template_id=str(metadata.get("id") or _path_id(repo_relative)),
                        path=repo_relative,
                        absolute_path=path,
                        source="discovered",
                        tags=_string_list(metadata.get("tags")),
                        metadata=metadata,
                        aliases=_aliases_for(
                            str(metadata.get("id") or _path_id(repo_relative)),
                            metadata.get("aliases"),
                        ),
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
        aliases: Tuple[str, ...] = (),
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
            aliases=aliases,
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

    def _finish_resolution(self, result: ResolutionResult) -> ResolutionResult:
        self._record_discovery_metric(_metric_key_for_source(result.source))
        return result

    def _record_discovery_metric(self, key: str) -> None:
        if key not in DISCOVERY_METRIC_KEYS:
            key = "error"
        with self._lock:
            self._discovery_metrics[key] = self._discovery_metrics.get(key, 0) + 1

    def _suggestions_for(self, query: str, index: _RegistryIndex, *, limit: int = 5) -> Tuple[str, ...]:
        query_key = _normal_key(query)
        if not query_key:
            return ()

        scored: Dict[str, float] = {}

        for record in index.records:
            candidates = [
                record.id,
                record.path,
                record.title or "",
                record.type or "",
                record.category or "",
                *record.tags,
                *record.aliases,
            ]
            score = max((_similarity(query_key, candidate) for candidate in candidates), default=0.0)
            if score >= 0.55:
                scored[record.id] = max(scored.get(record.id, 0.0), score)

        templates_rel = self.templates_root.relative_to(self.repo_root).as_posix()
        for entry in self.compatibility_map.entries:
            current = entry.current
            legacy = entry.legacy
            if templates_rel != "templates":
                if current.startswith("templates/"):
                    current = f"{templates_rel}/{current[len('templates/'):]}"
                if legacy.startswith("templates/"):
                    legacy = f"{templates_rel}/{legacy[len('templates/'):]}"
            score = max(_similarity(query_key, legacy), _similarity(query_key, current))
            if score >= 0.55:
                scored[current] = max(scored.get(current, 0.0), score)

        return tuple(
            suggestion
            for suggestion, _score in sorted(scored.items(), key=lambda item: (-item[1], item[0]))[:limit]
        )

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


class TemplateDiscoveryAPI:
    """Serializable facade for template discovery and dependency access."""

    def __init__(self, registry: Optional[TemplateRegistry] = None, *, repo_root: Path | str | None = None) -> None:
        self.registry = registry or TemplateRegistry(repo_root=repo_root)

    def get_template(self, template_id: str) -> Optional[Dict[str, object]]:
        record = self.registry.get(template_id)
        return self.serialize_record(record) if record else None

    def search_templates(
        self,
        query: Optional[str] = None,
        *,
        category: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, object]:
        records = self.registry.search(type=type, category=category, tags=tags, text=query)
        filtered = self._filter_records(records, status=status, version=version)
        return self._paginated_response(filtered, limit=limit, offset=offset)

    def list_by_category(
        self,
        category: str,
        *,
        status: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, object]:
        return self.search_templates(
            category=category,
            status=status,
            version=version,
            tags=tags,
            limit=limit,
            offset=offset,
        )

    def get_dependencies(self, template_id: str) -> Optional[Dict[str, object]]:
        record = self.registry.get(template_id)
        if record is None:
            return None

        dependencies = _string_list(record.metadata.get("dependencies"))
        resolved: List[Dict[str, object]] = []
        missing: List[str] = []
        for dependency in dependencies:
            result = self.registry.resolve(dependency, allow_serena=False, strict=False)
            if result.record is None:
                missing.append(dependency)
                continue
            resolved.append(
                {
                    "query": dependency,
                    "id": result.record.id,
                    "path": result.record.path,
                    "source": result.source,
                    "status": result.status,
                }
            )

        return {
            "id": record.id,
            "path": record.path,
            "dependencies": list(dependencies),
            "resolved": resolved,
            "missing": missing,
        }

    @staticmethod
    def serialize_record(record: TemplateRecord) -> Dict[str, object]:
        return {
            "id": record.id,
            "path": record.path,
            "title": record.title,
            "type": record.type,
            "category": record.category,
            "status": record.status,
            "version": _string_or_none(record.metadata.get("version")),
            "tags": list(record.tags),
            "dependencies": list(_string_list(record.metadata.get("dependencies"))),
            "source": record.source,
            "good_first_handler": record.good_first_handler,
            "good_first_workflow": record.good_first_workflow,
            "metadata": dict(record.metadata),
        }

    def _filter_records(
        self,
        records: Sequence[TemplateRecord],
        *,
        status: Optional[str],
        version: Optional[str],
    ) -> List[TemplateRecord]:
        filtered: List[TemplateRecord] = []
        for record in records:
            if status and _normal_key(record.status or "") != _normal_key(status):
                continue
            record_version = _string_or_none(record.metadata.get("version"))
            if version and _normal_key(record_version or "") != _normal_key(version):
                continue
            filtered.append(record)
        return filtered

    def _paginated_response(
        self,
        records: Sequence[TemplateRecord],
        *,
        limit: int,
        offset: int,
    ) -> Dict[str, object]:
        if limit < 1:
            raise ValueError("limit must be greater than zero")
        if offset < 0:
            raise ValueError("offset must be greater than or equal to zero")

        total = len(records)
        page = records[offset : offset + limit]
        return {
            "items": [self.serialize_record(record) for record in page],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "count": len(page),
                "has_more": offset + len(page) < total,
            },
        }


TemplateAPI = TemplateDiscoveryAPI


def _string_or_none(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _metric_key_for_source(source: str) -> str:
    if source == "compatibility":
        return "compatibility"
    if source in {"legacy", "discovered"}:
        return "legacy"
    if source == "serena":
        return "serena"
    if source == "error":
        return "error"
    return "modular"


def _similarity(query_key: str, candidate: str) -> float:
    candidate_key = _normal_key(candidate)
    if not candidate_key:
        return 0.0
    if query_key == candidate_key:
        return 1.0
    if query_key in candidate_key or candidate_key in query_key:
        return 0.9
    return SequenceMatcher(None, query_key, candidate_key).ratio()
