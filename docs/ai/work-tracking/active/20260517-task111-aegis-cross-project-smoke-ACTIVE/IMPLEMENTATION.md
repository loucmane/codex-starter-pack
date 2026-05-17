# Task 111 Aegis Cross-Project Install Smoke Harness and Distribution Readiness – Implementation Notes

## Planned Workstreams
- [x] Reconcile Task 111 scope and correct the generated plan wording before implementation.
- [x] Create `designs/aegis-cross-project-smoke-matrix.md` with the target repository matrix, invocation matrix, safety matrix, and subtask mapping.
- [x] Add `tests/meta_workflow_guard/test_aegis_cross_project_smoke.py` with isolated CLI smoke coverage.
- [ ] Add MCP wrapper equivalence coverage for the same target contract.
- [ ] Add negative/safety cases and final evidence.

## 2026-05-17 CLI Smoke Slice

- Added local target-shape builders for empty, Python/library, web/app, and docs-heavy repositories.
- Added CLI helpers that invoke `python3 scripts/codex-task aegis ...` from `REPO_ROOT` while targeting only pytest `tmp_path` repositories.
- Asserted `inspect` and `plan-install` are dry-run/no-mutation paths.
- Asserted `install --apply` and `verify` produce parseable JSON, applied status, passed verification, expected `.aegis/` reports, manifest fields, schema copies, adapter files, and gate files.
- Asserted seeded user files are preserved byte-for-byte.
- Added a source fingerprint over key source files to confirm CLI target smoke runs do not mutate the source repository.
- Captured evidence at `reports/aegis-cross-project-smoke/tests-2026-05-17-aegis-cli-smoke.txt` with `60 passed`.
