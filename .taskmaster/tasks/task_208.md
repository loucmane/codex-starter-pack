# Task ID: 208

**Title:** Capsule PR-3: narration

**Status:** pending

**Dependencies:** 207 ✓

**Priority:** medium

**Description:** Spec: docs/aegis/AEGIS_CAPSULE_SPEC.md section 4, revised by docs/aegis/decisions/2026-07-03-capsule-resume-drift-gate.md. PR-3 narration is optional, not the automatic next step after PR-2 computed capsules and SessionStart injection. Keep the technical scope ready: deterministic Stop-hook checkpoints every turn (ts, turn index, mutation-event count, dirty-file list, branch — no LLM); narration is ONE budgeted per-session distill over transcript tail + checkpoints, triggered by the SessionEnd detached finalizer (nohup, exit 0, never inline) or lazily at next SessionStart compile-on-read when SessionEnd never fired. Day-one guards: AEGIS_COMPILE=1 short-circuits Aegis hooks in the distiller session; skip subagent/headless/short sessions (<10 mutation events); hard daily distill budget (4/day) with counter in the out-of-worktree store; LLM spend via subscription subagents only. Anti-compounding: distiller NEVER reads prior capsules including the injected-capsule transcript span. TTL scoping: story/decisions_made expire after 3 main-thread sessions unless re-evidenced; open_loops/risk_register/decisions_pending_owner are TTL-exempt with machine-checkable close/supersede conditions. Ship only if real resume/compact dogfood shows computed capsules are useful but insufficient to preserve intent or explain next actions. Merge gate: computed capsule proves useful but insufficient for intent continuity across real resumes, with low-noise evidence recorded; acceptance section 8 items 5 and 7 only apply after that gate is met. Cold-start A/B is not the owner-workflow blocker.

**Details:**

Codebase analysis found the current binding language in docs/aegis/AEGIS_CAPSULE_SPEC.md: the PR table marks PR-3 as optional until computed capsules prove insufficient across real resumes; section 4 defines the checkpoint and lazy distill design; section 7 makes resume-heavy drift refresh the primary owner workflow and keeps cold-start/headless A/B as secondary. The decision record docs/aegis/decisions/2026-07-03-capsule-resume-drift-gate.md explicitly reclassifies PR-3 narration as a dogfood-gated follow-on.

Before implementation, collect low-noise resume/compact dogfood evidence from the deployed PR-2 capsule showing a concrete gap that computed fields do not cover: stale conversation intent not preserved, next action unclear despite fresh repo/task/PR/test/risk state, or open-loop/risk context needing narrative continuity. Evidence should include the resume/compact event, the computed capsule output, the stale or missing intent, the corrected next action, and why adding narration would fix the gap without adding obvious/noisy prose. Do not use fixed-n cold-start A/B as the blocker for this owner workflow.

If the gate is met, implement against the existing capsule surfaces rather than adding a parallel system. Extend the live and asset copies of .claude/scripts/brief_lib.py and aegis_foundation/assets/.claude/scripts/brief_lib.py, which already provide compile_capsule(), render_markdown(), render_injection(), capsule_assignment(), write_capsule(), and check_capsule(). Extend .claude/scripts/session-brief.sh and aegis_foundation/assets/.claude/scripts/session-brief.sh only as needed for lazy compile-on-read behavior. Extend .claude/scripts/ledger-record.sh and the gate_lib.py hook dispatcher path it calls so Stop can append checkpoint events without blocking or failing the session. Keep live and installed asset copies in parity, following the existing tests/claude_adapter/test_ledger_lib.py copy-parity pattern.

Use the existing ledger vocabulary in docs/aegis/LEDGER_SCHEMA.md: event_type 'checkpoint' is reserved for the PR-3 Stop hook and should record deterministic per-turn checkpoint data. Checkpoint appends must use the out-of-worktree ledger opened through .claude/scripts/ledger_lib.py / aegis_foundation/assets/.claude/scripts/ledger_lib.py, not .aegis/state. SessionEnd narration must be best-effort and detached; SessionStart lazy narration must tolerate missing SessionEnd, transcript paths from hook payloads, and corrupted or unavailable transcript tails without breaking injection.

The distiller input contract is strict: transcript tail plus deterministic checkpoints only, excluding prior capsules, archive capsules, and injected-capsule transcript spans. AEGIS_COMPILE=1 must disable Aegis hooks inside the distiller's own headless session. Enforce skip rules for subagent/headless/short sessions and enforce the hard daily distill budget in the out-of-worktree store. Narrated fields must obey TTL rules from section 4: last_session_story and decisions_made expire after 3 qualifying main-thread sessions unless re-evidenced; open_loops, risk_register, and decisions_pending_owner clear only through their machine-checkable close/supersede or recorded-decision conditions. On conflict, computed fields beat narrated fields and the conflict surfaces as drift.

