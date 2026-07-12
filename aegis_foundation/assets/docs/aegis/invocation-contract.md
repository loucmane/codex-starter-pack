# Aegis Invocation Contract

This document defines the supported V1 ways to run Aegis from a project that is not the Aegis source checkout.

## Public Flow

The stable public adoption commands are:

```bash
aegis mcp register claude
aegis init
# restart Claude if init reports client_reload.required=true
aegis start "Improve BrandMark accessibility"
```

`aegis init` is the task-master-init style setup command. `aegis start "<title>"` is the local-task path for projects without an external task id. In projects that already use Taskmaster, the public path is `task-master next`, `task-master show <id>`, then `aegis kickoff --task <id> --slug <slug> --title "<title>"` so Aegis uses Taskmaster's numeric task id instead of allocating a local one. The lower-level `inspect`, `plan-install`, and `install --apply` commands remain supported for advanced use and debugging.

Task 112 deliberately separates two modes:

- **Package-style mode**: use the `aegis` and `aegis-mcp-server` console commands. This is the canonical portable surface.
- **Development checkout mode**: use a local checkout only to provide package assets while keeping the same command semantics.

Taskmaster and Serena are optional integrations. The installed runtime must still work without either one by using Aegis-native workflow state.

## Release Package Identity

Task 113 uses `aegis-foundation` as the working public distribution name. The import packages remain `aegis_foundation` and `aegis_mcp`, and the console commands remain:

```bash
aegis --version
aegis-mcp-server --describe-config
```

`aegis --version` reports the Aegis package version. `aegis-mcp-server --describe-config` reports the package distribution name plus foundation, installer, and schema versions alongside the resolved source and target directories.

The release package identity is additive. It does not remove the development checkout or editable package-style commands below.

See `docs/aegis/distribution.md` for local wheel, `pip`, `uvx`, `pipx`, MCP startup, and hosted-service release snippets.
See `docs/aegis/state-recovery-model.md` for the doctor/repair, replay, and idempotency contract.

## Package-Style Mode

Run Aegis from the target project directory:

```bash
aegis inspect --target-dir .
aegis status --target-dir .
aegis plan-install --target-dir . --primary-agent claude --agent claude
aegis install --target-dir . --primary-agent claude --agent claude --apply
aegis verify --target-dir .
aegis verify --target-dir . --strict
aegis doctor --target-dir .
aegis repair --target-dir .
aegis closeout --target-dir . --update-handoff
```

The agent-facing `status`, `next`, readiness, `doctor`, `verify`, `update`, `witness`,
`replay`, and `closeout` surfaces use one context-budget contract. Default output is at
most 60 lines and 8 KiB of UTF-8; it reports exact aggregate counts, bounded samples,
truncation, full-detail artifact paths, and one copyable next action. `--verbose`
expands the sample while remaining bounded at 120 lines and 32 KiB. `--all` is the
explicit unbounded operator/debug mode. `--json` selects representation and remains
bounded; use `--all --json` only when complete structured stdout is intentional. These
flags change presentation only: checks, exit codes, stored state, and report artifacts
always use the complete payload.

The corresponding MCP tools apply the budget to the complete MCP response envelope.
Their `detail` argument accepts `default`, `verbose`, or `all`; `detail=all` is the
MCP equivalent of CLI `--all --json`.

Start tracked local work without requiring Taskmaster or Serena:

```bash
aegis start --target-dir . "First Task"
bash .claude/scripts/readiness.sh --quick
```

`aegis start` allocates the next local Aegis task id, derives the slug, creates the task branch, and renders `.aegis/state/current-work.json`, `sessions/current`, `plans/current`, and `docs/ai/work-tracking/active/<date>-task<id>-<slug>-ACTIVE/`. The active folder is not a placeholder: it includes `TRACKER.md`, `FINDINGS.md`, `DECISIONS.md`, `HANDOFF.md`, `IMPLEMENTATION.md`, `CHANGELOG.md`, `designs/`, and `reports/<slug>/` rendered from packaged workflow templates. The templates are installed for inspection under `.aegis/templates/workflow/`. Use `aegis kickoff --task ...` only when the project or user provides an explicit external numeric task id.

