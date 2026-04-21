# Codex Execution Engine

This directory contains the current execution-engine reference set for the repo. It is no longer a "Phase 1 only" extraction target from a monolithic `CLAUDE.md`; it is the canonical engine surface that registry and metadata discovery point to today.

## Current Directory Structure

```text
templates/engine/
├── README.md
├── MODULARIZATION-COMPLETE.md
├── verify-phase1.sh
├── activation/
│   └── context-aware.md
├── core/
│   ├── codex-readiness.md
│   ├── enforcement-check.md
│   ├── pre-ultrathink.md
│   ├── session-resolver.md
│   └── ultrathink-protocol.md
├── debugging/
│   └── system-debug.md
├── enforcement/
│   ├── behavioral-hooks.md
│   ├── cannot-proceed.md
│   ├── meta-workflow-guard-ci-plan.md
│   └── meta-workflow-guard-remediation.md
├── examples/
│   └── practical.md
├── execution/
│   └── swhe-format.md
├── fallbacks/
│   └── error-handling.md
├── navigation/
│   ├── common-flows.md
│   └── template-protocol.md
├── structure/
│   └── template-system.md
└── validation/
    ├── ENFORCEMENT-SUMMARY.md
    ├── integration-guide.md
    └── validation-framework.md
```

## What Changed Since the Original Modularization

The earlier roadmap in this directory described additional pending Phase 2/3 modules that are not part of the current engine tree. Those older placeholders are not referenced by the current registry/metadata surfaces and should not be treated as the canonical implementation target.

The current canonical sources for engine discoverability are:

- `templates/registry/index.json`
- `templates/metadata/template-inventory.txt`
- `templates/metadata/template-summary.csv`
- `templates/metadata/template-overview.md`

Those discovery surfaces align with the directory structure listed above.

## Engine Surface by Area

### Core protocols

- `core/codex-readiness.md`
- `core/enforcement-check.md`
- `core/pre-ultrathink.md`
- `core/session-resolver.md`
- `core/ultrathink-protocol.md`

### Request activation and execution

- `activation/context-aware.md`
- `execution/swhe-format.md`

### Navigation and structure

- `navigation/common-flows.md`
- `navigation/template-protocol.md`
- `structure/template-system.md`

### Enforcement and validation

- `enforcement/behavioral-hooks.md`
- `enforcement/cannot-proceed.md`
- `enforcement/meta-workflow-guard-ci-plan.md`
- `enforcement/meta-workflow-guard-remediation.md`
- `validation/ENFORCEMENT-SUMMARY.md`
- `validation/integration-guide.md`
- `validation/validation-framework.md`

### Support and examples

- `debugging/system-debug.md`
- `examples/practical.md`
- `fallbacks/error-handling.md`

## Relationship to `CLAUDE.md`

`CLAUDE.md` is no longer an engine import hub with inline HTML import comments. The current root file imports Taskmaster instructions only:

```markdown
# Claude Code Instructions
@./.taskmaster/CLAUDE.md
```

That means engine discoverability should be treated as a registry/metadata concern rather than a `CLAUDE.md` comment-import concern.

## Module Conventions

Some engine files carry YAML frontmatter (`id`, `name`, `type`, and related metadata); others are plain markdown reference documents. Do not assume every engine file shares the same frontmatter schema.

When adding or updating engine modules:

1. Keep file placement aligned with the current category structure.
2. Add or preserve frontmatter where the module already uses it.
3. Update registry/metadata surfaces if the canonical engine inventory changes.
4. Re-run the verification script after edits.

## Verification

Run the verification script to validate the current engine surface and discovery references:

```bash
chmod +x templates/engine/verify-phase1.sh
templates/engine/verify-phase1.sh
```

The script name is retained for continuity, but it now validates the current engine tree rather than the original `.claude`-era Phase 1 extraction assumptions.

## Task 90 Focus

Task 90 begins by reconciling engine roadmap drift and validation drift:

1. Keep this README aligned with the actual engine files on disk.
2. Keep `verify-phase1.sh` aligned with the current engine tree and discovery surfaces.
3. Only author new engine modules when a real gap remains after those surfaces are reconciled.

## Progress Log

- **2026-04-21 13:27** — [S:20260421|W:task90-complete-engine-migration|H:templates/engine/README.md|E:docs/ai/work-tracking/active/20260421-task90-complete-engine-migration-ACTIVE/reports/complete-engine-migration/verify-phase1-2026-04-21-pass.txt] Rewrote the README around the canonical current engine tree and validated it against the refreshed engine-surface verifier

---
Last Updated: 2026-04-21
