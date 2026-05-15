# Task 75 Knowledge Base Scope Reconciliation

## Current Task Text

Taskmaster Task 75 says to build a searchable knowledge repository, with historical details for Confluence/GitBook setup, documentation import, search indexing, categorization, access controls, contribution guidelines, version control, and analytics.

## Current Repository Reality

The portable foundation already stores its knowledge in repo-native artifacts:

- user-facing guide surfaces: `templates/USER-GUIDE.md`, `templates/guides/index.md`, quickstart, onboarding, troubleshooting, communication, and reference docs
- operational/report surfaces: `reports/README.md` and report family README files
- task lifecycle evidence: Taskmaster task files, plans, sessions, work-tracking active/archive folders, and handoff files
- search/discovery surfaces: `templates/REGISTRY.md`, registry indexes, template metadata, and the new migration archive index
- continuity surfaces: Serena memories, compaction checkpoints, work-tracking handoffs, and session logs

Task 54 already implemented `python3 scripts/codex-task knowledge transfer-review` as a static readiness review over knowledge-transfer evidence. That task explicitly left a future searchable knowledge base as Task 75. Task 75 should therefore build the repo-native searchable index, not repeat Task 54's review packet or introduce external platform infrastructure.

## Options Considered

1. **Hosted knowledge base platform**: configure Confluence, GitBook, an LMS, a database, access controls, and analytics.
   - Rejected. This repository is a portable file-backed foundation. No platform credentials, hosting target, user directory, analytics backend, or external deployment requirement exists.

2. **Documentation rewrite or copy-based export**: duplicate all docs into a new `knowledge-base/` tree.
   - Rejected. Copying canonical docs would create drift against templates, reports, sessions, plans, and work-tracking archives.

3. **Repo-native searchable knowledge-base index**: add a deterministic `codex-task` command that inventories existing canonical knowledge surfaces, categorizes them, supports query filtering, and renders JSON/Markdown runbook artifacts.
   - Chosen. This satisfies the current-state gap without moving source artifacts or creating external dependencies.

## Chosen Implementation Boundary

Implement `python3 scripts/codex-task knowledge base` as a static, non-destructive knowledge repository index.

Expected behavior:

- inventory canonical knowledge surfaces across guides, reports, templates, workflows, plans, sessions, Taskmaster task files, work-tracking handoffs, and Serena memories
- categorize entries into operator guides, workflow protocols, tool/report references, task evidence, decisions/lessons, and continuity artifacts
- support `--query` for focused search packets
- write deterministic JSON and Markdown when `--report-file` / `--runbook-file` are provided
- include explicit non-goals for hosted platforms, access-control systems, analytics backends, LMS/video/Q&A systems, and source artifact mutation

Out of scope:

- Confluence/GitBook/LMS setup
- hosted search service
- external access controls or user provisioning
- analytics collection or dashboards
- copying or rewriting canonical source documentation
- mutating Taskmaster, sessions, plans, work-tracking, templates, reports, memories, or external systems beyond the requested report files

## Acceptance Evidence

- focused parser/build/render/write/query tests for the knowledge-base command
- generated Task 75 knowledge-base and query artifacts under the active work-tracking reports folder
- plan sync, work-tracking audit, Taskmaster health, guard validation, and diff-check evidence
- Taskmaster Task 75 and subtasks 75.1/75.2 marked done only after verification is captured
