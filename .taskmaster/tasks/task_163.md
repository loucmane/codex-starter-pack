# Task ID: 163

**Title:** Update GitHub Actions for Node 24 runner transition

**Status:** done

**Dependencies:** None

**Priority:** medium

**Description:** Track the GitHub Actions Node 20 deprecation warning separately from shadow evidence work and verify CI artifacts still upload under Node 24-compatible action versions.

**Details:**

Scope: address the GitHub Actions warning observed on run 26967742927. The affected actions are actions/checkout@v4, actions/setup-node@v4, actions/setup-python@v5, and actions/upload-artifact@v4. GitHub indicates Node 24 becomes default on 2026-06-16 and Node 20 is removed on 2026-09-16. Update to Node-24-compatible action versions when available or set an explicit transition strategy. Acceptance criteria: CI remains green, shadow context proof, cascade validation, taskmaster toolchain, pytest, and reconcile-shadow-accumulation artifacts still upload intact, and the change remains orthogonal to apply or enablement behavior. Non-goals: no changes to shadow precision logic, no apply enablement, no Taskmaster status mutation, no evidence corpus changes.

**Test Strategy:**

No test strategy provided.
