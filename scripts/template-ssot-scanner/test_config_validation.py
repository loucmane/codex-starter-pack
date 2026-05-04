#!/usr/bin/env python3
"""Tests for scanner configuration jsonschema validation helpers."""

import copy
import sys
import time
from pathlib import Path

import pytest
import yaml

SCANNER_DIR = Path(__file__).resolve().parent

if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))

from config.config_loader import ConfigLoadError, ConfigLoader, ConfigValidationError  # noqa: E402
from config.validation import (  # noqa: E402
    ConfigDataValidationError,
    ConfigSchemaDefinitionError,
    ConfigValidationReport,
    ScannerConfigValidator,
    load_config_file,
    validate_config_data,
    validate_config_file,
)


@pytest.fixture(autouse=True)
def reset_config_loader_singletons():
    ConfigLoader.reset_instances_for_tests()
    yield
    ConfigLoader.reset_instances_for_tests()


def copy_default_config(path: Path) -> Path:
    path.write_text((SCANNER_DIR / "scanner_config.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    return path


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_validator_accepts_default_config_and_reports_timing():
    payload = load_yaml(SCANNER_DIR / "scanner_config.yaml")
    report = validate_config_data(payload)

    assert isinstance(report, ConfigValidationReport)
    assert report.valid
    assert report.issues == ()
    assert report.duration_seconds >= 0
    assert "valid scanner config" in report.summary()


def test_validator_reports_multiple_deterministic_issues():
    payload = load_yaml(SCANNER_DIR / "scanner_config.yaml")
    payload["validation_rules"]["broken_references"]["severity"] = "critical"
    payload["validation_rules"]["broken_references"]["threshold"] = -1

    with pytest.raises(ConfigDataValidationError) as excinfo:
        validate_config_data(payload)

    paths = [issue.path for issue in excinfo.value.issues]
    assert paths == sorted(paths)
    assert "validation_rules.broken_references.severity" in paths
    assert "validation_rules.broken_references.threshold" in paths
    assert "validation_rules.broken_references.severity" in excinfo.value.summary()


def test_validator_report_does_not_raise_for_invalid_data():
    payload = load_yaml(SCANNER_DIR / "scanner_config.yaml")
    payload["validation_rules"]["broken_references"]["priority"] = "urgent"

    report = ScannerConfigValidator().report(payload)

    assert not report.valid
    assert report.issues[0].path == "validation_rules.broken_references.priority"
    assert report.issues[0].validator == "enum"


def test_validate_config_file_loads_yaml_and_rejects_non_mapping_root(tmp_path):
    config_path = copy_default_config(tmp_path / "scanner_config.yaml")

    assert validate_config_file(config_path).valid
    assert load_config_file(config_path)["schema_version"] == "1.0.0"

    list_config = tmp_path / "list.yaml"
    list_config.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    with pytest.raises(ConfigDataValidationError, match="document root"):
        validate_config_file(list_config)


def test_validator_rejects_invalid_schema_definition(tmp_path):
    schema_path = tmp_path / "invalid-schema.json"
    schema_path.write_text('{"type": 123}', encoding="utf-8")

    with pytest.raises(ConfigSchemaDefinitionError, match="Invalid scanner config schema"):
        ScannerConfigValidator(schema_path).check_schema()


def test_config_loader_converts_invalid_schema_to_loader_error(tmp_path):
    schema_path = tmp_path / "missing-schema.json"
    config_path = copy_default_config(tmp_path / "scanner_config.yaml")
    loader = ConfigLoader.get_instance(config_path, schema_path=schema_path)

    with pytest.raises(ConfigLoadError, match="Unable to read JSON schema"):
        loader.load()


def test_config_loader_validates_resolved_profiles_and_overlays(tmp_path):
    config_path = copy_default_config(tmp_path / "scanner_config.yaml")
    data = load_yaml(config_path)
    data["environment_overlays"]["broken"] = {
        "description": "Invalid runtime overlay",
        "extends": None,
        "merge_strategy": "deep_merge",
        "overrides": {
            "validation_rules": {
                "broken_references": {
                    "severity": "urgent",
                }
            }
        },
    }
    config_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    loader = ConfigLoader.get_instance(config_path)

    with pytest.raises(ConfigValidationError, match="validation_rules.broken_references.severity"):
        loader.resolve(environment="broken")


def test_validation_overhead_is_predictable():
    payload = load_yaml(SCANNER_DIR / "scanner_config.yaml")
    validator = ScannerConfigValidator()
    validator.check_schema()

    start = time.perf_counter()
    for _ in range(200):
        validator.validate(copy.deepcopy(payload))
    elapsed = time.perf_counter() - start

    assert elapsed < 3.0
