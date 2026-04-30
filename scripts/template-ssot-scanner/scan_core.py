#!/usr/bin/env python3
"""Core file-discovery utilities for the Template SSOT scanner suite."""

from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Optional, Sequence

SCANNABLE_SUFFIXES = (".md", ".json", ".yml", ".yaml")

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
    exclude_patterns: Sequence[str] = field(default_factory=lambda: DEFAULT_EXCLUDE_PATTERNS)

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


def relative_posix_path(base_path: Path, file_path: Path) -> str:
    """Return a stable POSIX-style path relative to the scan base."""
    return file_path.relative_to(base_path).as_posix()


def should_scan_relative_path(
    relative_path: str,
    include_pattern: Optional[str] = None,
    exclude_patterns: Sequence[str] = DEFAULT_EXCLUDE_PATTERNS,
) -> bool:
    """Return whether a relative path belongs in scanner diagnostics."""
    if include_pattern and not fnmatch(relative_path, include_pattern):
        return False

    return not any(fnmatch(relative_path, pattern) for pattern in exclude_patterns)


def collect_scannable_files(directory: Path, config: ScannerConfig) -> list[Path]:
    """Collect markdown/config files in deterministic scanner order."""
    files: list[Path] = []
    for suffix in SCANNABLE_SUFFIXES:
        files.extend(directory.rglob(f"*{suffix}"))

    filtered_files = []
    for file_path in files:
        relative_path = relative_posix_path(config.base_path, file_path)
        if should_scan_relative_path(relative_path, config.include_pattern, config.exclude_patterns):
            filtered_files.append(file_path)

    return filtered_files


def discover_config_dirs(base_path: Path) -> list[Path]:
    """Return supported project config directories in scan order."""
    config_dirs = []
    for dir_name in (".codex", ".claude"):
        config_path = base_path / dir_name
        if config_path.exists():
            config_dirs.append(config_path)
    return config_dirs
