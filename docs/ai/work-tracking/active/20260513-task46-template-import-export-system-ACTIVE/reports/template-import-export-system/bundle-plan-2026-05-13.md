# Template Bundle Plan

- Label: task46-baseline
- Created at: 2026-05-13T15:02:57+02:00
- Mode: non-destructive-template-bundle-plan
- Executes mutations: False
- Source: . (`templates`)
- Target: .
- Include dependencies: True

## Requested Templates

- `engine-core-ultrathink-protocol`
- `handlers-index`

## Status Counts

- identical: 9
- different: 0
- missing: 0
- source-missing: 0
- not-checked: 0

## Planned Templates

| Template | Status | Source | Target | Dependencies |
| --- | --- | --- | --- | --- |
| engine-core-ultrathink-protocol | identical | templates/engine/core/ultrathink-protocol.md | templates/engine/core/ultrathink-protocol.md | templates/engine/core/enforcement-check.md, templates/engine/core/pre-ultrathink.md, templates/patterns/#execute-ultrathink |
| handlers-index | identical | templates/handlers/index.md | templates/handlers/index.md | templates/registry/handlers/triggers-registry.md, templates/registry/handlers/orchestrators-registry.md, templates/registry/handlers/operators-registry.md, templates/handlers/templates/handlers/triggers/development/start-new-work.md, templates/handlers/templates/handlers/triggers/debug/fix-bug.md, templates/handlers/templates/handlers/triggers/test/create-test-checkpoint.md |
| engine-core-enforcement-check | identical | templates/engine/core/enforcement-check.md | templates/engine/core/enforcement-check.md | templates/engine/core/codex-readiness.md, templates/engine/core/pre-ultrathink.md |
| engine-core-pre-ultrathink | identical | templates/engine/core/pre-ultrathink.md | templates/engine/core/pre-ultrathink.md | templates/registry/index.md, templates/engine/core/enforcement-check.md |
| triggers-registry | identical | templates/registry/handlers/triggers-registry.md | templates/registry/handlers/triggers-registry.md | none |
| orchestrators-registry | identical | templates/registry/handlers/orchestrators-registry.md | templates/registry/handlers/orchestrators-registry.md | none |
| operators-registry | identical | templates/registry/handlers/operators-registry.md | templates/registry/handlers/operators-registry.md | none |
| engine-core-codex-readiness | identical | templates/engine/core/codex-readiness.md | templates/engine/core/codex-readiness.md | none |
| registry-index | identical | templates/registry/index.md | templates/registry/index.md | none |

## Missing Inputs

- Dependency `templates/patterns/#execute-ultrathink` requested by `engine-core-ultrathink-protocol`: Dependency could not be resolved from the local registry.
- Dependency `templates/handlers/templates/handlers/triggers/development/start-new-work.md` requested by `handlers-index`: Dependency could not be resolved from the local registry.
- Dependency `templates/handlers/templates/handlers/triggers/debug/fix-bug.md` requested by `handlers-index`: Dependency could not be resolved from the local registry.
- Dependency `templates/handlers/templates/handlers/triggers/test/create-test-checkpoint.md` requested by `handlers-index`: Dependency could not be resolved from the local registry.

## Manual Review Queue

- No manual review items. All compared templates are identical.

## Recommended Verification Commands

- `python3 scripts/codex-task template bundle-plan --template <id> --target-dir <target-repo> --report-file <manifest.json> --runbook-file <runbook.md>`
- `python3 scripts/codex-task bootstrap init --target-dir <target-repo>`
- `python3 scripts/codex-guard drift-check --strict`
- `python3 scripts/codex-task taskmaster health`
- `python3 scripts/codex-guard validate --include-untracked`
- `git diff --check`

## Non-Goals

- No template files are copied into the target repository.
- No ZIP archive is created or extracted.
- No marketplace, package registry, or remote service is contacted.
- No cryptographic signing or key management is performed.
- No bulk import/export mutation is executed.
- No target repository branch, commit, push, or pull request is created.

No template copy, archive, extraction, marketplace, signing, Git, or target-repository mutation was executed by this plan.