Update docs only after the dogfood gate is satisfied. The wording should say PR-3 is optional and evidence-gated, not the default follow-up to PR-2. Keep cold-start A/B docs/tests available for deployments that need them, but do not describe them as the owner HP-Coach interactive/resume-heavy blocker.

**Test Strategy:**

First, record the dogfood gate evidence before coding: real resume/compact examples showing computed capsule usefulness plus insufficiency for intent continuity, with false/noisy items rare. Treat absence of such evidence as a stop condition and leave PR-3 unbuilt.

If implementing, add focused tests around the existing capsule and hook surfaces: tests/claude_adapter/test_ledger_lib.py for checkpoint event schema/store behavior and live-vs-asset parity; tests/claude_adapter/test_ledger_record.py or a new PR-3 hook test for Stop checkpoint appends that never block or fail; tests/claude_adapter/test_capsule_injection.py for lazy SessionStart compile-on-read behavior and injected-span exclusion; tests/claude_adapter/test_brief_lib.py for rendered last-narration metadata, TTL expiry, computed-over-narrated conflict handling, and budget/degradation behavior; tests/meta_workflow_guard/test_aegis_installer.py for installed Stop/SessionEnd/SessionStart hook wiring in generated settings/assets.

Cover acceptance section 8 items 5 and 7 only after the resume-drift gate is met: kill -9 or missing SessionEnd still yields fresh computed fields plus lazy checkpointed narration with ended-cleanly=no, and a 6-agent fan-out produces zero distill recursion and no more than one narration pass. Add negative tests for AEGIS_COMPILE=1 recursion prevention, subagent/headless/short-session skips, daily budget exhaustion, transcript corruption, and refusal to read prior capsule/archive content. Run the focused suites: tests/claude_adapter/test_brief_lib.py, tests/claude_adapter/test_capsule_injection.py, tests/claude_adapter/test_ledger_lib.py, tests/claude_adapter/test_ledger_record.py, and relevant installer tests under tests/meta_workflow_guard/.

## Subtasks

### 208.1. Collect resume-drift dogfood gate evidence

**Status:** pending
**Dependencies:** None

Capture real resume/compact examples proving computed capsules are useful but insufficient for preserving intent or explaining next actions, with low-noise evidence recorded before implementation starts.

**Details:**

Use docs/aegis/decisions/2026-07-03-capsule-resume-drift-gate.md and docs/aegis/AEGIS_CAPSULE_SPEC.md section 7 as the gate source of truth. Record the computed capsule output, stale or missing intent, corrected next action, and why narration would address the gap. Do not use cold-start A/B as the owner-workflow blocker.

### 208.2. Implement deterministic Stop checkpoints

**Status:** pending
**Dependencies:** 208.1

Append deterministic checkpoint events from the Stop hook using the existing out-of-worktree ledger path, without LLM involvement or blocking behavior.

**Details:**

Extend the existing hook dispatcher used by .claude/scripts/ledger-record.sh and mirrored asset files. Emit event_type checkpoint as defined in docs/aegis/LEDGER_SCHEMA.md with ts, turn index, mutation-event count, dirty-file list, and current branch. Keep live and aegis_foundation/assets copies synchronized.

### 208.3. Implement lazy per-session narration distill

**Status:** pending
**Dependencies:** 208.2

Add one budgeted per-session distill over transcript tail plus checkpoints, detached from SessionEnd or lazily compiled at next SessionStart when SessionEnd did not fire.

**Details:**

Extend brief_lib.py/session-brief.sh surfaces. Enforce AEGIS_COMPILE=1 recursion prevention, subagent/headless/short-session skips, daily out-of-worktree budget, subscription-subagent LLM usage, prior-capsule/archive exclusion, and injected-capsule span exclusion. Never compile inline in SessionEnd.

### 208.4. Apply TTL and render narrated fields

**Status:** pending
**Dependencies:** 208.3

Render narration metadata and free-claim fields only within the section 4 TTL and conflict rules.

**Details:**

Expose last narration timestamp and ended-cleanly yes/no in the capsule. Expire last_session_story and decisions_made after 3 qualifying main-thread sessions unless re-evidenced. Keep open_loops, risk_register, and decisions_pending_owner TTL-exempt and clearable only by their machine-checkable close/supersede or recorded-decision conditions. Computed fields always beat narrated fields and conflicts surface as drift.

### 208.5. Update documentation and acceptance notes

**Status:** pending
**Dependencies:** 208.4

After the dogfood gate and implementation pass, update docs to describe PR-3 as optional and resume-drift-gated rather than automatic after computed capsule shipment.

**Details:**

Update docs/aegis/AEGIS_CAPSULE_SPEC.md and related program/acceptance notes only if implementation ships. Preserve cold-start A/B as a secondary deployment-specific track, not the owner HP-Coach interactive/resume-heavy blocker.
