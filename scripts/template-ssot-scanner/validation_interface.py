#!/usr/bin/env python3
"""Shared validation result interfaces for scanner modules."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Literal, Mapping, Optional

import yaml

Severity = Literal["info", "warning", "error"]
ALLOWED_SEVERITIES = {"info", "warning", "error"}


@dataclass(frozen=True)
class ValidationFinding:
    """Serializable validation finding emitted by scanner modules."""

    category: str
    severity: Severity
    message: str
    source_file: Optional[str] = None
    target_file: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
        }
        if self.source_file:
            payload["source_file"] = self.source_file
        if self.target_file:
            payload["target_file"] = self.target_file
        if self.details:
            payload["details"] = self.details
        return payload


def threshold_severity(count: int, threshold: Optional[int]) -> Severity:
    """Map a count/threshold pair to a scanner severity."""
    if threshold is None:
        return "info"
    return "error" if count > threshold else "info"


@dataclass(frozen=True)
class ValidationRule:
    """Configured scanner validation rule."""

    name: str
    category: str
    severity: Severity
    threshold: Optional[int] = None
    enabled: bool = True

    @classmethod
    def from_mapping(cls, name: str, mapping: Mapping[str, Any]) -> "ValidationRule":
        severity = mapping.get("severity", "warning")
        if severity not in ALLOWED_SEVERITIES:
            valid = ", ".join(sorted(ALLOWED_SEVERITIES))
            raise ValueError(f"Invalid severity for '{name}': {severity!r}. Expected one of: {valid}")

        threshold = mapping.get("threshold")
        if threshold is not None and not isinstance(threshold, int):
            raise ValueError(f"Invalid threshold for '{name}': expected integer or null")

        enabled = mapping.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError(f"Invalid enabled flag for '{name}': expected boolean")

        return cls(
            name=name,
            category=mapping.get("category", name),
            severity=severity,
            threshold=threshold,
            enabled=enabled,
        )


def load_validation_rules(
    config_path: Path,
    *,
    config_data: Mapping[str, Any] | None = None,
    loader: Any = None,
    rule_engine: Any = None,
    profile: str | None = None,
    environment: str | None = None,
    apply_environment_overrides: bool = False,
    environ: dict[str, str] | None = None,
) -> Dict[str, ValidationRule]:
    """Load validation rules from scanner config data or a ConfigLoader."""
    if rule_engine is not None:
        return _validation_rules_from_rule_engine(rule_engine)

    if config_data is None:
        if not config_path.exists():
            return {}
        data = _load_config_data(
            config_path,
            loader=loader,
            profile=profile,
            environment=environment,
            apply_environment_overrides=apply_environment_overrides,
            environ=environ,
        )
    else:
        data = dict(config_data)
    raw_rules = data.get("validation_rules", {})
    if not isinstance(raw_rules, dict):
        raise ValueError("scanner_config.yaml field 'validation_rules' must be a mapping")

    return {
        name: ValidationRule.from_mapping(name, mapping or {})
        for name, mapping in raw_rules.items()
        if (mapping or {}).get("enabled", True)
    }


def finding_from_count(rule: ValidationRule, count: int, message: str) -> ValidationFinding:
    """Create a configured threshold finding from a count."""
    if not rule.enabled:
        return ValidationFinding(
            category=rule.category,
            severity="info",
            message=message,
            details={"count": count, "threshold": rule.threshold, "enabled": False},
        )

    severity = threshold_severity(count, rule.threshold)
    if severity == "error":
        severity = rule.severity

    return ValidationFinding(
        category=rule.category,
        severity=severity,
        message=message,
        details={"count": count, "threshold": rule.threshold},
    )


def _load_config_data(
    config_path: Path,
    *,
    loader: Any = None,
    profile: str | None = None,
    environment: str | None = None,
    apply_environment_overrides: bool = False,
    environ: dict[str, str] | None = None,
) -> Mapping[str, Any]:
    raw_data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if isinstance(raw_data, Mapping) and "schema_version" not in raw_data and "validation_rules" in raw_data:
        return raw_data

    try:
        from config.config_loader import ConfigLoader
    except ImportError:
        return raw_data

    resolved_loader = loader or ConfigLoader.get_instance(config_path)
    if profile or environment:
        return resolved_loader.resolve(
            profile=profile,
            environment=environment,
            apply_environment_overrides=apply_environment_overrides,
            environ=environ,
        )
    if apply_environment_overrides:
        return resolved_loader.load_with_env_overrides(environ=environ)
    return resolved_loader.load()


def _validation_rules_from_rule_engine(rule_engine: Any) -> Dict[str, ValidationRule]:
    return {
        name: ValidationRule(
            name=rule.name,
            category=rule.category,
            severity=rule.effective_severity,
            threshold=rule.threshold,
            enabled=rule.enabled,
        )
        for name, rule in rule_engine.rules(enabled_only=True).items()
    }
