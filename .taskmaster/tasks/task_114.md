# Task ID: 114

**Title:** Aegis MCP Release Candidate Validation

**Status:** done

**Dependencies:** 113 ✓

**Priority:** high

**Description:** Validate the packaged Aegis CLI and MCP server as a release candidate from clean external projects, proving install, startup, discovery, inspect, plan, install, verify, and documentation paths without relying on repository-local execution.

**Details:**

Scope:
- Build wheel/sdist from main and treat the artifacts as release candidates.
- Install the candidate into clean temporary projects using local artifact paths and documented uvx/pipx-style commands.
- Start aegis-mcp-server from the installed artifact outside the repository and verify MCP tools, resources, and prompts are discoverable.
- Use the installed MCP/CLI surfaces to inspect, plan-install, install, status, and verify Aegis in clean target repositories.
- Produce user-facing setup instructions for Codex, Claude, and generic MCP clients.
- Decide and document the first release channel: GitHub artifact, TestPyPI, PyPI, or git/uvx source install.
- Capture all evidence under the task work-tracking reports folder and leave clear release blockers if any remain.
Acceptance:
- Clean-project CLI smoke passes from an installed artifact.
- Clean-project MCP stdio smoke passes from an installed artifact.
- Cross-agent MCP setup docs are explicit and tested where practical.
- Guard, taskmaster health, work-tracking audit, plan sync, and diff-check pass.
- Task ends with a concrete go/no-go for public MCP release readiness.

**Test Strategy:**

No test strategy provided.

## Subtasks

### 114.1. Define release-candidate scope and test matrix

**Status:** done  
**Dependencies:** None  

Document the release-candidate boundary, first release-channel options, clean-project target matrix, and go/no-go criteria before building artifacts.

### 114.2. Build and inspect local release-candidate artifacts

**Status:** done  
**Dependencies:** None  

Build wheel and sdist from the task branch, inspect metadata/package data/entry points, and store artifact evidence as release-candidate baseline.

### 114.3. Verify clean-project CLI install and workflow smoke

**Status:** done  
**Dependencies:** None  

Install the release-candidate artifact into clean external target projects and prove aegis inspect, plan-install, install, status, and verify work without repository-local paths.

### 114.4. Verify clean-project MCP stdio startup and discovery

**Status:** done  
**Dependencies:** None  

Start aegis-mcp-server from an installed release-candidate artifact outside the repo, verify tools/resources/prompts discovery, and call inspect/plan/status paths through MCP.

### 114.5. Document cross-agent MCP setup and release-channel decision

**Status:** done  
**Dependencies:** None  

Write Codex, Claude, and generic MCP setup guidance for the installed server, document the chosen first release channel, and list any blockers before public release.

### 114.6. Finalize release-candidate evidence and handoff

**Status:** done  
**Dependencies:** None  

Run final regression, plan sync, Taskmaster health, work-tracking audit, guard, and diff-check; update tracker/handoff with a concrete go/no-go for public MCP release readiness.
