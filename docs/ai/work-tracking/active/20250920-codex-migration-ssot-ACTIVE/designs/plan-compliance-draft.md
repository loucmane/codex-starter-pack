# Plan Compliance Guardrails (Draft)

## Objective
Codify a reusable enforcement pattern that ensures every Codex task begins with a detailed plan and cannot proceed without stakeholder confirmation.

## Core Requirements
1. **Minimum Plan Structure**
   - Plan must contain at least three steps:
     1. `Confirm scope with loucmane` (discussion checkpoint).
     2. Implementation step(s) referencing concrete deliverables (files/tests).
     3. Verification/reporting step (tests, documentation, handoff).
   - Additional steps allowed, but these three are mandatory anchors.

2. **Evidence Expectations**
   - Each completed plan step must cite files or commands (S:W:H:E alignment).
   - Session log and tracker entries must mention plan compliance status.

3. **Guard Hook (`codex-guard validate`)**
   - Guard fails if no plan exists, if mandatory steps missing, or if scope step not completed.
   - Guard checks that plan steps reference real files/commands before marking complete.

4. **Behavior Enforcement**
   - New behavior: `templates/behaviors/planning/plan-compliance.md` (to be authored after approval).
   - Behavior triggers at start of any workflow or when S:W:H:E becomes non-VOID.
   - Blocks progress until plan compliance confirmed.

5. **Plan Template**
   - Provide reusable markdown snippet (e.g., `templates/workflows/processes/plan-template.md`) with required sections.
   - Helper script (`scripts/codex-task plan scaffold`, future) can pre-fill mandatory steps.

6. **Integration Points**
   - Session lifecycle workflow → include plan compliance step right after ULTRATHINK.
   - Meta workflow authoring process → enforce planning before drafting new assets.
   - Taskmaster alignment → require plan reference before touching `tasks.json`.

## Open Questions
- Should guard auto-populate missing plan steps or just block? (currently block + instructions)
- How to handle small trivial tasks? Proposal: behavior allows bypass only when work category explicitly marked "informational" in session log.
- How to surface plan state in Serena memories? (Idea: include plan summary in every handoff memory.)

## Next Steps (Pending Approval)
1. Review this draft with loucmane.
2. Author behavior + plan template files that mirror these rules.
3. Extend `codex-guard` to implement the validation logic.
4. Update workflows to reference behavior/plan template once implemented.


## Plan Sync Validator (Draft)
- Script: `scripts/codex-task plan sync` (future) validates before writing.
  1. Read plan (`plans/current`) and tracker checklist; ensure identical step IDs.
  2. Compare status/evidence for each step; abort if mismatched.
  3. Verify plan S:W:H matches active session and timestamps are fresh.
  4. After confirmation, update both plan and tracker to matching values.
  5. Record sync event in `.plan_state/sync.log` (timestamp, plan path, hash).
- Guard checks:
  - Sync log timestamp > last plan/tracker edit.
  - Step sets and statuses aligned.
  - Evidence strings consistent across plan + tracker.
  - If lint fails, `codex-guard` blocks and reports mismatches.


## Plan Template Outline (Draft)
- Location: `plans/<date>-<task>-plan.md` (draft) → `plans/current` symlink.
- Sections:
  1. Header (Session ID, Work Context, Handler Target, Evidence Summary).
  2. Plan Table (Step ID, Description, Evidence, Status).
  3. Risks & Mitigations.
  4. Verification Checklist (tests, guard, documentation).
  5. Handoff Notes (what to summarize in sessions/Serena).
- Example table will be defined in the actual template file.

## Guard Specification (Draft)
- Command: `scripts/codex-guard validate --plan` (or default guard).
- Checks:
  - `plans/current` exists, points to file under `plans/`.
  - File mtime > session start timestamp.
  - Required steps (scope, implementation, verification) present.
  - Scope step marked completed with timestamp after user confirmation.
  - Evidence fields reference real files/commands (checked via filesystem and regex).
  - `.plan_state/sync.log` contains entry with hash matching plan/tracker.
  - Tracker checklist status matches plan status.
- On failure: guard outputs mismatch details and aborts workflow.

## Plan Bypass Policy (Draft)
- Default: planning required.
- Waiver allowed only when session marked `informational` with explicit note.
- Waiver requires tracker entry: `Plan compliance waived – reason`.
- Guard verifies waiver note before allowing work without plan.

## Plan State Logging
- File: `.plan_state/sync.log` (JSON array of entries).
- Each entry: `{ "plan": "plans/2025-09-23-action-2-plan.md", "hash": "...", "synced_at": "2025-09-23T17:45Z", "tracker_hash": "..." }`.
- Guard compares latest entry to current plan/tracker hash.

