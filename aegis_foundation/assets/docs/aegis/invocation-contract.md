# Aegis Invocation Contract

This document defines the supported V1 ways to run Aegis from a project that is not the Aegis source checkout.

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

## Package-Style Mode

Run Aegis from the target project directory:

```bash
aegis inspect --target-dir .
aegis status --target-dir .
aegis plan-install --target-dir . --primary-agent claude --agent claude
aegis install --target-dir . --primary-agent claude --agent claude --apply
aegis verify --target-dir .
aegis verify --target-dir . --strict
aegis closeout --target-dir . --update-handoff
```

Start tracked work without requiring Taskmaster or Serena:

```bash
aegis kickoff --target-dir . --task 1 --slug first-task --title "First Task"
bash .claude/scripts/readiness.sh --quick
```

Kickoff creates `.aegis/state/current-work.json`, `sessions/current`, `plans/current`, and `docs/ai/work-tracking/active/<date>-task<id>-<slug>-ACTIVE/`. The active folder is not a placeholder: it includes `TRACKER.md`, `FINDINGS.md`, `DECISIONS.md`, `HANDOFF.md`, `IMPLEMENTATION.md`, `CHANGELOG.md`, `designs/`, and `reports/<slug>/` rendered from packaged workflow templates. The templates are installed for inspection under `.aegis/templates/workflow/`.

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

`aegis closeout` writes `.aegis/reports/closeout-report.json` and exits non-zero unless readiness is READY, pending S:W:H:E tracking is empty, strict verification passes, plan/tracker scope/implement/verify steps are complete and ordered, required evidence is cross-referenced in session/tracker/implementation/changelog/handoff/plan, and `HANDOFF.md` has semantic current-state and next-step sections. `--update-handoff` rewrites only the Aegis-owned semantic sections and preserves `## Progress Log`.

The closeout report may include normal git/GitHub command guidance (`git status`, `git add`, `git commit`, `git push`, `gh pr create`). `gac` is legacy/manual only and is not the default generated path.

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
aegis --source-root /path/to/codex kickoff --target-dir . --task 1 --slug first-task --title "First Task"
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
- `aegis.install` requires explicit `apply=true`.
- `aegis.verify` writes a verification report and requires `acknowledge_report_write=true`.
- `aegis.closeout` writes a closeout report and requires `acknowledge_report_write=true`.
- `aegis.kickoff` writes current work state and requires `apply=true`.
- `aegis.kickoff` renders the packaged workflow templates into a full session/plan/work-tracking scaffold, not thin placeholder docs.
- `aegis.log` writes S:W:H:E entries to `sessions/current`, the active `TRACKER.md`, and event-aware canonical surfaces; it writes plan evidence only when `plan_step` is supplied; it can consume pending hook events through `pending_event_id`; and it requires `apply=true` when invoked through MCP.
- `aegis.closeout` is the final completion gate. It should run only after strict verification evidence has been logged and before an agent claims the task is complete.
- Installed Claude `PostToolUse` and `Stop` hooks enforce pending S:W:H:E completion: task-scoped writes create `.aegis/state/pending-tracking.json`, further mutations are blocked until `aegis.log` clears it, and session stop is blocked while pending events remain.
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
aegis kickoff --target-dir . --task 1 --slug first-task --title "First Task"
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
