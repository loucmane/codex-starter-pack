# Task ID: 165

**Title:** Fail-close live apply semantic validation

**Status:** pending

**Dependencies:** 164 ✓

**Priority:** high

**Description:** Close A7 by making live apply semantic-delta validation fail closed instead of defaulting missing semantic evidence to allowed.

**Details:**

Scope: update the default-off live apply runtime so semantic_delta_matches_prediction must be present and true. Missing, None, or absent semantic validation result must refuse. Confirm the path-delta fallback still relies only on required validation attributes and does not introduce another default-true security gate. Non-goals: no apply enablement, no new apply surface, no candidate-class broadening, no governed-repo Taskmaster mutation.

**Test Strategy:**

No test strategy provided.
