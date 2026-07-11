# Decisions

- 2026-07-11 - Archive the completed Task 235 projection through the supported work-tracking
  helper before starting Task 236. Preserve every Task 235 evidence file and its done state.

- 2026-07-10 — Record `sha256:<hex>` on each materialized managed asset, excluding the
  self-referential manifest record.
- 2026-07-10 — Treat a target checksum that differs from the installed baseline as a managed
  `manual-review`, not an unmanaged conflict and never a safe modification.
- 2026-07-10 — Fail closed when a legacy source-backed asset differs and its recorded Git
  baseline cannot be recovered. Keep existing specialized merge behavior for marker-managed
  entrypoints and seed-once configuration.
- 2026-07-10 — Keep the pre-runtime manifest immutable across both preview and apply planning.
- 2026-07-10 — Promote the blog completed-archive guard implementation byte-for-byte so the
  blocked downstream branch converges without another fork-only patch.