Start tracked work from Taskmaster when a numeric task already exists:

```bash
task-master next
task-master show <id>
aegis kickoff --target-dir . --task <id> --slug <slug> --title "<title>"
```

Taskmaster MCP discovery may be used instead of the CLI when it is available: `help`, `get_tasks`, `next_task`, and `get_task` are treated as read-only even while readiness is `BLOCKED` before kickoff. Taskmaster MCP mutations and unknown Taskmaster MCP tools remain blocked until readiness is `READY`, except for the narrow post-closeout completion bookkeeping path for the matching task.

For Taskmaster-backed work, Aegis creates the same branch, current-work file, session, plan, and active work-tracking scaffold as `aegis start`, but it does not create `.aegis/state/local-tasks.json` for that task. `aegis start` refuses to bypass an available Taskmaster task. After implementation, verification, strict verification, closeout, and read-only `aegis doctor` pass, mark the Taskmaster task done and refresh the targeted generated task file.

Claude Code hook activation has a session boundary. If `aegis init` or `aegis install` creates or modifies `.claude/settings.json` or `.claude/scripts/*`, the install report includes `client_reload.required=true` and Aegis writes `.aegis/state/client-reload-required.json`. MCP `aegis.init` / `aegis.install` surface this as a blocked hard-stop response: `ok=false`, `error.code=client_reload_required`, `error.status=blocked`, and `details.must_stop=true`, while preserving the applied install report under `details.report`. In that state, `aegis.start` and `aegis.kickoff` are blocked, and the current Claude session must not edit source, run project verification, mutate Taskmaster, or attempt closeout. Stop, restart Claude in the project, let the installed `PreToolUse` hook clear the marker, run `aegis next`, and continue only after the installed hooks are active.

Taskmaster generated task-file refresh should use the project-specific targeted helper when present. If no targeted helper exists, run broad `task-master generate` deliberately after Taskmaster done and report the broad refresh in the final evidence.

After a successful mutation, the installed Claude `PostToolUse` hook records pending S:W:H:E tracking in `.aegis/state/pending-tracking.json`. The next persistent mutation and session stop are refused until the agent records the work across the active workflow surfaces:

```bash
aegis log --target-dir . --pending-id current --note "Recorded task result evidence" --plan-step plan-step-implement --plan-status completed
```

If the global command is not on PATH, use the installed project shim:

```bash
./.aegis/bin/aegis log --target-dir . --pending-id current --note "Recorded task result evidence" --plan-step plan-step-implement --plan-status completed
```

`aegis log` appends a `[S:<date>|W:task<id>-<slug>|H:<handler>|E:<evidence>]` line to `sessions/current` and the active `TRACKER.md`; it clears the matching pending event; and it updates current plan evidence only when `--plan-step` is supplied. Omit `--surface` for event-aware canonical defaults: scope logs update `FINDINGS.md`, `DECISIONS.md`, and `HANDOFF.md`; implementation logs update `IMPLEMENTATION.md`, `CHANGELOG.md`, and `HANDOFF.md`; verification logs update `IMPLEMENTATION.md`, `CHANGELOG.md`, and `HANDOFF.md`. Use repeated `--surface <name>` only to override those defaults for a targeted repair. Use `--pending-id <id>` or `--pending-id current` when the hook has already recorded the handler/evidence pair in `.aegis/state/pending-tracking.json`; use explicit `--handler` and `--evidence` when logging evidence that did not come from a pending event. This is the portable Aegis equivalent of this repository's S:W:H:E progress discipline; it does not require Taskmaster or Serena.

Finish task work with the closeout gate:

```bash
aegis verify --target-dir . --strict
aegis log --target-dir . --pending-id current --note "Recorded strict verification evidence" --plan-step plan-step-verify --plan-status completed
aegis closeout --target-dir . --update-handoff
```

`aegis closeout` prints a concise bounded human summary by default, writes `.aegis/reports/closeout-report.json` during final closeout, and exits non-zero unless readiness is READY, pending S:W:H:E tracking is empty, strict verification passes, plan/tracker scope/implement/verify steps are complete and ordered, required evidence is cross-referenced in session/tracker/implementation/changelog/handoff/plan, and `HANDOFF.md` has semantic current-state and next-step sections. Use `--json` for bounded structured output or `--all --json` for intentional complete stdout; the stored report is always complete. `--update-handoff` rewrites only the Aegis-owned semantic sections and preserves `## Progress Log`. A passed final closeout marks `.aegis/state/current-work.json` as `completed` while retaining the closeout evidence path.

