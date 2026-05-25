# Task 123 Existing Project Live Proof - hpfetcher

Date: 2026-05-25

## Source and Copies

- Source project: `/home/loucmane/dev/hpfetcher`
- Full live copy: `/tmp/aegis-task123-hpfetcher-copy-5RKOic/hpfetcher`
- Merge-fix validation copy: `/tmp/aegis-task123-hpfetcher-merge-copy-h37v0w/hpfetcher`

The original source project was not mutated.

## Wheel-Backed Native MCP Registration

The release-candidate wheel was registered with Claude through the native client path:

```text
claude mcp add --scope local aegis -e UV_CACHE_DIR=.aegis/uv-cache -e UV_TOOL_DIR=.aegis/uv-tools -- uvx --from /tmp/aegis-task123-dist-clean/aegis_foundation-0.1.0-py3-none-any.whl aegis-mcp-server --default-target-dir . --transport stdio
```

Registration verification passed. `claude mcp get aegis` reported:

- Scope: local project config
- Status: connected
- Command: `uvx`
- Source spec: `/tmp/aegis-task123-dist-clean/aegis_foundation-0.1.0-py3-none-any.whl`
- Environment: `UV_CACHE_DIR=.aegis/uv-cache`, `UV_TOOL_DIR=.aegis/uv-tools`

`aegis-mcp-server --describe-config` reported:

```json
{
  "asset_origin": "package",
  "default_target_dir": "/tmp/aegis-task123-hpfetcher-copy-5RKOic/hpfetcher",
  "distribution_name": "aegis-foundation",
  "foundation_version": "0.1.0",
  "installer_version": "0.1.0",
  "schema_version": "1.0.0"
}
```

## Headless Claude Live Workflow

Command shape:

```text
claude -p <Task 123 live prompt> --permission-mode auto --max-budget-usd 5
```

Outcome:

- Aegis MCP was available to Claude.
- Aegis installed into the copied existing project.
- Kickoff created branch `feat/task-42-brandmark-accessibility`.
- Readiness moved from `BLOCKED` before kickoff to `READY | task=42` after kickoff.
- Claude used native source editing for `app/src/components/BrandMark.tsx`.
- The source change added `role="img"` and `aria-label="HP-Coach"` to the outer BrandMark span.
- Verification command passed: `pnpm --dir app exec biome check src/components/BrandMark.tsx`.
- Strict verify passed: 27 checks, 0 required failures, 1 unsupported policy-only memory gate.
- `aegis.closeout_ready` passed, was read-only, and left pending tracking empty.
- `aegis.closeout --update-handoff` passed: 22/22 gates.

Final copied-project evidence:

- Source line reference: `/tmp/aegis-task123-hpfetcher-copy-5RKOic/hpfetcher/app/src/components/BrandMark.tsx:35`
- Active session: `sessions/2026/05/2026-05-25-001-task42-brandmark-accessibility.md`
- Active plan: `plans/2026-05-25-task42-brandmark-accessibility.md`
- Active work-tracking folder: `docs/ai/work-tracking/active/20260525-task42-brandmark-accessibility-ACTIVE/`
- Closeout report: `.aegis/reports/closeout-report.json`
- Pending tracking: absent at the end

## Existing Project Issue Found

The first live workflow passed mechanically but exposed a release-blocking existing-project usability issue: `hpfetcher` already had a project-specific `CLAUDE.md`. The old installer policy treated that file as unsafe manual-review, and the live Claude session resolved the blockage by moving the original file to backups before installing Aegis. That left Aegis' generated `CLAUDE.md` active and the HP-Coach project instructions displaced into `CLAUDE.md.orig` / `CLAUDE.md.bak`.

That is not acceptable for a reusable installer. Existing agent instructions must remain active.

## Fix Implemented

Aegis now handles an existing `CLAUDE.md` as a safe merge:

- Insert or update an Aegis-managed block delimited by:
  - `<!-- AEGIS:BEGIN claude-runtime -->`
  - `<!-- AEGIS:END claude-runtime -->`
- Preserve the original project instructions below `## Existing Project Instructions`.
- Classify the operation as `modify`, not `manual-review`.
- Keep `safe_to_apply: true`.
- Continue refusing unrelated unsafe conflicts, such as a conflicting `.aegis/foundation-manifest.json`.

Touched implementation files:

