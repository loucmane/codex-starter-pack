# Task ID: 109

**Title:** Build Portable Foundation Installer and MCP Distribution Contract

**Status:** in-progress

**Dependencies:** 100 ✓, 102 ✓, 107 ✓

**Priority:** high

**Description:** Create the next tracked phase for turning the completed Codex starter-pack foundation into a reusable system that can be installed, verified, updated, and optionally exposed through MCP across new and existing projects.

**Details:**

Document and implement a CLI/library-first foundation installer with an optional MCP wrapper. The design must cover inspect, plan-install, install, verify, update, rollback, project profiles, managed-file manifest, fixture-based testing, idempotence checks, rollback checks, MCP protocol resources/tools/prompts, and cross-agent smoke tests. Capture alternatives considered: MCP-only installer, template-repo copy, package-only distribution, git submodule/subtree, and CLI core plus optional MCP wrapper. Acceptance: session/plan/work-tracking are scaffolded; architecture decision is documented; Taskmaster subtasks align to implementation phases; guard, taskmaster health, work-tracking audit, and diff-check pass.

**Test Strategy:**

No test strategy provided.

## Subtasks

### 109.1. Document installer architecture and distribution decision

**Status:** done  
**Dependencies:** None  

Capture the CLI/library core plus optional MCP wrapper architecture, alternatives considered, chosen decision, risks, and acceptance gates in tracked design documentation.

### 109.2. Define foundation manifest, profiles, and install-plan schema

**Status:** pending  
**Dependencies:** None  

Specify versioned foundation manifest fields, managed-file/customized-file tracking, project profile selection, install-plan structure, conflict classes, and dry-run/apply semantics.

### 109.3. Design CLI installer lifecycle and verification commands

**Status:** pending  
**Dependencies:** None  

Define deterministic library and CLI commands for inspect, plan-install, install, verify, plan-update, update, rollback, status, and report generation, including refusal/rollback behavior.

### 109.4. Specify fixture, idempotence, rollback, and cross-agent tests

**Status:** pending  
**Dependencies:** None  

Define fixture repo matrix, golden install-plan tests, install twice/idempotence checks, rollback failure tests, guard/readiness verification, and Codex/Claude smoke-test evidence requirements.

### 109.5. Define MCP wrapper contract and evidence handoff

**Status:** pending  
**Dependencies:** None  

Define MCP tools, resources, prompts, schemas, read-only versus mutating behavior, apply gates, relation to CLI core, documentation locations, evidence files, and handoff criteria.
