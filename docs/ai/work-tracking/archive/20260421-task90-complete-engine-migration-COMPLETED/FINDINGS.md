# Findings

- 2026-04-21 — Task 90 is the logical continuation after the completed 81-89 lane even though raw Taskmaster ordering still recommends Task 1.
- 2026-04-21 — Task 89 work-tracking must be archived before Task 90 starts to preserve the single-active-folder workflow.
- 2026-04-21 — `templates/engine/README.md` is out of sync with the actual engine tree and references multiple non-existent Phase 2/3 modules.
- 2026-04-21 — Registry and metadata discovery already point at a newer engine surface (`core/session-resolver.md`, `validation/*`) that the README does not document.
- 2026-04-21 — Current `CLAUDE.md` no longer imports the engine module tree, so Task 90 may be as much about roadmap/discoverability reconciliation as authoring missing modules.
- 2026-04-21 — `templates/engine/verify-phase1.sh` is also stale: it still validates `.claude/templates/...` paths and old `CLAUDE.md` import comments.
- 2026-04-21 — The current engine tree uses mixed frontmatter conventions: most structured modules use `id`, while validation docs such as `integration-guide.md` and `validation-framework.md` use `name`.
- 2026-04-21 — After README/verifier reconciliation, the current engine surface validates cleanly against on-disk files plus registry/metadata discovery references; remaining Task 90 scope should be driven by real coverage gaps, not obsolete roadmap placeholders.
- 2026-04-21 — `template-overview.md` and `template-summary.csv` still carried the old README heading even after the README itself was updated.
- 2026-04-21 — `codex-readiness.md` was present in metadata but missing from `templates/registry/index.json`.
- 2026-04-21 — `meta-workflow-guard-ci-plan.md` and `meta-workflow-guard-remediation.md` existed in the engine tree but were missing from inventory, overview, and summary metadata.
- 2026-04-21 — The guard’s legacy monolith detection was too broad: substring matching flagged valid files such as `common-workflows.md` and `usage-patterns.md`.
- 2026-04-21 — Final reference scans show no concrete missing engine markdown modules; Task 90’s remaining work is status reconciliation, not module authoring.

## Progress Log
- **2026-04-21 12:51** — [S:20260421|W:task90-complete-engine-migration|H:docs/findings|E:docs/ai/work-tracking/active/20260421-task90-complete-engine-migration-ACTIVE/FINDINGS.md] Logged Task 90 continuity rationale and active-folder rollover requirement
- **2026-04-21 12:51** — [S:20260421|W:task90-complete-engine-migration|H:docs/findings|E:docs/ai/work-tracking/active/20260421-task90-complete-engine-migration-ACTIVE/FINDINGS.md] Logged engine README/discoverability drift and the likely need to reconcile roadmap intent before implementation
- **2026-04-21 12:51** — [S:20260421|W:task90-complete-engine-migration|H:docs/findings|E:docs/ai/work-tracking/active/20260421-task90-complete-engine-migration-ACTIVE/FINDINGS.md] Logged stale phase-1 verification script still targeting `.claude` paths and old `CLAUDE.md` import markers
- **2026-04-21 13:27** — [S:20260421|W:task90-complete-engine-migration|H:docs/findings|E:templates/engine/verify-phase1.sh] Logged mixed `id`/`name` frontmatter convention surfaced by the new verifier
- **2026-04-21 13:27** — [S:20260421|W:task90-complete-engine-migration|H:docs/findings|E:docs/ai/work-tracking/active/20260421-task90-complete-engine-migration-ACTIVE/reports/complete-engine-migration/verify-phase1-2026-04-21-pass.txt] Logged successful current-engine verification after README and script reconciliation
- **2026-04-21 14:17** — [S:20260421|W:task90-complete-engine-migration|H:docs/findings|E:templates/metadata/template-summary.csv] Logged stale engine README heading plus missing engine discoverability entries across metadata and registry surfaces
- **2026-04-21 14:17** — [S:20260421|W:task90-complete-engine-migration|H:docs/findings|E:scripts/codex-guard] Logged guard false positive caused by substring-based legacy monolith detection on hyphenated filenames
- **2026-04-21 14:31** — [S:20260421|W:task90-complete-engine-migration|H:docs/findings|E:cmd`python3 - <<'PY' ... engine reference scan ... PY`] Logged final audit result that Task 90 does not require new engine markdown modules
