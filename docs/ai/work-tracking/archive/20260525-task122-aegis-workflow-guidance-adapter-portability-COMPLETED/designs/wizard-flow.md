# Task 122 Scope Baseline - Aegis Workflow Guidance and Adapter Portability

## Purpose

Task 122 builds on the Task 121 repair layer. Task 121 made the existing workflow easier to complete by improving default logging surfaces, pending event repair, closeout guidance, evidence location metadata, and same-task multi-day session guard behavior. Task 122 should add a guidance layer that tells fresh agents exactly what to do next while preserving the core architecture:

- Aegis CLI/MCP is the workflow control plane.
- Native agent tools remain the implementation path.
- Installed hooks and guards remain the enforcement layer.
- Taskmaster and Serena are optional integrations, not hard dependencies for installed Aegis projects.

## Implementation Boundary

In scope:
- Add a read-only `aegis next` CLI surface and MCP `aegis.next` tool, with shared deterministic state evaluation.
- Embed the same workflow guidance payload in `aegis.status` for discovery.
- Add deterministic `plan_step=auto` support for `aegis log` without free-text AI inference.
- Add a pre-closeout readiness surface, either `aegis closeout --dry-run` or `aegis closeout-ready`, sharing closeout gate evaluation.
- Improve MCP tool descriptions and prompts so new Claude sessions naturally use Aegis to install, start, log, verify, and close out work.
- Document the live acceptance matrix, adapter contract, and release readiness boundaries.

Out of scope:
- Publishing to TestPyPI or PyPI.
- Adding MCP source-editing tools.
- Implementing full Codex, Gemini, or future-agent runtimes beyond adapter contracts and roadmap entries.
- Making Taskmaster or Serena required for installed Aegis target projects.

## First Implementation Slice

Start with the shared guidance evaluator in `scripts/_aegis_installer.py`, then mirror into `aegis_foundation/assets/scripts/_aegis_installer.py`. The first slice should prove the evaluator can identify:

- not installed,
- installed with no current work,
- active work with missing scope evidence,
- pending tracking,
- missing implementation evidence,
- missing verification evidence,
- strict verification needed,
- closeout blocked,
- closeout ready,
- closeout passed.

The evaluator output should include `phase`, `state`, `next_required_action`, `suggested_cli`, `suggested_mcp_call`, `missing_gates`, `copyable_repairs`, `read_only: true`, and an architecture note saying Aegis coordinates workflow state while native tools perform implementation edits.

## Verification Direction

Focused tests should land before broad live tests:

- unit tests for guidance states and read-only behavior,
- CLI/MCP schema tests for `aegis.next`,
- `aegis.status` payload tests,
- `plan_step=auto` inference tests,
- closeout-ready/dry-run repair guidance tests,
- docs/package parity tests.

Live client matrix testing should follow once the guidance surfaces are deterministic enough to be useful.
