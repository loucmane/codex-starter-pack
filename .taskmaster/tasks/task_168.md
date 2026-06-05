# Task ID: 168

**Title:** Migrate GitHub Actions majors with artifact layout proof

**Status:** pending

**Dependencies:** 167

**Priority:** medium

**Description:** Replace the temporary Node 24 JavaScript-actions runtime force path with compatible action major versions, while proving shadow evidence artifact transport/layout remains unchanged.

**Details:**

Scope: update GitHub Actions action versions away from the temporary FORCE_JAVASCRIPT_ACTIONS_TO_NODE24 dependency when compatible majors are selected. Preserve Taskmaster runtime Node 22. Preserve permissions: contents read. Verify downloaded artifact internal layout, especially /aegis-shadow precision and accumulation artifacts, before/after migration. Confirm JSON record_type/classification/schema fields are unchanged. Non-goals: no shadow/apply Python logic changes, no toolchain pin changes, no apply enablement, no candidate-class broadening.

**Test Strategy:**

No test strategy provided.
