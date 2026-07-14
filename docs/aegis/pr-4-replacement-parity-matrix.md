# PR-4 Replacement Parity And Coexistence Matrix

Task: TM-243, refreshing the original TM-229 prerequisite for TM-210.

Status: reviewed evidence checkpoint. This document does not authorize or implement PR-4
retirement. It records the owner's current policy that passive Aegis evidence and legacy
S:W:H:E scaffolding complement one another. TM-233 and TM-234 established generated shadow
projections; Tasks 237–252 hardened guidance, context budgets, worktree identity, witness output,
managed updates, autonomous delivery, Codex adapters, advisory closeout, and hook bootstrap.

## Hard Rule

PR-4 is not “delete old workflow.” Machine-observed facts may move to the ledger, capsule, or
witness, while human intent, rationale, progress narrative, and recovery context remain in
legacy surfaces. The preferred architecture is coexistence:

- ledger for observed facts;
- capsule for computed orientation;
- witness and protected CI for delivery proof;
- Taskmaster for current task truth until a separately authorized migration;
- S:W:H:E files for declared intent and durable human narrative;
- derived Obsidian vault for read-only graph navigation.

PR-4 MUST NOT remove, demote, stop validating, or stop generating an existing workflow surface
unless a later, separately reviewed decision proves that surface has no remaining unique content,
replacement behavior is equal or better, dogfood covers failure and recovery paths, and rollback
is tested. Current Task 243 evidence authorizes no such change.

Allowed retirement states remain:

- `keep`: the legacy surface remains load-bearing.
- `shadow`: machine evidence runs beside it and may own selected observed facts.
- `demote`: a later replacement owns the whole job; legacy becomes a generated/view-only
  artifact.
- `retire`: a later replacement owns the whole job and the legacy surface may be removed.

At this checkpoint every row is `keep` or `shadow`. Task 210 is **NO-GO**.

## Evidence Baseline

The Task 243 read-only dogfood built deterministic derived vaults for Aegis source, Blog, and
HP-Fetcher from 15,463, 2,506, and 45,473 ledger rows respectively. Those same repositories
retain 72,963, 8,114, and 3,948 human-authored nonblank legacy lines after generated Aegis marker
blocks are excluded. See:

- `docs/ai/work-tracking/archive/20260714-task243-pr4-parity-and-obsidian-vault-COMPLETED/reports/obsidian-vault/dogfood.md`
- `docs/ai/work-tracking/archive/20260714-task243-pr4-parity-and-obsidian-vault-COMPLETED/reports/coexistence-audit.md`

Blog PRs #7–#24 contribute 17 merged delivery runs and one closed draft. HP-Fetcher preserves
the stale Task 80 fixture and a 45,473-row ledger. The source history contributes Tasks 237–252.
Together they support coexistence and selective shadowing, not broad retirement.

## Matrix

