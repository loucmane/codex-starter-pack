# Task 122 Roadmap

This note separates immediate fixes from Task 122 deliverables and deferred release or adapter work.

## Task 121 Baseline

Task 121 already handled the first-pass workflow UX fixes:

- event-aware `aegis log` defaults
- `pending_event_id=current`
- closeout repair guidance
- project-local CLI shim
- live Claude workflow proof for install, kickoff, implementation logging, verification, strict verify, and closeout

Task 122 must not re-litigate those fixes unless a regression appears.

## Task 122 Deliverables

Task 122 owns the guidance and portability layer:

- read-only `aegis next` / MCP `aegis.next`
- `workflow_guidance` in `aegis.status`
- deterministic `plan_step=auto`
- read-only closeout readiness / dry-run
- MCP descriptions and prompts that teach fresh agents the correct control-plane/native-tool split
- installed Claude guidance that starts from readiness/status/next and uses `plan_step=auto`
- live acceptance matrix for fresh/existing web, Python, backend, no-Taskmaster/no-Serena, existing MCP config, and local shim fallback rows
- adapter contract documenting Claude as implemented and Codex/Gemini/future agents as planned

## Deferred Work

These are intentionally outside Task 122:

- publishing to TestPyPI or PyPI
- hosted MCP service deployment
- full Codex or Gemini runtime adapter implementation
- replacing native source editing with MCP source-editing tools
- claiming policy-only memory or MCP mutation surfaces are mechanically enforced

If later evidence shows a different architecture is better, this roadmap and `docs/aegis/live-acceptance-matrix.md` identify the exact assumptions to revisit.

