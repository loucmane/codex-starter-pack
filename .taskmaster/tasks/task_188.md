# Task ID: 188

**Title:** Install cross-agent natural continuation contract

**Status:** pending

**Dependencies:** 187 ✓

**Priority:** high

**Description:** Make short user intents such as continue, go, proceed, finish this, and next work consistently across Aegis-installed projects and supported agents.

**Details:**

Add a reusable continuation-contract template to the Aegis installed guidance for Claude, Codex, and generic agent surfaces. Define what short continuation intents authorize, how agents must consult aegis doctor and aegis next, how Taskmaster remains authority when present, which actions can proceed autonomously, which boundaries require confirmation, and which actions are never allowed automatically. Ensure installed instructions are project-agnostic and do not depend on HP-Coach-specific paths. Add installer tests proving fresh Aegis installs include the contract in the relevant agent guidance files.

**Test Strategy:**

No test strategy provided.
