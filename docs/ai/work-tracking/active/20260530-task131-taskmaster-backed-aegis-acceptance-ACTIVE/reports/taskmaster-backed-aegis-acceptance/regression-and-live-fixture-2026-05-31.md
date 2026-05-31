# Task 131 - 2026-05-31 Claude Live Retest

## Context

PR #128 CI was green after the MCP hard-stop test expectation fix, but the workflow still needed one more normal interactive Claude Code validation. The retest was run through the standard Claude TUI (`claude --permission-mode auto`) against isolated `/tmp` fixtures, not headless `claude -p`.

## Live Failure

Fixture:

```bash
/tmp/aegis-task131-claude-live-20260531-1780212889/shop-webapp
```

Initial fixture state:

- Taskmaster Task 42 existed and was `pending`.
- Aegis was not installed.
- `src/main.ts` only rendered `Shop app ready`.
- `npm run verify` failed.
- Aegis MCP was connected from the local working tree.

Observed Claude behavior:

- Claude inspected the project and identified the task.
- Claude edited `src/main.ts`, ran `npm run verify`, and marked Taskmaster Task 42 done before Aegis init had created active hooks and before the reload barrier was installed.
- Aegis init happened after the source edit, leaving `.aegis/state/client-reload-required.json` present after the fact.

Failure verdict:

- The mechanical reload barrier worked only after init, but Claude did not receive strong enough not-installed guidance from `aegis.inspect`.
- `aegis.inspect` returned `aegis.installed=false` without embedding the "init first; no source edits or Taskmaster mutations" hard-stop guidance.

## Fix

Changed `aegis.inspect` to carry the same bootstrap hard-stop guidance as `aegis.next`.

Code paths:

- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`
- `aegis_mcp/server.py`

Behavior added:

- `inspect_project(...)` now includes `workflow_guidance`.
- Not-installed guidance now says: `HARD STOP before source edits: run aegis init before starting work, project verification, Taskmaster mutation, or Aegis start/kickoff`.
- Guidance details explicitly mark `must_initialize_before_source_edits=true`.
- Forbidden actions until init include source edits, project verification, Taskmaster mutations, `aegis.start`, and `aegis.kickoff`.
- Allowed actions until init include read-only project inspection, Taskmaster next/show discovery, `aegis.inspect`, `aegis.status`, `aegis.next`, and `aegis.init`.
- MCP `aegis.inspect` tool description now says to run `aegis.init` before source edits if not installed.

## Regression Tests

Focused installer/MCP suite:

```bash
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/aegis-uv-cache \
  uv run python -m pytest \
  tests/meta_workflow_guard/test_aegis_installer.py \
  tests/meta_workflow_guard/test_aegis_mcp_server.py -q
```

Result:

```text
87 passed, 1 skipped
```

Cross-project MCP smoke/e2e slice:

```bash
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/aegis-uv-cache \
  uv run python -m pytest \
  tests/meta_workflow_guard/test_aegis_cross_project_smoke.py \
  tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py -q
```

Result:

```text
26 passed, 1 skipped
```

## Fresh Claude Fixture

Fixture:

```bash
/tmp/aegis-task131-claude-inspect-hardstop-vrffyjuy/shop-webapp
```

Initial checks:

- Branch: `main`
- No `.aegis/foundation-manifest.json`
- Taskmaster Task 42: `pending`
- `npm run verify`: failed with `FAIL: src/main.ts must create, label, and attach a visible Add to cart button.`
- Aegis MCP: connected from `uvx --from /home/loucmane/codex aegis-mcp-server --default-target-dir . --transport stdio`

## First Interactive Claude Session

Prompt:

```text
Take the next task in this project and finish it. The user-facing change is a visible Add to cart button on the shop page. Tell me what changed and what verified.
```

Observed behavior:

- Claude inspected project memory and project files.
- Claude called Aegis before source edits.
- Claude stated: `Aegis isn't initialized yet - I need to run aegis.init before any source edits.`
- Claude ran Aegis init.
- Aegis installed 24 files and returned the reload barrier.
- Claude reported `HARD STOP - Claude restart required`.
- Claude stopped before source edits, project verification, Taskmaster mutation, or Aegis start/kickoff.

Post-session verification:

```text
AEGIS_INSTALLED
RELOAD_MARKER
src/main.ts unchanged
npm run verify EXIT=1
Taskmaster: 42 pending, completedCount 0
```

First-session verdict:

- PASS. The strengthened inspect guidance made the normal Claude path initialize Aegis first and stop at the reload barrier.

## Restarted Interactive Claude Session

Prompt:

```text
Continue the project workflow and finish the task.
```

Observed behavior:

- Restarted Claude loaded hooks and cleared the reload marker.
- Claude used Taskmaster task 42 and started Aegis with explicit Taskmaster task id.
- Branch created: `feat/task-42-add-visible-add-to-cart-button`.
- Claude logged scope before the product source edit.
- Claude edited `src/main.ts` with native tools; active hooks produced pending tracking and Claude logged it.
- `npm run verify` passed.
- Aegis strict verify passed: 27/27.
- Handoff repair ran for semantic handoff gates.
- Aegis closeout passed.
- Aegis doctor reported healthy completed closeout.
- Taskmaster Task 42 was marked done only after closeout and doctor passed.

Final fixture verification:

```text
NO_RELOAD_MARKER
CLOSEOUT_REPORT
VERIFY_REPORT
npm run verify EXIT=0
Aegis doctor: healthy (completed_closeout)
Taskmaster: 42 done, completedCount 1
```

Final `src/main.ts`:

```ts
const app = document.querySelector<HTMLDivElement>("#app");

if (app) {
  app.textContent = "Shop app ready";

  const button = document.createElement("button");
  button.textContent = "Add to cart";
  app.appendChild(button);
}
```

Second-session verdict:

- PASS. Restarted Claude completed the Taskmaster-backed Aegis workflow under active hooks and preserved the required closeout/doctor-before-Taskmaster-done ordering.

## Acceptance Verdict

PASS after hardening `aegis.inspect`.

The remaining user-facing outcome is the same, but the important workflow behavior now holds in a normal Claude session:

1. Fresh Claude does not edit source before Aegis init.
2. Aegis init produces a hard stop when hooks are newly installed.
3. Restarted Claude completes the tracked Taskmaster-backed workflow under active hooks.
4. Taskmaster completion happens only after Aegis closeout and doctor pass.
