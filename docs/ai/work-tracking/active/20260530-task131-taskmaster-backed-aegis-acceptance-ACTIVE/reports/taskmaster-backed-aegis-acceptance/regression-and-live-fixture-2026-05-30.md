# Task 131 Regression And Live Fixture - 2026-05-30

## Regression Coverage

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_installer_fixtures.py tests/meta_workflow_guard/test_aegis_acceptance_assertions.py
```

Result:

```text
99 passed, 1 skipped in 9.22s
```

Taskmaster health:

```text
Taskmaster health: OK
Tasks: 131
Statuses: done=130, in-progress=1
Invalid dependency refs: 0
```

## Hardened Behavior

- `aegis.next` now detects available numeric Taskmaster work in `.taskmaster/tasks/tasks.json`.
- Installed projects with Taskmaster work receive `aegis.kickoff` guidance using the Taskmaster id, title, and slug.
- `aegis.start` refuses to allocate a competing local Aegis task when Taskmaster has available numeric work.
- Installed `CLAUDE.md` now tells Claude to run `task-master next` and `task-master show <id>` before Aegis kickoff in Taskmaster-backed projects.
- Generated Claude settings allow `Bash(task-master *)`.
- MCP `aegis.start_task` prompt tells Claude to use Taskmaster next/show before choosing the start path.

## Reload Boundary Hardening

Follow-up regression command:

```bash
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/aegis-uv-cache uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py::test_install_report_flags_claude_reload_when_adapter_hooks_change tests/meta_workflow_guard/test_aegis_installer.py::test_public_init_requires_claude_reload_before_start_as_next_action tests/meta_workflow_guard/test_aegis_mcp_server.py::test_prompts_preserve_workflow_and_evidence_invariants
```

Result:

```text
3 passed in 0.49s
```

Full follow-up regression command:

```bash
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/aegis-uv-cache uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_installer_fixtures.py tests/meta_workflow_guard/test_aegis_acceptance_assertions.py
```

Result:

```text
99 passed, 1 skipped in 9.22s
```

Hardening completed after the interactive Claude retry:

- `aegis.install` now reports `client_reload.required=true` when Claude adapter settings or hook scripts are created or modified.
- Public `aegis.init` now returns `next_action.action=restart_claude_before_mutation` after installing Claude hooks, instead of immediately steering Claude into source edits in the same session.
- Installed `CLAUDE.md` and `.aegis/contract.md` now explicitly explain that Claude loads `.claude/settings.json` at session start and must be restarted after first-time hook installation.
- MCP bootstrap/start prompts now tell Claude to stop when `client_reload.required=true` or `restart_claude_before_mutation` is returned.
- MCP tool descriptions now make Aegis discoverable from normal task requests by marking `aegis.inspect` proactive for fresh/existing coding work and `aegis.init` as public project workflow setup.
- MCP closeout guidance now explicitly says to use `aegis.handoff_repair apply=true` for repairable handoff semantic gates instead of hand-editing `HANDOFF.md`.
- Taskmaster closeout guidance now includes generated task-file refresh instructions: use the project helper when present, otherwise run broad `task-master generate` deliberately and report it.
- Public docs now describe the Claude restart boundary, post-reload continuation, and Taskmaster generated-file refresh requirement.
- `scripts/_aegis_installer.py` was mirrored to `aegis_foundation/assets/scripts/_aegis_installer.py` so packaged MCP installs carry the same behavior.

## Mechanical Reload Barrier

Follow-up regression command:

```bash
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/aegis-uv-cache uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py::test_install_report_flags_claude_reload_when_adapter_hooks_change tests/meta_workflow_guard/test_aegis_installer.py::test_start_and_kickoff_are_blocked_until_claude_reload_hook_runs
```

Result:

```text
2 passed in 0.34s
```

Full targeted regression command:

```bash
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/aegis-uv-cache uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_installer_fixtures.py tests/meta_workflow_guard/test_aegis_acceptance_assertions.py
```

Result:

```text
99 passed, 1 skipped in 9.22s
```

Taskmaster health after the change:

```text
Taskmaster health: OK
Statuses: done=130, in-progress=1
Invalid dependency refs: 0
```

Schema regression:

```text
tests/meta_workflow_guard/test_aegis_schemas.py: 15 passed in 0.27s
```

Mechanical behavior now implemented:

- `aegis.install` / public `aegis.init` write `.aegis/state/client-reload-required.json` when Claude settings or hook scripts are created or modified.
- `aegis.next` reports `state=client_reload_required` while the marker exists and directs the agent to restart/reload before workflow mutation.
- `aegis.start` and `aegis.kickoff` are blocked while the marker exists. This prevents Claude from installing Aegis and immediately beginning source work in a session whose hooks were not loaded at startup.
- The installed Claude `PreToolUse` hook clears the marker when it actually runs. That makes the barrier mechanical: after a real reload, the first hook invocation proves the hook stack is active and unblocks `start` / `kickoff`.
- Regression tests now explicitly simulate the reload boundary before older install-and-kickoff scenarios.
- The marker-clearing hook change was mirrored to `aegis_foundation/assets/.claude/scripts/gate_lib.py`, and the installer marker logic was mirrored to `aegis_foundation/assets/scripts/_aegis_installer.py`.

## Live Fixture

Fixture path:

```bash
cd /tmp/aegis-task131-taskmaster-live-IgTOxG/shop-webapp
```

Fixture state:

- Git repo initialized on `main`.
- Aegis is not installed yet.
- Taskmaster exists with pending Task 42: `Add visible Add to cart button`.
- `task-master next` and `task-master show 42` both resolve Task 42.
- `npm run verify` currently fails until `src/main.ts` creates, labels, and appends a visible `Add to cart` button.
- A headless `claude -p ...` attempt produced no output and was terminated; the fixture remained unmodified with no `.aegis/` or `.claude/` runtime installed.
- Interactive Claude then completed the app edit and marked Taskmaster Task 42 done, but did not initialize or use Aegis. This is a live acceptance failure: no Aegis MCP calls, no Aegis init, no `aegis.next`, no Taskmaster-backed `aegis.kickoff`, no Aegis closeout, and no read-only doctor.
- Diagnosis after the failure: `claude mcp list` from this source repo showed `aegis: python3 scripts/aegis-mcp-server`, which is checkout-relative. Running the same command from the fixture did not list Aegis. The fresh project could not discover Aegis, so Claude fell back to shell/Taskmaster behavior.
- Correct next run requires registering Aegis at user scope with a source/absolute or package-backed command, for example `uvx --from /home/loucmane/codex aegis-mcp-server --default-target-dir . --transport stdio` during local pre-PyPI testing.

## Source-Mode MCP Registration

Command applied:

```bash
claude mcp add --scope user aegis -e UV_CACHE_DIR=.aegis/uv-cache -e UV_TOOL_DIR=.aegis/uv-tools -- uvx --from /home/loucmane/codex aegis-mcp-server --default-target-dir . --transport stdio
```

Verification from a fresh project:

```text
aegis: uvx --from /home/loucmane/codex aegis-mcp-server --default-target-dir . --transport stdio - ✓ Connected
```

Structured registration verification:

```text
status: passed
failed_required: 0
uvx_command: pass
source_spec: /home/loucmane/codex
server_command: aegis-mcp-server
default_target_dir: .
transport: stdio
```

Clean retry fixture:

```bash
cd /tmp/aegis-task131-taskmaster-live2-o98HIm/shop-webapp
```

Retry fixture state:

- Aegis MCP is visible and connected from the fixture.
- Taskmaster Task 42 is pending and returned by `task-master next`.
- `npm run verify` fails until the app adds the button.
- No `.aegis/` runtime is installed yet.

## Interactive Claude Source-Mode Retry

Fixture:

```bash
cd /tmp/aegis-task131-taskmaster-live2-o98HIm/shop-webapp
```

Result: mostly passed.

Observed successful behavior:

- Claude discovered and used the `aegis` MCP server.
- Claude initialized Aegis from the fresh project.
- Claude used Taskmaster as task authority with next/show for Task 42.
- Claude started Aegis with explicit Taskmaster Task 42 via `aegis.kickoff`, not `aegis.start`.
- Aegis created branch `feat/task-42-add-to-cart-button`.
- `.aegis/state/current-work.json` uses task id `42`, slug `add-to-cart-button`, status `completed`.
- `.aegis/state/local-tasks.json` is absent, proving no competing local Aegis task was allocated.
- `src/main.ts` was edited with native Claude tools.
- `npm run verify` passed.
- Strict Aegis verification passed: 27 checks, 0 failed required.
- Aegis closeout passed: 22 checks, 0 failed required.
- Read-only Aegis doctor reported healthy: 20 checks, 0 failed required, state `completed_closeout`.
- Taskmaster Task 42 was marked `done` after closeout and doctor.
- `.aegis/state/pending-tracking.json` is absent at final state.

Remaining hardening observations:

- The source edit did not create a pending tracking sentinel in the same Claude session after Aegis installed `.claude/settings.json`; this suggests installed hooks are not active until the client reloads. Claude recovered by logging explicit implementation evidence, but this did not prove the pending-blocking guard in the install session.
- Claude manually edited `HANDOFF.md` instead of using `aegis.handoff_repair` after closeout readiness reported handoff gaps.
- `.taskmaster/tasks/task_042.txt` still says `Status: pending` even though `.taskmaster/tasks/tasks.json` has status `done`. Generic Taskmaster only offers broad `task-master generate`; this fixture lacks this repository's targeted `scripts/codex-task taskmaster generate-one` helper.

Acceptance verdict:

- Core Taskmaster-backed Aegis path: pass.
- Full state-of-the-art workflow goal: not complete until the hook activation/reload behavior and handoff-repair preference are hardened.

## Post-Reload Live Acceptance Rerun Protocol

Fresh fixture prepared:

```bash
cd /tmp/aegis-task131-postreload-1YQY7E/shop-webapp
```

Prepared fixture checks:

- Git repo initialized on `main`.
- Aegis MCP is visible from the fixture through user-scope source-mode registration.
- Taskmaster Task 42 is pending and `npx task-master next` returns `Add visible Add to cart button`.
- `npm run verify` fails before implementation with `FAIL: src/main.ts must create, label, and attach a visible Add to cart button.`
- Aegis is not installed yet; this fixture is ready for the post-reload split-session test.
- The fixture README is intentionally ordinary project context: it mentions Taskmaster and `npm run verify`, but does not mention Aegis, hook reloads, closeout, or doctor. Aegis behavior must come from MCP tool descriptions and installed runtime files, not from a bespoke user prompt.

The live Claude run should intentionally split installation from implementation:

1. Start Claude in the fresh fixture with Aegis MCP registered.
2. Ask Claude a normal task request, without naming Aegis, reloads, closeout, doctor, or workflow internals.
3. Expected first-session behavior: Claude proactively inspects/initializes the Aegis project workflow from MCP affordances, sees `client_reload.required=true` or `next_action.action=restart_claude_before_mutation`, and stops before source edits.
4. Manually restart Claude in the same fixture.
5. Ask Claude to continue the project workflow.
6. Expected second-session behavior: Claude runs `aegis.next`, uses `task-master next/show`, starts Aegis through `aegis.kickoff apply=true` with Taskmaster Task 42, logs scope, edits source with native tools, and the PostToolUse hook creates pending tracking.
7. Claude must clear pending tracking with `aegis.log pending_event_id=current`, run task verification, strict verify, `aegis.closeout_ready`, use `aegis.handoff_repair apply=true` if handoff gates fail, run final closeout, run read-only doctor, then mark Taskmaster done and refresh generated task files.

Acceptance for the rerun requires all of the above plus final empty pending tracking, no local Aegis task allocation, closeout passed, doctor healthy, Taskmaster `tasks.json` done, and generated Taskmaster task text refreshed or an explicit broad `task-master generate` note. The user prompt must not spoon-feed `client_reload`, `aegis.handoff_repair`, closeout, doctor, or the expected command sequence.

Suggested normal-language Claude prompt:

```text
Take the next task in this project and finish it. The user-facing change is a visible Add to cart button on the shop page. Tell me what changed and what verified.
```

Expected acceptance:

- Claude initializes Aegis through MCP or CLI without hand-editing workflow files.
- Claude uses Taskmaster as task authority (`task-master next/show` or Taskmaster MCP equivalent).
- Claude starts Aegis with Taskmaster Task 42 via `aegis.kickoff`, not `aegis.start`.
- Current work, branch, session, plan, and work-tracking paths use Task 42.
- Source edit is made with native agent tools.
- Aegis logs scope, implementation, task verification, and strict verification evidence.
- Aegis closeout and read-only doctor pass before Taskmaster Task 42 is marked done.
- Pending tracking is empty at the end.

## Mechanical Reload Barrier Live Fixture

Fresh fixture prepared:

```bash
cd /tmp/aegis-task131-reload-barrier-Kv3ASC/shop-webapp
```

Fixture files:

```text
./.taskmaster/state.json
./.taskmaster/tasks/task_042.txt
./.taskmaster/tasks/tasks.json
./README.md
./index.html
./package.json
./scripts/assert-cart-button.mjs
./src/main.ts
```

Prepared fixture checks:

```text
git branch: main
Aegis manifest: absent
Taskmaster next: #42 Add visible Add to cart button, status pending
npm run verify: FAIL before implementation
Claude MCP from fixture: aegis connected through user-scope uvx source-mode registration
```

Note: running `claude mcp list` creates `.aegis/uv-cache` and `.aegis/uv-tools` because the registered source-mode command sets `UV_CACHE_DIR=.aegis/uv-cache` and `UV_TOOL_DIR=.aegis/uv-tools`. That is not an Aegis project install; `.aegis/foundation-manifest.json` is absent.

First-session prompt:

```text
Take the next task in this project and finish it. The user-facing change is a visible Add to cart button on the shop page. Tell me what changed and what verified.
```

Expected first-session result:

- Claude discovers Aegis from the global MCP affordance.
- Claude runs `aegis.init` / `aegis.install`.
- Aegis returns `client_reload.required=true` and writes `.aegis/state/client-reload-required.json`.
- Aegis refuses `aegis.start` and `aegis.kickoff` while that marker exists.
- Claude stops before source edits and asks for Claude to be restarted/reloaded in the same fixture.

Second-session prompt after manual Claude restart:

```text
Continue the project workflow and finish the task.
```

Expected second-session result:

- Installed Claude `PreToolUse` clears `.aegis/state/client-reload-required.json`.
- Claude runs `aegis.next`.
- Claude uses Taskmaster Task 42 and starts Aegis through `aegis.kickoff`, not `aegis.start`.
- The native source edit creates pending tracking.
- Claude clears pending tracking with `aegis.log pending_event_id=current`.
- Task verification, strict verify, closeout, read-only doctor, Taskmaster done, and generated task-file refresh all complete in that order.

## Mechanical Reload Barrier Live Run - First Session

Fixture:

```bash
cd /tmp/aegis-task131-reload-barrier-Kv3ASC/shop-webapp
```

Prompt used:

```text
Take the next task in this project and finish it. The user-facing change is a visible Add to cart button on the shop page. Tell me what changed and what verified.
```

Observed behavior: passed the first-session reload-barrier gate.

- Claude discovered Aegis from MCP.
- Claude initialized Aegis in the project.
- Aegis installed `.claude/settings.json`, `.claude/scripts/*`, `CLAUDE.md`, `.aegis/`, schemas, and local runtime files.
- Aegis returned `client_reload.required=true` in `.aegis/reports/install-report.json`.
- Aegis wrote `.aegis/state/client-reload-required.json`.
- Claude recognized `state=client_reload_required`, reported that hooks are not active in the already-running session, and stopped before source edits.
- `src/main.ts` remained unchanged:

```ts
const app = document.querySelector<HTMLDivElement>("#app");

if (app) {
  app.textContent = "Shop app ready";
}
```

- Taskmaster Task 42 remained `pending`.

Marker evidence:

```json
{
  "status": "required",
  "agent": "claude",
  "clearance": {
    "method": "installed_claude_pretooluse_hook",
    "path": ".claude/scripts/pretooluse-gate.sh"
  }
}
```

Verdict: the mechanical barrier prevents first-session implementation after hook installation. The remaining required live proof is the restarted second session: hook clears marker, Taskmaster-backed `aegis.kickoff`, native edit creates pending tracking, closeout/doctor pass, then Taskmaster done.

## Mechanical Reload Barrier Live Run - Second Session

Fixture:

```bash
cd /tmp/aegis-task131-reload-barrier-Kv3ASC/shop-webapp
```

Prompt used after starting a new Claude session:

```text
Continue the project workflow and finish the task.
```

Observed behavior: exposed a post-closeout Taskmaster completion gate conflict.

Successful path:

- Restarted Claude loaded the installed project hooks.
- Claude used Taskmaster Task 42 and Aegis kickoff.
- Source edit was made with native tools:

```ts
const addToCartButton = document.createElement("button");
addToCartButton.type = "button";
addToCartButton.textContent = "Add to cart";
app.appendChild(addToCartButton);
```

- `npm run verify` passed.
- Aegis strict verify passed: 27 checks, 0 required failures, 0 warnings.
- Aegis closeout passed and wrote `.aegis/reports/closeout-report.json`.
- Read-only Aegis doctor reported healthy, state `completed_closeout`, 20 checks, 0 failures.

Failure discovered:

- After closeout, `.aegis/state/current-work.json` was correctly marked `status=completed` with `closeout_passed_at`.
- Taskmaster Task 42 was still `pending`.
- The installed `PreToolUse` readiness gate blocked `task-master set-status --id=42 --status=done` because readiness expected Aegis current work to remain `in-progress`.
- Taskmaster MCP status mutation was also classified as mutating and blocked.

Root cause:

```text
Documented order: Aegis closeout + doctor -> Taskmaster done -> generated task refresh
Installed gate: completed closeout -> readiness BLOCKED for all Taskmaster mutations
```

Fix implemented after the live finding:

- Installed Claude gate now allows only the narrow post-closeout Taskmaster bookkeeping path when current work is closeout-passed and pending tracking is empty:
  - matching `task-master set-status --id=<task-id> --status=done`
  - matching Taskmaster MCP `set_task_status` with `status=done`
  - `task-master generate` for generated task-file refresh
- Mismatched Taskmaster ids, source edits, and other mutations remain blocked after closeout.
- `PostToolUse` no longer creates pending tracking for completed-closeout bookkeeping.
- Packaged `aegis_foundation/assets/.claude/scripts/gate_lib.py` was mirrored.

Regression command:

```bash
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/aegis-uv-cache uv run python -m pytest tests/claude_adapter/test_pretooluse_gates.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_installer_fixtures.py tests/meta_workflow_guard/test_aegis_acceptance_assertions.py tests/meta_workflow_guard/test_aegis_schemas.py
```

Result:

```text
141 passed, 1 skipped in 12.19s
```

Verdict: second-session live run proved the reload barrier and core workflow path, but exposed a post-closeout Taskmaster completion bug. That bug is fixed in code and automated tests; final Task 131 completion still needs one more fresh live retest with the patched hook.

## Final Fresh Retest Fixture - Patched Hook

Fixture:

```bash
cd /tmp/aegis-task131-final-QPqUnJ/shop-webapp
```

Baseline checks:

- Git branch: `main`.
- `.aegis/foundation-manifest.json`: absent.
- `npm run verify`: fails before implementation with `FAIL: src/main.ts must create, label, and attach a visible Add to cart button.`
- `npx task-master next`: returns Taskmaster task 42, status `pending`, title `Add visible Add to cart button`.
- `claude mcp list`: global `aegis` MCP connected from the fixture via `uvx --from /home/loucmane/codex aegis-mcp-server --default-target-dir . --transport stdio`.
- `taskmaster-ai` MCP is not connected in this Claude config because provider env vars are missing, so the live retest should exercise the Taskmaster CLI path.

First prompt to use in a new Claude session:

```text
Take the next task in this project and finish it. The user-facing change is a visible Add to cart button on the shop page. Tell me what changed and what verified.
```

Expected first-session result:

- Claude discovers Taskmaster task 42 and Aegis MCP.
- Claude initializes Aegis.
- Aegis reports `client_reload.required=true` and writes `.aegis/state/client-reload-required.json`.
- Claude stops before `aegis.kickoff`, source edits, Taskmaster status mutation, or test execution.

Second prompt to use after starting a new Claude session in the same directory:

```text
Continue the project workflow and finish the task.
```

Expected second-session result:

- Installed Claude hook clears the reload marker.
- Claude uses Taskmaster task 42 and `aegis.kickoff` rather than allocating a local Aegis task id.
- Source edit uses native tools and creates the Add to cart button in `src/main.ts`.
- `npm run verify` passes.
- `aegis.verify --strict`, `aegis.closeout`, and read-only `aegis.doctor` pass.
- After closeout/doctor, the patched installed hook allows matching Taskmaster completion bookkeeping:
  - `task-master set-status --id=42 --status=done`
  - `task-master generate` if no targeted generated-file helper exists.
- Mismatched Taskmaster ids and source edits remain blocked after closeout.

Task 131 remains in progress until this final fresh retest passes end to end.

## Final Fresh Retest Attempt - Same-Session Edit Failure

Fixture:

```bash
cd /tmp/aegis-task131-final-QPqUnJ/shop-webapp
```

Prompt used:

```text
Take the next task in this project and finish it. The user-facing change is a visible Add to cart button on the shop page. Tell me what changed and what verified.
```

Observed failure:

- Claude discovered Taskmaster task 42 and installed Aegis.
- Aegis wrote `.aegis/state/client-reload-required.json`.
- Claude still edited `src/main.ts` and ran `npm run verify` in the same session.
- Aegis closeout correctly failed because no governed kickoff/session/plan/work-tracking state existed.
- Claude briefly marked Taskmaster 42 done, then reverted it to `in-progress`.

Root cause:

```text
The reload barrier blocked Aegis start/kickoff, but newly installed Claude PreToolUse hooks cannot block native Edit/Write/Bash in the already-running session because Claude only loads those hooks at session startup.
```

Hardening implemented after this finding:

- MCP `aegis.init` and `aegis.install` now return a structured blocked response when they apply an install that requires Claude reload:
  - `ok=false`
  - `error.code=client_reload_required`
  - `error.status=blocked`
  - `details.must_stop=true`
  - the applied install report is still preserved at `details.report`
- The install report now marks the condition as `severity=hard_stop`, `must_stop=true`, and explicitly lists forbidden actions until reload:
  - source edits
  - project verification commands
  - Taskmaster mutations
  - `aegis.start`
  - `aegis.kickoff`
  - `aegis.verify`
  - `aegis.closeout`
- Docs now state that MCP install/init returning `client_reload_required` is a hard stop, not a normal successful continuation path.

Regression command:

```bash
PYTHONDONTWRITEBYTECODE=1 UV_CACHE_DIR=/tmp/aegis-uv-cache uv run python -m pytest tests/claude_adapter/test_pretooluse_gates.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_installer_fixtures.py tests/meta_workflow_guard/test_aegis_acceptance_assertions.py tests/meta_workflow_guard/test_aegis_schemas.py
```

Result:

```text
142 passed, 1 skipped in 10.73s
```

## Replacement Fresh Retest Fixture - Hard-Stop MCP Contract

Fixture:

```bash
cd /tmp/aegis-task131-hardstop-x0GaqA/shop-webapp
```

Baseline checks:

- Git branch: `main`.
- `.aegis/foundation-manifest.json`: absent.
- `npm run verify`: fails before implementation with `FAIL: src/main.ts must create, label, and attach a visible Add to cart button.`
- `npx task-master next`: returns Taskmaster task 42, status `pending`, title `Add visible Add to cart button`.
- `claude mcp list`: global `aegis` MCP connected from the fixture via `uvx --from /home/loucmane/codex aegis-mcp-server --default-target-dir . --transport stdio`.
- `taskmaster-ai` MCP remains disconnected in this Claude config because provider env vars are missing, so the live retest should exercise the Taskmaster CLI path.

First prompt to use in a new Claude session:

```text
Take the next task in this project and finish it. The user-facing change is a visible Add to cart button on the shop page. Tell me what changed and what verified.
```

Expected first-session result:

- Claude discovers Taskmaster task 42 and Aegis MCP.
- Claude calls MCP `aegis.init` or `aegis.install`.
- The MCP response is blocked with `error.code=client_reload_required` and `details.must_stop=true`.
- Claude stops before source edits, project verification, Taskmaster mutation, or Aegis kickoff/start.

Second prompt to use after starting a new Claude session in the same directory:

```text
Continue the project workflow and finish the task.
```

Expected second-session result:

- Installed Claude hook clears the reload marker.
- Claude uses Taskmaster task 42 and `aegis.kickoff` rather than allocating a local Aegis task id.
- Source edit uses native tools and creates the Add to cart button in `src/main.ts`.
- `npm run verify` passes.
- `aegis.verify --strict`, `aegis.closeout`, and read-only `aegis.doctor` pass.
- After closeout/doctor, the patched installed hook allows matching Taskmaster completion bookkeeping:
  - `task-master set-status --id=42 --status=done`
  - `task-master generate` if no targeted generated-file helper exists.

Task 131 remains in progress until this replacement fresh retest passes end to end.

## Replacement Fresh Retest - First Session Pass

Fixture:

```bash
cd /tmp/aegis-task131-hardstop-x0GaqA/shop-webapp
```

Prompt used:

```text
Take the next task in this project and finish it. The user-facing change is a visible Add to cart button on the shop page. Tell me what changed and what verified.
```

Observed behavior:

- Claude discovered Taskmaster task 42.
- Claude detected that Aegis was not installed.
- Claude ran Aegis init through the MCP path.
- MCP returned `client_reload_required` as a hard stop.
- Claude stopped and explicitly refused to edit source, run project verification, mutate Taskmaster, or call Aegis start/kickoff in the same session.

Post-run fixture checks:

```text
.aegis/state/client-reload-required.json: present
src/main.ts: unchanged; still renders only "Shop app ready"
npm run verify: FAIL, as expected before implementation
Taskmaster task 42: pending
```

Verdict: first-session hard-stop behavior passed. The remaining required proof is the restarted second session: installed hook clears the marker, Aegis kickoff uses Taskmaster task 42, implementation and verification run under active hooks, closeout/doctor pass, and post-closeout Taskmaster done/generate bookkeeping succeeds.

## Replacement Fresh Retest - Second Session Pass

Fixture:

```bash
cd /tmp/aegis-task131-hardstop-x0GaqA/shop-webapp
```

Prompt used after starting a new Claude session:

```text
Continue the project workflow and finish the task.
```

Observed behavior:

- The installed hook was active in the restarted Claude session.
- Readiness initially reported `BLOCKED` because branch `main` had no task id, which is the expected pre-kickoff state.
- Claude used Taskmaster task 42 as task authority.
- Claude marked Taskmaster task 42 `in-progress`, then ran Aegis kickoff for task 42.
- Aegis created branch `feat/task-42-add-cart-button`.
- Readiness reported `READY | task=42`.
- Claude logged scope before source edits.
- Claude edited `src/main.ts` with native tools and added:

```ts
const addToCartButton = document.createElement("button");
addToCartButton.type = "button";
addToCartButton.textContent = "Add to cart";
app.append(addToCartButton);
```

- The installed hook created pending S:W:H:E tracking, and Claude cleared it with `aegis log --pending-id current`.
- `npm run verify` passed.
- Task-specific verification was logged against `plan-step-verify`.
- `aegis verify --strict` passed: 27 checks, 0 required failures.
- Strict verification evidence was logged.
- Closeout dry-run initially failed on handoff semantic gates; Claude ran `aegis handoff repair`.
- Closeout dry-run then passed.
- Final `aegis closeout --update-handoff` passed.
- Read-only `aegis doctor --target-dir .` reported healthy: `completed_closeout`, 20 checks, 0 required failures, 0 warnings.
- After closeout and doctor, the patched post-closeout Taskmaster allowance worked: `task-master set-status --id=42 --status=done` succeeded instead of being blocked.
- The fixture had no targeted `scripts/codex-task` helper, so Claude deliberately ran broad `task-master generate`.

Post-run verification:

```text
git branch: feat/task-42-add-cart-button
npm run verify: PASS
aegis closeout --dry-run --update-handoff: PASSED
aegis doctor --target-dir .: healthy (completed_closeout), 20 checks, 0 failures
.aegis/state/current-work.json: task 42 completed, closeout_passed_at present
.aegis/state/pending-tracking.json: absent
.taskmaster/tasks/tasks.json: task 42 done
.taskmaster/tasks/task_042.md: Status done
```

Note: the seed fixture also contains a legacy hand-written `.taskmaster/tasks/task_042.txt` that still says `Status: pending`; Taskmaster generated the current-format `.taskmaster/tasks/task_042.md` with `Status: done` and uses `tasks.json` as authority. This legacy `.txt` file is not the Taskmaster-generated refreshed artifact for the installed CLI version.

Verdict: final replacement live retest passed end to end. Taskmaster-backed Claude MCP flow now proves:

- normal-language task discovery through Taskmaster,
- Aegis install hard-stop before same-session native edits,
- restart-required hook activation,
- Taskmaster-backed `aegis.kickoff`,
- native edit tracking,
- strict verification,
- handoff repair,
- closeout and doctor,
- and post-closeout Taskmaster completion/generate bookkeeping.
