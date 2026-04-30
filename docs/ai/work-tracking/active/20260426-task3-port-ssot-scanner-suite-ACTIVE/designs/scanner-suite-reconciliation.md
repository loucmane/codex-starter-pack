# Task 3 Scanner Suite Foundation Reconciliation

## Purpose

Task 3 was originally written as a port from the FPL MCP scanner suite into this Codex repository. Later foundation work already created and evolved a broader Codex starter-pack foundation around scanners, guards, metadata policy, template drift detection, portable repository structure, metrics, and cross-project adoption.

The current operational scope is therefore bigger than an FPL MCP port. FPL MCP is a historical comparison point, not the authority. The authority for Task 3 is the current Codex starter-pack foundation and the scanner capabilities it needs.

## Working Assumption

Treat Task 3 as a stale-baseline foundation reconciliation task until the audit proves otherwise. The task is not complete because Taskmaster still has all subtasks pending, but implementation must be based on current scanner capabilities, current foundation requirements, and proven gaps.

## Initial Scope

- Audit `scripts/template-ssot-scanner/` modules currently present in this repository.
- Compare current files against Taskmaster expectations: `scanner.py`, validator/deduplication/migration modules, metadata versioning, schema validation, config/severity support, legacy compatibility, tests, and performance behavior.
- Compare scanner behavior against the current foundation surfaces: `templates/`, `.codex/config.toml` repo-structure portability, metadata policy, `scripts/codex-guard`, template metrics, and cross-project bootstrap/adoption workflows.
- Revisit Task 1 findings relevant to scanner hardening: large generated outputs, unsafe/incorrect help behavior, runtime artifact hygiene, and noisy default scan scope.
- Decide which subtasks are already satisfied, which need documentation only, and which require code changes.

## Safety Rules

- Do not overwrite current scanner files with stale source from another repository without a specific diff-backed reason.
- Do not change tests just to force a pass.
- Capture findings and decisions before implementation.
- Prefer small, evidence-backed changes over a broad scanner rewrite.
- Keep the scanner suite aligned with the portable foundation rather than only the old FPL source layout.

## Audit Questions

- What scanner commands exist today, and which have unsafe or surprising CLI behavior?
- Which generated outputs are source-controlled versus runtime-only?
- Is metadata output versioned and stable enough for downstream guard/metrics workflows?
- Does scanner behavior respect repo-structure portability or hardcode this repository layout?
- Do current tests cover the scanner behavior that foundation workflows depend on?
- Are FPL MCP modules still needed as a comparison source, or has later Codex work superseded them?
