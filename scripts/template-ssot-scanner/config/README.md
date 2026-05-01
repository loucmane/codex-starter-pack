# Scanner Configuration Contract

Task 4.1 defines the scanner configuration shape before the loader and rule engine are implemented.

## Files

- `scanner_config.schema.json` - JSON Schema for scanner YAML configuration.
- `config_loader.py` - thread-safe singleton/lazy loader with schema validation, default fallback, and hot reload detection.
- `inheritance.py` - profile and environment overlay resolver with explicit merge strategies.
- `pattern_matcher.py` - allowlist/blocklist matcher for path/reference entries using `glob` or `regex`.
- `rule_engine.py` - rule registry and execution layer with priority taxonomy, thresholds, and finding emission.
- `validation.py` - reusable jsonschema validator with normalized issue reporting for file, runtime, and resolved-config validation.
- `env_override.py` - `CODEX_SCANNER_` environment override parser and resolver.
- `examples/scanner_config.example.yaml` - complete example covering scan scope, validation rules, allowlists, blocklists, profiles, and environment overlays.
- `../scanner_config.yaml` - current default scanner configuration.

## Contract

The schema keeps the current scanner behavior compatible while making future Task 4 implementation explicit:

- `schema_version` identifies the config contract version.
- `scan_scope` describes include/exclude patterns, config directories, supported suffixes, and checkpoint defaults.
- `validation_rules` configures rule category, scanner output severity, rule-engine priority, threshold, enablement, parameters, and future auto-fix intent.
- `allowlists` and `blocklists` define path/reference exemptions or hard stops using `glob` or `regex` patterns.
- `profiles` and `environment_overlays` describe named inheritance targets, merge strategy, and partial config overrides that later loader work can merge.

`ConfigLoader` loads and validates the config contract, returns defensive copies, falls back to the bundled default config when a requested file is missing, and detects file changes using path state plus content digest. `validation.py` owns the reusable `ScannerConfigValidator`, normalized `ConfigValidationIssue` reporting, file-level validation helpers, and validation timing reports used by both tests and loader runtime hooks. `ConfigResolver` resolves profile inheritance and environment overlays using explicit `deep_merge` or `replace` strategies, detects inheritance cycles, and validates resolved configs through `ConfigLoader.resolve()`. `env_override.py` applies `CODEX_SCANNER_` variables after YAML/profile/overlay resolution and before runtime validation; double underscores separate nested path segments, for example `CODEX_SCANNER_VALIDATION_RULES__BROKEN_REFERENCES__SEVERITY=warning`. `RuleEngine` loads `validation_rules`, maps rule priorities (`critical`, `high`, `medium`, `low`, `info`) onto the existing scanner finding severity contract (`error`, `warning`, `info`), evaluates thresholds, and emits `ValidationFinding` instances. `PatternMatcher` loads `allowlists` and `blocklists`, supports path/reference targets, evaluates `glob` and `regex` entries, honors rule scoping and expiration dates, and resolves decisions with blocklist matches taking precedence over allowlist matches. Later Task 4 subtasks will implement dependency injection into scanner modules.
