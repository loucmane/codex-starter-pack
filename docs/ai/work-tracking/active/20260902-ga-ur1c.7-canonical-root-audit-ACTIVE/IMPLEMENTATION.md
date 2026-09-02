# Bead ga-ur1c.7 Detect and reconcile stale canonical project roots – Implementation Notes

## Planned Workstreams
- `continuity_capture.py` now captures exact canonical root path, HEAD, branch/detached state, local target ref/head, ahead/behind counts, and tracked cleanliness without fetching or writing.
- `continuity_model.py` validates the record and blocks unresolved bases or stale/ahead target branches. Deliberate non-base branches and dirty roots produce one warning each.
- `continuity-snapshot.schema.json` binds the new canonical record and keeps its shape closed.
- Tests include the original missed-state RED/GREEN classifier proof and a real temporary Git repository proving offline local-ref collection.
- The plugin README documents the blocking/warning boundary and the no-network/no-mutation contract.

## Verification
- Focused continuity suite: `44 passed`.
- Full `tests/meta_workflow_guard`: `1559 passed, 21 skipped`.
- Ruff: PASS.
- Codex plugin validation: PASS.
- `git diff --check`: PASS.
