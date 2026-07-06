# Task ID: 220

**Title:** Closeout populate step for path-lost evidence sub-mode

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Resolution: no additional implementation is needed for this task. The path-lost closeout populate sub-mode was subsumed by Task 217 and shipped in PR #241 / commit c5cc544 (`fix: populate closeout evidence from logged plan rows`). Current production code already includes the bounded closeout surface populate path in `scripts/_aegis_installer.py` and the packaged asset mirror `aegis_foundation/assets/scripts/_aegis_installer.py`. Preserve this task as closed-by-existing-implementation evidence rather than adding duplicate code.

**Details:**

Codebase verification found `_populate_closeout_surfaces` in `scripts/_aegis_installer.py`. The function back-fills closeout-owned progress lines from already-logged plan evidence using existing S:W:H:E entries, updates only closeout evidence surfaces (`session`, `tracker`, `implementation`, `changelog`) plus deterministic handoff repair, and preserves dry-run read-only behavior through `would_update_surfaces`. The closeout flow invokes this populate step only when pending tracking is empty and strict verification has passed, preserving the invariant that `strict_verify` and `pending_tracking` independently gate final closeout. The same `_populate_closeout_surfaces` implementation is present in the packaged runtime asset at `aegis_foundation/assets/scripts/_aegis_installer.py`, so installed targets receive the shipped behavior. The exact path-lost regression exists at `tests/meta_workflow_guard/test_aegis_installer.py::test_closeout_populates_path_lost_plan_evidence_before_final_closeout`: it removes implementation evidence from session/tracker while leaving it in implementation/changelog, asserts dry-run reports session/tracker population without mutating files, then asserts normal closeout passes and records updated session/tracker surfaces. No new code should be added under Task 220; future work should only adjust this area if the existing Task 217/PR #241 implementation regresses.

**Test Strategy:**

Verified with `pytest -q tests/meta_workflow_guard/test_aegis_installer.py::test_closeout_populates_path_lost_plan_evidence_before_final_closeout`; result: 1 passed. Keep this regression as the acceptance test for Task 220's path-lost sub-mode coverage, along with source/packaged asset parity for `_populate_closeout_surfaces`.
