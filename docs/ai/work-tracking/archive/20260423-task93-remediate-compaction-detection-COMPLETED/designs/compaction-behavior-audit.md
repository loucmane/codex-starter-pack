# Task 93 Compaction Behavior Audit

## Purpose

Task 93 exists because the compaction flow still has stale behavior text that can cause an agent to confuse context compaction with session ending. The corrected system distinction is:

- **Compaction**: save checkpoint state, keep the session active, and provide exact resume instructions.
- **Session end**: close the day's/task's work, update handoff/tracker, and provide commit guidance.

## Files Reviewed

- `templates/behaviors/session/compaction-detection.md`
- `templates/behaviors/session/compaction-preparation.md`
- `templates/behaviors/session/session-end.md`
- `templates/handlers/triggers/session/prepare-compaction.md`
- `templates/workflows/session/compaction.md`
- `templates/BEHAVIORS.md`
- `templates/behaviors/index.md`
- `scripts/codex-guard`
- `tests/meta_workflow_guard/test_guard_rules.py`

## Findings

1. `templates/behaviors/session/compaction-detection.md` is marked deprecated but still contains a full blocking session-end checklist and a full `gac "..."` output format. This preserves the exact ambiguity Task 93 is meant to remove.
2. `templates/behaviors/session/compaction-preparation.md` correctly says compaction does not end the session, does not archive anything, does not create handoff documents, and does not generate commit messages.
3. `templates/handlers/triggers/session/prepare-compaction.md` aligns with the corrected distinction: checkpoint current work, update current session, create checkpoint memory, and emit a continuation message only.
4. `templates/workflows/session/compaction.md` mostly aligns with checkpoint/resume behavior, but its example text still says "ready for new context" without clearly requiring the current session to remain active.
5. `templates/BEHAVIORS.md` still has an aggregate section titled "Detecting Session End / Compaction Need" that combines end-session and compaction triggers into one flow with required initialization and GAC messages.
6. `templates/behaviors/index.md` already treats `compaction-detection.md` as deprecated, which supports retiring it as an executable behavior source instead of rewriting it as another active path.
7. `scripts/codex-guard` still includes `templates/behaviors/session/compaction-detection.md` in `GAC_SUMMARY_DOCS`, so the guard currently preserves the deprecated file as a GAC-bearing canonical source.

## Decision

Retire `compaction-detection.md` as executable behavior. Keep a minimal tombstone/redirect only if needed for link compatibility, and remove it from guard expectations that treat it as canonical GAC guidance.

The active compaction protocol should live in:

- `templates/behaviors/session/compaction-preparation.md`
- `templates/handlers/triggers/session/prepare-compaction.md`
- `templates/workflows/session/compaction.md`

The active session-end protocol should live in:

- `templates/behaviors/session/session-end.md`
- `templates/handlers/triggers/session/end-session.md`

## Implementation Implications

- Replace the deprecated long behavior body with a short tombstone that points to the active compaction/session-end sources.
- Update `templates/BEHAVIORS.md` so compaction and session ending are separate sections.
- Update `scripts/codex-guard` so GAC summary enforcement does not keep the deprecated compaction detection file alive as a canonical source.
- Add or update guard tests to make the retired behavior explicit and prevent reintroducing combined compaction/session-end guidance.
