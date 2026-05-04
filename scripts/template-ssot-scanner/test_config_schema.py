#!/usr/bin/env python3
"""Tests for the scanner configuration schema contract."""

import copy
import sys
import time
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

SCANNER_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SCANNER_DIR / "config"

if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_schema() -> dict:
    return load_yaml(CONFIG_DIR / "scanner_config.schema.json")


def validate_config(payload: dict) -> None:
    Draft202012Validator(load_schema(), format_checker=FormatChecker()).validate(payload)


@pytest.mark.parametrize(
    "config_path",
    [
        SCANNER_DIR / "scanner_config.yaml",
        CONFIG_DIR / "examples" / "scanner_config.example.yaml",
    ],
)
def test_scanner_config_files_match_schema(config_path: Path):
    Draft202012Validator.check_schema(load_schema())
    validate_config(load_yaml(config_path))


def test_current_config_still_loads_existing_validation_interface():
    from validation_interface import load_validation_rules

    rules = load_validation_rules(SCANNER_DIR / "scanner_config.yaml")

    assert rules["broken_references"].severity == "error"
    assert rules["broken_references"].threshold == 0
    assert rules["duplicate_references"].severity == "info"


def test_schema_rejects_invalid_rule_severity():
    payload = load_yaml(SCANNER_DIR / "scanner_config.yaml")
    payload["validation_rules"]["broken_references"]["severity"] = "critical"

    with pytest.raises(ValidationError, match="'critical' is not one of"):
        validate_config(payload)


def test_schema_accepts_rule_priority_taxonomy():
    payload = load_yaml(SCANNER_DIR / "scanner_config.yaml")

    priorities = {
        rule["priority"]
        for rule in payload["validation_rules"].values()
        if "priority" in rule
    }

    assert priorities == {"critical", "high", "medium", "low", "info"}
    validate_config(payload)


def test_schema_rejects_invalid_rule_priority():
    payload = load_yaml(SCANNER_DIR / "scanner_config.yaml")
    payload["validation_rules"]["broken_references"]["priority"] = "urgent"

    with pytest.raises(ValidationError, match="'urgent' is not one of"):
        validate_config(payload)


def test_schema_rejects_invalid_pattern_kind():
    payload = load_yaml(CONFIG_DIR / "examples" / "scanner_config.example.yaml")
    invalid = copy.deepcopy(payload)
    invalid["allowlists"]["paths"][0]["kind"] = "prefix"

    with pytest.raises(ValidationError, match="'prefix' is not one of"):
        validate_config(invalid)


def test_schema_rejects_negative_threshold():
    payload = load_yaml(SCANNER_DIR / "scanner_config.yaml")
    payload["validation_rules"]["broken_references"]["threshold"] = -1

    with pytest.raises(ValidationError):
        validate_config(payload)


def test_schema_rejects_missing_validation_rules():
    payload = load_yaml(SCANNER_DIR / "scanner_config.yaml")
    del payload["validation_rules"]

    with pytest.raises(ValidationError, match="'validation_rules' is a required property"):
        validate_config(payload)


def test_schema_rejects_unknown_top_level_properties():
    payload = load_yaml(SCANNER_DIR / "scanner_config.yaml")
    payload["unexpected"] = True

    with pytest.raises(ValidationError, match="Additional properties are not allowed"):
        validate_config(payload)


def test_schema_rejects_unknown_rule_properties():
    payload = load_yaml(SCANNER_DIR / "scanner_config.yaml")
    payload["validation_rules"]["broken_references"]["legacy_flag"] = True

    with pytest.raises(ValidationError, match="Additional properties are not allowed"):
        validate_config(payload)


def test_schema_rejects_invalid_rule_names():
    payload = load_yaml(SCANNER_DIR / "scanner_config.yaml")
    payload["validation_rules"]["BrokenReferences"] = payload["validation_rules"].pop("broken_references")

    with pytest.raises(ValidationError):
        validate_config(payload)


def test_schema_rejects_duplicate_scan_scope_entries():
    payload = load_yaml(CONFIG_DIR / "examples" / "scanner_config.example.yaml")
    payload["scan_scope"]["include"].append(payload["scan_scope"]["include"][0])

    with pytest.raises(ValidationError, match="has non-unique elements"):
        validate_config(payload)


def test_schema_rejects_invalid_expiration_dates():
    payload = load_yaml(CONFIG_DIR / "examples" / "scanner_config.example.yaml")
    payload["allowlists"]["paths"][0]["expires"] = "not-a-date"

    with pytest.raises(ValidationError):
        validate_config(payload)


def test_schema_rejects_invalid_profile_inheritance_target():
    payload = load_yaml(CONFIG_DIR / "examples" / "scanner_config.example.yaml")
    payload["profiles"]["ci"]["extends"] = "Default Profile"

    with pytest.raises(ValidationError):
        validate_config(payload)


def test_schema_validation_performance_is_predictable():
    schema = load_schema()
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    payloads = [
        load_yaml(SCANNER_DIR / "scanner_config.yaml"),
        load_yaml(CONFIG_DIR / "examples" / "scanner_config.example.yaml"),
    ]

    start = time.perf_counter()
    for _ in range(50):
        for payload in payloads:
            validator.validate(copy.deepcopy(payload))
    elapsed = time.perf_counter() - start

    assert elapsed < 3.0
