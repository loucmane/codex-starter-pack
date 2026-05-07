#!/usr/bin/env python3
"""Tests for the template security validation scanner."""

import json
import sys
from pathlib import Path

SCANNER_DIR = Path(__file__).resolve().parent
if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))

from config.integration import create_scanner_config_context  # noqa: E402
from scan_metadata import load_with_metadata, validate_output_file  # noqa: E402
from security_validator import SecurityValidator, main  # noqa: E402


def config_fixture(**overrides):
    config = {
        "schema_version": "1.0.0",
        "metadata": {"name": "security-validator-test"},
        "scan_scope": {
            "include": ["templates/**", ".claude/**"],
            "exclude": [],
            "config_dirs": [".claude"],
            "scannable_suffixes": [".md", ".json", ".yml", ".yaml"],
        },
        "validation_rules": {
            "security_path_traversal": {
                "category": "security",
                "severity": "warning",
                "priority": "medium",
                "threshold": 0,
                "enabled": True,
                "auto_fix": False,
            },
            "security_template_injection": {
                "category": "security",
                "severity": "warning",
                "priority": "medium",
                "threshold": 0,
                "enabled": True,
                "auto_fix": False,
            },
            "security_inline_secret": {
                "category": "security",
                "severity": "error",
                "priority": "critical",
                "threshold": 0,
                "enabled": True,
                "auto_fix": False,
            },
        },
        "allowlists": {"paths": [], "references": []},
        "blocklists": {"paths": [], "references": []},
        "profiles": {},
        "environment_overlays": {},
    }
    config.update(overrides)
    return config


def test_security_validator_detects_traversal_template_injection_and_inline_secret(tmp_path):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "unsafe.md").write_text(
        "\n".join(
            [
                "# Unsafe",
                "source_path: ../../etc/passwd",
                "render: {{ env.SECRET_TOKEN }}",
                "token = ghp_abcdefghijklmnopqrstuvwxyzABCDEFGHIJ",
            ]
        ),
        encoding="utf-8",
    )

    context = create_scanner_config_context(config_data=config_fixture())
    report = SecurityValidator(tmp_path, config_context=context).validate()

    rule_names = {
        finding["details"]["rule_name"]
        for finding in report["findings"]
    }
    assert rule_names == {
        "security_path_traversal",
        "security_template_injection",
        "security_inline_secret",
    }
    assert report["summary"]["severity_counts"] == {"error": 1, "warning": 2}
    traversal = next(
        finding
        for finding in report["findings"]
        if finding["details"]["rule_name"] == "security_path_traversal"
    )
    assert traversal["details"]["escapes_base"] is True


def test_security_validator_suppresses_rule_specific_allowlisted_paths(tmp_path):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "allowed.md").write_text(
        "token = ghp_abcdefghijklmnopqrstuvwxyzABCDEFGHIJ\n",
        encoding="utf-8",
    )
    config = config_fixture(
        allowlists={
            "paths": [
                {
                    "pattern": "templates/allowed.md",
                    "kind": "glob",
                    "rules": ["security_inline_secret"],
                    "reason": "fixture false positive",
                }
            ],
            "references": [],
        }
    )

    context = create_scanner_config_context(config_data=config)
    report = SecurityValidator(tmp_path, config_context=context).validate()

    assert report["findings"] == []


def test_security_validator_keeps_placeholder_values_clean(tmp_path):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "safe.md").write_text(
        "\n".join(
            [
                "# Safe",
                "OPENAI_API_KEY=your_key_here",
                "password: CHANGE_ME_PLACEHOLDER",
                "secret: process.env.JWT_SECRET",
                "render: {{ user.name }}",
                "path: templates/current/file.md",
            ]
        ),
        encoding="utf-8",
    )

    context = create_scanner_config_context(config_data=config_fixture())
    report = SecurityValidator(tmp_path, config_context=context).validate()

    assert report["summary"]["total_findings"] == 0
    assert report["files_scanned"] == 1


def test_security_validator_ignores_relative_paths_that_stay_inside_project(tmp_path):
    templates = tmp_path / "templates"
    nested = templates / "nested"
    nested.mkdir(parents=True)
    (templates / "shared.md").write_text("# Shared\n", encoding="utf-8")
    (nested / "safe.md").write_text("See ../shared.md\n", encoding="utf-8")

    context = create_scanner_config_context(config_data=config_fixture())
    report = SecurityValidator(tmp_path, config_context=context).validate()

    assert report["summary"]["total_findings"] == 0


def test_security_validator_saves_metadata_wrapped_report(tmp_path):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "unsafe.md").write_text("api_key: live_secret_value_123456789\n", encoding="utf-8")
    output_file = tmp_path / "security.json"

    context = create_scanner_config_context(config_data=config_fixture())
    report = SecurityValidator(tmp_path, config_context=context).save(output_file)

    validate_output_file(output_file)
    data, metadata = load_with_metadata(output_file)
    assert data == report
    assert metadata["scanner"] == "security_validator"
    assert metadata["stats"]["findings"] == 1


def test_security_validator_cli_writes_requested_output(tmp_path):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "unsafe.md").write_text("path: ../../outside\n", encoding="utf-8")
    config_path = tmp_path / "scanner_config.yaml"
    config_path.write_text(json.dumps(config_fixture()), encoding="utf-8")
    output_file = tmp_path / "out" / "security.json"

    result = main(["--base", str(tmp_path), "--config", str(config_path), "--output", str(output_file)])

    assert result == 0
    validate_output_file(output_file)
    data, metadata = load_with_metadata(output_file)
    assert metadata["scanner"] == "security_validator"
    assert data["summary"]["rule_counts"] == {"security_path_traversal": 1}
