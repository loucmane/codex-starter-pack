---
id: portable-foundation-spec
title: Portable Foundation Specification
type: engine-component
status: stable
dependencies:
  - templates/metadata/template-metadata-policy.json
  - .codex/config.toml
  - templates/workflows/taskmaster/alignment.md
  - templates/workflows/taskmaster/work-tracking-enforcement.md
---

# Portable Foundation Specification

## Purpose

Define the reusable contract for the Codex workflow foundation so the core behavior can be reused across different repositories while repo-specific layout and rollout choices remain configuration-driven.

This specification separates:

- **portable core logic** that should behave the same in every repo
- **repo-local adapter configuration** that tells the core where things live and which scopes are enabled

## Goals

The portable foundation must support repositories that are not identical to this one, including product-web repos, game repos, docs-heavy repos, and lighter utility repos.

The foundation should preserve these properties across projects:

- deterministic session and work-tracking lifecycle
- consistent S:W:H:E evidence handling
- config-driven enforcement rather than hardcoded repo assumptions
- portable metadata rules with repo-local rollout control
- stable boundaries between core engine logic and repo adapters

## Architectural Layers

### 1. Core engine layer

This is the reusable logic that should remain consistent across projects.

Examples:

- `scripts/codex-guard`
- `scripts/codex-task`
- `scripts/template-metrics-dashboard`
- `scripts/template-migration-health-dashboard`
- plan/tracker/session validation rules
- metadata validation semantics
- template lifecycle, versioning, and governance assessment semantics
- work-tracking lifecycle rules

Core logic may read configuration, but it should not hardcode a single repo shape as a requirement.

### 2. Repo adapter layer

This is the project-specific configuration that tells the core how to operate in a given repository.

Examples:

- `[repo_structure]` in `.codex/config.toml`
- `templates/metadata/template-metadata-policy.json`
- branch policy conventions that are documented per repo
- rollout choices for which template families are enforced or exempt

Repo adapters should change behavior by data/configuration, not by forking core script logic.

## Portable Contracts

### Metadata contract

The portable metadata baseline is:

- `title`
- `type`
- `status`

These keys define the minimum portable metadata schema for governed template documents.

Rules:

- the core guard enforces required keys based on repo-local policy
- the repo may narrow or broaden scope through include/exclude rules
- repos may add local metadata keys, but they should not remove the portable baseline without explicitly changing the policy contract

### Policy-file contract

The metadata policy file is repo-local data, not core logic.

Current canonical file:

- `templates/metadata/template-metadata-policy.json`

Related repo-local policy files may extend the same pattern for adjacent governance concerns:

- `templates/metadata/template-lifecycle-policy.json`
- `templates/metadata/template-versioning-policy.json`
- `templates/metadata/template-governance-policy.json`

The portable policy contract includes:

- `version`
- `description`
- `defaults.required_keys`
- `defaults.frontmatter`
- ordered `rules`
- optional `exemptions`

Each rule may define:

- `name`
- `enforce`
- `include`
- `exclude`
- `notes`

Semantics:

- core logic interprets the policy
- repos own the policy contents
- rollout sequencing belongs in policy data, not in hardcoded script branches

### Repo-structure contract

Repo structure is defined by repo-local configuration.

Current canonical section:

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

Portable rule:

- core scripts derive operational paths from these roots
- defaults may match this repo’s current layout
- alternate repositories may override roots without patching core scripts

Derived paths include:

- active session link and session state file
- active plan link and plan sync log
- Taskmaster task files
- work-tracking active/archive roots
- report directories
- template metadata policy path

### Session lifecycle contract

Portable expectations for session handling:

- sessions are real dated artifacts, not abstract conversation state
- one active session is represented through the configured `sessions/current` link
- session state is mirrored in the configured session-state file
- session logs must record same-day progress with S:W:H:E evidence
- continuation and closeout behavior must remain compatible with guard enforcement

The exact root path is configurable. The lifecycle semantics are not.

### Work-tracking lifecycle contract

Portable expectations for work tracking:

- each active task uses one `-ACTIVE` folder
- active folders contain tracker, findings, decisions, implementation, changelog, handoff, and reports
- completed tasks are moved to archive rather than deleted
- tracker updates are same-day and evidence-backed
- guard enforcement treats archival as the valid transition out of active work

Folder roots are repo-local. The lifecycle behavior is core.

### Plan contract

Portable expectations for plans:

- one active plan is referenced through the configured current-plan link
- plans must contain `plan-step-scope`, `plan-step-implement`, and `plan-step-verify`
- tracker checkboxes must stay aligned with plan status
- plan sync must record hashes and timestamps in the configured sync log
- stale or overlapping active plans are enforcement issues unless clearly completed/passive

### Enforcement semantics contract

Portable enforcement semantics include:

- validate only against the repo’s configured roots and policy data
- fail when required evidence or lifecycle invariants are missing
- prefer data-driven scope selection over special-case code branches
- keep runtime artifacts out of commits
- preserve canonical response rules such as GAC formatting and session/work-tracking evidence expectations

Core scripts may evolve, but these semantics should remain stable enough for other repos to rely on.

## Boundary: Core vs Repo Adapter

### Belongs in core logic

- how metadata validation works
- how plan/tracker/session consistency is checked
- how work-tracking archival is recognized
- how reports are generated once locations are resolved
- how S:W:H:E records are parsed and validated

### Belongs in repo adapter configuration

- which template families are governed
- where templates/sessions/plans/reports/work-tracking live
- which paths are exempt from specific policies
- rollout sequencing and enforcement flags
- repo-specific naming/layout conventions that do not change the core semantics

### Should not happen

- hardcoding one repo layout into core scripts
- encoding repo-specific policy rollout in script branches
- forking core scripts per repository when configuration is sufficient

## Compatibility Rules

When applying this foundation to another repo:

1. keep the portable metadata baseline unless the repo intentionally defines a different policy contract
2. configure repo roots in `.codex/config.toml`
3. provide a repo-local metadata policy file
4. preserve session/plan/work-tracking lifecycle semantics
5. validate the configured layout with automated tests or fixtures before adoption

## Relationship to Completed Tasks

- **Task 91** established the portable metadata baseline and repo-local metadata policy model
- **Task 98** externalized repo-structure assumptions into repo-local configuration
- **Task 99** defines the contract that explains how those pieces fit together as a reusable foundation

## Relationship to Follow-on Tasks

- **Task 100** should bootstrap this foundation into new repositories
- **Task 101** should verify it across multiple repo shapes
- **Task 102** should document migration and adoption guidance

## Non-Goals

This specification does not:

- define a bootstrap installer
- define migration tooling
- define cross-project fixtures
- require a web UI or service layer

Those belong to follow-on tasks.

## Progress Log

- **2026-05-12 16:08** — [S:20260512|W:task36-template-governance-board|H:templates/engine/core/portable-foundation-spec.md|E:docs/ai/work-tracking/active/20260512-task36-template-governance-board-ACTIVE/designs/template-governance-scope-reconciliation.md] Added template governance policy to the repo-local policy-file contract and core semantic inventory.
- **2026-04-24 19:14** — [S:20260424|W:task99-portable-foundation-spec|H:templates/engine/core/portable-foundation-spec.md|E:docs/ai/work-tracking/active/20260424-task99-portable-foundation-spec-ACTIVE/designs/portable-foundation-spec-outline.md] Drafted the canonical portable foundation specification by combining the Task 91 metadata policy model, Task 98 repo-structure contract, and current workflow lifecycle rules
