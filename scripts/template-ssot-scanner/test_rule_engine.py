#!/usr/bin/env python3
"""Tests for the scanner rule engine."""

import sys
import time
from pathlib import Path

import pytest

SCANNER_DIR = Path(__file__).resolve().parent

if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))

from config.config_loader import ConfigLoader  # noqa: E402
from config.rule_engine import (  # noqa: E402
    PRIORITY_TO_SEVERITY,
    RuleDefinition,
    RuleDefinitionError,
    RuleEngine,
    RuleExecutionError,
    RulePriority,
)
from validation_interface import ValidationFinding  # noqa: E402


@pytest.fixture(autouse=True)
def reset_config_loader_singletons():
    ConfigLoader.reset_instances_for_tests()
    yield
    ConfigLoader.reset_instances_for_tests()


def test_rule_definition_loads_priority_taxonomy_from_mapping():
    rule = RuleDefinition.from_mapping(
        "broken_references",
        {
            "category": "references",
            "severity": "warning",
            "priority": "critical",
            "threshold": 0,
            "enabled": True,
            "auto_fix": True,
            "parameters": {"mode": "strict"},
        },
    )

    assert rule.priority == RulePriority.CRITICAL
    assert rule.effective_severity == "error"
    assert rule.auto_fix
    assert rule.parameters == {"mode": "strict"}


def test_rule_definition_defaults_priority_from_existing_severity():
    assert RuleDefinition.from_mapping("hard", {"severity": "error"}).priority == RulePriority.HIGH
    assert RuleDefinition.from_mapping("medium", {"severity": "warning"}).priority == RulePriority.MEDIUM
    assert RuleDefinition.from_mapping("soft", {"severity": "info"}).priority == RulePriority.INFO


def test_rule_priority_maps_to_scanner_output_severity():
    assert PRIORITY_TO_SEVERITY[RulePriority.CRITICAL] == "error"
    assert PRIORITY_TO_SEVERITY[RulePriority.HIGH] == "error"
    assert PRIORITY_TO_SEVERITY[RulePriority.MEDIUM] == "warning"
    assert PRIORITY_TO_SEVERITY[RulePriority.LOW] == "warning"
    assert PRIORITY_TO_SEVERITY[RulePriority.INFO] == "info"


def test_rule_engine_loads_default_config_rules():
    engine = RuleEngine.from_config_loader()

    rules = engine.rules()

    assert set(rules) >= {
        "broken_references",
        "migrated_monolith_references",
        "circular_dependencies",
        "orphaned_files",
        "duplicate_references",
    }
    assert rules["broken_references"].priority == RulePriority.CRITICAL
    assert rules["duplicate_references"].effective_severity == "info"


def test_rule_engine_evaluates_threshold_and_emits_finding_details():
    engine = RuleEngine(
        {
            "broken_references": {
                "category": "references",
                "severity": "error",
                "priority": "critical",
                "threshold": 1,
                "auto_fix": False,
            }
        }
    )

    evaluation = engine.evaluate_count(
        "broken_references",
        2,
        "Broken references exceed threshold",
        source_file="templates/source.md",
        details={"kind": "file"},
    )

    assert evaluation.triggered
    assert evaluation.count == 2
    assert evaluation.threshold == 1
    assert evaluation.finding is not None
    assert evaluation.finding.to_dict() == {
        "category": "references",
        "severity": "error",
        "message": "Broken references exceed threshold",
        "source_file": "templates/source.md",
        "details": {
            "rule": "broken_references",
            "priority": "critical",
            "threshold": 1,
            "count": 2,
            "auto_fix": False,
            "kind": "file",
        },
    }


def test_rule_engine_does_not_emit_when_count_is_at_threshold():
    engine = RuleEngine({"orphaned_files": {"severity": "warning", "priority": "low", "threshold": 2}})

    evaluation = engine.evaluate_count("orphaned_files", 2, "Orphaned files exceed threshold")

    assert not evaluation.triggered
    assert evaluation.finding is None


def test_rule_engine_skips_disabled_rules():
    engine = RuleEngine({"duplicate_references": {"severity": "info", "enabled": False, "threshold": 0}})

    evaluation = engine.evaluate_count("duplicate_references", 10, "Duplicate references detected")

    assert not evaluation.triggered
    assert evaluation.finding is None
    assert engine.rules(enabled_only=True) == {}


def test_rule_engine_evaluates_multiple_counts_in_rule_order():
    engine = RuleEngine(
        {
            "first": {"severity": "warning", "threshold": 0},
            "second": {"severity": "error", "threshold": 5},
            "third": {"severity": "info", "threshold": 0},
        }
    )

    evaluations = engine.evaluate_counts({"third": 1, "first": 1}, {"first": "first message", "third": "third message"})

    assert [evaluation.rule_name for evaluation in evaluations] == ["first", "third"]
    assert [evaluation.triggered for evaluation in evaluations] == [True, True]
    assert evaluations[0].finding is not None
    assert evaluations[0].finding.message == "first message"


def test_rule_engine_executes_custom_evaluator_returning_finding():
    engine = RuleEngine({"custom": {"category": "custom", "severity": "warning", "priority": "medium"}})

    evaluation = engine.execute(
        "custom",
        lambda rule: ValidationFinding(
            category=rule.category,
            severity=rule.effective_severity,
            message="Custom finding",
        ),
    )

    assert evaluation.triggered
    assert evaluation.finding is not None
    assert evaluation.finding.severity == "warning"


def test_rule_engine_executes_custom_evaluator_returning_count():
    engine = RuleEngine({"custom": {"category": "custom", "severity": "warning", "threshold": 2}})

    evaluation = engine.execute("custom", lambda _rule: 3)

    assert evaluation.triggered
    assert evaluation.finding is not None
    assert evaluation.finding.details["count"] == 3


@pytest.mark.parametrize(
    "definition, expected",
    [
        ({"severity": "critical"}, "Invalid severity"),
        ({"severity": "warning", "priority": "urgent"}, "Invalid rule priority"),
        ({"severity": "warning", "threshold": "0"}, "Invalid threshold"),
        ({"severity": "warning", "enabled": "yes"}, "Invalid enabled"),
        ({"severity": "warning", "auto_fix": "yes"}, "Invalid auto_fix"),
        ({"severity": "warning", "parameters": []}, "Invalid parameters"),
    ],
)
def test_rule_definition_rejects_invalid_config(definition, expected):
    with pytest.raises(RuleDefinitionError, match=expected):
        RuleDefinition.from_mapping("bad_rule", definition)


def test_rule_engine_rejects_unknown_rule_and_negative_count():
    engine = RuleEngine({"known": {"severity": "warning"}})

    with pytest.raises(RuleExecutionError, match="Unknown rule"):
        engine.evaluate_count("missing", 1, "missing")

    with pytest.raises(RuleExecutionError, match="negative count"):
        engine.evaluate_count("known", -1, "negative")


def test_rule_engine_rejects_unsupported_evaluator_result():
    engine = RuleEngine({"known": {"severity": "warning"}})

    with pytest.raises(RuleExecutionError, match="Unsupported evaluator result"):
        engine.execute("known", lambda _rule: {"bad": "result"})


def test_rule_engine_performance_is_predictable():
    engine = RuleEngine.from_config_loader()

    start = time.perf_counter()
    for _ in range(500):
        engine.evaluate_counts(
            {
                "broken_references": 1,
                "migrated_monolith_references": 1,
                "circular_dependencies": 0,
                "orphaned_files": 0,
                "duplicate_references": 4,
            }
        )
    elapsed = time.perf_counter() - start

    assert elapsed < 2.0
