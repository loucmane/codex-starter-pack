#!/usr/bin/env python3
"""Rule engine primitives for scanner validation rules."""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping

from validation_interface import ALLOWED_SEVERITIES, Severity, ValidationFinding

from .config_loader import ConfigLoader

RuleEvaluator = Callable[["RuleDefinition"], int | bool | ValidationFinding | None]


class RuleEngineError(ValueError):
    """Base exception for rule engine failures."""


class RuleDefinitionError(RuleEngineError):
    """Raised when a rule definition is invalid."""


class RuleExecutionError(RuleEngineError):
    """Raised when a rule cannot be executed."""


class RulePriority(str, Enum):
    """Task 4 rule-engine priority taxonomy."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @classmethod
    def from_value(cls, value: str | None, fallback_severity: Severity = "warning") -> "RulePriority":
        if value is None:
            return DEFAULT_PRIORITY_BY_SEVERITY[fallback_severity]
        try:
            return cls(value)
        except ValueError as exc:
            valid = ", ".join(priority.value for priority in cls)
            raise RuleDefinitionError(f"Invalid rule priority {value!r}. Expected one of: {valid}") from exc


PRIORITY_TO_SEVERITY: dict[RulePriority, Severity] = {
    RulePriority.CRITICAL: "error",
    RulePriority.HIGH: "error",
    RulePriority.MEDIUM: "warning",
    RulePriority.LOW: "warning",
    RulePriority.INFO: "info",
}

DEFAULT_PRIORITY_BY_SEVERITY: dict[Severity, RulePriority] = {
    "error": RulePriority.HIGH,
    "warning": RulePriority.MEDIUM,
    "info": RulePriority.INFO,
}


@dataclass(frozen=True)
class RuleDefinition:
    """Configured rule definition loaded from scanner configuration."""

    name: str
    category: str
    severity: Severity
    priority: RulePriority
    threshold: int | None = None
    enabled: bool = True
    auto_fix: bool = False
    description: str = ""
    parameters: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, name: str, mapping: Mapping[str, Any] | None) -> "RuleDefinition":
        data = dict(mapping or {})
        severity = data.get("severity", "warning")
        if severity not in ALLOWED_SEVERITIES:
            valid = ", ".join(sorted(ALLOWED_SEVERITIES))
            raise RuleDefinitionError(f"Invalid severity for rule {name!r}: {severity!r}. Expected one of: {valid}")

        threshold = data.get("threshold")
        if threshold is not None and not isinstance(threshold, int):
            raise RuleDefinitionError(f"Invalid threshold for rule {name!r}: expected integer or null")

        enabled = data.get("enabled", True)
        if not isinstance(enabled, bool):
            raise RuleDefinitionError(f"Invalid enabled flag for rule {name!r}: expected boolean")

        auto_fix = data.get("auto_fix", False)
        if not isinstance(auto_fix, bool):
            raise RuleDefinitionError(f"Invalid auto_fix flag for rule {name!r}: expected boolean")

        parameters = data.get("parameters", {})
        if parameters is None:
            parameters = {}
        if not isinstance(parameters, Mapping):
            raise RuleDefinitionError(f"Invalid parameters for rule {name!r}: expected mapping")

        priority = RulePriority.from_value(data.get("priority"), severity)

        return cls(
            name=name,
            category=data.get("category", name),
            severity=severity,
            priority=priority,
            threshold=threshold,
            enabled=enabled,
            auto_fix=auto_fix,
            description=data.get("description", ""),
            parameters=copy.deepcopy(dict(parameters)),
        )

    @property
    def effective_severity(self) -> Severity:
        """Return scanner output severity after priority mapping."""
        mapped_severity = PRIORITY_TO_SEVERITY[self.priority]
        if mapped_severity == "error" or self.severity == "error":
            return "error"
        if mapped_severity == "warning" or self.severity == "warning":
            return "warning"
        return "info"

    def should_trigger(self, count: int) -> bool:
        """Return whether a count exceeds this rule threshold."""
        threshold = 0 if self.threshold is None else self.threshold
        return count > threshold

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable rule definition."""
        return {
            "name": self.name,
            "category": self.category,
            "severity": self.severity,
            "priority": self.priority.value,
            "threshold": self.threshold,
            "enabled": self.enabled,
            "auto_fix": self.auto_fix,
            "description": self.description,
            "parameters": copy.deepcopy(dict(self.parameters)),
        }


@dataclass(frozen=True)
class RuleEvaluation:
    """Result of a rule evaluation."""

    rule_name: str
    triggered: bool
    count: int | None = None
    threshold: int | None = None
    finding: ValidationFinding | None = None
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "rule_name": self.rule_name,
            "triggered": self.triggered,
            "duration_seconds": self.duration_seconds,
        }
        if self.count is not None:
            payload["count"] = self.count
        if self.threshold is not None:
            payload["threshold"] = self.threshold
        if self.finding is not None:
            payload["finding"] = self.finding.to_dict()
        return payload


