# Task 195 Aegis vNext Phase 0 replay harness – Handoff Summary

## Current State
- Replay harness live: every PR now runs the corpora through the real gate (the
  standing rule 'no gate change ships unreplayed' is now CI, not policy). FP baseline
  locked at 9; standing gaps exactly the two documented ones.

## Next Steps
- Push, PR, CI, owner merge approval.
- Next ungated Phase-0 tasks: #200 (MCP/CLI version handshake) then #197 (size
  budgets); #201 (break-glass) builds on this harness's fixtures.
- When any future policy change frees a historical FP or closes a gap, update the
  corpus locks IN THE SAME PR — the tests force it.
- Archived on 2026-06-11 00:15 CEST — Folder moved to archive and tracker marked COMPLETED.
