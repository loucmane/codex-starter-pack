# PR-2a scope — computed `aegis brief`

Binding contract: AEGIS_CAPSULE_SPEC.md sections 1.2 (row 2a), 3, 3.1 (computed
stratum), 3.2 (sentinel). NO injection (2b), NO narration (3).

## Deliverables

1. **`brief_lib.py`** in assets/.claude/scripts/ (stdlib-only, mirrored live, same
   dual-copy + parity-test convention): compile_capsule(root) producing the 8 computed
   fields, render_markdown (answer-shaped: branch? merged? tests? next? known reds? —
   every fact with as-of stamp + citation), and capsule file writing
   (.aegis/capsule/current.md + current.json, in-worktree per spec section 3).
2. **Computed fields** — all recomputed at read time; any revalidation failure renders
   STALE-recheck, never a cached value:
   - capsule_meta (version, compile ts, source_commit, ledger span, size chars)
   - repo_pose (branch, uncommitted tracked edits, untracked summary, ahead/behind
     best-effort)
   - delivery_state (ONE gh pr list with ~800ms timeout; on miss render STALE-recheck
     plus cached last-success from the out-of-worktree store with as-of stamp —
     network-derived fields are second-class by design)
   - verification_ledger (per package-x-gate from brief.json: last run exit_class +
     commit + ts; ABSENCE REPORTED EXPLICITLY as no-run-on-record; STALE flag when HEAD
     moved past the run's commit)
   - task_truth (parent counts by status, recent ledger flips,
     claimed-done-vs-shipped: done-flips visible in uncommitted tasks.json diff flag
     the stranded-#73 class)
   - governance (enforcement mode/set_by/reason + gate-decision tallies since last
     compile, watermark in the out-of-worktree store)
   - drift_sentinel (below)
   - repo_hygiene (branch count vs threshold, oversized unignored files, capped scan)
3. **Drift sentinel v1** — exactly 5 deterministic checks, no LLM, each producing
   attempted/parsed/drift accounting; claim-absent surfaces parse clean (no drift);
   claim-present-but-unparseable IS drift. Canary fixture at .aegis/capsule/canary.md
   (created at compile when missing; planted claim contradicts the checker constant)
   must ALWAYS flag — canary missing or unflagged renders the sentinel as broken,
   never silent zero-drift. Output: N attempted, M parsed, K drift items.
4. **risk-seed consumption**: .aegis/capsule/risk-seed.json read once at first compile
   into the capsule json's risk_register (data only — the narrated machinery is PR-3);
   consumed marker in the out-of-worktree store.
5. **CLI**: `aegis brief` (compile + print markdown) and `aegis brief --check`
   (offline strict validation: char budget 8000 + canary + parse counters — the ONLY
   mode where over-budget fails). Read-only gate classification for both.

## Merge gate (spec 1.2 row 2a)
Brief output matches independently-checked reality in this repo (codex is the live
deployment until HP-Coach runs its upgrade).

## Out of scope
SessionStart injection, char-budget degradation ordering at injection time, falsifier
stamping (all 2b); narrated stratum and TTLs (3).
