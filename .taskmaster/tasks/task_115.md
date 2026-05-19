# Task ID: 115

**Title:** Aegis MCP End-to-End Target Project Validation

**Status:** done

**Dependencies:** 114 ✓

**Priority:** high

**Description:** Validate the packaged Aegis MCP server against representative local target projects before public release artifacts. Generate throwaway empty, Python, web, backend, docs-heavy, partial-install, and conflict targets; exercise MCP inspect, plan, install, verify, resources, and prompt discovery from an installed local wheel; and record whether the MCP is ready for GitHub release-candidate artifact publication.

**Details:**

Create generated target-project fixtures rather than permanent demo apps. Run the MCP from packaged artifacts where possible and keep source-checkout shortcuts explicit. Prove safe behavior for new projects, existing projects, partial Aegis installs, and conflict/manual-review cases. Store evidence under Task 115 work tracking and update docs or tests only where needed.

**Test Strategy:**

No test strategy provided.

## Subtasks

### 115.1. Define MCP E2E target matrix and fixture strategy

**Status:** done
**Dependencies:** None

Define the representative target-project shapes, MCP operations, safety expectations, evidence paths, and go/no-go criteria for local end-to-end validation.

**Details:**

Cover empty, Python app, web app, backend server, docs-heavy project, partial Aegis install, and conflict/manual-review targets. Prefer generated throwaway fixtures in pytest tmp_path over checked-in demo applications.

### 115.2. Build generated target-project fixtures

**Status:** done
**Dependencies:** None

Implement generated local target fixtures for empty, Python, web, backend, docs-heavy, partial-install, and conflict project shapes.

**Details:**

Use pytest tmp_path factory helpers. Fixtures should include enough realistic files to test safe Aegis planning without committing full demo apps to the repository.

### 115.3. Validate MCP install flow for new and Python targets

**Status:** done
**Dependencies:** None

Exercise MCP inspect, plan_install, install, verify, status, and resources against empty and Python target projects from packaged local artifacts.

**Details:**

Assert .aegis reports, manifest, contract, managed files, and verification resources are created and readable. Ensure inspect/status/plan remain read-only and install/verify require explicit acknowledgements.

### 115.4. Validate MCP install flow for web, backend, and docs-heavy targets

**Status:** done
**Dependencies:** None

Exercise the same MCP E2E install and verification flow against representative web app, backend API, and docs-heavy existing projects.

**Details:**

Confirm Aegis preserves unrelated project files, handles existing docs/source directories safely, and reports installed runtime state consistently across project shapes.

### 115.5. Validate partial-install and conflict safety paths

**Status:** done
**Dependencies:** None

Prove MCP behavior for partial Aegis installs and target-file conflicts, including structured refusal or manual-review outcomes.

**Details:**

Seed partial .aegis state and conflicting managed files. Assert plan/install do not blindly overwrite unrelated or conflicting content and that structured errors/resources make the safety state clear.

### 115.6. Finalize evidence, docs, and release-readiness decision

**Status:** done
**Dependencies:** None

Capture local MCP E2E evidence, update work tracking and any release docs needed, and decide whether the MCP is ready for GitHub release-candidate artifact publication.

**Details:**

Run focused MCP E2E tests, relevant package/server regressions, guard, audit, plan sync, and diff check. Record readiness decision and remaining risks in Task 115 handoff.

### 115.7. Validate real local target projects through packaged MCP flow

**Status:** done
**Dependencies:** None

Add a second validation layer that creates concrete local Python, web, and backend target projects in temporary directories, including new and already-started variants, then exercises the packaged MCP inspect/plan/install/verify flow and records evidence that existing project files remain unchanged.

### 115.8. Prove or implement installed-project READY kickoff path

**Status:** done
**Dependencies:** None

Validate the positive path after Aegis installation: from inside a newly installed target project, create or invoke the project-local workflow state needed for Claude readiness, including task branch, Taskmaster or lightweight task state, sessions/current, plans/current, active work-tracking folder, and tracker/plan alignment. If the path does not exist, implement or explicitly block release readiness until it does.

### 115.9. Make Aegis kickoff scaffold the full portable workflow

**Status:** done
**Dependencies:** None

Replace the thin installed-project kickoff output with packaged workflow templates that create session, plan, work-tracking, current pointers, state, reports, and audit docs comparable to this repository's operating model.

**Details:**

Use templates/aegis/workflow as source and package the same templates into aegis_foundation/assets. Update CLI/MCP kickoff to render templates from source assets. Extend installed target-project tests to assert scaffold content, not just file existence.

### 115.10. Enforce S:W:H:E tracking after installed-project mutations

**Status:** done
**Dependencies:** None

Add portable post-mutation tracking enforcement so Aegis-installed projects require meaningful S:W:H:E entries in the active session and tracker after task-scoped mutations. The live Claude smoke proved ready-state writes work but are not yet forced into the audit trail.

**Details:**

Implement an Aegis-native logging workflow that records pending mutation events, exposes an explicit tracking command or equivalent helper that writes S:W:H:E entries to sessions/current and the active TRACKER.md, and gates subsequent mutation or session stop until the pending event is represented in the audit trail. Tests must prove a READY write creates pending tracking, another mutation is refused until logging occurs, logging writes S:W:H:E entries to both files, and Taskmaster/Serena remain optional.

### 115.11. Enforce full workflow-surface accountability in installed projects

**Status:** done
**Dependencies:** None

Extend Aegis runtime beyond session/tracker mutation logging so installed projects enforce this repository's workflow model: plan status/evidence alignment, task-scoped implementation/finding/decision/changelog/handoff surfaces, and Stop/verification gates that prevent Claude from ending or claiming completion with only minimal S:W:H:E entries. The fix must be mechanical through Aegis commands/hooks/tests, not documentation-only.
