# Task ID: 134

**Title:** Private GitHub Distribution and Cross-Machine Install Flow

**Status:** in-progress

**Dependencies:** 133 ✓

**Priority:** high

**Description:** Make the private GitHub repository install path first-class for Aegis so Claude and Codex can use the workflow across machines without PyPI or public package publication.

**Details:**

Implement and document a private GitHub based install and MCP registration path for Aegis. Keep PyPI and TestPyPI out of scope. Cover install from the private repository into a fresh tmp target and into a copied real project, preserving existing CLAUDE.md and AGENTS.md content. Provide exact commands for a new machine to install or register Aegis for Claude and Codex from the private repository source. Verify that MCP registration, aegis init, start or kickoff, log, strict verify, closeout, and doctor work from the private install source. Preserve current package and local source flows. Store all acceptance evidence under the task work-tracking reports folder, including transcripts or command logs for Claude and Codex where feasible. Do not mutate the real HPFetcher project directly; use tmp copies for real-project acceptance.

**Test Strategy:**

No test strategy provided.
