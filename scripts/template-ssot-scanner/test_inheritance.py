#!/usr/bin/env python3
"""Tests for scanner configuration inheritance and overlays."""

import copy
import sys
import time
from pathlib import Path

import pytest

SCANNER_DIR = Path(__file__).resolve().parent

if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))

from config.config_loader import ConfigLoader  # noqa: E402
from config.inheritance import (  # noqa: E402
    ConfigInheritanceCycleError,
    ConfigInheritanceError,
    ConfigMergeStrategyError,
    ConfigResolver,
    MergeStrategy,
    UnknownConfigProfileError,
    UnknownEnvironmentOverlayError,
    merge_config,
)


@pytest.fixture(autouse=True)
def reset_config_loader_singletons():
    ConfigLoader.reset_instances_for_tests()
    yield
    ConfigLoader.reset_instances_for_tests()


def load_example_config() -> dict:
    loader = ConfigLoader.get_instance(SCANNER_DIR / "config" / "examples" / "scanner_config.example.yaml")
    return loader.load()


def test_deep_merge_preserves_nested_values_and_replaces_lists():
    base = {
        "scan_scope": {"exclude": ["a/**"], "config_dirs": [".codex"]},
        "validation_rules": {
            "duplicate_references": {
                "category": "references",
                "severity": "info",
                "priority": "info",
                "threshold": 0,
            }
        },
    }
    overrides = {
        "scan_scope": {"exclude": ["b/**"]},
        "validation_rules": {
            "duplicate_references": {
                "severity": "warning",
                "priority": "low",
            }
        },
    }

    merged = merge_config(base, overrides, MergeStrategy.DEEP_MERGE)

    assert merged["scan_scope"]["exclude"] == ["b/**"]
    assert merged["scan_scope"]["config_dirs"] == [".codex"]
    assert merged["validation_rules"]["duplicate_references"] == {
        "category": "references",
        "severity": "warning",
        "priority": "low",
        "threshold": 0,
    }
    assert base["scan_scope"]["exclude"] == ["a/**"]


def test_replace_merge_swaps_top_level_sections():
    base = {
        "validation_rules": {
            "first": {"severity": "warning"},
            "second": {"severity": "info"},
        },
        "scan_scope": {"exclude": ["a/**"]},
    }
    overrides = {"validation_rules": {"third": {"severity": "error"}}}

    merged = merge_config(base, overrides, "replace")

    assert merged["validation_rules"] == {"third": {"severity": "error"}}
    assert merged["scan_scope"] == {"exclude": ["a/**"]}


def test_profile_resolution_deep_merges_profile_chain():
    config = load_example_config()

    resolved = ConfigResolver(config).resolve(profile="ci")

    duplicate_rule = resolved.data["validation_rules"]["duplicate_references"]
    assert resolved.applied_profiles == ("default", "ci")
    assert duplicate_rule["category"] == "references"
    assert duplicate_rule["severity"] == "warning"
    assert duplicate_rule["priority"] == "low"
    assert duplicate_rule["threshold"] == 0


def test_environment_overlay_extending_profile_uses_that_profile_as_base():
    config = load_example_config()

    resolved = ConfigResolver(config).resolve(environment="ci")

    duplicate_rule = resolved.data["validation_rules"]["duplicate_references"]
    assert resolved.applied_profiles == ("default", "ci")
    assert resolved.applied_overlays == ("ci",)
    assert duplicate_rule["severity"] == "warning"
    assert resolved.data["scan_scope"]["checkpointing"] == {"enabled": False, "interval": 0}


def test_environment_overlay_without_extends_applies_to_requested_profile_base():
    config = load_example_config()
    config["environment_overlays"]["strict"] = {
        "description": "strict local overlay",
        "extends": None,
        "merge_strategy": "deep_merge",
        "overrides": {"validation_rules": {"broken_references": {"threshold": 5}}},
    }

    resolved = ConfigResolver(config).resolve(profile="ci", environment="strict")

    assert resolved.applied_profiles == ("default", "ci")
    assert resolved.applied_overlays == ("strict",)
    assert resolved.data["validation_rules"]["duplicate_references"]["severity"] == "warning"
    assert resolved.data["validation_rules"]["broken_references"]["threshold"] == 5


