# PR-4 Replacement Parity Matrix

Task: TM-229

Status: design-only prerequisite for TM-210 (`Capsule PR-4: retirement`). This document does
not authorize or implement PR-4 retirement.

## Hard Rule

PR-4 is not "delete old workflow." PR-4 is: prove the capsule + ledger + witness stack fully
replaces each old workflow responsibility, then retire only duplicated load-bearing parts.

PR-4 MUST NOT remove, demote, stop validating, or stop generating any existing workflow
surface until this matrix proves the replacement covers the same function with equal or better
reliability. A PR-4 change that touches a legacy surface must cite that surface's row, its
proof, its dogfood evidence, and its rollback path. If parity is not proven, the retirement
state remains `keep` or `shadow`.

Allowed retirement states:

- `keep`: legacy surface remains load-bearing.
- `shadow`: replacement runs beside the legacy surface, but legacy still owns the job.
- `demote`: replacement owns the job; legacy may remain as a generated/view-only artifact.
- `retire`: replacement owns the job; legacy surface can be removed or no longer generated.

## Matrix

| Old surface | Current job performed | Current owner | Replacement surface | Proof required for equal-or-better behavior | Dogfood evidence required | Rollback path | Retirement state | PR-4 go/no-go |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `sessions/` markdown logs | Preserve chronological session history, command/evidence notes, failures, and recovery context. | Session/log scaffolding plus old closeout evidence gates. | Out-of-worktree append-only ledger + computed capsule summaries. | Fresh agent can answer what happened and what failed from ledger/capsule without chat transcript for several real tasks. | At least three resumed tasks where capsule/ledger reconstructs session history with fewer or equal misses than `sessions/`. | Re-enable session markdown generation and make closeout read session files again. | `shadow` | NO-GO for retirement; continue shadow comparison. |
| `sessions/current` pointer | Identify the active session file for continuity and stop/closeout checks. | Session scaffolding. | Ledger `session_id` events + latest capsule freshness snapshot. | Current session can be identified from ledger events across normal starts, resumes, compactions, and interrupted sessions. | SessionStart/resume dogfood showing correct `session_begin` and capsule reason in real use. | Restore `sessions/current` pointer as required readiness input. | `shadow` | NO-GO until interrupted-session recovery is proven. |
| `sessions/state.json` | Store session lifecycle metadata and terminal state. | Session scaffolding and repair logic. | Ledger session events (`session_begin`, `session_end`, checkpoint) + capsule metadata. | Lifecycle can distinguish clean end, missing SessionEnd, and resumed session without manual repair. | Missing-SessionEnd or interrupted-session fixture plus a real resume showing correct capsule status. | Restore `sessions/state.json` lifecycle checks. | `keep` | NO-GO; PR-3 checkpoints are not shipped. |
| `plans/` markdown plans | Preserve declared intent, plan steps, progress, and verification expectations. | Plan scaffolding + old plan sync/closeout checks. | Scope records + Taskmaster task details + witness scope/diff accounting. | Witness can prove shipped diff matches declared scope without a hand-maintained plan file. | Several PRs where witness scope accounting passes and no required intent only exists in `plans/`. | Keep plans as required and restore plan-sync checks. | `shadow` | NO-GO until scope records cover non-task branches and ambiguous work. |
| `plans/current` pointer | Identify active plan for closeout and log-step attribution. | Plan scaffolding and old S:W:H:E log commands. | Branch/task convention + scope record + ledger event ranges. | Active scope is recoverable from branch, Taskmaster, and ledger without current-plan pointer drift. | Resume/compact dogfood where `aegis next` points to correct active task and scope after branch changes. | Restore `plans/current` readiness requirement. | `shadow` | NO-GO until branch/task-less micro work is covered. |
| `TRACKER.md` | Human-readable progress ledger for work-tracking envelopes. | Work-tracking scaffolding. | Ledger event stream + capsule open-loop/task-truth sections. | Progress, blocker, and verification facts can be reconstructed from ledger/capsule with less ceremony. | At least three completed tasks where `TRACKER.md` adds no unique recovery fact beyond ledger/capsule. | Continue generating and requiring `TRACKER.md`. | `shadow` | NO-GO until unique-content comparison passes. |
| `HANDOFF.md` | Summarize state for a future agent or resumed session. | Closeout/handoff repair. | Computed capsule injection + optional PR-3 narration if needed. | Fresh/resumed agent orients from capsule as well or better than handoff; missing "why" cases are either rare or covered by PR-3. | Real resume/compact evidence: stale assumptions corrected, next action validated, and no critical handoff-only facts. | Restore handoff generation and semantic closeout gates. | `shadow` | NO-GO until resume-drift evidence is strong enough. |
| `docs/ai/work-tracking/active/` and `archive/` folders | Represent active/completed envelope state and preserve per-task artifacts. | Work-tracking state machine, readiness, repair. | Taskmaster status + branch/task convention + ledger/capsule + PR delivery evidence. | No state drift from folder naming; active/completed work recoverable without folder moves. | Multiple tasks across kickoff, done flip, PR merge, and resume with correct capsule/witness state and no folder-derived recovery needed. | Restore folder readiness checks and repair actions. | `keep` | NO-GO; folder drift failures motivated the redesign but parity is not proven. |
| `.aegis/state/pending-tracking.json` | Force every mutation to be acknowledged by a manual log before next mutation/Stop. | PostToolUse pending tracker + PreToolUse/Stop gates. | Passive ledger events + boundary annotations/capsule + witness at delivery. | Mutations are recorded without per-mutation ceremony; witness catches unverified or out-of-scope changes. | Real tasks showing near-zero ceremony, complete ledger, and witness correctly enforcing delivery. | Re-enable pending-tracking hard blocks. | `shadow` | NO-GO until witness catches a meaningful delivery miss and false blocks stay low. |
| `posttooluse-tracking.sh` pending path | Create manual S:W:H:E pending entries after mutations. | Claude PostToolUse tracking hook. | PR-1b passive recorder hook and out-of-worktree ledger. | Recorder covers mutation, failure, task-truth, delivery, and subagent events without blocking. | Hook fixture tests plus live HP-Coach/Codex events in ledger. | Restore pending tracking hook while keeping recorder. | `shadow` | NO-GO for full retirement; recorder is live but equivalence needs longer dogfood. |
| `tracking-stop-gate.sh` | Block session stop when pending S:W:H:E entries remain. | Claude Stop hook. | Boundary witness + capsule freshness + optional PR-3 checkpoints. | Missing evidence is caught at boundary without tail-chasing "log command creates log pending" loops. | Stop/resume dogfood with missing SessionEnd and no lost recovery context. | Restore Stop hard gate. | `keep` | NO-GO; PR-3 checkpoint substitute is not shipped. |
| Closeout/handoff semantic gates | Require task summary, evidence, changelog, handoff sections before completion. | Aegis closeout/readiness gates. | `aegis witness` delivery report + capsule state + Taskmaster status containment. | Delivery report proves scope, tests-at-head, task flip containment, PR/CI, and evidence without prose-string reconciliation. | Required witness check passes on several real PRs and fails on at least one seeded bad case. | Restore closeout semantic gates. | `shadow` | NO-GO until witness has more real/negative evidence. |
| Strict readiness/current-work blocks | Prevent mutations outside an active envelope or in broken workflow state. | PreToolUse readiness gate. | Advisory mode + ledger decision recording + GitHub boundary protection/witness. | False-positive blocks disappear while protected actions and delivery discipline remain covered. | Real product work with advisory decisions recorded and no lost task/delivery discipline. | Set enforcement mode back to strict. | `shadow` | NO-GO for permanent demotion until advisory dogfood is longer. |
| `aegis kickoff` required ceremony | Create branch/task/session/plan/work-tracking envelope before work starts. | Aegis lifecycle commands. | Taskmaster task + branch naming + inferred scope records + capsule orientation. | Work scope is recoverable and enforceable without requiring kickoff for every task. | Several normal branches where scope inference and witness mapping are correct, including ambiguity handling. | Require kickoff for source edits again. | `shadow` | NO-GO until scope inference handles non-standard work. |
| `aegis closeout` required ceremony | Close task envelope, repair handoff, and prepare done status. | Aegis closeout command. | Witness delivery report + PR merge evidence + Taskmaster done containment. | Done status and merge state are reconstructable and protected without closeout ceremony. | Multiple merged PRs where witness + Taskmaster truth replace closeout without missing facts. | Restore closeout as required before done/merge. | `shadow` | NO-GO until delivery report is complete enough to replace closeout. |
| Protected workflow path rules for `sessions/`, `plans/`, and work-tracking | Prevent direct edits to load-bearing workflow state. | Path guards and `WORKFLOW_LINK_PREFIXES`. | State surfaces become derived or non-load-bearing; protected hard blocks narrow to settings/hooks and destructive paths. | Direct edits to retired paths cannot corrupt authority because those paths are no longer inputs. | Tests proving old paths are ignored/derived plus rollback test restoring old authority. | Restore protected path prefixes. | `keep` | NO-GO until old paths are no longer load-bearing. |
| Target-repo ceremony scaffolding | Provide repo-local CLAUDE/AGENTS guidance, work-tracking folders, and generated ceremony docs. | Installed Aegis assets in each target repo. | Installed capsule config, capsule current files, witness check, and repo-specific deployment doc. | Target repo can start/resume/deliver work from capsule/witness without ceremony docs. | HP-Coach companion PR demonstrating same or better continuity across real work. | Reinstall prior Aegis assets and guidance. | `shadow` | NO-GO until HP-Coach companion evidence exists. |
| Packaged workflow templates | Seed new projects with session/plan/tracker/closeout workflow ceremony. | `aegis_foundation/assets/templates/` and installer renderer. | New-project PRD + Taskmaster + capsule/ledger/witness defaults. | Fresh project can go from PRD to tasks to PR without old ceremony and without losing continuity. | New-project dry run or fixture acceptance using capsule defaults. | Keep templates and strict workflow profile available. | `keep` | NO-GO; new-project parity is unproven. |
| Installed ceremony guidance docs | Tell agents to maintain handoff/tracker/plan/session surfaces. | Managed docs such as invocation/runtime/live-acceptance guidance. | Slim guidance pointing at `aegis brief`, `aegis witness`, Taskmaster, and capsule files. | Agents follow the new path naturally and do not lose required workflow facts. | Real sessions where "continue" goes to capsule-guided work without extra prompts. | Restore old docs from installer assets. | `shadow` | NO-GO until docs are validated in HP-Coach and codex. |
| Doctor/repair of old surfaces | Detect and repair drift in current-work, folders, plans, sessions, and handoff. | `aegis doctor` / `aegis repair`. | Doctor reports capsule/witness/ledger health; old surfaces either derived or non-authoritative. | Repair cannot corrupt live state, and missing old surfaces are not treated as blockers after retirement. | Regression tests for old corruption classes plus live doctor output under capsule mode. | Restore old repair actions and readiness checks. | `keep` | NO-GO until shared detector/replacement doctor behavior is proven. |

## Reviewer Checklist For PR-4

- Every deleted, demoted, or advisory-only legacy surface has a row in this matrix.
- No row marked `demote` or `retire` has missing proof, missing dogfood evidence, or missing
  rollback steps.
- No target-repo ceremony scaffolding is removed without a companion target-repo rollback path.
- No protected-path, readiness, closeout, or Stop semantics are relaxed unless witness,
  capsule, or ledger evidence demonstrates equivalent boundary discipline.
- PR-4 remains per-surface and reversible. Big-bang retirement is rejected.

## Dogfood Fixtures

- HP-Fetcher Task 80 stale workflow-state residue is an active PR-4 fixture; see
  `docs/aegis/decisions/2026-07-07-hp-fetcher-task80-pr4-fixture.md`. Do not repair,
  close out, archive, or clear that residue merely to make strict verification green. It is
  evidence that the capsule can surface legacy scaffold drift, and PR-4 must cite this
  fixture when changing current-work, session, plan, work-tracking, pending-tracking, or
  strict readiness behavior.

## Current Decision

PR-4 is blocked. The replacement stack is promising and several surfaces are ready for shadow
comparison, but no legacy surface is currently authorized for full retirement by this matrix.
