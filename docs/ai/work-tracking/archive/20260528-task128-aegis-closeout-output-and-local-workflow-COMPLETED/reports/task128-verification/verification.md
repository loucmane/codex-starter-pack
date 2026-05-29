# Task 128 Verification

## Static/Syntax Checks

- Command: `python3 -m py_compile scripts/_aegis_installer.py aegis_foundation/assets/scripts/_aegis_installer.py aegis_foundation/cli.py aegis_mcp/server.py scripts/codex-task aegis_foundation/assets/scripts/codex-task`
- Result: passed.

## Focused Regression Suite

- Command: `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_invocation_contract.py tests/meta_workflow_guard/test_aegis_release_distribution.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py`
- Result: passed, `108 passed, 4 skipped`.
- Skips were the existing opt-in release/wheel smoke tests gated by environment variables.
- After the dry-run wording refinement, reran `tests/meta_workflow_guard/test_aegis_installer.py::test_closeout_requires_semantic_handoff_and_passes_with_update`; result: passed.
- After the fresh Claude acceptance exposed MCP `aegis.start` readiness gating, added regression coverage that:
  - `aegis verify` and MCP `aegis.verify` remain blocked before readiness.
  - CLI `aegis start` and MCP `mcp__aegis__aegis_start` are allowed as readiness-bootstrap operations.
  - CLI/MCP start payloads do not create pending S:W:H:E tracking events after current work exists.
- Reran the focused regression suite after the bootstrap-gate fix; result: passed, `108 passed, 4 skipped`.

## Live Temp-Project Check

- Target: `/tmp/aegis-task128-live-w97Ha0/project`
- Flow:
  - Created a fresh git repo on `main`.
  - Ran `python3 scripts/codex-task aegis init --target-dir /tmp/aegis-task128-live-w97Ha0/project`.
  - Ran `./.aegis/bin/aegis next --target-dir .`; output suggested MCP tool `aegis.start` with `apply=true`.
  - Ran `./.aegis/bin/aegis start --target-dir . "Improve closeout clarity"`; Aegis allocated local task id `1` and branch `feat/task-1-improve-closeout-clarity`.
  - Readiness returned `READY | task=1`.
  - Logged scope, implementation evidence, task verification evidence, strict verification evidence, repaired handoff, and ran final closeout.
- Closeout concise output before final closeout:

```text
Aegis closeout readiness: PASSED
mode: dry-run
failed_required: 0
warnings: 0
pending_tracking: 0
closeout_report: .aegis/reports/closeout-report.json (not written by this run)
next: ./.aegis/bin/aegis closeout --target-dir . --update-handoff
json: rerun with --json for the full structured report
```

- Final closeout concise output:

```text
Aegis closeout: PASSED
mode: final
failed_required: 0
warnings: 0
pending_tracking: 0
closeout_report: .aegis/reports/closeout-report.json (written)
next: git status --short
json: rerun with --json for the full structured report
```

- Post-closeout state:
  - `.aegis/state/current-work.json.status`: `completed`
  - `.aegis/state/current-work.json.task.status`: `completed`
  - task id: `1`
  - closeout report: `.aegis/reports/closeout-report.json`
- Post-closeout dry-run with `--json` passed and reported readiness as `READY from completed closeout state`.
- Post-closeout dry-run default concise output passed and suggested `git status --short`.

## Fresh Claude Acceptance Check

- Target: `/tmp/aegis-claude-task128-x741yE/shop-webapp`
- Prompt used normal project language: set up Aegis, add a visible "Add to cart" button, verify, close out, and report workflow details.
- Result:
  - Claude installed Aegis through MCP init.
  - Claude started local work with `./.aegis/bin/aegis start "Add visible Add to cart button"`.
  - Aegis allocated local task id `1` and branch `feat/task-1-add-visible-add-to-cart-button`.
  - Source change, task verification, strict verification, handoff repair, and final closeout all passed.
  - `.aegis/state/current-work.json.status` and nested task status were `completed`.
  - `.aegis/state/pending-tracking.json` was absent at the end.
  - Post-closeout dry-run with `--json` passed and reported readiness as `READY from completed closeout state`.
- Follow-up found by the acceptance run:
  - Claude reported that MCP `aegis.start` was blocked by readiness and fell back to the project-local CLI shim.
  - Fixed by making CLI/MCP `aegis.start` a bootstrap exception in `.claude/scripts/gate_lib.py` and the packaged asset copy.
- Next acceptance target prepared for retest: `/tmp/aegis-claude-task128-bootstrap-aSq2xd/shop-webapp`.

## Fresh Claude Retest After MCP Start Bootstrap Fix

- Target: `/tmp/aegis-claude-task128-bootstrap-aSq2xd/shop-webapp`
- Result:
  - Claude installed Aegis through MCP and started tracked work with MCP `aegis.start`, not the CLI shim.
  - Branch: `feat/task-1-add-visible-add-to-cart-button`.
  - Source change: `src/main.ts` now renders a visible "Add to cart" button with `type="button"`, `aria-label="Add to cart"`, and a click handler.
  - Project verification command: `npm run verify`; result: passed with three `Add to cart` matches.
  - Aegis strict verification: passed, `27` checks, `0` failed required, `0` warnings, `1` unsupported policy-only gate.
  - Aegis closeout: passed, `22` gates, `0` failed required, `0` warnings.
  - Pending tracking: `.aegis/state/pending-tracking.json` absent at final inspection.
  - Post-closeout dry-run with `--json`: passed and reported readiness as `READY from completed closeout state`.
- Direct verification after Claude finished:
  - `git branch --show-current` returned `feat/task-1-add-visible-add-to-cart-button`.
  - `npm run verify` passed.
  - `./.aegis/bin/aegis closeout --target-dir . --dry-run --update-handoff --json` returned `status: passed`, `summary.failed_required: 0`, and `next_action.action: task_complete`.