## Plan ↔ Plan Tool Protocol (Draft)
- Steps:
  1. Update plan file first (edit table, statuses).
  2. Mirror updates via `update_plan` (Plan tool) using same IDs.
  3. Run `scripts/codex-task plan sync` to validate parity.
  4. If mismatch detected, guard blocks until resolved.

## Change Control
- Drafts stored under `plans/drafts/`; promoted by moving file and updating symlink.
- Archive old plans under `plans/archive/` with timestamped filenames.

## Workflow Integration Summary
| Workflow | Plan Checkpoint |
|----------|-----------------|
| Session Lifecycle | Immediately after ULTRATHINK; behavior ensures plan exists |
| Meta Workflow Authoring | Step 0 before drafting new assets |
| Taskmaster Alignment | Before editing `tasks.json`; guard enforces active plan |
| Compaction Recovery | Plan must be reopened and revalidated after session resume |


## Plan Step Identifiers
- Standard IDs:
  - `plan-step-scope`
  - `plan-step-implement`
  - `plan-step-verify`
- Both plan file and tracker must use these IDs; guard checks for exact matches.

## S/W/H/E Binding
- Plan header includes Session ID (S), Work context (W), Handler target (H), and Evidence summary (E).
- Guard validates plan fields against current session/work-tracking entries.

## Plan Template Table
| Step ID | Description | Evidence | Status |
|---------|-------------|----------|--------|
| plan-step-scope | Confirm scope with loucmane | Session log entry (time) | pending |
| plan-step-implement | [deliverable list] | File paths, commands | pending |
| plan-step-verify | Run tests/guard, update docs | Test command output | pending |

## Plan ↔ Plan Tool Procedure
1. Edit plan file first (update table).
2. Mirror updates via `update_plan` (matching step IDs).
3. Run `scripts/codex-task plan sync` to confirm parity.
4. If automation absent, manually verify both representations match before proceeding.

## Handoff / Memory
- Include plan summary in Serena handoff memory (`plan-step outcomes`, evidence references).
- Session end: note plan status and archive path.

## Plan Lifecycle
- On completion, set symlink `plans/current` to `null` or archive plan file.
- Guard ensures no stale plan referenced in subsequent sessions.

## Multi-Task Handling
- Plans are scope-specific; new tasks require new plan files.
- Shared plan allowed only if explicit note links tasks and guard verifies shared context.


## Execution Tasks (Draft)
- **TaskMASTER Task Proposal**
  - Task: "Implement plan compliance enforcement"
    - Subtask 1: Finalize design (including emergency bypass, amendments, cross-session continuation, conflict detection)
    - Subtask 2: Implement `plan-compliance` behavior file
    - Subtask 3: Implement guard core validation (mandatory plan structure & IDs)
    - Subtask 4: Implement plan-tracker sync validation logic
    - Subtask 5: Implement evidence verification (S:W:H:E + command proofs)
    - Subtask 6: Integrate guard with existing workflows (session lifecycle, meta workflow authoring)
    - Subtask 7: Implement emergency bypass flow with post-mortem logging
    - Subtask 8: Implement plan amendment/version tracking (archival + guard awareness)
    - Subtask 9: Document plan continuation/hand-off protocol
    - Subtask 10: Build regression tests/automation for plan compliance
- **TaskMASTER Task Proposal**
  - Task: "Implement plan compliance enforcement"
    - Subtask 1: Draft behavior spec (this document)
    - Subtask 2: Implement `plan-compliance` behavior file
    - Subtask 3: Extend `codex-guard` with plan validation
    - Subtask 4: Create plan template file and helper script stub
    - Subtask 5: Update workflows (session/meta/etc.) to reference behavior
    - Subtask 6: Document tracker/plan tool integration
  - Evidence: tracker checklist, guard output, plan sync log.

## Emergency Bypass Protocol (Draft)
- Define `plan-step-emergency` with explicit justification and post-mortem requirement.
- Guard allows bypass only with `emergency-bypass` flag and tracker entry.
- Post-mortem plan must be created within 24 hours documenting remediation and follow-up tasks.

## Plan Amendments & Versioning
- Maintain `plans/archive/<plan>-vN.md` when major changes occur mid-execution.
- Section in plan template for "Amendments" capturing rationale, approver, timestamp.
- Guard compares plan hash against last validated version; prompts re-validation when changed.

## Cross-Session Continuation
- Add "Continuation" block in plan template listing next session owner, required context reload steps.
- Tracker checklist includes "Plan continuation validated" for multi-session efforts.
- Serena handoff must reference plan path and amendment history.

## Plan Conflict Detection
- Guard checks for overlapping plans touching same files (via git diff + plan file lists).
- If conflict detected, guard blocks and instructs merge via designated conflict-resolution workflow.
- Plan sync log records conflict resolutions for audit.
