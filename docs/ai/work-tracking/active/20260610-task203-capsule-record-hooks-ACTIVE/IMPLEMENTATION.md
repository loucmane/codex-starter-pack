# Task 203 Capsule PR-1b: async record hooks – Implementation Notes

## Planned Workstreams
1. Payload reality check — real hook fixtures captured. DONE.
2. Five touchpoints — recorder wired end to end. DONE.
3. Hygiene rider — gitignore coverage + oversized-file warnings. DONE.

## What was built

- **Payload fixtures** (`tests/fixtures/hook_payloads/*.jsonl`): REAL payloads captured
  from live headless Claude Code sessions in a scratch project (capture hooks in that
  project's settings; no self-modification of this repo's runtime config). Covers
  PostToolUse (Bash/Write/Edit + a subagent-context event with agent_id/agent_type),
  PostToolUseFailure (error field), PreToolUse, SessionStart (source), SessionEnd
  (reason), Stop, SubagentStop (agent_transcript_path), UserPromptSubmit.
- **Recorder** (`gate_lib.py` `record` command, both copies): parses any hook payload
  from stdin, classifies (delivery → git push / gh pr create|merge|ready; task_truth →
  task-master mutations or tasks.json writes; tool_failure; session_begin/session_end;
  mutation default with extra.is_mutation carrying gate classification), resolves
  branch best-effort, reuses gate_lib path/handler/digest helpers, appends via
  ledger_lib (importlib from script dir). ALWAYS exits 0 — every error path degrades
  silently; verified against garbage stdin, no-git cwd, and missing ledger_lib.
- **Bootstrap script** `.claude/scripts/ledger-record.sh` (live + assets) following the
  existing asset pattern; installed targets get the rendered dispatcher (`aegis hook
  record` with gate_lib fallback) via CLAUDE_RUNTIME_HOOK_PHASES.
- **Settings renderer**: parallel async PostToolUse entry + new PostToolUseFailure
  entry. SHELL-FORM, not exec-form — live probe showed $CLAUDE_PROJECT_DIR is not
  expanded in exec-form args on CLI 2.1.170 (the hook silently never fires); async is
  the load-bearing property. Live `.claude/settings.json` mirrors the rendered entries.
- **Dispatcher**: `aegis hook` choices += record, posttoolusefailure, sessionstart,
  sessionend (the latter three route to the recorder; payload hook_event_name
  disambiguates).
- **Manifest**: ledger_lib.py joins CLAUDE_SUPPORT_FILES and ledger-record.sh joins
  CLAUDE_REQUIRED_FILES — both now propagate to targets with hashes on install/upgrade.
- **Hygiene rider**: `gitignore_hygiene_report()` (warn-only) — .gitignore coverage of
  .aegis output prefixes + unignored Aegis files over 5 MB — surfaced in the install
  report and runtime_update payloads.
- **Live acceptance (codex as first deployment)**: real events in the repo's store from
  BOTH this running session (settings hot-reload picked up the shell-form entry) and a
  fresh headless session. Nothing blocked; the recorder is invisible to the session.

## Boundary notes

Gate-decisions dual-write is PR-1c; gate registry/brief.json/scope records are PR-1d;
synchronous tracking hooks remain untouched until PR-4. HP-Coach rollout requires the
plan-install + install --apply upgrade run there (spec section 1.1).
