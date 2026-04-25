# Task 102 Foundation Migration and Adoption Outline

## Objective

Document how to adopt the portable foundation in both brand-new repositories and existing repositories without requiring readers to reconstruct the workflow from Tasks 99-101.

## Required Deliverables

1. A canonical migration/adoption guide under the engine docs.
2. A minimal setup checklist for brand-new repositories.
3. A migration path for existing repositories moving from repo-specific workflow state to the portable foundation contract.
4. A clear distinction between required core setup and optional follow-on layers.

## Documentation Inputs

- `templates/engine/core/portable-foundation-spec.md`
- Task 100 bootstrap layer handoff and setup behavior
- Task 101 cross-project fixture findings
- current tooling docs in `templates/TOOLS.md`
- current workflow docs in `templates/workflows/taskmaster/`

## Recommended Structure

### 1. Adoption overview

Explain what the portable foundation is, what problem it solves, and which tasks/components established the current model.

### 2. New repository adoption

Document:
- bootstrap command usage
- minimum required files and roots
- first validation steps
- first-task kickoff flow

### 3. Existing repository migration

Document:
- how to map current repo layout into `[repo_structure]`
- how to introduce metadata policy without forcing immediate full rollout
- how to bootstrap safely when workflow files already exist
- how to validate before wider enforcement

### 4. Optional layers

Separate required core setup from optional layers such as metrics, drift reports, and broader template policy rollout.

### 5. Verification checklist

Document the commands or evidence needed to confirm a successful adoption:
- `codex-task bootstrap init`
- `codex-task plan sync`
- `codex-guard validate --include-untracked`
- relevant tests or fixture validation where applicable

## Non-Goals

- adding new helper commands
- expanding bootstrap behavior
- creating new UI or dashboards

Task 102 is documentation-only unless a doc bug exposes a concrete mismatch in existing behavior.
