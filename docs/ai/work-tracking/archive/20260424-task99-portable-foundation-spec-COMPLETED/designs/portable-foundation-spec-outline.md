# Task 99 Portable Foundation Specification - Outline

## Objective

Write the reusable contract that turns the current workflow system into a portable foundation rather than a repo-specific set of rules.

## Inputs

- Task 91 metadata portability model
- Task 98 repo-structure configuration contract
- Taskmaster alignment workflow
- work-tracking enforcement workflow
- current `codex-guard` enforcement semantics

## Required Sections

1. purpose and goals
2. architectural layers: core engine vs repo adapter
3. metadata contract
4. policy-file contract
5. repo-structure contract
6. session lifecycle contract
7. work-tracking lifecycle contract
8. plan contract
9. enforcement semantics contract
10. compatibility rules for other repos
11. relationship to follow-on tasks

## Delivery Shape

- Canonical reusable spec: `templates/engine/core/portable-foundation-spec.md`
- Task-local design/evidence: this outline plus tracker/session/findings/decisions updates

## Boundary

Task 99 defines the contract. It does not implement bootstrap, migration tooling, or cross-project fixtures.
