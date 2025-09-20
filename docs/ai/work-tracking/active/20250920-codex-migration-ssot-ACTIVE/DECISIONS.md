# Decisions

## 2025-09-20 - Preserve Serena Workflow

### Context
Earlier attempts to "de-Serena" the templates caused protocol drift. Codex MCP supports Serena, so we keep the semantic tooling in place.

### Options Considered
1. Remove Serena references and fall back to `rg`/manual editing (risk: regressions, lost safety).
2. Reinstate Serena guidance and ensure MCP config loads it in Codex.

### Decision
Option 2. Document Serena usage prominently in `templates/TOOLS.md` and keep the MCP server registered.

### Consequences
- Templates remain consistent between Claude and Codex workflows.
- Codex operators must ensure Serena MCP server is available, but tooling continuity is preserved.

## 2025-09-20 - Run SSOT Tools In-Repo

### Context
Previously the scanners were run from the Claude repo and results copied over, leading to drift.

### Options Considered
1. Continue generating scanner output in the source repo and copy artifacts across.
2. Port scanner suite into Codex repo and run it locally.

### Decision
Option 2. Keeps Codex as the single source of truth for modularization going forward.

### Consequences
- Scanner scripts require minor adjustments for `.codex/`, already completed.
- Outputs now live alongside the code they describe.

## 2025-09-20 - codex-task Enforcement Helper

### Context
Template adherence must be automated across all workflows without forcing wrapper hacks.

### Options Considered
1. Bolt enforcement into the wrapper (pre-run hooks, heavy coupling).
2. Build a dedicated helper + validator (`codex-task`, diff-aware guard, optional auto-fix).

### Decision
Option 2. `codex-task <workflow>` drives Serena handler lookup, scaffolds S:W:H:E entries, and runs a smart validator that can also power pre-commit/CI checks.

### Consequences
- Provides strong enforcement with explicit commands and immediate feedback.
- Validator can suggest auto-fixes (skeleton entries) when safe (roadmap item).
- Keeps wrapper lightweight while still enabling mandatory compliance.
- Implementation: `scripts/codex-task` (scaffolds logs) + `scripts/codex-guard` (validates S:W:H:E).
