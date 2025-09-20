# Implementation Plan

## Overview
Codex-first migration of the Claude template system. We need a clean Single Source of Truth that runs entirely inside this repository, including the SSOT scanner suite, modular templates, and Codex-specific enforcement docs.

## Approach
- Stand up the Codex work-tracking and session structure so changes stay compliant with the templates.
- Port the SSOT scanner tooling into this repo, align it with `.codex/`, and confirm the safety fixes described in the August work logs.
- Run the scanners locally, review outputs, and apply Codex-tailored fixes without re-introducing the dangerous scripts.
- Migrate remaining monolithic references into the modular folders once the tooling reports are clean.

## Steps
1. Scaffold work-tracking folder (`docs/ai/work-tracking/active/20250920-codex-migration-ssot-ACTIVE`) with the required seven files and supporting subdirectories (`plans/`, `designs/`, `code/`, `archive/`, `reports/`).
2. Spin up a new session log under `sessions/2025/09/` and link `sessions/current`.
3. Review historical safety notes (2025-08 work logs) to ensure we keep Serena tooling, safe reorganize scripts, and corrected reference fix scripts.
4. Copy the SSOT scanner suite into this repo, patch it for `.codex`, and rerun `scanner.py`, `analyze_references.py`, and follow-up scanners.
5. Triage scanner results: catalog broken references, circular dependencies, and migration status deltas.
6. Plan and apply modular template fixes (post-scanner) with `--dry-run` validation.
7. Document outcomes in FINDINGS/CHANGELOG and update TRACKER/HANDOFF.
8. Implement `codex-task` helper + diff-aware guard (see Plans section):
   - `scripts/codex-task` provides `sessions update`, `work-tracking update`, and `scanner run` subcommands that auto-scaffold S:W:H:E entries.
   - `scripts/codex-guard validate` inspects changed session/work-tracking files for handler/evidence compliance (supports `--include-untracked`).
   - Document usage in CODEX.md, AGENTS.md, and templates/TOOLS.md; keep optional pre-commit/CI wiring on the roadmap.
   - TODO: extend guard with auto-fix skeletons when safe (tracked in plans).

## Success Criteria
- Work-tracking structure exists with populated files and subfolders.
- Sessions directory records today’s migration work with evidence links.
- SSOT scanner outputs live under `scripts/template-ssot-scanner/output/` for this repo and match the safety rules from the August analysis.
- Tooling documentation explicitly references Serena + Codex MCP usage.
- Ready list of remaining modularization tasks accompanied by clean scanner reports.
- `codex-task` helper + guard run cleanly (`codex-task …`, `codex-guard --validate`).
