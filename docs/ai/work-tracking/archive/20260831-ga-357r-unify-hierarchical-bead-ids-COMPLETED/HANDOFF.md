# Bead ga-357r Unify hierarchical Bead IDs across readiness and evidence surfaces – Handoff Summary

## Current State
- Implementation and verification complete.
- Real Claude readiness accepts native hierarchical Bead identity `ga-ur1c.1`.
- Live/package witness and `codex-task` copies are byte-identical.
- Seven focused tests, 394 affected regressions, and the complete 2372-test repository suite pass; 21 skips are pre-existing documented optional/Taskmaster-dependent cases.

## Next Steps
- Publish the exact signed head under the standing CI and merge gates.
- Finish and archive this repair transaction.
- Recover the preserved `ga-ur1c.1` transaction and verify it reaches READY without recreation.

## Publication
- PR #331 merged exact signed head `ea96ba9aecf6ca686128d1618d78472934fd0fb9` into exact base `c6b6d2c158673004be5da731aafde66e1fac4150` as `9e73529a5690ad7e45f0cb5596dfc5c1b3d8c153`.
- Merge tree `73f1cac83a6ce7f13588fc605adc1dcb6a2c6d3a` is byte-identical to the reviewed candidate; GitHub signature valid; required CI green; CLEAN/MERGEABLE; zero unresolved review threads.
- Archived on 2026-08-31 12:27 CEST — Folder moved to archive and tracker marked COMPLETED.
