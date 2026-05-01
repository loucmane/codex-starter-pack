#!/usr/bin/env python3
"""Thread-safe YAML configuration loader for the Template SSOT scanner."""

from __future__ import annotations

import copy
import hashlib
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

import yaml
from config.validation import (
    ConfigDataValidationError,
    ConfigSchemaDefinitionError,
    ConfigSchemaReadError,
    ScannerConfigValidator,
)

SCANNER_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = SCANNER_DIR / "scanner_config.yaml"
DEFAULT_SCHEMA_PATH = Path(__file__).resolve().with_name("scanner_config.schema.json")

BUILTIN_DEFAULT_CONFIG: dict[str, Any] = {
    "schema_version": "1.0.0",
    "metadata": {
        "name": "codex-default-scanner-config",
        "description": "Built-in fallback scanner configuration.",
    },
    "scan_scope": {
        "include": ["**/*.md", "**/*.json", "**/*.yml", "**/*.yaml"],
        "exclude": [
            ".codex/.tmp/**",
            ".codex/cache/**",
            ".codex/log/**",
            ".codex/plugins/**",
            ".codex/sessions/**",
            ".codex/shell_snapshots/**",
            ".codex/skills/**",
            ".codex/tmp/**",
            ".codex/auth.json",
            ".codex/history.jsonl",
            ".codex/installation_id",
            ".codex/models_cache.json",
            ".codex/state_*.sqlite*",
            ".codex/version.json",
        ],
        "config_dirs": [".codex", ".claude"],
    },
    "validation_rules": {
        "broken_references": {
            "category": "references",
            "severity": "error",
            "priority": "critical",
            "threshold": 0,
            "enabled": True,
            "auto_fix": False,
        },
        "migrated_monolith_references": {
            "category": "migration",
            "severity": "error",
            "priority": "high",
            "threshold": 0,
            "enabled": True,
            "auto_fix": False,
        },
        "circular_dependencies": {
            "category": "dependencies",
            "severity": "warning",
            "priority": "medium",
            "threshold": 0,
            "enabled": True,
            "auto_fix": False,
        },
        "orphaned_files": {
            "category": "coverage",
            "severity": "warning",
            "priority": "low",
            "threshold": 0,
            "enabled": True,
            "auto_fix": False,
        },
        "duplicate_references": {
            "category": "references",
            "severity": "info",
            "priority": "info",
            "threshold": 0,
            "enabled": True,
            "auto_fix": False,
        },
    },
    "allowlists": {"paths": [], "references": []},
    "blocklists": {"paths": [], "references": []},
    "profiles": {
        "default": {
            "description": "Built-in fallback profile.",
            "extends": None,
            "merge_strategy": "deep_merge",
            "overrides": {},
        }
    },
    "environment_overlays": {},
}


class ConfigLoaderError(ValueError):
    """Base exception for scanner configuration loading failures."""


class ConfigLoadError(ConfigLoaderError):
    """Raised when a scanner configuration file cannot be read or parsed."""


class ConfigValidationError(ConfigLoaderError):
    """Raised when a scanner configuration does not match the schema."""


@dataclass(frozen=True)
class ConfigFileState:
    """Reload comparison state for a configuration path."""

    exists: bool
    mtime_ns: int | None
    size: int | None
    digest: str | None


@dataclass(frozen=True)
class ConfigSnapshot:
    """Loaded configuration data plus reload metadata."""

    path: Path
    schema_path: Path
    data: dict[str, Any]
    source: str
    file_state: ConfigFileState
    loaded_at: float


def _resolve_path(path: str | Path | None, default: Path) -> Path:
    if path is None:
        return default.resolve(strict=False)
    return Path(path).expanduser().resolve(strict=False)


