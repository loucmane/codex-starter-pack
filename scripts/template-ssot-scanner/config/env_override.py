#!/usr/bin/env python3
"""Environment variable overrides for scanner configuration."""

from __future__ import annotations

import copy
import os
import time
from dataclasses import dataclass
from typing import Any, Mapping

import yaml

DEFAULT_ENV_PREFIX = "CODEX_SCANNER_"
SECTION_ALIASES = {
    "ALLOWLISTS": "allowlists",
    "BLOCKLISTS": "blocklists",
    "ENVIRONMENT": "environment_overlays",
    "ENVIRONMENT_OVERLAYS": "environment_overlays",
    "METADATA": "metadata",
    "PROFILES": "profiles",
    "SCAN": "scan_scope",
    "SCAN_SCOPE": "scan_scope",
    "VALIDATION": "validation_rules",
    "VALIDATION_RULES": "validation_rules",
}


class EnvOverrideError(ValueError):
    """Base exception for environment override failures."""


class EnvOverrideNameError(EnvOverrideError):
    """Raised when an override environment variable cannot be mapped to config keys."""


class EnvOverrideValueError(EnvOverrideError):
    """Raised when an override value cannot be coerced safely."""


@dataclass(frozen=True)
class EnvOverride:
    """Single parsed environment override."""

    env_name: str
    path: tuple[str, ...]
    value: Any
    raw_value: str


@dataclass(frozen=True)
class EnvOverrideResult:
    """Config data plus applied override metadata."""

    data: dict[str, Any]
    overrides: tuple[EnvOverride, ...]
    duration_seconds: float


def _normalize_segment(segment: str) -> str:
    normalized = segment.strip("_").lower()
    if not normalized:
        raise EnvOverrideNameError("Environment override path segments must not be empty")
    return normalized


def _path_from_suffix(suffix: str) -> tuple[str, ...]:
    if "__" in suffix:
        raw_parts = suffix.split("__")
        if any(part == "" for part in raw_parts):
            raise EnvOverrideNameError(f"Invalid empty path segment in override suffix {suffix!r}")
        parts = [_normalize_segment(part) for part in raw_parts]
        first = SECTION_ALIASES.get(raw_parts[0].upper(), parts[0])
        return (first, *parts[1:])

    upper_suffix = suffix.upper()
    for alias in sorted(SECTION_ALIASES, key=len, reverse=True):
        prefix = f"{alias}_"
        if upper_suffix.startswith(prefix):
            first = SECTION_ALIASES[alias]
            remainder = suffix[len(prefix) :]
            if not remainder:
                raise EnvOverrideNameError(f"Override suffix {suffix!r} is missing a nested path")
            return (first, *(_normalize_segment(part) for part in remainder.split("_") if part))

    return tuple(_normalize_segment(part) for part in suffix.split("_") if part)


def parse_env_value(raw_value: str) -> Any:
    """Parse an environment override value using YAML scalar/list/map rules."""
    try:
        parsed = yaml.safe_load(raw_value)
    except yaml.YAMLError as exc:
        raise EnvOverrideValueError(f"Unable to parse environment override value {raw_value!r}: {exc}") from exc
    if parsed is None and raw_value.strip().lower() not in {"null", "~"}:
        return ""
    return parsed


def parse_env_overrides(
    environ: Mapping[str, str] | None = None,
    prefix: str = DEFAULT_ENV_PREFIX,
) -> tuple[EnvOverride, ...]:
    """Parse CODEX_SCANNER_ environment variables into override objects."""
    source = os.environ if environ is None else environ
    overrides: list[EnvOverride] = []
    for env_name in sorted(source):
        if not env_name.startswith(prefix):
            continue
        suffix = env_name[len(prefix) :]
        if not suffix:
            raise EnvOverrideNameError(f"Environment override {env_name!r} is missing a config path")
        raw_value = source[env_name]
        overrides.append(
            EnvOverride(
                env_name=env_name,
                path=_path_from_suffix(suffix),
                value=parse_env_value(raw_value),
                raw_value=raw_value,
            )
        )
    return tuple(overrides)


def _assign_path(data: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    cursor: dict[str, Any] = data
    for segment in path[:-1]:
        existing = cursor.get(segment)
        if existing is None:
            next_cursor: dict[str, Any] = {}
            cursor[segment] = next_cursor
            cursor = next_cursor
            continue
        if not isinstance(existing, dict):
            joined = ".".join(path)
            raise EnvOverrideNameError(f"Cannot apply override {joined}: {segment!r} is not a mapping")
        cursor = existing
    cursor[path[-1]] = copy.deepcopy(value)


def apply_env_overrides(
    config: Mapping[str, Any],
    environ: Mapping[str, str] | None = None,
    prefix: str = DEFAULT_ENV_PREFIX,
) -> EnvOverrideResult:
    """Apply CODEX_SCANNER_ overrides to a config mapping."""
    start = time.perf_counter()
    output = copy.deepcopy(dict(config))
    overrides = parse_env_overrides(environ=environ, prefix=prefix)
    for override in overrides:
        _assign_path(output, override.path, override.value)
    return EnvOverrideResult(
        data=output,
        overrides=overrides,
        duration_seconds=time.perf_counter() - start,
    )
