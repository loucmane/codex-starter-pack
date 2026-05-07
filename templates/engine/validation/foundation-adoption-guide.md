---
name: foundation-adoption-guide
title: Portable Foundation Migration and Adoption Guide
type: documentation
status: stable
dependencies:
  - templates/engine/core/portable-foundation-spec.md
  - templates/TOOLS.md
  - templates/workflows/taskmaster/work-tracking-enforcement.md
---

# Portable Foundation Migration and Adoption Guide

## Purpose

This guide explains how to apply the portable Codex foundation to both brand-new repositories and existing repositories that already contain workflow or template state.

Use this guide after reading `templates/engine/core/portable-foundation-spec.md`. The specification defines the contract; this guide explains how to roll it out safely.

## Foundation Surface

The current portable foundation consists of:

- the portable core contract in `templates/engine/core/portable-foundation-spec.md`
- repo-local `[repo_structure]` configuration in `.codex/config.toml`
- repo-local metadata policy data
- bootstrap support via `python3 scripts/codex-task bootstrap init`
- task kickoff support via `python3 scripts/codex-task wizard kickoff`
- validation via `python3 scripts/codex-guard validate --include-untracked`
- cross-project fixture coverage proving the model works outside this repository’s default layout

## Required vs Optional Layers

### Required core setup

The minimum required setup is:

1. `.codex/config.toml` with `[repo_structure]`
2. a metadata policy file at the configured templates root
3. configured roots for sessions, plans, Taskmaster, work-tracking, and reports
4. guard-compatible session/plan/tracker lifecycle
5. validation evidence confirming the configured layout works

### Optional layers

These can be adopted later:

- broader metadata-policy rollout to more template families
- drift reporting
- metrics dashboard generation
- broader compatibility fixtures or repo-specific verification

Do not block first adoption on optional layers if the required setup is already correct.

## New Repository Adoption

Use this path when the repository does not yet have foundation assets.

### 1. Bootstrap starter assets

Run:

```bash
python3 scripts/codex-task bootstrap init --target-dir <repo>
```

By default this creates:

- `.codex/config.toml`
- a starter metadata policy file
- sessions root
- plans root
- plan-state directory
- Taskmaster root scaffold
- work-tracking root with `active/` and `archive/`
- reports root plus drift/metrics/session-continuation subdirectories
- `.codex/bootstrap/FOUNDATION-SETUP.md`

Important behavior:

- existing config and policy files are preserved by default
- pass `--force` only when you intentionally want to refresh starter files
- pass repo-root override flags when the target repository should not use the defaults

### 2. Review `[repo_structure]`

Inspect `.codex/config.toml` and make sure the configured roots match the target repository.

Default roots in this repository are:

```toml
[repo_structure]
templates_root = "templates"
sessions_root = "sessions"
plans_root = "plans"
plan_state_dir = ".plan_state"
taskmaster_root = ".taskmaster"
work_tracking_root = "docs/ai/work-tracking"
reports_root = "reports"
```

If the target repository is docs-heavy, app-centric, or otherwise structured differently, change these roots before active work begins.

### 3. Review metadata policy scope

The metadata policy is repo-local data, not core logic. Confirm that:

- the governed template families are correct
- exemptions match the repo’s reality
- rollout scope is narrow enough for first adoption

### 4. Validate the setup

Before the first task, run:

```bash
python3 scripts/codex-guard validate --include-untracked
```

If the target repository has local compatibility tests, run them as well.

### 5. Start the first task

After bootstrap and validation:

1. create a branch matching `feat/task-<id>-...`
2. move the Taskmaster task to `in-progress`
3. run:

```bash
python3 scripts/codex-task wizard kickoff --task <id>
```

From there, the normal session/work-tracking/plan rules apply.

When changing Taskmaster status or task metadata outside the kickoff helper, refresh the generated task file with:

```bash
python3 scripts/codex-task taskmaster generate-one --id <id>
```

Use broad in-place `task-master generate` only when a deliberate repository-wide generated task-file refresh is explicitly scoped.

## Existing Repository Migration

Use this path when the repository already has workflow or template state.

### 1. Inventory the current layout

Identify:

- where templates already live
- where docs already live
- whether an existing task system is present
- whether session-like logs or decision records already exist
- where reports should live in this repository

Do not start by forcing the repository into this repository’s directory names.

### 2. Map the repository into `[repo_structure]`

Translate the existing layout into repo-local roots in `.codex/config.toml`.

Examples:

- product-web repo: `ops/templates`, `ops/state/`, `ops/reports`
- docs-heavy repo: `docs/templates`, `docs/ops/`
- utility repo: compact `workflow/` roots

The principle is: scripts follow config, not the other way around.

### 3. Introduce metadata policy safely

Do not force immediate enforcement across every markdown family in an existing repository.

Start by:

1. keeping the portable metadata baseline (`title`, `type`, `status`)
2. limiting policy scope to ready template families
3. adding exemptions for aggregate docs, historical reports, or other intentional exceptions

### 4. Bootstrap without clobbering existing files

Run:

```bash
python3 scripts/codex-task bootstrap init --target-dir <repo>
```

Expected behavior:

- missing assets are created
- existing config/policy files are skipped by default
- existing workflow directories are treated as valid inputs

Use `--force` only after reviewing what would be refreshed.

### 5. Validate before wider rollout

At minimum, run:

```bash
python3 scripts/codex-guard validate --include-untracked
python3 scripts/codex-task plan sync --plan <active-plan> --tracker <active-tracker>
```

If portability fixtures or repo-local tests exist, run them before wider enforcement.

## Phased Rollout Model

For an existing repository, use this order:

1. define repo roots
2. add starter config/policy files
3. validate the configured layout
4. start using the session/plan/work-tracking lifecycle on new work
5. expand metadata-policy scope gradually
6. adopt optional reporting layers later

This is safer than attempting a full workflow rewrite in one pass.

## Verification Checklist

- [ ] `.codex/config.toml` exists and `[repo_structure]` matches the target repository
- [ ] the metadata policy exists at the configured templates root
- [ ] sessions, plans, Taskmaster, work-tracking, and reports roots resolve correctly
- [ ] bootstrap setup notes exist and were reviewed
- [ ] `python3 scripts/codex-guard validate --include-untracked` passes
- [ ] active plan and tracker sync cleanly with `python3 scripts/codex-task plan sync ...`
- [ ] first-task kickoff works on a feature branch

## Cross-Project Validation Reference

Task 101 validated the current foundation across four representative repo-shape families:

- product-web
- game/tool
- docs-heavy
- utility/library

That fixture coverage proved:

- repo-structure overrides resolve correctly
- bootstrap does not depend on this repository’s default paths
- guard and metrics logic follow configured roots

## Anti-Patterns

Avoid these migration mistakes:

- hardcoding this repository’s layout into another repository when config would solve it
- forcing full metadata rollout before the target repo is ready
- using `--force` during bootstrap without reviewing what already exists
- treating optional layers as mandatory blockers for first adoption
- documenting workflow steps that current helpers do not support

## References

- `templates/engine/core/portable-foundation-spec.md`
- `templates/TOOLS.md`
- `templates/workflows/taskmaster/work-tracking-enforcement.md`

## Progress Log

- **2026-04-24 21:50** — [S:20260424|W:task102-foundation-migration-adoption|H:templates/engine/validation/foundation-adoption-guide.md|E:docs/ai/work-tracking/active/20260424-task102-foundation-migration-adoption-ACTIVE/designs/foundation-migration-outline.md] Authored the canonical migration/adoption guide using the portable spec, bootstrap layer behavior, and cross-project fixture findings as the rollout model
