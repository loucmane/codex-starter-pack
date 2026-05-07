# Decisions

- 2026-05-07 — Implement a tracked safe runner at `scripts/template-ssot-scanner/apply_reference_fixes.py`. Rationale: generated output scripts are not a stable implementation surface and should delegate to supported code.
- 2026-05-07 — Default reference-fix execution to dry-run unless `--apply` is passed. Rationale: this is a potentially broad template mutation surface and should require explicit apply intent.
- 2026-05-07 — Defer actually applying current generated reference fixes. Rationale: Task 10 is tool implementation; reference cleanup should happen through a separate reviewed fix run after the tool proves safe.
- 2026-05-07 — Choose a repo-installed local runtime plus CLI/package with an MCP installer/control-plane wrapper as the target portability architecture. Rationale: MCP is useful for install/upgrade/scaffold operations, but local repo hooks, guards, tests, CI, and manifests must remain the enforcement source so projects protect themselves when MCP is unavailable. Option analysis and reversal criteria are captured in `designs/agent-foundation-portability-options.md`.
