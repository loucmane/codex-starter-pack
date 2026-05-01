#!/usr/bin/env python3
"""jsonschema validation helpers for scanner configuration files."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator, FormatChecker, SchemaError, ValidationError

DEFAULT_SCHEMA_PATH = Path(__file__).resolve().with_name("scanner_config.schema.json")


class ScannerConfigValidationError(ValueError):
    """Base exception for scanner configuration validation failures."""


class ConfigSchemaReadError(ScannerConfigValidationError):
    """Raised when the JSON Schema or YAML config file cannot be read or parsed."""


class ConfigSchemaDefinitionError(ScannerConfigValidationError):
    """Raised when the JSON Schema document is not a valid schema."""


class ConfigDataValidationError(ScannerConfigValidationError):
    """Raised when configuration data does not match the schema."""

    def __init__(self, issues: Iterable["ConfigValidationIssue"], schema_path: Path) -> None:
        self.issues = tuple(issues)
        self.schema_path = schema_path
        super().__init__(self.summary())

    def summary(self) -> str:
        """Return a compact human-readable validation summary."""
        if not self.issues:
            return f"Invalid scanner config for schema {self.schema_path}"
        return "; ".join(issue.format() for issue in self.issues)


@dataclass(frozen=True)
class ConfigValidationIssue:
    """Normalized jsonschema validation issue."""

    path: str
    message: str
    validator: str
    schema_path: str

    def format(self) -> str:
        """Format issue for CLI/error messages."""
        return f"{self.path}: {self.message}"


@dataclass(frozen=True)
class ConfigValidationReport:
    """Validation result with deterministic issue formatting and timing."""

    valid: bool
    issues: tuple[ConfigValidationIssue, ...]
    schema_path: Path
    duration_seconds: float

    def summary(self) -> str:
        """Return a concise report summary."""
        if self.valid:
            return f"valid scanner config ({self.duration_seconds:.6f}s)"
        return "; ".join(issue.format() for issue in self.issues)


def _resolve_path(path: str | Path | None, default: Path) -> Path:
    if path is None:
        return default.resolve(strict=False)
    return Path(path).expanduser().resolve(strict=False)


def _format_error_path(error: ValidationError) -> str:
    if not error.absolute_path:
        return "<root>"
    return ".".join(str(part) for part in error.absolute_path)


def _format_schema_path(error: ValidationError) -> str:
    if not error.absolute_schema_path:
        return "<schema>"
    return ".".join(str(part) for part in error.absolute_schema_path)


def _issue_from_error(error: ValidationError) -> ConfigValidationIssue:
    return ConfigValidationIssue(
        path=_format_error_path(error),
        message=error.message,
        validator=str(error.validator),
        schema_path=_format_schema_path(error),
    )


def _sort_errors(errors: Iterable[ValidationError]) -> list[ValidationError]:
    return sorted(
        errors,
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            str(error.validator),
            error.message,
        ),
    )


class ScannerConfigValidator:
    """Reusable JSON Schema validator for scanner configuration data."""

    def __init__(self, schema_path: str | Path | None = None) -> None:
        self.schema_path = _resolve_path(schema_path, DEFAULT_SCHEMA_PATH)
        self._schema: dict[str, Any] | None = None
        self._validator: Draft202012Validator | None = None

    @property
    def schema(self) -> dict[str, Any]:
        """Return the parsed schema document."""
        if self._schema is None:
            try:
                parsed = json.loads(self.schema_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ConfigSchemaReadError(f"Unable to parse JSON schema {self.schema_path}: {exc}") from exc
            except OSError as exc:
                raise ConfigSchemaReadError(f"Unable to read JSON schema {self.schema_path}: {exc}") from exc

            if not isinstance(parsed, dict):
                raise ConfigSchemaDefinitionError(f"Scanner config schema {self.schema_path} must be a JSON object")
            self._schema = parsed
        return self._schema

    @property
    def validator(self) -> Draft202012Validator:
        """Return the compiled Draft 2020-12 validator."""
        if self._validator is None:
            try:
                Draft202012Validator.check_schema(self.schema)
            except SchemaError as exc:
                raise ConfigSchemaDefinitionError(
                    f"Invalid scanner config schema {self.schema_path}: {exc.message}"
                ) from exc
            self._validator = Draft202012Validator(self.schema, format_checker=FormatChecker())
        return self._validator

    def check_schema(self) -> None:
        """Validate that the schema document is well-formed."""
        _ = self.validator

    def report(self, data: dict[str, Any]) -> ConfigValidationReport:
        """Return a validation report without raising on invalid data."""
        start = time.perf_counter()
        errors = _sort_errors(self.validator.iter_errors(data))
        duration = time.perf_counter() - start
        issues = tuple(_issue_from_error(error) for error in errors)
        return ConfigValidationReport(
            valid=not issues,
            issues=issues,
            schema_path=self.schema_path,
            duration_seconds=duration,
        )

    def validate(self, data: dict[str, Any]) -> ConfigValidationReport:
        """Validate config data and raise with normalized issues on failure."""
        report = self.report(data)
        if not report.valid:
            raise ConfigDataValidationError(report.issues, self.schema_path)
        return report


def load_config_file(config_path: str | Path) -> dict[str, Any]:
    """Load a YAML configuration file and require a mapping root."""
    path = _resolve_path(config_path, Path.cwd())
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigSchemaReadError(f"Unable to parse YAML config {path}: {exc}") from exc
    except OSError as exc:
        raise ConfigSchemaReadError(f"Unable to read config {path}: {exc}") from exc

    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        issue = ConfigValidationIssue(
            path="<root>",
            message="scanner configuration must contain a mapping at the document root",
            validator="type",
            schema_path="<loader>",
        )
        raise ConfigDataValidationError((issue,), DEFAULT_SCHEMA_PATH)
    return parsed


def validate_config_data(
    data: dict[str, Any],
    schema_path: str | Path | None = None,
) -> ConfigValidationReport:
    """Validate an in-memory scanner configuration mapping."""
    return ScannerConfigValidator(schema_path=schema_path).validate(data)


def validate_config_file(
    config_path: str | Path,
    schema_path: str | Path | None = None,
) -> ConfigValidationReport:
    """Validate a YAML scanner configuration file."""
    data = load_config_file(config_path)
    return validate_config_data(data, schema_path=schema_path)
