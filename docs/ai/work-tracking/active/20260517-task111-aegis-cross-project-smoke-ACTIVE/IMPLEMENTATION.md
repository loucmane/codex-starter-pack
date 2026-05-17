# Task 111 Aegis Cross-Project Install Smoke Harness and Distribution Readiness – Implementation Notes

## Planned Workstreams
- [x] Reconcile Task 111 scope and correct the generated plan wording before implementation.
- [x] Create `designs/aegis-cross-project-smoke-matrix.md` with the target repository matrix, invocation matrix, safety matrix, and subtask mapping.
- [x] Add `tests/meta_workflow_guard/test_aegis_cross_project_smoke.py` with isolated CLI smoke coverage.
- [x] Add MCP wrapper equivalence coverage for the same target contract.
- [x] Add negative/safety cases.
- [x] Capture final evidence and distribution-readiness recommendation.

## 2026-05-17 CLI Smoke Slice

- Added local target-shape builders for empty, Python/library, web/app, and docs-heavy repositories.
- Added CLI helpers that invoke `python3 scripts/codex-task aegis ...` from `REPO_ROOT` while targeting only pytest `tmp_path` repositories.
- Asserted `inspect` and `plan-install` are dry-run/no-mutation paths.
- Asserted `install --apply` and `verify` produce parseable JSON, applied status, passed verification, expected `.aegis/` reports, manifest fields, schema copies, adapter files, and gate files.
- Asserted seeded user files are preserved byte-for-byte.
- Added a source fingerprint over key source files to confirm CLI target smoke runs do not mutate the source repository.
- Captured evidence at `reports/aegis-cross-project-smoke/tests-2026-05-17-aegis-cli-smoke.txt` with `60 passed`.

## 2026-05-17 MCP Equivalence Slice

- Added local MCP helpers for `server.call_tool` and `server.read_resource` payload assertions.
- Added an MCP happy path over a Python/library target: `aegis.inspect`, `aegis.plan_install`, `aegis.install` apply gate, applied install, `aegis.verify` acknowledgement gate, acknowledged verify, and read-only resources.
- Asserted MCP plan/inspect/resource paths preserve dry-run/read-only behavior.
- Asserted MCP installation and verification create the same installed target artifacts checked by the CLI smoke.
- Added a conflict equivalence case comparing MCP `install_refused` payloads against direct core installer refusal reports for a pre-existing `CLAUDE.md`.
- Captured evidence at `reports/aegis-cross-project-smoke/tests-2026-05-17-aegis-mcp-equivalence.txt` with `62 passed`.

## 2026-05-17 Safety Smoke Slice

- Added CLI partial-install refusal coverage for an existing conflicting `.aegis/foundation-manifest.json`, including no partial writes and preserved existing project files.
- Added CLI missing-required-gate verification coverage by deleting `.claude/scripts/readiness.sh` after install and asserting structured failed verification output.
- Added MCP failed-apply cleanup coverage using the real core cleanup path via a controlled `_write_asset` failure, preserving user files while removing newly-created files.
- Captured evidence at `reports/aegis-cross-project-smoke/tests-2026-05-17-aegis-safety-smoke.txt` with `65 passed`.

## 2026-05-17 Final Evidence And Recommendation

- Added `designs/distribution-readiness-recommendation.md`.
- Captured final focused Aegis smoke evidence at `reports/aegis-cross-project-smoke/tests-2026-05-17-aegis-final.txt` with `65 passed`.
- Marked Taskmaster subtask 111.5 and parent Task 111 done.
- Recommendation: create Task 112 for Aegis packaging and invocation contract before publishing or broader distribution work.
- Captured final workflow evidence:
  - `reports/aegis-cross-project-smoke/plan-sync-2026-05-17-final.txt`
  - `reports/aegis-cross-project-smoke/taskmaster-health-2026-05-17-final.txt`
  - `reports/aegis-cross-project-smoke/work-tracking-audit-2026-05-17-final.txt`
  - `reports/aegis-cross-project-smoke/guard-2026-05-17-final.txt`
  - `reports/aegis-cross-project-smoke/diff-check-2026-05-17-final.txt`
