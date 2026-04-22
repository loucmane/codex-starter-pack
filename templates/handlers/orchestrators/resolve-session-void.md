---
id: resolve-session-void
name: Resolve Session Void
title: Resolve Session Void
role: orchestrator
type: orchestrator
domain: session
stability: stable
status: stable
triggers:
  - "S = VOID"
  - "no session found"
  - "session unclear"
  - "VOID→conventions"
dependencies:
  - session-start
tools:
  - date
version: 1.0.0
---

#### Handler: resolve-session-void {#resolve-session-void}
**Triggers**: "S = VOID", "no session found", "session unclear", "VOID→conventions"
**Target Pattern**: Missing session context in ULTRATHINK
**Pre-conditions**: 
- ULTRATHINK attempted
- S value is VOID
- sessions/ accessible
**Process**:
1. Run `date '+%Y%m%d'` for today's date
2. Check sessions/ for matching entry
3. If no entry for today:
   - Output: "No session found for today"
   - Route to session-start handler
   - Wait for session creation
4. If entry exists:
   - Extract session date in YYYYMMDD format
   - Verify matches today's date
   - Return valid S value
5. Update ULTRATHINK with resolved value
**Success**: Valid session ID obtained
**Failure**: Cannot determine session
**Examples**:
- ULTRATHINK "[S:VOID|W:testing|H:fix-bug]" → Resolve S first
- First request of day → Routes to session-start
- After compaction → Create fresh session

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/orchestrators/resolve-session-void.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
