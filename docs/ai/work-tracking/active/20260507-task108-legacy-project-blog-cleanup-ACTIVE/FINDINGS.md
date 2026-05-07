# Findings

- 2026-05-07 — `templates/PROJECT-BLOG.md` is project-specific "Animal Protection Foundation Blog" configuration from an older product iteration, not portable foundation material.
- 2026-05-07 — The Task 18 security baseline finding points at `../../../packages/backend` inside the old blog template. Rewriting only that line would clear the scanner but leave stale product-specific content in the foundation.
- 2026-05-07 — Live current references to `templates/PROJECT-BLOG.md` are limited to navigation, metadata, and scanner helper lists, so removing the legacy root is scoped and tractable.
- 2026-05-07 — After removal, `security_validator.py` reports 332 files scanned and 0 findings. This confirms the Task 18 baseline is clean without scanner rule changes or allowlists.
- 2026-05-07 — Final live-reference check found no `PROJECT-BLOG` references under `templates/` or scanner source, excluding generated scanner output.
