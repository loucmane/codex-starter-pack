# Aegis Live Acceptance Matrix

This matrix defines the live evidence needed before Aegis is treated as a portable workflow runtime, not just an installable package. The goal is to prove the same workflow behavior across fresh and already-started projects without requiring Taskmaster or Serena.

Public-flow rows must exercise `aegis init` and `aegis start "<normal task title>"` where possible. MCP clients should reach the same behavior through `aegis.init apply=true` followed by `aegis.start apply=true`. Existing low-level plan-install/install/kickoff rows remain useful for regression coverage, but public acceptance is measured against the normal command path and a no-large-prompt Claude session.

Canonical roadmap context for Task 122 lives in `docs/ai/work-tracking/active/20260525-task122-aegis-workflow-guidance-adapter-portability-ACTIVE/designs/task122-roadmap.md`.

## Evidence Standard

Each live row must capture:

- install surface: MCP, CLI, or project-local `./.aegis/bin/aegis`
- starting project shape
- expected `aegis.next` sequence
- expected readiness state before and after kickoff
- required workflow surfaces: `sessions/current`, `plans/current`, active work-tracking folder, tracker, implementation log, changelog, handoff
- required reports: install, kickoff, task verification, strict verification, closeout dry-run when used, and closeout
- proof that source edits are done with native agent tools, while Aegis records workflow state
- proof that pending S:W:H:E tracking blocks the next mutation until `aegis log --pending-id current --plan-step auto` clears it
- proof that closeout cannot be claimed until strict verification and closeout pass

Application behavior evidence must be semantic wherever practical. Web, Python, and backend fixtures should prefer runtime checks, AST/import checks, parsed DOM/source intent, schema-backed payload assertions, or reusable acceptance helpers over literal source-grep checks. A live row should not force an agent to rewrite idiomatic application code only to satisfy a fixture substring.

Literal assertions remain valid for Aegis-owned runtime contracts: managed block markers, public command names such as `aegis init` and `aegis start`, required report paths, schema keys, hook names, and S:W:H:E token syntax. If an application fixture genuinely requires a literal implementation style, that fixture must document why a semantic check is not available.

Policy-only limitations are not accepted as live evidence.

## Matrix

| Row | Target Shape | Command Surface | Expected Next-Action Sequence | Required Evidence | Closeout Criteria | Status |
| --- | --- | --- | --- | --- | --- | --- |
| web-new | Fresh Vite-style web app with no Aegis, no Taskmaster, no Serena | MCP `aegis.init` or CLI `aegis init`, native Claude edit, MCP/CLI log | inspect/next -> init -> start -> scope log -> native edit -> pending log -> app verify -> strict verify -> closeout_ready -> closeout | `.aegis/reports/install-report.json`, `src/main.ts`, task verification report, `.aegis/reports/verification-report.json`, `.aegis/reports/closeout-report.json` | all six workflow surfaces reference the changed source file and pending queue is empty | automated plus manual-live |
| web-started | Existing web app with source files and package scripts | MCP `aegis.init` into existing project | same as web-new, with no overwrite of unrelated files | install report, changed app source, npm or project verification evidence | closeout passes without hand-editing `.aegis/`, `IMPLEMENTATION.md`, or `CHANGELOG.md` | automated plus manual-live |
| python-new | Fresh Python package or script project | CLI or MCP public init/start | init -> start -> scope -> native Python edit -> pytest/command verify -> strict verify -> closeout | Python source evidence, pytest or command output report | plan-step-scope, implement, verify completed through `plan_step=auto` | automated |
| python-started | Existing Python project | CLI or MCP public init/start | inspect existing files -> init -> start -> task flow | install report, source diff, test evidence | no Taskmaster/Serena dependency unless explicitly required | automated |
| backend-new | Fresh backend/server skeleton | CLI or MCP public init/start | same as python-new, with server route or handler edit | route/handler source, smoke command report | closeout-ready dry-run reports pass before final closeout | automated |
| backend-started | Existing backend service | CLI or MCP public init/start | inspect -> init -> start -> task flow | conflict review when needed, source edit, service-level verification | closeout report and handoff cite implementation and verification evidence | automated |
| existing-mcp-json | Project already has `.mcp.json` or client MCP config | native client registration preferred | registration generate/execute/verify, then install workflow | registration payload, no clobber of unrelated MCP entries | Aegis tools discoverable and target workflow works | automated |
| cli-shim-fallback | Global `aegis` unavailable | project-local `./.aegis/bin/aegis` | kickoff/log/verify/closeout through shim | local shim version, log evidence, closeout report | same gates as MCP path | automated |
| no-taskmaster-no-serena | Project with neither integration | MCP or CLI | Aegis-native current work reaches READY | current-work JSON, readiness READY, no optional integration failure | strict verify passes with optional integrations absent | automated |
| live-claude | Fresh Claude client in installed project | MCP for Aegis control plane, native Claude tools for implementation | `aegis.next` guides each phase; Claude logs pending events and closeout evidence | transcript, changed source, all workflow surfaces, strict verify and closeout reports | first-pass closeout passes or repair guidance is followed mechanically | manual-live |

## Accepted Deferrals

- Hosted MCP service deployment is deferred until transport, authentication, version pinning, rollback, and verification evidence exist.
- Non-Claude adapters are documented in `docs/aegis/agent-adapter-contract.md`; full Codex/Gemini runtime implementation is deferred unless a task explicitly owns it.
- TestPyPI/PyPI publication is blocked until the local artifact and live matrix evidence are complete.