def test_overlay_chain_applies_parent_then_child():
    config = load_example_config()
    config["environment_overlays"]["base_overlay"] = {
        "extends": None,
        "merge_strategy": "deep_merge",
        "overrides": {"scan_scope": {"exclude": ["base/**"]}},
    }
    config["environment_overlays"]["child_overlay"] = {
        "extends": "base_overlay",
        "merge_strategy": "deep_merge",
        "overrides": {"scan_scope": {"config_dirs": [".codex", ".github"]}},
    }

    resolved = ConfigResolver(config).resolve(environment="child_overlay")

    assert resolved.applied_overlays == ("base_overlay", "child_overlay")
    assert resolved.data["scan_scope"]["exclude"] == ["base/**"]
    assert resolved.data["scan_scope"]["config_dirs"] == [".codex", ".github"]


def test_resolver_does_not_mutate_original_config():
    config = load_example_config()
    original = copy.deepcopy(config)

    ConfigResolver(config).resolve(profile="ci", environment="ci")

    assert config == original


def test_config_loader_resolve_validates_and_returns_resolved_data():
    loader = ConfigLoader.get_instance(SCANNER_DIR / "config" / "examples" / "scanner_config.example.yaml")

    resolved = loader.resolve(profile="ci", environment="ci")
    snapshot = loader.resolved_snapshot(profile="ci", environment="ci")

    assert resolved["validation_rules"]["duplicate_references"]["severity"] == "warning"
    assert snapshot.applied_profiles == ("default", "ci")
    assert snapshot.applied_overlays == ("ci",)


def test_unknown_profile_and_overlay_raise_specific_errors():
    resolver = ConfigResolver(load_example_config())

    with pytest.raises(UnknownConfigProfileError, match="missing"):
        resolver.resolve(profile="missing")

    with pytest.raises(UnknownEnvironmentOverlayError, match="missing"):
        resolver.resolve(environment="missing")


def test_profile_inheritance_cycle_is_rejected():
    config = load_example_config()
    config["profiles"]["one"] = {"extends": "two", "overrides": {}}
    config["profiles"]["two"] = {"extends": "one", "overrides": {}}

    with pytest.raises(ConfigInheritanceCycleError, match="one -> two -> one"):
        ConfigResolver(config).resolve(profile="one")


def test_environment_overlay_cycle_is_rejected():
    config = load_example_config()
    config["environment_overlays"]["one"] = {"extends": "two", "overrides": {}}
    config["environment_overlays"]["two"] = {"extends": "one", "overrides": {}}

    with pytest.raises(ConfigInheritanceCycleError, match="one -> two -> one"):
        ConfigResolver(config).resolve(environment="one")


def test_overlay_extending_unknown_parent_is_rejected():
    config = load_example_config()
    config["environment_overlays"]["bad"] = {"extends": "missing", "overrides": {}}

    with pytest.raises(ConfigInheritanceError, match="unknown profile or overlay"):
        ConfigResolver(config).resolve(environment="bad")


def test_invalid_merge_strategy_and_override_shape_are_rejected():
    config = load_example_config()
    config["profiles"]["bad_strategy"] = {"merge_strategy": "append", "overrides": {}}
    config["profiles"]["bad_overrides"] = {"overrides": []}

    with pytest.raises(ConfigMergeStrategyError, match="Invalid merge strategy"):
        ConfigResolver(config).resolve(profile="bad_strategy")

    with pytest.raises(ConfigInheritanceError, match="overrides"):
        ConfigResolver(config).resolve(profile="bad_overrides")


def test_inheritance_resolution_performance_is_predictable():
    resolver = ConfigResolver(load_example_config())

    start = time.perf_counter()
    for _ in range(500):
        resolver.resolve(profile="ci", environment="ci")
    elapsed = time.perf_counter() - start

    assert elapsed < 2.0
