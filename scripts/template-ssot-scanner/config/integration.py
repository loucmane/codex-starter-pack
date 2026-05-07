#!/usr/bin/env python3
"""Dependency-injection helpers for scanner modules."""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from scan_core import (
    DEFAULT_CONFIG_DIRS,
    DEFAULT_EXCLUDE_PATTERNS,
    SCANNABLE_SUFFIXES,
    ScannerConfig,
)
from validation_interface import ValidationRule

from .config_loader import DEFAULT_CONFIG_PATH, ConfigLoader
from .pattern_matcher import PatternMatcher
from .rule_engine import RuleEngine


class ScannerConfigIntegrationError(ValueError):
    """Raised when scanner config integration cannot be built."""


@dataclass(frozen=True)
class ScannerConfigContext:
    """Resolved scanner config dependencies ready for module injection."""

    config: Mapping[str, Any]
    loader: ConfigLoader | None
    rule_engine: RuleEngine
    pattern_matcher: PatternMatcher
    source: str
    profile: str | None = None
    environment: str | None = None
    duration_seconds: float = 0.0

    def config_data(self) -> dict[str, Any]:
        """Return resolved config data as a defensive copy."""
        return copy.deepcopy(dict(self.config))

    def validation_rules(self, enabled_only: bool = True) -> dict[str, ValidationRule]:
        """Return validation-interface rules backed by the RuleEngine."""
        rules = self.rule_engine.rules(enabled_only=enabled_only)
        return {
            name: ValidationRule(
                name=rule.name,
                category=rule.category,
                severity=rule.effective_severity,
                threshold=rule.threshold,
                enabled=rule.enabled,
            )
            for name, rule in rules.items()
        }

    def file_discovery_config(
        self,
        base_path: Path,
        include_pattern: str | None = None,
        exclude_pattern: str | None = None,
    ) -> ScannerConfig:
        """Build the file-discovery config consumed by scanner modules."""
        scan_scope = self.config.get("scan_scope", {})
        if scan_scope is None:
            scan_scope = {}
        if not isinstance(scan_scope, Mapping):
            raise ScannerConfigIntegrationError("Config field 'scan_scope' must be a mapping")

        include_patterns = _string_tuple(scan_scope.get("include"), default=())
        exclude_patterns = list(_string_tuple(scan_scope.get("exclude"), default=DEFAULT_EXCLUDE_PATTERNS))
        if exclude_pattern:
            exclude_patterns.extend(
                pattern.strip()
                for pattern in exclude_pattern.split(",")
                if pattern.strip()
            )

        return ScannerConfig(
            base_path=base_path,
            include_pattern=include_pattern,
            include_patterns=include_patterns,
            exclude_patterns=tuple(exclude_patterns),
            supported_suffixes=_string_tuple(scan_scope.get("scannable_suffixes"), default=SCANNABLE_SUFFIXES),
            config_dirs=_string_tuple(scan_scope.get("config_dirs"), default=DEFAULT_CONFIG_DIRS),
            pattern_matcher=self.pattern_matcher,
        )

    def module_examples(self) -> dict[str, str]:
        """Return concise examples for injecting this context into scanner modules."""
        return scanner_module_examples()


def create_scanner_config_context(
    config_path: str | Path | None = None,
    *,
    loader: ConfigLoader | None = None,
    config_data: Mapping[str, Any] | None = None,
    profile: str | None = None,
    environment: str | None = None,
    apply_environment_overrides: bool = False,
    environ: dict[str, str] | None = None,
    force_reload: bool = False,
    validate: bool = True,
) -> ScannerConfigContext:
    """Resolve scanner config once and package scanner dependencies for injection."""
    start = time.perf_counter()
    source = "mapping"
    resolved_loader = loader

    if config_data is None:
        resolved_loader = resolved_loader or ConfigLoader.get_instance(
            config_path or DEFAULT_CONFIG_PATH,
            validate=validate,
        )
        source = str(resolved_loader.config_path)
        if profile or environment:
            resolved_data = resolved_loader.resolve(
                profile=profile,
                environment=environment,
                apply_environment_overrides=apply_environment_overrides,
                environ=environ,
                force_reload=force_reload,
            )
        elif apply_environment_overrides:
            resolved_data = resolved_loader.load_with_env_overrides(
                environ=environ,
                force_reload=force_reload,
            )
        else:
            resolved_data = resolved_loader.load(force_reload=force_reload)
    else:
        resolved_data = copy.deepcopy(dict(config_data))

    rule_engine = RuleEngine.from_config(resolved_data)
    pattern_matcher = PatternMatcher.from_config(resolved_data)
    duration = time.perf_counter() - start

    return ScannerConfigContext(
        config=resolved_data,
        loader=resolved_loader,
        rule_engine=rule_engine,
        pattern_matcher=pattern_matcher,
        source=source,
        profile=profile,
        environment=environment,
        duration_seconds=duration,
    )


def create_template_scanner(
    base_path: Path,
    *,
    context: ScannerConfigContext | None = None,
    config_path: str | Path | None = None,
    checkpoint_interval: int = 25,
    include_pattern: str | None = None,
    exclude_pattern: str | None = None,
):
    """Create a TemplateScanner with scanner config dependencies injected."""
    from scanner import TemplateScanner

    resolved_context = context or create_scanner_config_context(config_path)
    return TemplateScanner(
        base_path=base_path,
        checkpoint_interval=checkpoint_interval,
        include_pattern=include_pattern,
        exclude_pattern=exclude_pattern,
        config_context=resolved_context,
    )


def create_reference_analyzer(
    scan_results_file: str = "output/data/template_scan_results.json",
    *,
    context: ScannerConfigContext | None = None,
    config_path: str | Path | None = None,
):
    """Create a ReferenceAnalyzer with scanner config dependencies injected."""
    from analyze_references import ReferenceAnalyzer

    resolved_context = context or create_scanner_config_context(config_path)
    return ReferenceAnalyzer(
        scan_results_file=scan_results_file,
        config_file=str(config_path or DEFAULT_CONFIG_PATH),
        config_context=resolved_context,
    )


def scanner_module_examples() -> dict[str, str]:
    """Return integration examples for the scanner suite modules."""
    return {
        "scanner.py": "TemplateScanner(base_path, config_context=context)",
        "analyze_references.py": "ReferenceAnalyzer(scan_results_file, config_context=context)",
        "find_duplicates.py": "DuplicateFinder(scan_results_file) consumes config-driven scanner outputs",
        "migration_detector.py": "MigrationDetector(base_path) runs before config-driven reference analysis",
        "security_validator.py": "SecurityValidator(base_path, config_context=context)",
        "generate_fixes.py": "FixGenerator() consumes reports produced by configured scanners",
        "safe_reorganize.py": "SafeReorganizer(project_root) consumes configured scan output metadata",
        "run_all_scanners.py": "run_all_scanners.py --config scanner_config.yaml --profile ci",
    }


def _string_tuple(raw: Any, default: tuple[str, ...]) -> tuple[str, ...]:
    if raw is None:
        return tuple(default)
    if isinstance(raw, str):
        return (raw,)
    if not isinstance(raw, (list, tuple)):
        raise ScannerConfigIntegrationError("Expected a string or sequence of strings")
    return tuple(str(item) for item in raw)