The closeout report may include normal git/GitHub command guidance (`git status`, `git add`, `git commit`, `git push`, `gh pr create`). `gac` is legacy/manual only and is not the default generated path.

Diagnose and repair workflow state with the recovery surfaces:

```bash
aegis doctor --target-dir .
aegis repair --target-dir .
aegis repair --target-dir . --apply
```

`aegis doctor` is read-only and classifies the current state, failed checks, safe repair candidates, manual-review items, and next action. `aegis repair` previews the same repair plan by default. `aegis repair --apply` may only apply deterministic low-risk fixes such as missing current symlinks, expected empty directories, absent managed runtime files, executable bits, and completed closeout metadata that is already proven by the closeout report. It must not overwrite divergent user files, clear non-empty pending tracking, delete stale active folders, or invent work state.

## Development Checkout Mode

From the target project directory, replace `/path/to/codex` with the absolute path to the Aegis source checkout. The command surface remains the package-style `aegis` CLI; `--source-root` points it at local assets.

Inspect without mutating the project:

```bash
aegis --source-root /path/to/codex inspect --target-dir .
```

Plan an install without mutating the project:

```bash
aegis --source-root /path/to/codex plan-install --target-dir . --primary-agent claude --agent claude
```

Check release/update status without mutating the project:

```bash
aegis --source-root /path/to/codex status --target-dir .
```

Apply the install after reviewing the plan:

```bash
aegis --source-root /path/to/codex install --target-dir . --primary-agent claude --agent claude --apply
```

Verify the installed runtime:

```bash
aegis --source-root /path/to/codex verify --target-dir .
```

Create portable Aegis workflow state:

```bash
aegis --source-root /path/to/codex start --target-dir . "First Task"
aegis --source-root /path/to/codex log --target-dir . --pending-id current --note "Recorded task result evidence" --plan-step plan-step-implement --plan-status completed
aegis --source-root /path/to/codex closeout --target-dir . --update-handoff
```

Use `--target-dir .` when running from the target project. Use an explicit target path when running from somewhere else.

## Release Certification

Before preparing GitHub release artifacts, run the release-candidate certification workflow from the Aegis source checkout:

```bash
aegis certify-release --source-dir /path/to/codex --dist-dir /tmp/aegis-rc --report-file reports/aegis-release-certification/certification-report.json
```

The certification workflow builds wheel and sdist artifacts, computes SHA-256 checksums, records git/package/Python provenance, inspects artifact contents for Aegis assets and entry points, and can run a clean installed-wheel CLI smoke that reaches `aegis verify --strict`. Use `--skip-build` only when inspecting prebuilt artifacts, and use `--skip-smoke` only for a deliberately lighter local evidence pass. PyPI publication remains a separate explicit release task.

## MCP Development Startup

Run the MCP server from the same local checkout, but point the default target directory at the project being managed.

```bash
python3 /path/to/codex/scripts/aegis-mcp-server \
  --source-root /path/to/codex \
  --default-target-dir /path/to/project
```

To inspect the resolved configuration without starting the transport:

```bash
python3 /path/to/codex/scripts/aegis-mcp-server \
  --source-root /path/to/codex \
  --default-target-dir /path/to/project \
  --describe-config
```

The MCP tools keep the same safety boundary as the CLI:

