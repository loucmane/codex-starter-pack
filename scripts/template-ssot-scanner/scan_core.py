#!/usr/bin/env python3
"""Core file-discovery utilities for the Template SSOT scanner suite."""

from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Optional, Sequence

SCANNABLE_SUFFIXES = (".md", ".json", ".yml", ".yaml")
DEFAULT_CONFIG_DIRS = (".codex", ".claude")

DEFAULT_EXCLUDE_PATTERNS = (
    ".codex/.tmp/**",
    ".codex/cache/**",
    ".codex/log/**",
    ".codex/plugins/**",
    ".codex/sessions/**",
    ".codex/shell_snapshots/**",
    ".codex/skills/**",
    ".codex/tmp/**",
    ".codex/auth.json",
    ".codex/history.jsonl",
    ".codex/installation_id",
    ".codex/models_cache.json",
    ".codex/state_*.sqlite*",
    ".codex/version.json",
)


@dataclass(frozen=True)
class ScannerConfig:
    """Resolved file-discovery configuration for scanner modules."""

    base_path: Path
    include_pattern: Optional[str] = None
    include_patterns: Sequence[str] = field(default_factory=tuple)
    exclude_patterns: Sequence[str] = field(default_factory=lambda: DEFAULT_EXCLUDE_PATTERNS)
    supported_suffixes: Sequence[str] = field(default_factory=lambda: SCANNABLE_SUFFIXES)
    config_dirs: Sequence[str] = field(default_factory=lambda: DEFAULT_CONFIG_DIRS)
    pattern_matcher: Any = None
    scan_rule_name: Optional[str] = "scan_scope"

    @classmethod
    def from_cli(
        cls,
        base_path: Path,
        include_pattern: Optional[str] = None,
        exclude_pattern: Optional[str] = None,
    ) -> "ScannerConfig":
        excludes = list(DEFAULT_EXCLUDE_PATTERNS)
        if exclude_pattern:
            excludes.extend(
                pattern.strip()
                for pattern in exclude_pattern.split(",")
                if pattern.strip()
            )
        return cls(base_path=base_path, include_pattern=include_pattern, exclude_patterns=tuple(excludes))

    @property
    def effective_include_patterns(self) -> tuple[str, ...]:
        """Return configured include patterns with CLI include taking precedence."""
        if self.include_pattern:
            return (self.include_pattern,)
        return tuple(self.include_patterns)

    def should_scan(self, relative_path: str) -> bool:
        """Return whether a relative path should be included in scanner diagnostics."""
        return should_scan_relative_path(
            relative_path,
            include_pattern=self.include_pattern,
            exclude_patterns=self.exclude_patterns,
            include_patterns=self.include_patterns,
            pattern_matcher=self.pattern_matcher,
            rule_name=self.scan_rule_name,
        )


def relative_posix_path(base_path: Path, file_path: Path) -> str:
    """Return a stable POSIX-style path relative to the scan base."""
    return file_path.relative_to(base_path).as_posix()


def should_scan_relative_path(
    relative_path: str,
    include_pattern: Optional[str] = None,
    exclude_patterns: Sequence[str] = DEFAULT_EXCLUDE_PATTERNS,
    include_patterns: Sequence[str] = (),
    pattern_matcher: Any = None,
    rule_name: Optional[str] = "scan_scope",
) -> bool:
    """Return whether a relative path belongs in scanner diagnostics."""
    if pattern_matcher is not None:
        decision = pattern_matcher.decide(relative_path, "paths", rule_name)
        if decision.blocked:
            return False
        if decision.allowed:
            return True

    effective_include_patterns = (include_pattern,) if include_pattern else tuple(include_patterns)
    if effective_include_patterns and not any(fnmatch(relative_path, pattern) for pattern in effective_include_patterns):
        return False

    return not any(fnmatch(relative_path, pattern) for pattern in exclude_patterns)


def collect_scannable_files(directory: Path, config: ScannerConfig) -> list[Path]:
    """Collect markdown/config files with one deterministic directory traversal."""
    supported_suffixes = tuple(dict.fromkeys(config.supported_suffixes))
    filtered_files = []
    for file_path in sorted(
        directory.rglob("*"),
        key=lambda path: relative_posix_path(config.base_path, path),
    ):
        if not file_path.is_file() or file_path.suffix not in supported_suffixes:
            continue
        relative_path = relative_posix_path(config.base_path, file_path)
        if config.should_scan(relative_path):
            filtered_files.append(file_path)

    return filtered_files


def discover_config_dirs(base_path: Path, config_dirs: Sequence[str] = DEFAULT_CONFIG_DIRS) -> list[Path]:
    """Return supported project config directories in scan order."""
    discovered = []
    for dir_name in config_dirs:
        config_path = base_path / dir_name
        if config_path.exists():
            discovered.append(config_path)
    return discovered
