# Task ID: 225

**Title:** Surface doctor safe-repair vs manual-review states in aegis next

**Status:** done

**Dependencies:** 189 ✓

**Priority:** high

**Description:** Residual #2 of TM 189: surface the doctor-derived safe-repair vs manual-review-repair classification as distinct next_action states, each with a continuation brief, so a bare "continue" routes a repairable workflow to the correct (and correctly-gated) repair path.

**Details:**

next_action does not currently emit repair-oriented states; the safe vs manual_review classification lives in doctor's repair_plan (_doctor_repair_actions). When the installed workflow is in a repairable state, next_action should detect it and emit a safe_repair_available state (continue_means: review the repair plan, then run aegis repair --apply for safe actions) vs a manual_review_repair state (continue_means: surface the plan; manual-review actions need explicit human decision, never auto-applied). Add CONTINUATION_BRIEF_BY_STATE entries for both (manual_review_repair confirmation-gated). Mirror assets installer; add tests asserting the states + briefs, that safe-repair stays apply-gated and manual-review never auto-applies.

**Test Strategy:**

No test strategy provided.