- `aegis.inspect` and `aegis.plan_install` are read-only.
- `aegis.status` is read-only and reports release/update state without writing target files.
- `aegis.doctor` is read-only and reports recovery/idempotency state plus repair candidates.
- `aegis.repair` is read-only unless `apply=true`; mutating repair writes a repair report and only applies safe deterministic actions.
- `aegis.install` requires explicit `apply=true`.
- `aegis.verify` writes a verification report and requires `acknowledge_report_write=true`.
- `aegis.closeout` writes a closeout report, returns structured MCP data, and requires `acknowledge_report_write=true`.
- `aegis.start` writes local current work state and requires `apply=true`; this is the default local path when no external task id exists.
- `aegis.kickoff` writes current work state for explicit external numeric task ids and requires `apply=true`.
- `aegis.start` and `aegis.kickoff` render the packaged workflow templates into a full session/plan/work-tracking scaffold, not thin placeholder docs.
- Installed Claude hooks treat `aegis.start` and `aegis.kickoff` as readiness bootstrap operations after `.aegis/state/client-reload-required.json` has been cleared by a running `PreToolUse` hook. They are allowed when readiness is otherwise blocked because their job is to create the missing branch/session/plan/work-tracking state; normal mutations and non-bootstrap Aegis operations remain blocked until readiness passes.
- `aegis.log` writes S:W:H:E entries to `sessions/current`, the active `TRACKER.md`, and event-aware canonical surfaces; it writes plan evidence only when `plan_step` is supplied; it can consume pending hook events through `pending_event_id`; and it requires `apply=true` when invoked through MCP.
- `aegis.closeout` is the final completion gate. It should run only after strict verification evidence has been logged and before an agent claims the task is complete.
- Installed Claude `PostToolUse` and `Stop` hooks enforce pending S:W:H:E completion: task-scoped writes create `.aegis/state/pending-tracking.json`, further mutations are blocked until `aegis.log` clears it, and session stop is blocked while pending events remain.
- After a successful closeout, installed Claude hooks allow only the narrow Taskmaster bookkeeping path for the matching task: `task-master set-status --id=<task-id> --status=done` or the Taskmaster MCP equivalent, plus `task-master generate` for generated task-file refresh. Other source, Aegis, Git, unknown Taskmaster MCP tools, or mismatched Taskmaster mutations remain blocked in the completed-closeout state.
- Agents must cite `.aegis/reports/*` or MCP tool/resource results as evidence, not prompt text.

## Editable Package-Style Mode

Task 112 supports local editable package-style invocation. This gives agents and developers the final command shape without requiring a public package release yet.

Create a local environment and install the checkout in editable mode:

```bash
python3 -m venv .venv-aegis
.venv-aegis/bin/python -m pip install -e /path/to/codex
```

Then run Aegis from the target project directory:

```bash
aegis inspect --target-dir .
aegis status --target-dir .
aegis plan-install --target-dir . --primary-agent claude --agent claude
aegis install --target-dir . --primary-agent claude --agent claude --apply
aegis verify --target-dir .
aegis verify --target-dir . --strict
aegis start --target-dir . "First Task"
aegis log --target-dir . --pending-id current --note "Recorded task result evidence" --plan-step plan-step-implement --plan-status completed
aegis closeout --target-dir . --update-handoff
```

Start the editable package-style MCP server from the target project directory:

```bash
aegis-mcp-server --default-target-dir .
```

Inspect package-style MCP configuration without starting the transport:

```bash
aegis-mcp-server --default-target-dir . --describe-config
```

The editable install resolves Aegis assets from the source checkout. Public wheel assets, `uvx`, `pipx`, package signing, update migrations, rollback, hosted services, and CI install templates are out of scope for this contract task and belong to release hardening.

## Installed Target Commands

After Aegis is installed into a target project, the generated target still contains project-local helper files. Those are the runtime files used inside that target. The external invocation commands in this document are for adoption and management from outside the Aegis source repository.

## Safety Notes

- Do not run `install --apply` until the plan output has been reviewed.
- Do not write `.aegis/` directly. Use Aegis CLI or MCP operations.
- Do not perform a second mutation after a successful task write until `aegis log --pending-id <id>` or `aegis log --pending-id current` has recorded the S:W:H:E entry in the active session, tracker, and canonical event surfaces. Include explicit `--plan-step` flags when that evidence should advance scope/implementation/verification plan state.
- Do not claim task completion until `aegis closeout` passes.
- Treat `.aegis/reports/install-plan.json`, `.aegis/reports/install-report.json`, `.aegis/reports/verification-report.json`, and `.aegis/reports/closeout-report.json` as the evidence trail.
- Development checkout snippets may contain the source checkout path in local shell or MCP client configuration. Installed target `.aegis/` state should not depend on an absolute source checkout path.
