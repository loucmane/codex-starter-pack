# Findings

- 2026-07-13 — Blog's pre-Task-248 manifest is a valid migration source but fails the new
  schema because Codex is enabled without the new hook managed-file and gate records.
  `project_update` preview handled that state, while apply failed because it called strict
  `runtime_update` before `install` could migrate the manifest.
- 2026-07-13 — Install-before-runtime fixes the real Blog-shaped snapshot without a schema
  exception. The patched update applied successfully and strict verification passed all
  42 checks; advisory enforcement remained a warning only.
- 2026-07-13 — Blog's existing untracked hook is materially divergent, not formatting-only.
  It uses alias matchers, lacks canonical `apply_patch`, omits the ledger recorder and
  `AEGIS_INVOKING_AGENT=codex`, and has no timeout/status metadata. Installer refusal is
  therefore correct.
- 2026-07-13 — Hook evidence for the later attended Blog boundary:
  operator raw SHA-256 `ca892b3fec1633ac05d36006d28da1e7b5d292ca8573135f942f991a34aba0e6`;
  managed candidate raw SHA-256 `3334c040bd46a92bd542d53e2919a43b14ba1bf001fa79883a5385dc5ba487d5`.
- 2026-07-13 — The affected installer/adapter/distribution/schema matrix passed 181 tests;
  three release smoke tests remained explicitly opt-in.
- 2026-07-13 — The complete local suite passed 1,957 tests with four opt-in skips. Its one
  failure is the established location-sensitive isolation test whose premise excludes a
  repository rooted under `/tmp`; hosted CI must provide the unfiltered non-`/tmp` proof.
