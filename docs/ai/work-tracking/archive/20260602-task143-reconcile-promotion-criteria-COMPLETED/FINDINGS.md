# Findings

- 2026-06-02 — Squash-shaped no-GitHub history correctly stayed clean; reconcile left merge truth unknown instead of creating false certainty.
- 2026-06-02 — Git ancestry proof produced a high-confidence `merged_but_not_done` drift finding in the mixed-drift fixture.
- 2026-06-02 — GitHub-style PR metadata produced a high-confidence `done_but_not_merged` drift finding in the mixed-drift fixture.
- 2026-06-02 — Ambiguity/stub-heavy fixture produced warning-only manual-review findings and no error-severity drift.
- 2026-06-02 — All fixture before/after status diffs were empty; reconcile remained read-only on the target histories.
