# Task 32 Documentation Suite Scope Reconciliation

## Context

Task 32 was created with broad historical wording:

- update `CODEX.md`
- create `AGENTS.md`
- write `templates/TOOLS.md`
- generate user guides, migration guide, FAQ, API documentation, and video walkthrough scripts

That wording predates the current portable foundation work. The current repository already has the major documentation suite surfaces in place, so this task should not create a parallel documentation tree or rewrite unrelated stable docs.

## Current Evidence

| Surface | Evidence | Current state |
| --- | --- | --- |
| Portable foundation contract | `templates/engine/core/portable-foundation-spec.md` | Stable contract exists for sessions, plans, work tracking, repo structure, metadata, and guard semantics. |
| User guide hub | `templates/guides/index.md` | Current guide hub exists and points at onboarding, foundation adoption, Taskmaster alignment, session lifecycle, and Claude runtime contract. |
| Foundation adoption guide | `templates/engine/validation/foundation-adoption-guide.md` | Migration/adoption guide exists for applying the portable foundation to other repositories. |
| Tooling docs | `templates/TOOLS.md` | Current command router exists, including `codex-task`, `codex-guard`, direct Git execution mode, Serena status, bootstrap guidance, and repo-structure config. |
| Agent entrypoint | `AGENTS.md` | Agent catalog and Taskmaster integration guide exist. |
| Codex entrypoint | `CODEX.md` | Entry point exists, but its documentation hub has malformed markdown links on several items. |
| Beginner quickstart | `templates/guides/quickstart/getting-started.md` | Still framed as an older Claude-only guide and does not describe the current Codex foundation workflow. |
| Top-level user guide | `templates/USER-GUIDE.md` | Still framed as a legacy Claude guide, includes stale `gac` examples, and contains relative links such as `templates/workflows/...` that are wrong from inside `templates/USER-GUIDE.md`. |

## Findings

1. The main documentation suite already exists; creating a new suite would duplicate current foundation docs.
2. The proven current gap is the user-facing entry layer: the top-level guide and beginner quickstart still teach the pre-foundation Claude prompt-system model instead of the current Codex foundation with Taskmaster, sessions, plans, work tracking, guard evidence, direct Git execution, and Claude runtime gates.
3. `CODEX.md` has malformed markdown in the documentation hub:
   - `templates/workflows/examples/common-workflows.md`](templates/workflows/examples/common-workflows.md)
   - `templates/workflows/domain/README.md`](templates/workflows/domain/README.md)
   - `templates/integration/guides/creating-handlers.md`](templates/integration/guides/creating-handlers.md)
   - `templates/conventions/docs/documentation-standards.md`](templates/conventions/docs/documentation-standards.md)
   - `templates/handlers/orchestrators/system-improvement.md`](templates/handlers/orchestrators/system-improvement.md)

## Decision

For Task 32, implement the smallest documentation-suite repair with current evidence:

1. Replace `templates/USER-GUIDE.md` with a current user guide for the portable Codex foundation.
2. Replace `templates/guides/quickstart/getting-started.md` with a current quickstart that teaches the actual session/task/work-tracking workflow.
3. Update `templates/guides/index.md` so the quickstart is no longer labeled as older Claude-only material.
4. Fix malformed markdown links in the `CODEX.md` documentation hub.

## Out Of Scope

- Broad rewrite of every legacy Claude wording occurrence across the template tree.
- New video walkthrough scripts.
- New API documentation generator.
- New migration framework; the foundation adoption guide and bootstrap helper already cover that layer.
- Changes to runtime behavior, guard logic, Taskmaster graph structure, or Claude runtime hooks.

## Validation Plan

- Run a focused markdown-link check for the touched docs.
- Run `python3 scripts/codex-task plan sync`.
- Run `python3 scripts/codex-task work-tracking audit`.
- Run `python3 scripts/codex-guard validate --include-untracked`.
- Run `git diff --check`.
- Capture evidence under `reports/documentation-suite/`.