| Old surface | Current job performed | Current owner | Replacement surface | Proof required for equal-or-better behavior | Dogfood evidence | Remaining unique legacy content | Rollback path | Retirement state | PR-4 go/no-go |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `sessions/` markdown logs | Preserve chronological work, reasoning, failed approaches, evidence, interruptions, and recovery. | Session scaffolding and human authors. | Ledger session and failure events, capsule summaries, generated marker blocks, and vault links cover machine-observed facts only. | A future per-surface proposal must prove every recovery-relevant narrative class is either intentionally retained or faithfully represented without raw transcript dependence. | Task 243 inventories 11,061 source, 965 Blog, and 833 HP-Fetcher human session lines; all three vault builds were deterministic no-ops on rebuild. | Human reasoning, discarded approaches, interruptions, explanations, and recovery narrative that tool events cannot infer. | Keep session generation and readers enabled; restore any narrowed checks from the reviewed prior release. | `keep` | NO-GO — unique narrative is large and useful. |
| `sessions/current` pointer | Provide a stable path to the active session for agents, guards, closeout, and recovery. | Session scaffolding. | Capsule session metadata and ledger session IDs offer computed orientation. | Prove all installed clients and recovery paths resolve the same active session after starts, resumes, compaction, branch changes, and interrupted termination. | Tasks 244–245 fixed completed-state ordering while Task 243 still consumes the pointer during its active workflow. | Compatibility contract and deterministic navigation to the human session record, even though the pointer has no prose. | Continue maintaining the pointer and its integrity checks. | `keep` | NO-GO — active workflow still consumes it. |
| `sessions/state.json` | Persist session lifecycle, active target, and terminal projection state. | Session lifecycle scaffolding and guards. | Ledger lifecycle events plus capsule metadata provide observational state. | Demonstrate transactional equivalence for clean end, missing end, resume, compaction, branch transition, and crash recovery across supported clients. | Task 243 kickoff updated this state through the supported workflow; Tasks 244–245 show ordering defects still require explicit lifecycle semantics. | Compact compatibility state used by existing guards and deterministic recovery; not all lifecycle transitions exist as authoritative ledger projections. | Keep the state file and validation; restore from the task-specific pre-change projection if a future experiment fails. | `keep` | NO-GO — transactional lifecycle parity is unproven. |
| `plans/` markdown plans | Preserve declared scope, ordered intent, amendments, expected evidence, and verification strategy. | Human plan authors plus plan-sync checks. | Task details, scope events, witness diff accounting, capsule, and vault links expose related facts. | Prove intent and amendment semantics remain recoverable and reviewable without asking a model to infer purpose from mutations. | Task 243 inventories 15,024 source, 1,831 Blog, and 462 HP-Fetcher human plan lines; the current plan drives four explicit hardening steps. | Purpose, approach, sequencing, amendments, trade-offs, evidence expectations, and owner constraints. | Keep plans required for scoped work and retain plan-sync validation. | `keep` | NO-GO — passive evidence cannot infer intent. |
| `plans/current` pointer | Identify the active plan for agents, sync checks, closeout, and recovery. | Plan scaffolding. | Branch/task inference and capsule orientation provide a computed candidate. | Prove ambiguity, branchless work, completed branches, multiple worktrees, and resume all select the correct plan without stale-pointer recovery cost. | Task 243 uses the pointer and plan-sync contract; Tasks 244–245 fixed related historical-branch ordering rather than removing the projection. | Stable compatibility path used by current tooling and humans; pointer drift itself remains a valuable detectable signal. | Continue updating it through supported kickoff and closeout commands. | `keep` | NO-GO — the current workflow remains pointer-aware. |
| `TRACKER.md` | Preserve human progress narrative, blockers, checklist state, and evidence references per task. | Work-tracking scaffolding and task owner. | Ledger events, capsule open loops, generated markers, and vault task links add machine facts. | Show generated facts can remain bounded and marker-safe while every human-only blocker and decision remains durable. | Task 243 inventories 7,459 source, 961 Blog, and 665 HP-Fetcher human tracker lines, including 1,653, 156, and 29 checkboxes. | Curated progress, checklist semantics, blocker explanation, owner-facing status, and links selected for future recovery. | Keep tracker files, marker-external preservation checks, and tracker validation. | `keep` | NO-GO — substantial unique human progress content remains. |
| `HANDOFF.md` | Explain current state, next action, risks, and recovery instructions to a later agent or human. | Closeout workflow and human author. | Capsule orientation and generated boundary markers keep factual fields fresh. | Prove a resumed agent never loses why, risk, or owner-decision context when only computed fields are available. | Task 243 counts 5,605, 1,574, and 827 human risk-context lines across source, Blog, and HP-Fetcher; capsule dogfood corrects facts but does not replace prose. | Why the state exists, unresolved risk, non-obvious next steps, cautions, and owner decisions. | Keep semantic handoff sections and marker-safe repair; generated facts remain bounded sections. | `keep` | NO-GO — computed orientation and human handoff are complementary. |
| `docs/ai/work-tracking/active/` and `archive/` | Represent task envelopes and preserve plans, reports, decisions, findings, implementation notes, and delivery evidence. | Work-tracking lifecycle and repository history. | Task status, ledger, capsule, witness, GitHub, and vault indexes expose machine truth and links. | Prove every archived evidence and rationale class remains durable, searchable, and reversible without folder state. | Task 243 derives links across 2,175 source and 214 Blog legacy documents without mutating them; Blog PRs #7–#24 repeatedly used the archives. | Per-task reports, review evidence, decisions, findings, implementation rationale, and auditable human history. | Keep active/archive transitions and restore any future projection experiment by reverting its isolated change. | `keep` | NO-GO — archives are evidence, not redundant state alone. |
| `.aegis/state/pending-tracking.json` | Preserve unresolved mutation evidence and support strict per-mutation reconciliation. | Post-tool tracking and enforcement profile. | Append-only passive ledger is the primary advisory evidence stream; Task 251 prevents advisory delivery from requiring manual drain. | Preserve every advisory event without blocking delivery, while proving strict mode still fails closed for required unresolved tracking. | Task 251 regression coverage plus Blog Task 40 reproduction proves advisory pending evidence survives closeout without generic repair or deletion. | Strict-profile reconciliation semantics and a forensic compatibility queue for installed runtimes. | Re-enable strict reconciliation behavior through the enforcement profile; never bulk-delete evidence as rollback. | `shadow` | NO-GO — advisory ownership changed, but strict compatibility remains intentional. |
| `posttooluse-tracking.sh` pending path | Translate completed mutations into pending evidence and legacy tracking behavior. | Managed hook adapter. | Passive ledger recorder and generated S:W:H:E markers own advisory observation. | Demonstrate equivalent capture for Claude, Codex, worktrees, failures, and malformed or degraded hook payloads while retaining strict behavior. | Tasks 239–240 and 248–252 cover worktree identity, canonical Codex apply-patch capture, migration, executor stability, advisory semantics, and shared bootstrap. | Cross-client compatibility and the strict-mode boundary between observed mutation and required acknowledgment. | Keep the hook path available and switch behavior by tested enforcement mode. | `shadow` | NO-GO — passive capture is primary in advisory mode, not a universal replacement. |
| `tracking-stop-gate.sh` | Enforce stop-time evidence completeness under profiles that require it. | Managed Stop hook and enforcement mode. | Capsule freshness and witness cover different session and delivery boundaries. | Prove missing session evidence is always recoverable without stop enforcement across crashes, compaction, and every client. | Task 237 made guidance mode-aware and Task 251 separated advisory from strict semantics; no evidence justifies deleting strict Stop behavior. | Explicit strict-profile session boundary and compatibility for teams choosing stronger ceremony. | Keep the Stop hook and mode switch; restore strict as an operator-selected profile. | `keep` | NO-GO — strict mode deliberately retains the boundary. |
| Closeout and handoff semantic gates | Require coherent summary, evidence, changelog, handoff, and terminal task state. | Aegis closeout plus legacy validators. | Quiet witness, capsule, Taskmaster containment, and GitHub evidence prove deterministic delivery facts. | Prove machine checks cover facts while human semantic sections remain meaningful, marker-safe, and non-ceremonial. | Tasks 241, 244–247, and 251 hardened witness, completed-state ordering, autonomous delivery, and advisory closeout; Blog PRs #7–#24 exercise real merges. | Delivery rationale, summary quality, known limitations, and future-agent guidance beyond binary check outcomes. | Keep semantic gates; revert individual gate changes through reviewed source PRs. | `keep` | NO-GO — the witness replaces hand-rolled facts, not human meaning. |
| Strict readiness and current-work blocks | Prevent mutation outside an authorized envelope or while strict workflow state is inconsistent. | Pre-tool readiness gate and enforcement profile. | Advisory recording, scope inference, protected CI, and witness reduce interior interruption. | Maintain low false-block rates in advisory mode and replay-proof every strict block retained for protected state or delivery. | Tasks 237–252 and Blog delivery dogfood show advisory work can stay quiet; HP-Fetcher preserves the false-block and stale-state corpus. | An operator-selectable fail-closed profile and explicit protection for workflow-owned state. | Set enforcement to strict only through the sanctioned command; retain decision records and replay tests. | `shadow` | NO-GO — advisory is the default dogfood posture, strict remains a supported control. |
| `aegis kickoff` required ceremony | Create a coherent task, branch, session, plan, and work-tracking envelope before scoped work. | Aegis lifecycle workflow. | Scope inference and capsule orientation reduce repeated questions once work exists. | Prove every supported task source and nonstandard branch can establish equivalent intent and recovery state without manual reconstruction. | Task 243 itself used guided kickoff after main readiness correctly blocked; Blog dogfood shows inferred scope helps after kickoff rather than replacing it. | Atomic scaffolding of declared intent, branch policy, plan, session, tracker, and current pointers. | Keep kickoff as the supported source-work entry point. | `keep` | NO-GO — envelope creation still has unique value. |
| `aegis closeout` required ceremony | Validate and archive the task envelope, preserve handoff, and establish terminal workflow state. | Aegis closeout workflow. | Witness and GitHub prove delivery; Tasks 244–245 derive some completed source state. | Prove terminal projections, archives, handoff meaning, and resumed-state ordering remain correct without explicit lifecycle transition. | Tasks 244–245 fixed derivation and ordering; Task 251 removed only the advisory pending contradiction, not closeout itself. | Intentional archival boundary, final human summary, and coherent terminal projections consumed by later sessions. | Keep closeout; use dry-run, deterministic handoff repair, and reviewed rollback. | `keep` | NO-GO — deterministic delivery is only one closeout responsibility. |
| Protected workflow path rules for sessions, plans, and work-tracking | Prevent accidental direct edits from corrupting load-bearing workflow state. | Path guards and workflow-owned prefix rules. | Derived machine sections reduce the amount of direct mutation needed. | Prove a path is no longer authoritative or consumed before narrowing its guard, with negative tests for protected-later multi-path edits. | Tasks 248–252 expand Codex and shared-hook protection; no dogfood shows these paths are safe to leave unguarded. | Integrity boundary around human evidence, current pointers, lifecycle state, and generated markers. | Keep guards; revert any per-path relaxation through its own tested PR. | `keep` | NO-GO — all listed paths remain inputs or evidence. |
| Target-repo ceremony scaffolding | Give each repository local guidance, hooks, plans, sessions, tracking, and recovery contracts. | Managed Aegis install plus repo-specific instructions. | Capsule, witness, adapters, and vault add lower-ceremony capabilities. | Prove Codex-only, Claude-only, multi-agent, worktree, update, and recovery scenarios preserve both machine evidence and human workflow. | Blog and HP-Fetcher dogfood plus Tasks 237–252 cover multiple clients and updates; Task 252 shows bootstrap failures still require hardened local assets. | Repository-specific policy, product context, client bootstrap, compatibility, and human evidence surfaces. | Re-run supported managed update or restore the prior manifest-reviewed asset set. | `keep` | NO-GO — installed local contracts remain essential. |
| Packaged workflow templates | Seed projects with plan, session, tracker, handoff, decision, finding, and implementation contracts. | Managed template assets and installer. | Capsule and vault defaults can add derived views but cannot author project intent. | Demonstrate a fresh project can omit a specific template without losing the corresponding narrative or recovery function. | Blog started from a clean multi-agent install and still accumulated 8,114 useful human lines across 214 legacy documents. | Customizable human workflow schema and predictable cross-project evidence layout. | Keep templates versioned; restore any removed template from the prior packaged release. | `keep` | NO-GO — clean-install dogfood supports coexistence, not deletion. |
| Installed ceremony guidance docs | Tell agents which workflow actions are required in strict mode and optional or automatic in advisory mode. | Managed AGENTS, CLAUDE, CODEX, and contract blocks. | Capsule injection and concise command output provide live orientation. | Guidance must remain truthful, bounded, client-specific, and consistent with current enforcement behavior after every update. | Task 237 removed fossil strict-only guidance and Task 238 bounded output; Blog and source dogfood show this improves use without eliminating instructions. | Stable operating contract, owner policy, client reload and trust guidance, and explicit exceptions that runtime inference cannot invent. | Reinstall the last verified managed guidance block. | `keep` | NO-GO — truthful instructions remain part of the control plane. |
| Doctor and repair of old surfaces | Diagnose drift across current work, folders, plans, sessions, handoff, adapters, and manifests; preview scoped repair. | `aegis doctor`, `aegis repair`, shared detectors, and managed update. | Capsule and vault make contradictions visible but intentionally do not mutate authority. | Prove each repair class is either obsolete or safely replaced, with corruption regressions and no destructive generic repair. | HP-Fetcher Task 80 remains intentionally unrepaired; Tasks 242, 244–245, 251, and 252 show diagnosis and narrow fixes are still needed. | Encoded corruption knowledge, dry-run repair plans, compatibility diagnosis, and operator-controlled recovery boundaries. | Keep doctor and scoped repair; roll back a repair implementation through a reviewed source change, never by deleting evidence. | `keep` | NO-GO — observability without safe recovery is incomplete. |

