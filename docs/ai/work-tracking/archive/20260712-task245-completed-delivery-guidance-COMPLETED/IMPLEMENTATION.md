# Task 245 Recognize Completed Delivery Before Historical Branch Mismatch – Implementation Notes

## Planned Workstreams
- Add a secret-free Blog Task 67/Task 38 replay fixture with exact PR and closeout identities.
- Bind closeout report truth to the current work envelope using the existing shared predicate.
- Add deterministic local delivery proof for PR base, merge-commit ancestry, upstream identity, and ahead/behind counts.
- Evaluate proven merged completion before branch-mismatch guidance; preserve all same-branch states.
- Keep source and packaged installer assets byte-identical and verify installed-target non-regressions.

## Implemented
- `_closeout_passed` now accepts the current-work envelope and treats a persisted passed report as current only when `_closeout_report_matches_current_work` confirms task and work-tracking identity. The existing per-envelope `closeout_passed_at` compatibility path remains available when no report exists.
- `_post_closeout_delivery_guidance` now checks the recorded branch's merged PR before returning historical branch-mismatch guidance. It emits `merged_complete` only when the current branch is the PR base, the configured upstream matches that base, the merge commit is an ancestor of `HEAD`, and `HEAD...@{u}` is exactly `0 0`.
- Existing GitHub PR projections now request `mergeCommit`; no second GitHub mechanism or mutation path was introduced.
- `tests/fixtures/aegis/blog-task67-completed-delivery.json` preserves the redacted Task 67 merged-main incident and the subsequent Task 38 stale-report state.
- Focused regressions cover the positive Task 67 replay, missing/non-ancestor/behind merge proof, unavailable GitHub, report identity mismatch, and the Task 38 stale-report negative.

## Live Canary
- The updated source API evaluated `/home/loucmane/dev/blog` as `authority=taskmaster:38`, `phase=closeout`, `state=closeout_required` without changing that repository. This is the expected active-task result and confirms that the retained Task 67 closeout report no longer controls Task 38.
