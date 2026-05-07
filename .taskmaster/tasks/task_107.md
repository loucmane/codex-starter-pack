# Task ID: 107

**Title:** Enforce Direct Git Execution Mode

**Status:** done

**Dependencies:** 106 ✓

**Priority:** high

**Description:** Make regular Git/GitHub command execution the default Codex commit/push/PR workflow when the user delegates Git work and SSH/GPG auth is available. Treat gac only as a legacy/user convenience alias that is emitted when explicitly requested or when auth failure requires manual fallback.

**Details:**

Update commit-format conventions, git operator handlers, session/handoff workflow wording, templates/TOOLS references, and guard coverage so stale 'developer manually runs gac' default guidance fails validation. Add a clear commit-mode model: direct-git-execution, full-gac-command-on-explicit-request, message-payload-only, and auth-refresh-required. Document the queue-jump rationale ahead of Task 10 because stale GAC-default behavior caused a live workflow regression immediately after Task 106. Verify with plan sync, work-tracking audit, guard, diff-check, and targeted meta workflow guard tests.

**Test Strategy:**

No test strategy provided.

## Subtasks

### 107.1. Scope direct Git execution policy

**Status:** done  
**Dependencies:** None  

Audit current GAC/direct-Git guidance and define the commit-mode model.

**Details:**

Identify conflicting template guidance, especially stale 'developer manually runs gac' default language. Define direct-git-execution as the default when the user delegates Git work and auth is available, full-gac-command only for explicit GAC requests, message-payload-only for message-only requests, and auth-refresh-required when SSH/GPG cache fails.

### 107.2. Update templates and guard coverage

**Status:** done  
**Dependencies:** None  

Patch commit workflow templates and validation so regular Git/GitHub execution is the default and stale GAC-default language fails.

**Details:**

Update templates/conventions/git/commit-format.md, templates/handlers/operators/git/create-commit-message.md, templates/TOOLS.md, and any session/handoff wording needed. Extend scripts/codex-guard/tests so canonical commit docs require direct-git-execution mode and reject 'gac is executed manually by the developer' as default guidance.

### 107.3. Verify and publish direct Git workflow

**Status:** done  
**Dependencies:** None  

Run targeted validation, record evidence, and commit/push through normal Git/GitHub commands.

**Details:**

Run plan sync, work-tracking audit, codex-guard validate --include-untracked, git diff --check, and targeted meta workflow guard tests. Record evidence in the Task 107 work-tracking folder. Commit and push using regular git add/git commit/git push rather than gac alias output.
