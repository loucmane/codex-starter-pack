# Task ID: 108

**Title:** Clean Legacy PROJECT-BLOG Security Finding

**Status:** done

**Dependencies:** 18 ✓

**Priority:** medium

**Description:** Clean up the legacy PROJECT-BLOG.md path traversal baseline finding surfaced by Task 18 security validation.

**Details:**

Inspect templates/PROJECT-BLOG.md and determine whether the stale blog-era content should be removed, archived, or rewritten. Update only the smallest necessary template content so the security validator baseline is clean without weakening scanner rules or allowlisting stale content. Capture session, plan, work-tracking, scanner report, tests, guard, audit, Taskmaster health, and Serena evidence. Include scope reconciliation before implementation and do not proceed with broad unrelated template cleanup.

**Test Strategy:**

No test strategy provided.

## Subtasks

### 108.1. Scope reconciliation for legacy PROJECT-BLOG cleanup

**Status:** done  
**Dependencies:** None  

Inspect templates/PROJECT-BLOG.md and Task 18 security validation evidence to decide whether the old blog-era content should be removed, archived, or minimally rewritten.

**Details:**

Document the decision in work-tracking before implementation. Do not weaken security validator rules or add an allowlist entry unless evidence proves the content is intentionally retained.

### 108.2. Clean baseline finding and capture evidence

**Status:** done  
**Dependencies:** None  

Apply the scoped PROJECT-BLOG.md cleanup and rerun security validation so the Task 18 baseline finding is resolved without scanner weakening.

**Details:**

Update only the smallest necessary template content. Capture security validator report, focused scanner tests, plan sync, work-tracking audit, guard, diff-check, Taskmaster health, and Serena memory evidence.