## Tested Decision Contract

The matrix regression enforces:

- every required legacy surface is represented;
- every row names remaining unique legacy content and a rollback path;
- every current state is `keep` or `shadow`;
- every current Task 210 decision is `NO-GO`;
- the matrix cites Task 243 cross-repository evidence;
- Task 210 depends on TM-229, TM-233, and TM-243.

Any future move to `demote` or `retire` must deliberately revise this contract and carry new
per-surface evidence. It cannot happen as an incidental cleanup.

## Dogfood Fixtures

- HP-Fetcher Task 80 stale workflow-state residue remains an active fixture; see
  `docs/aegis/decisions/2026-07-07-hp-fetcher-task80-pr4-fixture.md`. Do not repair or hide it
  merely to make strict verification green.
- HP-Fetcher capsule/advisory evidence remains documented in
  `docs/aegis/hpfetcher-capsule-advisory-dogfood-2026-07-09.md`.
- Blog legacy-shadow dogfood remains documented in
  `docs/aegis/blog-legacy-shadow-sweh-dogfood-2026-07-09.md`.
- Task 243's derived-vault dogfood and coexistence audit supersede the old single-fixture
  assessment with current source, Blog, and HP-Fetcher measurements.

## Current Decision

The passive stack is valuable and mature enough to own observed facts in advisory mode. The
legacy stack is valuable and still owns declared intent, narrative, recovery context, and several
lifecycle and compatibility contracts. The derived Obsidian vault makes both navigable without
becoming authority.

Task 210 remains **NO-GO**. No broad retirement, demotion, deletion, or cessation of generation is
authorized. Keep improving generated sections and reducing duplicated ceremony through small,
reversible changes; preserve both systems until the owner makes a later, explicit per-surface
decision.
