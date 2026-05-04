#!/usr/bin/env python3
"""Tests for the scanner ConfigLoader contract."""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
import yaml

SCANNER_DIR = Path(__file__).resolve().parent

if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))

from config.config_loader import (  # noqa: E402
    ConfigLoadError,
    ConfigLoader,
    ConfigValidationError,
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


def test_config_loader_is_singleton_per_config_path_and_lazy(tmp_path):
    config_path = copy_default_config(tmp_path / "scanner_config.yaml")

    first = ConfigLoader.get_instance(config_path)
    second = ConfigLoader(config_path)

    assert first is second
    assert not first.is_loaded

    data = first.load()

    assert first.is_loaded
    assert data["schema_version"] == "1.0.0"


def test_config_loader_uses_distinct_singletons_for_distinct_paths(tmp_path):
    first_path = copy_default_config(tmp_path / "first.yaml")
    second_path = copy_default_config(tmp_path / "second.yaml")

    first = ConfigLoader.get_instance(first_path)
    second = ConfigLoader.get_instance(second_path)

    assert first is not second


def test_config_loader_returns_defensive_copies(tmp_path):
    config_path = copy_default_config(tmp_path / "scanner_config.yaml")
    loader = ConfigLoader.get_instance(config_path)

    data = loader.load()
    data["validation_rules"]["broken_references"]["severity"] = "info"

    fresh_data = loader.load()

    assert fresh_data["validation_rules"]["broken_references"]["severity"] == "error"


def test_config_loader_loads_defaults_when_requested_config_is_missing(tmp_path):
    missing_path = tmp_path / "missing.yaml"
    loader = ConfigLoader.get_instance(missing_path)

    data = loader.load()
    snapshot = loader.snapshot()

    assert snapshot.source == "defaults"
    assert snapshot.file_state.exists is False
    assert data["validation_rules"]["broken_references"]["severity"] == "error"


def test_config_loader_detects_creation_after_missing_default_load(tmp_path):
    config_path = tmp_path / "late-created.yaml"
    loader = ConfigLoader.get_instance(config_path)

    assert loader.load()["metadata"]["name"] == "codex-default-scanner-config"

    copy_default_config(config_path)

    assert loader.reload_if_changed()
    assert loader.snapshot().source == "file"


def test_config_loader_rejects_invalid_yaml(tmp_path):
    config_path = tmp_path / "broken.yaml"
    config_path.write_text("schema_version: [", encoding="utf-8")

    loader = ConfigLoader.get_instance(config_path)

    with pytest.raises(ConfigLoadError, match="Unable to parse YAML config"):
        loader.load()


def test_config_loader_rejects_invalid_schema_data(tmp_path):
    config_path = copy_default_config(tmp_path / "scanner_config.yaml")
    data = load_yaml(config_path)
    data["validation_rules"]["broken_references"]["severity"] = "critical"
    config_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    loader = ConfigLoader.get_instance(config_path)

    with pytest.raises(ConfigValidationError, match="broken_references.severity"):
        loader.load()


def test_config_loader_rejects_non_mapping_root(tmp_path):
    config_path = tmp_path / "list.yaml"
    config_path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    loader = ConfigLoader.get_instance(config_path)

    with pytest.raises(ConfigValidationError, match="document root"):
        loader.load()


def test_config_loader_hot_reload_detects_same_size_content_change(tmp_path):
    config_path = copy_default_config(tmp_path / "scanner_config.yaml")
    loader = ConfigLoader.get_instance(config_path)

    assert loader.load()["validation_rules"]["broken_references"]["threshold"] == 0
    original_state = loader.snapshot().file_state
    assert original_state.mtime_ns is not None

    changed_text = config_path.read_text(encoding="utf-8").replace("threshold: 0", "threshold: 5", 1)
    config_path.write_text(changed_text, encoding="utf-8")
    os.utime(config_path, ns=(original_state.mtime_ns, original_state.mtime_ns))

    assert loader.has_changed()
    assert loader.reload_if_changed()
    assert loader.load()["validation_rules"]["broken_references"]["threshold"] == 5
    assert not loader.reload_if_changed()


def test_config_loader_force_reload_refreshes_cached_data(tmp_path):
    config_path = copy_default_config(tmp_path / "scanner_config.yaml")
    loader = ConfigLoader.get_instance(config_path)

    assert loader.load()["validation_rules"]["broken_references"]["threshold"] == 0

    changed_text = config_path.read_text(encoding="utf-8").replace("threshold: 0", "threshold: 3", 1)
    config_path.write_text(changed_text, encoding="utf-8")

    assert loader.load()["validation_rules"]["broken_references"]["threshold"] == 0
    assert loader.load(force_reload=True)["validation_rules"]["broken_references"]["threshold"] == 3


def test_config_loader_singleton_and_load_are_thread_safe(tmp_path):
    config_path = copy_default_config(tmp_path / "scanner_config.yaml")

    def load_from_thread() -> tuple[int, str]:
        loader = ConfigLoader.get_instance(config_path)
        data = loader.load()
        return id(loader), data["validation_rules"]["broken_references"]["severity"]

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: load_from_thread(), range(32)))

    loader_ids = {loader_id for loader_id, _ in results}
    severities = {severity for _, severity in results}

    assert len(loader_ids) == 1
    assert severities == {"error"}


def test_config_loader_cached_load_and_reload_performance_is_predictable(tmp_path):
    config_path = copy_default_config(tmp_path / "scanner_config.yaml")
    loader = ConfigLoader.get_instance(config_path)
    loader.load()

    start = time.perf_counter()
    for _ in range(200):
        loader.load()
    for _ in range(25):
        loader.load(force_reload=True)
    elapsed = time.perf_counter() - start

    assert elapsed < 3.0