class ConfigLoader:
    """Singleton YAML config loader with lazy loading and hot reload support."""

    _instances: ClassVar[dict[tuple[Path, Path, bool], "ConfigLoader"]] = {}
    _instances_lock: ClassVar[threading.RLock] = threading.RLock()

    def __new__(
        cls,
        config_path: str | Path | None = None,
        schema_path: str | Path | None = None,
        validate: bool = True,
    ) -> "ConfigLoader":
        resolved_config = _resolve_path(config_path, DEFAULT_CONFIG_PATH)
        resolved_schema = _resolve_path(schema_path, DEFAULT_SCHEMA_PATH)
        key = (resolved_config, resolved_schema, bool(validate))

        with cls._instances_lock:
            instance = cls._instances.get(key)
            if instance is None:
                instance = super().__new__(cls)
                instance._singleton_key = key
                instance._initialized = False
                cls._instances[key] = instance
            return instance

    def __init__(
        self,
        config_path: str | Path | None = None,
        schema_path: str | Path | None = None,
        validate: bool = True,
    ) -> None:
        if self._initialized:
            return

        self.config_path = _resolve_path(config_path, DEFAULT_CONFIG_PATH)
        self.schema_path = _resolve_path(schema_path, DEFAULT_SCHEMA_PATH)
        self.validate = bool(validate)
        self._lock = threading.RLock()
        self._snapshot: ConfigSnapshot | None = None
        self._validator: ScannerConfigValidator | None = None
        self._initialized = True

    @classmethod
    def get_instance(
        cls,
        config_path: str | Path | None = None,
        schema_path: str | Path | None = None,
        validate: bool = True,
    ) -> "ConfigLoader":
        """Return the singleton loader for the resolved config/schema pair."""
        return cls(config_path=config_path, schema_path=schema_path, validate=validate)

    @classmethod
    def reset_instances_for_tests(cls) -> None:
        """Clear singleton state for isolated unit tests."""
        with cls._instances_lock:
            cls._instances.clear()

    @property
    def is_loaded(self) -> bool:
        """Return whether configuration data has been loaded into memory."""
        with self._lock:
            return self._snapshot is not None

    def load(self, force_reload: bool = False) -> dict[str, Any]:
        """Load and return scanner configuration as a defensive copy."""
        with self._lock:
            if self._snapshot is not None and not force_reload:
                return copy.deepcopy(self._snapshot.data)

            self._snapshot = self._load_snapshot()
            return copy.deepcopy(self._snapshot.data)

    def snapshot(self) -> ConfigSnapshot:
        """Return the current snapshot, loading lazily if needed."""
        with self._lock:
            if self._snapshot is None:
                self._snapshot = self._load_snapshot()
            return ConfigSnapshot(
                path=self._snapshot.path,
                schema_path=self._snapshot.schema_path,
                data=copy.deepcopy(self._snapshot.data),
                source=self._snapshot.source,
                file_state=self._snapshot.file_state,
                loaded_at=self._snapshot.loaded_at,
            )

    def has_changed(self) -> bool:
        """Return whether the tracked config file differs from the cached snapshot."""
        with self._lock:
            if self._snapshot is None:
                return True
            return self._file_state(self.config_path) != self._snapshot.file_state

    def reload_if_changed(self) -> bool:
        """Reload config only when the tracked file changed; return whether reloaded."""
        with self._lock:
            if self._snapshot is None or self.has_changed():
                self.load(force_reload=True)
                return True
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Return a top-level configuration value from the loaded config."""
        return self.load().get(key, default)

    def validation_rules(self) -> dict[str, Any]:
        """Return configured validation rules as a defensive copy."""
        rules = self.load().get("validation_rules", {})
        if not isinstance(rules, dict):
            raise ConfigValidationError("scanner configuration field 'validation_rules' must be a mapping")
        return copy.deepcopy(rules)

    def resolve(
        self,
        profile: str | None = None,
        environment: str | None = None,
        force_reload: bool = False,
    ) -> dict[str, Any]:
        """Resolve config inheritance for an optional profile and environment."""
        from config.inheritance import ConfigResolver

        resolved = ConfigResolver(self.load(force_reload=force_reload)).resolve(
            profile=profile,
            environment=environment,
        )
        self._validate_config(resolved.data)
        return copy.deepcopy(resolved.data)

    def resolved_snapshot(
        self,
        profile: str | None = None,
        environment: str | None = None,
        force_reload: bool = False,
    ):
        """Return resolved config plus inheritance metadata."""
        from config.inheritance import ConfigResolver

        resolved = ConfigResolver(self.load(force_reload=force_reload)).resolve(
            profile=profile,
            environment=environment,
        )
        self._validate_config(resolved.data)
        return resolved

    def _load_snapshot(self) -> ConfigSnapshot:
        file_state = self._file_state(self.config_path)

        if self.config_path.exists():
            data = self._read_yaml_file(self.config_path)
            source = "file"
        else:
            data = self._load_default_data()
            source = "defaults"

        self._validate_config(data)
        return ConfigSnapshot(
            path=self.config_path,
            schema_path=self.schema_path,
            data=data,
            source=source,
            file_state=file_state,
            loaded_at=time.time(),
        )

    def _read_yaml_file(self, path: Path) -> dict[str, Any]:
        try:
            parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ConfigLoadError(f"Unable to parse YAML config {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigLoadError(f"Unable to read config {path}: {exc}") from exc

        if parsed is None:
            return {}
        if not isinstance(parsed, dict):
            raise ConfigValidationError(f"Scanner config {path} must contain a mapping at the document root")
        return parsed

    def _load_default_data(self) -> dict[str, Any]:
        if DEFAULT_CONFIG_PATH.exists() and DEFAULT_CONFIG_PATH != self.config_path:
            return self._read_yaml_file(DEFAULT_CONFIG_PATH)
        return copy.deepcopy(BUILTIN_DEFAULT_CONFIG)

    def _validate_config(self, data: dict[str, Any]) -> None:
        if not self.validate:
            return

        try:
            self._schema_validator().validate(data)
        except ConfigDataValidationError as exc:
            raise ConfigValidationError(f"Invalid scanner config: {exc.summary()}") from exc

    def _schema_validator(self) -> ScannerConfigValidator:
        if self._validator is not None:
            return self._validator

        try:
            validator = ScannerConfigValidator(self.schema_path)
            validator.check_schema()
        except ConfigSchemaReadError as exc:
            raise ConfigLoadError(str(exc)) from exc
        except ConfigSchemaDefinitionError as exc:
            raise ConfigValidationError(str(exc)) from exc

        self._validator = validator
        return self._validator

    def _file_state(self, path: Path) -> ConfigFileState:
        try:
            stat = path.stat()
            content = path.read_bytes()
        except FileNotFoundError:
            return ConfigFileState(exists=False, mtime_ns=None, size=None, digest=None)
        except OSError as exc:
            raise ConfigLoadError(f"Unable to inspect config {path}: {exc}") from exc

        digest = hashlib.sha256(content).hexdigest()
        return ConfigFileState(
            exists=True,
            mtime_ns=stat.st_mtime_ns,
            size=stat.st_size,
            digest=digest,
        )
