# Findings

- 2026-06-04 — Claude red-team review identified `target_dir` on read-only Aegis MCP tools as a live arbitrary-read surface unless confined to the governed target root.
- 2026-06-04 — The hook had a separate degraded fallback classifier; Task 157 closes the drift risk by making degraded Bash/MCP decisions reuse the same low-level read-only helpers as the main classifier.
- 2026-06-04 — Substring-based plan-step inference could fabricate implementation progress from handler/evidence text such as `bash` or `edit`; Task 157 removes that route and relies on explicit or confident file-mutation signals.
- 2026-06-04 — Reconcile `base_ref` accepted option-shaped strings before Task 157; the implementation now rejects leading-dash, whitespace, and NUL-containing values before git invocation.
