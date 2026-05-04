#!/usr/bin/env python3
"""Configuration inheritance, profile, and environment overlay resolution."""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class ConfigInheritanceError(ValueError):
    """Base exception for config inheritance failures."""


class UnknownConfigProfileError(ConfigInheritanceError):
    """Raised when a requested profile does not exist."""


class UnknownEnvironmentOverlayError(ConfigInheritanceError):
    """Raised when a requested environment overlay does not exist."""


class ConfigInheritanceCycleError(ConfigInheritanceError):
    """Raised when profile or overlay inheritance has a cycle."""


class ConfigMergeStrategyError(ConfigInheritanceError):
    """Raised when a merge strategy is invalid."""


class MergeStrategy(str, Enum):
    """Supported merge strategies for profiles and overlays."""

    DEEP_MERGE = "deep_merge"
    REPLACE = "replace"

    @classmethod
    def from_value(cls, value: str | None) -> "MergeStrategy":
        if value is None:
            return cls.DEEP_MERGE
        try:
            return cls(value)
        except ValueError as exc:
            valid = ", ".join(strategy.value for strategy in cls)
            raise ConfigMergeStrategyError(f"Invalid merge strategy {value!r}. Expected one of: {valid}") from exc


@dataclass(frozen=True)
class ResolvedConfig:
    """Resolved scanner config plus inheritance metadata."""

    data: dict[str, Any]
    profile: str | None = None
    environment: str | None = None
    applied_profiles: tuple[str, ...] = field(default_factory=tuple)
    applied_overlays: tuple[str, ...] = field(default_factory=tuple)
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Return serializable resolution metadata and config data."""
        return {
            "profile": self.profile,
            "environment": self.environment,
            "applied_profiles": list(self.applied_profiles),
            "applied_overlays": list(self.applied_overlays),
            "duration_seconds": self.duration_seconds,
            "data": copy.deepcopy(self.data),
        }


class ConfigResolver:
    """Resolve base scanner config with profiles and environment overlays."""

    def __init__(self, config: Mapping[str, Any]) -> None:
        self._base_config = copy.deepcopy(dict(config))
        self._profiles = self._mapping_section("profiles")
        self._overlays = self._mapping_section("environment_overlays")

    def resolve(self, profile: str | None = None, environment: str | None = None) -> ResolvedConfig:
        """Resolve a config for an optional profile and environment overlay."""
        start = time.perf_counter()
        if environment is not None:
            base = self._resolve_profile(profile, stack=())
            overlay_result = self._resolve_overlay(environment, base.data, stack=())
            return ResolvedConfig(
                data=overlay_result.data,
                profile=profile,
                environment=environment,
                applied_profiles=_merge_applied_names(base.applied_profiles, overlay_result.applied_profiles),
                applied_overlays=overlay_result.applied_overlays,
                duration_seconds=time.perf_counter() - start,
            )

        profile_result = self._resolve_profile(profile, stack=())
        return ResolvedConfig(
            data=profile_result.data,
            profile=profile,
            environment=None,
            applied_profiles=profile_result.applied_profiles,
            applied_overlays=(),
            duration_seconds=time.perf_counter() - start,
        )

    def _mapping_section(self, section_name: str) -> dict[str, Any]:
        raw_section = self._base_config.get(section_name, {})
        if raw_section is None:
            return {}
        if not isinstance(raw_section, Mapping):
            raise ConfigInheritanceError(f"Config section {section_name!r} must be a mapping")
        return copy.deepcopy(dict(raw_section))

    def _resolve_profile(self, profile: str | None, stack: tuple[str, ...]) -> ResolvedConfig:
        if profile is None:
            return ResolvedConfig(data=copy.deepcopy(self._base_config), applied_profiles=())
        if profile in stack:
            cycle = " -> ".join((*stack, profile))
            raise ConfigInheritanceCycleError(f"Profile inheritance cycle detected: {cycle}")

        profile_data = self._profiles.get(profile)
        if profile_data is None:
            raise UnknownConfigProfileError(f"Unknown config profile {profile!r}")
        if not isinstance(profile_data, Mapping):
            raise ConfigInheritanceError(f"Profile {profile!r} must be a mapping")

        parent_name = profile_data.get("extends")
        parent = self._resolve_profile(parent_name, (*stack, profile)) if parent_name else ResolvedConfig(
            data=copy.deepcopy(self._base_config),
            applied_profiles=(),
        )
        resolved = merge_config(
            parent.data,
            _profile_overrides(profile_data),
            MergeStrategy.from_value(profile_data.get("merge_strategy")),
        )
        return ResolvedConfig(
            data=resolved,
            applied_profiles=(*parent.applied_profiles, profile),
        )

    def _resolve_overlay(
        self,
        environment: str,
        base_data: Mapping[str, Any],
        stack: tuple[str, ...],
    ) -> ResolvedConfig:
        if environment in stack:
            cycle = " -> ".join((*stack, environment))
            raise ConfigInheritanceCycleError(f"Environment overlay inheritance cycle detected: {cycle}")

        overlay_data = self._overlays.get(environment)
        if overlay_data is None:
            raise UnknownEnvironmentOverlayError(f"Unknown environment overlay {environment!r}")
        if not isinstance(overlay_data, Mapping):
            raise ConfigInheritanceError(f"Environment overlay {environment!r} must be a mapping")

        parent_name = overlay_data.get("extends")
        applied_profiles: tuple[str, ...] = ()
        if parent_name:
            if parent_name in self._overlays and parent_name != environment:
                parent = self._resolve_overlay(parent_name, base_data, (*stack, environment))
                parent_data = parent.data
                applied_profiles = parent.applied_profiles
                applied_overlays = parent.applied_overlays
            elif parent_name in self._profiles:
                parent = self._resolve_profile(parent_name, stack=())
                parent_data = parent.data
                applied_profiles = parent.applied_profiles
                applied_overlays = ()
            else:
                raise ConfigInheritanceError(
                    f"Environment overlay {environment!r} extends unknown profile or overlay {parent_name!r}"
                )
        else:
            parent_data = copy.deepcopy(dict(base_data))
            applied_overlays = ()

        resolved = merge_config(
            parent_data,
            _profile_overrides(overlay_data),
            MergeStrategy.from_value(overlay_data.get("merge_strategy")),
        )
        return ResolvedConfig(
            data=resolved,
            applied_profiles=applied_profiles,
            applied_overlays=(*applied_overlays, environment),
        )


def merge_config(
    base: Mapping[str, Any],
    overrides: Mapping[str, Any] | None,
    strategy: MergeStrategy | str | None = MergeStrategy.DEEP_MERGE,
) -> dict[str, Any]:
    """Merge override data into a base config using a supported strategy."""
    selected_strategy = strategy if isinstance(strategy, MergeStrategy) else MergeStrategy.from_value(strategy)
    base_copy = copy.deepcopy(dict(base))
    override_copy = copy.deepcopy(dict(overrides or {}))

    if selected_strategy == MergeStrategy.REPLACE:
        for key, value in override_copy.items():
            base_copy[key] = copy.deepcopy(value)
        return base_copy
    if selected_strategy == MergeStrategy.DEEP_MERGE:
        return _deep_merge(base_copy, override_copy)
    raise ConfigMergeStrategyError(f"Unsupported merge strategy {selected_strategy!r}")


def _deep_merge(base: dict[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
    for key, value in overrides.items():
        if isinstance(base.get(key), Mapping) and isinstance(value, Mapping):
            base[key] = _deep_merge(copy.deepcopy(dict(base[key])), value)
        else:
            base[key] = copy.deepcopy(value)
    return base


def _profile_overrides(profile_data: Mapping[str, Any]) -> dict[str, Any]:
    overrides = profile_data.get("overrides", {})
    if overrides is None:
        return {}
    if not isinstance(overrides, Mapping):
        raise ConfigInheritanceError("Profile or overlay 'overrides' must be a mapping")
    return copy.deepcopy(dict(overrides))


def _merge_applied_names(*groups: tuple[str, ...]) -> tuple[str, ...]:
    output: list[str] = []
    for group in groups:
        for name in group:
            if name not in output:
                output.append(name)
    return tuple(output)