class RuleEngine:
    """Registry and execution engine for configured scanner rules."""

    def __init__(self, rules: Mapping[str, Mapping[str, Any] | RuleDefinition] | None = None) -> None:
        self._rules: dict[str, RuleDefinition] = {}
        if rules:
            for name, definition in rules.items():
                self.register(name, definition)

    @classmethod
    def from_config_loader(cls, loader: ConfigLoader | None = None) -> "RuleEngine":
        """Create a rule engine from a ConfigLoader's validation_rules section."""
        config_loader = loader or ConfigLoader.get_instance()
        return cls(config_loader.validation_rules())

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> "RuleEngine":
        """Create a rule engine from a loaded config mapping."""
        raw_rules = config.get("validation_rules", {})
        if not isinstance(raw_rules, Mapping):
            raise RuleDefinitionError("Config field 'validation_rules' must be a mapping")
        return cls(raw_rules)

    def register(self, name: str, definition: Mapping[str, Any] | RuleDefinition) -> RuleDefinition:
        """Register or replace a rule definition."""
        rule = definition if isinstance(definition, RuleDefinition) else RuleDefinition.from_mapping(name, definition)
        self._rules[name] = rule
        return rule

    def unregister(self, name: str) -> None:
        """Remove a rule definition."""
        if name not in self._rules:
            raise RuleExecutionError(f"Unknown rule {name!r}")
        del self._rules[name]

    def get_rule(self, name: str) -> RuleDefinition:
        """Return a registered rule definition."""
        try:
            return self._rules[name]
        except KeyError as exc:
            raise RuleExecutionError(f"Unknown rule {name!r}") from exc

    def rules(self, enabled_only: bool = False) -> dict[str, RuleDefinition]:
        """Return registered rules."""
        rules = self._rules
        if enabled_only:
            rules = {name: rule for name, rule in rules.items() if rule.enabled}
        return copy.deepcopy(rules)

    def evaluate_count(
        self,
        rule_name: str,
        count: int,
        message: str,
        *,
        source_file: str | None = None,
        target_file: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> RuleEvaluation:
        """Evaluate a count against a configured rule threshold."""
        start = time.perf_counter()
        if count < 0:
            raise RuleExecutionError(f"Rule {rule_name!r} received a negative count")

        rule = self.get_rule(rule_name)
        if not rule.enabled:
            return RuleEvaluation(
                rule_name=rule_name,
                triggered=False,
                count=count,
                threshold=rule.threshold,
                duration_seconds=time.perf_counter() - start,
            )

        triggered = rule.should_trigger(count)
        finding = None
        if triggered:
            finding_details = {
                "rule": rule.name,
                "priority": rule.priority.value,
                "threshold": rule.threshold,
                "count": count,
                "auto_fix": rule.auto_fix,
            }
            if details:
                finding_details.update(copy.deepcopy(dict(details)))

            finding = ValidationFinding(
                category=rule.category,
                severity=rule.effective_severity,
                message=message,
                source_file=source_file,
                target_file=target_file,
                details=finding_details,
            )

        return RuleEvaluation(
            rule_name=rule_name,
            triggered=triggered,
            count=count,
            threshold=rule.threshold,
            finding=finding,
            duration_seconds=time.perf_counter() - start,
        )

    def execute(self, rule_name: str, evaluator: RuleEvaluator) -> RuleEvaluation:
        """Execute a custom evaluator against a registered rule."""
        start = time.perf_counter()
        rule = self.get_rule(rule_name)
        if not rule.enabled:
            return RuleEvaluation(rule_name=rule_name, triggered=False, duration_seconds=time.perf_counter() - start)

        result = evaluator(rule)
        if isinstance(result, ValidationFinding):
            return RuleEvaluation(
                rule_name=rule_name,
                triggered=True,
                finding=result,
                duration_seconds=time.perf_counter() - start,
            )
        if isinstance(result, bool):
            return RuleEvaluation(rule_name=rule_name, triggered=result, duration_seconds=time.perf_counter() - start)
        if isinstance(result, int):
            return self.evaluate_count(rule_name, result, f"Rule {rule_name} threshold exceeded")
        if result is None:
            return RuleEvaluation(rule_name=rule_name, triggered=False, duration_seconds=time.perf_counter() - start)

        raise RuleExecutionError(f"Unsupported evaluator result for rule {rule_name!r}: {type(result).__name__}")

    def evaluate_counts(
        self,
        counts: Mapping[str, int],
        messages: Mapping[str, str] | None = None,
    ) -> list[RuleEvaluation]:
        """Evaluate multiple rule counts in registered order."""
        output: list[RuleEvaluation] = []
        message_map = messages or {}
        for rule_name in self._rules:
            if rule_name in counts:
                output.append(
                    self.evaluate_count(
                        rule_name,
                        counts[rule_name],
                        message_map.get(rule_name, f"Rule {rule_name} threshold exceeded"),
                    )
                )
        return output