- `scripts/_aegis_installer.py`
- `aegis_foundation/assets/scripts/_aegis_installer.py`

Regression tests:

```text
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest \
  tests/meta_workflow_guard/test_aegis_installer.py \
  tests/meta_workflow_guard/test_aegis_mcp_server.py \
  tests/meta_workflow_guard/test_aegis_cross_project_smoke.py \
  tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py
```

Result:

```text
90 passed, 2 skipped
```

## Rebuilt Wheel With Merge Fix

New local artifact paths:

```text
/tmp/aegis-task123-dist-claude-merge/aegis_foundation-0.1.0.tar.gz
/tmp/aegis-task123-dist-claude-merge/aegis_foundation-0.1.0-py3-none-any.whl
```

SHA-256:

```text
edac489b74eeb8e63e9b01363b19c75425cb5279d7ffeb3ddf4feab53378433f  /tmp/aegis-task123-dist-claude-merge/aegis_foundation-0.1.0.tar.gz
aeebe3b63cabc6d47b59c4aee3bdd48524ffca67a68dc1f83c27c05b8aa8e4e8  /tmp/aegis-task123-dist-claude-merge/aegis_foundation-0.1.0-py3-none-any.whl
```

Artifact checks found no `__pycache__`, `.pyc`, or `.pyo` entries.

## Fresh hpfetcher Merge-Fix Validation

Using the rebuilt wheel against `/tmp/aegis-task123-hpfetcher-merge-copy-h37v0w/hpfetcher`:

- `aegis plan-install` reported `summary.creates=23`, `summary.modifies=1`, `summary.manual_reviews=0`.
- The `CLAUDE.md` operation was:
  - `action: modify`
  - `classification: modify`
  - `safe_to_apply: true`
  - reason: existing Claude instructions preserved below an Aegis-managed runtime block.
- `aegis install --apply` succeeded.
- `CLAUDE.md` now contains the Aegis runtime block at the top and the original HP-Coach instructions below `## Existing Project Instructions`.
- `aegis verify` passed standard install verification: 8 checks, 0 required failures, 1 unsupported policy-only memory gate.

## Remaining Work

The live Claude full workflow was first run against the pre-merge-fix wheel and surfaced the issue. The rebuilt wheel was then validated for install/merge behavior in a fresh hpfetcher copy.

## Final Rebuilt-Wheel Full Workflow

A final headless Claude workflow was run against the rebuilt wheel:

- Final copy: `/tmp/aegis-task123-hpfetcher-final-copy-6gDofR/hpfetcher`
- Registered wheel: `/tmp/aegis-task123-dist-claude-merge/aegis_foundation-0.1.0-py3-none-any.whl`
- Branch created by kickoff: `feat/task-42-brandmark-accessibility-final`
- Pre-kickoff readiness: `BLOCKED` because source branch `tier2-planen-block` did not contain a task ID
- Post-kickoff readiness: `READY | task=42`
- Active session: `sessions/2026/05/2026-05-25-001-task42-brandmark-accessibility-final.md`
- Active plan: `plans/2026-05-25-task42-brandmark-accessibility-final.md`
- Active work-tracking: `docs/ai/work-tracking/active/20260525-task42-brandmark-accessibility-final-ACTIVE/`
- Source changed: `app/src/components/BrandMark.tsx`
- Source line reference after change: `app/src/components/BrandMark.tsx:34`
- Task verification: `pnpm --dir app exec biome check src/components/BrandMark.tsx` passed with no fixes
- Strict verify: passed, 27 total checks, 0 required failures, 1 unsupported policy-only memory gate
- `aegis.closeout_ready`: passed, read-only, 22/22 gates, pending tracking empty
- `aegis.closeout --update-handoff`: passed, report written, state updated, handoff updated

Most important existing-project validation:

- Active `CLAUDE.md` contains `<!-- AEGIS:BEGIN claude-runtime -->` at line 1 and `<!-- AEGIS:END claude-runtime -->` at line 46.
- Original HP-Coach instructions remain active in the same `CLAUDE.md`, starting at line 58.
- No `CLAUDE.md.bak` file was created.
- No `CLAUDE.md.orig` file was created.

Task 123 acceptance implication: the final rebuilt wheel passed the global/native MCP registration path, install into an existing copied project, workflow kickoff, native source edit, tracking gates, strict verification, closeout readiness, and closeout while preserving existing project instructions.
