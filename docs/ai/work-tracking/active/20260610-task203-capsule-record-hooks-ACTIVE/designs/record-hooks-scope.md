# PR-1b scope — async record hooks

Binding contract: `docs/aegis/AEGIS_CAPSULE_SPEC.md` §1.1, §1.2 (row 1b), §2. Builds on
the PR-1a ledger core (task 202, merged as 3b45955).

## Deliverables (the five §1.1 touchpoints, named)

1. **Settings renderer** (`_render_claude_settings()` in `scripts/_aegis_installer.py`,
   both copies): NEW parallel hook entries — `PostToolUse` + `PostToolUseFailure` →
   `ledger-record.sh`, rendered **exec-form** (`command` + `args`, ≥2.1.139 pattern, new
   for the installer) with `async: true` so recording can never block or slow a tool
   call. Existing synchronous entries (pretooluse-gate, posttooluse-tracking,
   tracking-stop-gate) are UNTOUCHED — retirement is PR-4.
2. **New bootstrap script** `assets/.claude/scripts/ledger-record.sh` following the
   existing asset pattern (exec `python3 "$SCRIPT_DIR/gate_lib.py" record`).
3. **`aegis hook` dispatcher** (`aegis_foundation/cli.py` choices tuple): add
   `record`, `posttoolusefailure`, `sessionstart`, `sessionend`.
4. **`gate_lib.py` main() routing** (both copies): new `record` command → a recorder
   entry that parses the hook payload from stdin, classifies it, and appends to the
   ledger via `ledger_lib` (importlib from the script's own directory). One command for
   all record events: the payload's `hook_event_name` disambiguates
   PostToolUse/PostToolUseFailure. **The recorder always exits 0** — on any error it
   degrades silently (optional error breadcrumb in the store dir), never crashes, never
   blocks.
5. **Foundation manifest**: `ledger_lib.py` and `ledger-record.sh` enter managed_files
   with hashes (this is the moment ledger_lib starts propagating to targets).

## Event capture (basic events only, spec §2)

Fields: ts, session_id, cwd, branch (git -C cwd, best effort), tool_name, normalized
target paths (reuse gate_lib payload helpers), outcome class (PostToolUse=pass,
PostToolUseFailure=fail, tool_response.interrupted=interrupted, else unknown),
duration_ms, agent_id/agent_type when present. Classification at record time:
- `delivery` — Bash command matching git push / gh pr create / gh pr merge (+ branch→PR
  mapping detail in `extra`),
- `task_truth` — writes to `.taskmaster/tasks/tasks.json` or `task-master` commands,
- `tool_failure` — PostToolUseFailure events,
- `mutation` — everything else (an `extra.is_mutation` flag carries gate_lib's
  classification; read-only calls are still recorded — it is a flight recorder).
Command text is recorded under `extra.command` and passes through ledger_lib's
capture-time redaction.

## Payload reality check (prerequisite, spec §2)

Before building against docs: capture REAL hook payload fixtures from a live Claude
Code session via a temporary `.claude/settings.local.json` capture hook; commit
sanitized fixtures under `tests/fixtures/hook_payloads/`. Tests prove documented fields
(session_id, cwd, agent_id, agent_type, duration_ms, transcript_path) against fixtures
and that the recorder degrades gracefully (missing field → null). Events not capturable
mid-session (SessionStart/SessionEnd) are documented as gaps and filled when first
available; the recorder treats every field as optional regardless.

## Hygiene rider (installer-owned, spec §2)

Install/upgrade verifies `.gitignore` coverage for `.aegis/` output paths in the target
and warns when Aegis-generated files exceed a size threshold unignored (the 36 MB
observation-report incident class). Warnings surface in plan-install/install payloads.

## Out of scope

Gate-decisions dual-write (1c), gate registry/brief.json/scope records (1d), any
SessionStart injection (2b), narration checkpoints (3), retirement of the synchronous
tracking hooks (4). No HP-Coach deployment from this repo: the live acceptance
("events appear, nothing blocks") requires `aegis plan-install` + `aegis install
--apply` in the target repo and runs there after merge.

## Merge gate (spec §1.2 row 1b)

Codex-side: unit/fixture tests green; renderer/dispatcher/manifest tests updated.
Live acceptance slice happens in HP-Coach post-merge.
