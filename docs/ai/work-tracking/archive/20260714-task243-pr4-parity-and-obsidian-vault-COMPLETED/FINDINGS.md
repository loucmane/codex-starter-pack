# Findings

- 2026-07-14 — Cross-repository dogfood proves deterministic derived views while quantifying
  substantial unique human narrative that must remain preserved.

## 2026-07-14 — Source legacy corpus exceeds the provisional ceiling

- First real-ledger build failed closed before writing output because the source repository has
  2,175 eligible preserved legacy Markdown documents, above the provisional 2,000 limit.
- This was legitimate historical/evidence content, not recursive vault output or an unbounded
  dependency directory.
- Raised the explicit ceiling to 5,000. Per-file byte limits, high-signal event limits,
  out-of-repository enforcement, exact ownership checks, and atomic replacement remain unchanged.
- Blog (214 documents in the current audit snapshot) and HP-Fetcher (33) remain far below the
  limit; the source repository is the controlling fixture.

## 2026-07-14 — Sandboxed WAL metadata fallback silently erased fields

- A read-only SQLite connection could open the ledger database but could not access or create its
  WAL shared-memory sidecar in the sandbox.
- The reader built a `SELECT NULL AS ...` projection from an empty first metadata probe, then
  reopened immutably too late. Row counts looked real while every selected field was null.
- The reader now reopens immutably and resolves columns before constructing the query. If metadata
  remains unavailable, it raises rather than returning plausible but empty evidence.
- The focused regression preserves witness event ID, type, and outcome through the simulated
  fallback; live and packaged assets are byte-identical.

## 2026-07-14 — Human legacy content is materially unique

- Excluding generated marker blocks, the source, Blog, and HP-Fetcher retain 72,963, 8,114, and
  3,948 human-authored nonblank lines.
- The source alone has 15,024 plan lines, 11,061 session lines, and 7,459 tracker lines, compared
  with 204 high-signal projected ledger events.
- This is evidence of different semantic roles, not unexplained replacement debt.

## 2026-07-14 — Primary capsule is stale at the stopping checkpoint

- The preserved untracked source capsule was last compiled on `chore/task-252-definition` and
  suggests `start_task_210`.
- Current Task 243 evidence makes Task 210 no-go. Rewriting the owner's local capsule would violate
  the drift-preservation boundary, so the audit records the contradiction for a supported compile
  after merge.

## 2026-07-14 — Downstream managed runtime provenance lags source

- Blog records source commit `144bd4463dcec9c326b023ff53b45aa71660727e`; HP-Fetcher records
  `43e9a660c0b58f95c2f97031e16830443b40aa2e`; source main is `89e582a5` at audit time.
- Both point to source-root mode, but installed assets and recorded update provenance still require
  a repository-local preview and safe checkpoint.
- No downstream update was attempted because Blog has active managed rollout drift and HP-Fetcher
  preserves its own task and product changes.
