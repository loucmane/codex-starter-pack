#!/usr/bin/env python3
"""Shared validation result interfaces for scanner modules."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Literal, Optional

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

    @classmethod
    def from_mapping(cls, name: str, mapping: Dict[str, Any]) -> "ValidationRule":
        severity = mapping.get("severity", "warning")
        if severity not in ALLOWED_SEVERITIES:
            valid = ", ".join(sorted(ALLOWED_SEVERITIES))
            raise ValueError(f"Invalid severity for '{name}': {severity!r}. Expected one of: {valid}")

        threshold = mapping.get("threshold")
        if threshold is not None and not isinstance(threshold, int):
            raise ValueError(f"Invalid threshold for '{name}': expected integer or null")

        return cls(
            name=name,
            category=mapping.get("category", name),
            severity=severity,
            threshold=threshold,
        )


def load_validation_rules(config_path: Path) -> Dict[str, ValidationRule]:
    """Load validation rules from scanner_config.yaml if present."""
    if not config_path.exists():
        return {}

    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    raw_rules = data.get("validation_rules", {})
    if not isinstance(raw_rules, dict):
        raise ValueError("scanner_config.yaml field 'validation_rules' must be a mapping")

    return {
        name: ValidationRule.from_mapping(name, mapping or {})
        for name, mapping in raw_rules.items()
    }


def finding_from_count(rule: ValidationRule, count: int, message: str) -> ValidationFinding:
    """Create a configured threshold finding from a count."""
    severity = threshold_severity(count, rule.threshold)
    if severity == "error":
        severity = rule.severity

    return ValidationFinding(
        category=rule.category,
        severity=severity,
        message=message,
        details={"count": count, "threshold": rule.threshold},
    )
