# PR-2b scope — SessionStart injection

Binding contract: AEGIS_CAPSULE_SPEC.md sections 1.2 (row 2b), 3, 3.3, 3.4. First
user-visible capsule.

## Deliverables
1. **render_injection** in brief_lib: char-budgeted render (8000 budget; 10k hook hard
   cap) that NEVER fails at injection time — over budget it degrades in the decided
   order (repo_hygiene -> risk_register oldest-first -> drift items beyond top-3) and
   never drops repo_pose, delivery_state, verification_ledger, task_truth. Narrated
   fields (suggested_next, decisions_made, last_session_story, open_loops,
   decisions_pending_owner) do not exist until PR-3; the degradation table covers them
   by construction when they arrive. Reports what was dropped.
2. **SessionStart wiring**: gate_lib `sessionstart` phase extended — it already records
   the session_begin event (PR-1b); now it stamps the falsifier flag
   (capsule_injected on/off from AEGIS_CAPSULE env or brief.json inject) in that
   event's extra, and when ON prints the injected capsule to stdout (SessionStart
   stdout enters model context; synchronous on purpose). The injected wrapper carries
   the section 3.4 provenance label for future narrated content.
3. **Bootstrap script** .claude/scripts/session-brief.sh (live + assets) +
   CLAUDE_REQUIRED_FILES + phase map entry (rendered dispatcher) + settings renderer
   SessionStart entry with matcher startup|resume|clear|compact (synchronous, NOT
   async). Live .claude/settings.json mirrors it — next session in this repo is the
   dogfood.
4. Off-switch honored everywhere: AEGIS_CAPSULE=off env wins, then brief.json
   {"inject": false}; the stamp records the flag either way (A/B mechanism substrate).

## Out of scope
Narration/distill (3); witness (3.5); UserPromptSubmit fallback (documented, deferred
with the non-hook-agent file fallback already satisfied by .aegis/capsule/current.md).

## Merge gate (spec 1.2 row 2b)
Acceptance section 8 items 1-4 and 6 — codex-side: tests for stamp/inject/degrade/caps
+ live injection at the next session start in this repo.
