#!/usr/bin/env python3
"""Tests for CODEX_SCANNER_ environment override handling."""

import copy
import sys
import time
from pathlib import Path

import pytest

SCANNER_DIR = Path(__file__).resolve().parent

if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))

from config.config_loader import ConfigLoader, ConfigValidationError  # noqa: E402
from config.env_override import (  # noqa: E402
    EnvOverrideNameError,
    EnvOverrideValueError,
    apply_env_overrides,
    parse_env_overrides,
    parse_env_value,
)


@pytest.fixture(autouse=True)
def reset_config_loader_singletons():
    ConfigLoader.reset_instances_for_tests()
    yield
    ConfigLoader.reset_instances_for_tests()


def load_example_config() -> dict:
    loader = ConfigLoader.get_instance(SCANNER_DIR / "config" / "examples" / "scanner_config.example.yaml")
    return loader.load()


def test_parse_env_values_uses_yaml_scalar_list_and_mapping_rules():
    assert parse_env_value("true") is True
    assert parse_env_value("false") is False
    assert parse_env_value("5") == 5
    assert parse_env_value("[a, b]") == ["a", "b"]
    assert parse_env_value("{enabled: true, interval: 10}") == {"enabled": True, "interval": 10}
    assert parse_env_value("") == ""


def test_parse_env_overrides_supports_double_underscore_nested_paths():
    overrides = parse_env_overrides(
        {
            "CODEX_SCANNER_VALIDATION_RULES__BROKEN_REFERENCES__SEVERITY": "warning",
            "IGNORED": "value",
        }
    )

    assert len(overrides) == 1
    assert overrides[0].env_name == "CODEX_SCANNER_VALIDATION_RULES__BROKEN_REFERENCES__SEVERITY"
    assert overrides[0].path == ("validation_rules", "broken_references", "severity")
    assert overrides[0].value == "warning"


def test_parse_env_overrides_supports_section_aliases_with_single_underscores():
    overrides = parse_env_overrides(
        {
            "CODEX_SCANNER_SCAN_SCOPE_CHECKPOINTING_ENABLED": "true",
        }
    )

    assert overrides[0].path == ("scan_scope", "checkpointing", "enabled")
    assert overrides[0].value is True


def test_env_overrides_take_precedence_over_yaml_values():
    config = load_example_config()

    result = apply_env_overrides(
        config,
        {
            "CODEX_SCANNER_VALIDATION_RULES__BROKEN_REFERENCES__SEVERITY": "warning",
            "CODEX_SCANNER_SCAN_SCOPE__CHECKPOINTING__INTERVAL": "30",
        },
    )

    assert result.data["validation_rules"]["broken_references"]["severity"] == "warning"
    assert result.data["scan_scope"]["checkpointing"]["interval"] == 30
    assert config["validation_rules"]["broken_references"]["severity"] == "error"
    assert [override.env_name for override in result.overrides] == sorted(override.env_name for override in result.overrides)


def test_env_overrides_can_add_new_nested_values_before_validation():
    config = load_example_config()

    result = apply_env_overrides(
        config,
        {
            "CODEX_SCANNER_METADATA__OWNER": "platform-team",
        },
    )

    assert result.data["metadata"]["owner"] == "platform-team"


def test_env_override_rejects_invalid_empty_path_segments():
    with pytest.raises(EnvOverrideNameError, match="empty path segment"):
        parse_env_overrides({"CODEX_SCANNER_METADATA____OWNER": "team"})


def test_env_override_rejects_overriding_through_scalar_path():
    config = load_example_config()

    with pytest.raises(EnvOverrideNameError, match="not a mapping"):
        apply_env_overrides(config, {"CODEX_SCANNER_SCHEMA_VERSION__MAJOR": "2"})


def test_env_override_parse_errors_are_reported():
    with pytest.raises(EnvOverrideValueError, match="Unable to parse"):
        parse_env_value("[")


def test_config_loader_applies_env_overrides_and_validates_result():
    loader = ConfigLoader.get_instance(SCANNER_DIR / "config" / "examples" / "scanner_config.example.yaml")

    loaded = loader.load_with_env_overrides(
        environ={
            "CODEX_SCANNER_VALIDATION_RULES__DUPLICATE_REFERENCES__SEVERITY": "warning",
        }
    )
    resolved = loader.resolve(
        environment="ci",
        apply_environment_overrides=True,
        environ={
            "CODEX_SCANNER_SCAN_SCOPE__CHECKPOINTING__ENABLED": "true",
        },
    )
    snapshot = loader.resolved_snapshot(
        environment="ci",
        apply_environment_overrides=True,
        environ={
            "CODEX_SCANNER_SCAN_SCOPE__CHECKPOINTING__INTERVAL": "15",
        },
    )

    assert loaded["validation_rules"]["duplicate_references"]["severity"] == "warning"
    assert resolved["scan_scope"]["checkpointing"]["enabled"] is True
    assert snapshot.data["scan_scope"]["checkpointing"]["interval"] == 15
    assert snapshot.applied_overlays == ("ci",)


def test_config_loader_rejects_invalid_env_override_value():
    loader = ConfigLoader.get_instance(SCANNER_DIR / "config" / "examples" / "scanner_config.example.yaml")

    with pytest.raises(ConfigValidationError, match="validation_rules.broken_references.severity"):
        loader.load_with_env_overrides(
            environ={
                "CODEX_SCANNER_VALIDATION_RULES__BROKEN_REFERENCES__SEVERITY": "urgent",
            }
        )


def test_env_override_resolution_performance_is_predictable():
    config = load_example_config()
    environ = {
        "CODEX_SCANNER_VALIDATION_RULES__BROKEN_REFERENCES__SEVERITY": "warning",
        "CODEX_SCANNER_VALIDATION_RULES__DUPLICATE_REFERENCES__THRESHOLD": "2",
        "CODEX_SCANNER_SCAN_SCOPE__CHECKPOINTING__INTERVAL": "15",
    }

    start = time.perf_counter()
    for _ in range(1000):
        apply_env_overrides(copy.deepcopy(config), environ=environ)
    elapsed = time.perf_counter() - start

    assert elapsed < 2.0
