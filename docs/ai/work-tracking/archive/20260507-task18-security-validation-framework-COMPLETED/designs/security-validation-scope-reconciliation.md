# Task 18 Security Validation Scope Reconciliation

## Purpose
Task 18 predates the portable scanner and guard foundation. Its original wording asks for a broad security validation framework with path traversal detection, template injection scanning, `detect-secrets`, sanitization helpers, audit checklists, vulnerability reporting, false-positive allowlists, and SAST integration.

Current repository evidence shows that several pieces are already covered by newer foundation work, while one useful gap remains: a portable template security validator that runs inside the existing scanner suite and emits the same metadata-wrapped reports as the other scanners.

## Current Evidence
- `python3 scripts/codex-task taskmaster health` reports a healthy full Taskmaster graph with zero invalid dependency references.
- `task-master show 97` confirms Task 97 is `done`, even though `.taskmaster/tasks/task_018.txt` still renders dependency `97` without a check mark.
- `scripts/codex-guard` already covers workflow, template metadata, runtime artifacts, session state, evidence, plan sync, and Taskmaster evidence.
- `scripts/template-ssot-scanner/scan_core.py` already provides portable file discovery with include/exclude policy and config-driven path decisions.
- `scripts/template-ssot-scanner/config/pattern_matcher.py` already provides allowlist/blocklist matching with blocklist precedence.
- `scripts/template-ssot-scanner/validation_interface.py` already defines `ValidationFinding`, `ValidationRule`, and configured validation rule loading.
- `scripts/template-ssot-scanner/report_generator.py` already provides metadata-wrapped report output.
- `templates/engine/core/portable-foundation-spec.md` requires portable, config-driven foundation behavior and repo-specific policy in configuration, not hard-coded project assumptions.

## Historical Requirement Assessment

| Historical Detail | Current Assessment | Task 18 Decision |
| --- | --- | --- |
| Path traversal detection using `pathlib` | Still relevant for template references, command examples, and config paths. | Implement deterministic local checks for traversal-like tokens and unsafe path references in scannable template/config files. |
| Template injection scanner with regex patterns | Still relevant, but must avoid noisy generalized SAST claims. | Implement scoped template-expression detection for high-risk unresolved expressions and command interpolation patterns. |
| Secret detection using `detect-secrets` | External dependency is not currently in `pyproject.toml`; adding it would expand install/runtime scope. | Defer external dependency. Implement deterministic local patterns for common accidental secret material and document that this is not full secret scanning. |
| Input sanitization functions | No current code path consumes user template input directly. | Defer; no proven current-state consumer. |
| Security audit checklist automation | Existing work-tracking and guard evidence already provide audit trail. | Represent security validation as scanner findings/report evidence, not a new checklist subsystem. |
| Vulnerability reporting format | Scanner report metadata wrapper exists. | Reuse metadata-wrapped scanner JSON with `ValidationFinding` payloads and summary stats. |
| False-positive allowlist | Existing allowlist/blocklist pattern matcher exists. | Reuse scanner config allowlists/blocklists and rule-specific path decisions. |
| SAST integration for template code | Too broad for the portable foundation and not proven by current evidence. | Defer to a future explicit task if real code execution surfaces emerge. |

## Selected Implementation Scope
Implement `scripts/template-ssot-scanner/security_validator.py` as a config-aware scanner module that:
- Uses `create_scanner_config_context()` and `ScannerConfigContext.file_discovery_config()` for portable file discovery.
- Scans existing scannable suffixes from `scanner_config.yaml`.
- Emits findings through `ValidationFinding` and `save_scanner_report()`.
- Supports rule names for path traversal, template injection, and inline secret material.
- Respects configured path allowlists/blocklists through the shared `PatternMatcher`.
- Has a CLI accepting `--base`, `--config`, `--profile`, `--environment`, `--env-overrides`, and `--output`.
- Produces deterministic JSON under `scripts/template-ssot-scanner/output/data/security_validation.json` by default.
- Includes focused pytest coverage for detection, allowlisting, metadata-wrapped output, CLI behavior, and safe-file baseline behavior.

## Explicit Non-Goals
- No new `detect-secrets` dependency in this task.
- No broad SAST integration.
- No guard rewrite unless verification shows the scanner cannot satisfy Task 18 acceptance.
- No sanitization helper library without a consuming code path.
- No changes to unrelated generated Taskmaster files.

## Verification Plan
- `python3 -m pytest scripts/template-ssot-scanner/test_security_validator.py`
- `python3 -m pytest tests/meta_workflow_guard/test_template_registry.py tests/meta_workflow_guard/test_guard_rules.py`
- `python3 scripts/template-ssot-scanner/security_validator.py --base . --output docs/ai/work-tracking/active/20260507-task18-security-validation-framework-ACTIVE/reports/security-validation-framework/security-validation-2026-05-07.json`
- `python3 scripts/codex-task plan sync`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-guard validate --include-untracked`
- `git diff --check`

## Scope Result
Task 18 should be completed as a portable scanner-suite security validator, with historical broad SAST and third-party secret-scanner ambitions deferred unless a later task proves a concrete runtime or dependency need.
