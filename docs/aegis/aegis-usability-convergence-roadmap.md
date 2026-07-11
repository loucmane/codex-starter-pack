# Aegis Usability Convergence Roadmap

Status: Task 236 planning contract

Date: 2026-07-11

Gates: Capsule PR-4 / Task 210

## Thesis

Aegis has proved the replacement architecture: passive evidence, a computed capsule, policy
replay, a deterministic delivery witness, and generated legacy projections. It has not yet
proved that the old ceremony can be retired safely in the multi-agent workflow that now does
most real implementation work.

The next program is therefore not a broad PR-4 deletion pass. It is a convergence program that
makes Aegis:

1. truthful about advisory versus strict behavior;
2. bounded for an LLM context window;
3. present and attributable in worktrees and subagents;
4. useful as the canonical delivery-boundary witness;
5. safer to update and maintain; and
6. evidence-ready for per-surface PR-4 decisions.

Task 210 remains blocked until this program produces the required proof. Legacy surfaces remain
`keep` or `shadow` unless the replacement parity matrix explicitly authorizes `demote` or
`retire` with dogfood and rollback evidence.

## Consumer Evidence

The original HP-Fetcher deployment proved that strict per-mutation ceremony was too costly and
too fragile. The current advisory deployment proves that passive recording can stay out of the
way while preserving useful truth.

The 2026-07-11 evidence adds four corrections to the existing roadmap:

- **Context is a product budget.** A live `aegis status` invocation emitted roughly 21,600
  tokens and 3,559 lines because it enumerated thousands of pending event IDs. Every default
  command must be designed as if its output will enter an agent context window.
- **The instruction surface is stale.** The Blog's managed `CLAUDE.md` still spends 69 lines
  commanding strict kickoff/log/closeout ceremony while the project intentionally runs in
  advisory mode. Repeatedly teaching agents to ignore repository instructions degrades the
  authority of all project guidance.
- **The worktree corpus may be biased.** The ledger is keyed by Git common directory and should
  be shared by normal worktrees, but the primary Blog consumer reports that dispatched agents
  commonly see no active Aegis integration and skip ceremony. The failure may be asset presence,
  hook activation, client behavior, shared-store resolution, or attribution. It must be measured
  before a fix is selected.
- **The witness is the useful enforcement boundary.** The consumer's shipping loop already
  performs scope mapping, verification-at-HEAD, diff review, and skipped-gate review manually.
  A quiet deterministic witness can replace that hand-built process without blocking editing.

The dated command evidence is stored in the active Task 236 report directory. Existing primary
dogfood remains in:

- `docs/aegis/hpfetcher-capsule-advisory-dogfood-2026-07-09.md`
- `docs/aegis/blog-legacy-shadow-sweh-dogfood-2026-07-09.md`
- `docs/aegis/legacy-shadow-sweh-projection-contract.md`
- `docs/aegis/pr-4-replacement-parity-matrix.md`

## Program Invariants

- Advisory mode never requires per-mutation logging, pending-event draining, handoff repair, or
  closeout ceremony.
- Strict mode remains opt-in and preserves hard protection until a parity row authorizes change.
- A default command never emits an unbounded event, path, finding, or repair list.
- A missing hook or unsupported child-agent channel is reported as missing coverage, never as a
  successful capture.
- The upstream source checkout can complete and archive work without fabricating installed-target
  state or retaining a misleading sole `-ACTIVE` folder.
- Worktree and child-agent events cannot be used for policy replay unless branch, worktree,
  agent, and parent attribution are trustworthy.
- PR-controlled code is never executed to decide delivery eligibility.
- No task in this program drains HP-Fetcher's advisory pending queue or repairs the Task 80
  parity fixture.
- Installer decomposition is incremental and behavior-preserving; no rewrite is authorized.
- Task 210 may demote only matrix rows with complete proof, dogfood, rollback, and explicit
  go/no-go decisions.

## Workstream C1 / Task 237: Truthful Mode-Aware Guidance

Replace the strict-only managed `CLAUDE.md`, `AGENTS.md`, and `CODEX.md` entry blocks with a
small mode-aware contract.

Required behavior:

- Tell the agent to inspect the enforcement mode once at orientation.
- In advisory mode, say that passive recording is automatic, manual pending-event draining is
  forbidden, `aegis brief` supplies orientation, and `aegis witness` owns the delivery boundary.
- In strict mode, point to `.aegis/contract.md` for the detailed kickoff/log/verify/closeout loop.
- Keep the managed startup block at or below 25 nonblank lines per agent entrypoint.
- Preserve project-owned instructions outside the managed block byte-for-byte.
- Keep strict instructions installed and testable; this task changes guidance, not underlying
  gate behavior.

Acceptance evidence:

- Clean install, update, and local-divergence fixtures for Claude, Codex, and multi-agent modes.
- Negative assertions that advisory guidance does not command manual logging, handoff repair,
  pending draining, or required closeout.
- A Blog session where child agents no longer apologize for correctly skipping strict ceremony.

Rollback: reinstall the previous managed entry blocks while retaining advisory enforcement.

## Workstream C2 / Task 238: Universal Context Budgets

Introduce one shared output-budget contract for `status`, `next`, `doctor`, `verify`, `update`,
`witness`, `replay`, and closeout failures.

Default contract:

- at most 60 lines;
- at most 8 KiB encoded output;
- counts by category and bounded top samples;
- one copyable next action;
- artifact paths for full details;
- no event-ID, path, repair, or finding enumeration beyond the configured sample cap.

Explicit detail modes:

- `--verbose` expands bounded diagnostics;
- `--all` or a command-specific include flag requests full enumeration;
- `--json` remains bounded by default;
- complete machine detail is written to a report artifact rather than stdout.

Acceptance evidence:

- fixtures at 0, 10, 3,500, and 100,000 events;
- byte and line assertions for text and JSON output;
- exact counts and truncation markers preserved under sampling;
- CI failure output remains bounded while its artifact contains full detail;
- HP-Fetcher's pending-event fixture produces a one-screen status report.

Rollback: restore the previous renderer while retaining generated full-detail artifacts.

## Workstream C3 / Task 239: Worktree And Subagent Capture Audit

Build a diagnostic harness before changing recorder behavior. The audit must distinguish:

- worktree created from a pre-install commit;
- tracked Aegis assets absent from the child checkout;
- project settings present but hooks not loaded by the client;
- hook loaded but unable to resolve the source root;
- shared Git-common-dir ledger resolution mismatch;
- child events recorded without branch/worktree/agent attribution;
- parent dispatch events mistaken for child implementation traffic; and
- events lost when an ephemeral worktree is removed.

Required matrix columns:

- client and version;
- parent session and child identifier;
- worktree path, branch, HEAD, and Git common directory;
- presence and checksum of shim/settings/recorder assets;
- resolved ledger path;
- SessionStart/PostToolUse/PostToolUseFailure/Stop capability;
- event counts and event IDs before and after the child action;
- attribution fields; and
- supported, unsupported, degraded, or failed result.

Acceptance evidence:

- two normal linked Git worktrees;
- one actual dispatched Claude child agent;
- one Codex worktree or explicit unsupported result;
- successful mutation, failed command, verification, and worktree-deletion scenarios;
- a checked-in coverage report and replay-safe fixture with no secrets or raw prompts.

Rollback: diagnostic-only; remove the harness and fixtures without touching runtime behavior.

## Workstream C4 / Task 240: First-Class Worktree And Child Attribution

Implement only the correction selected by C3.

Required behavior:

- all worktrees of one repository resolve the intended shared ledger;
- events record repository identity, worktree root, branch, HEAD, `agent_id`, `agent_type`, and
  `parent_agent_id` where the client provides it;
- parent orchestration and child implementation events remain distinguishable;
- concurrent writers do not lose, duplicate, or cross-attribute events;
- branch-scoped witness and replay queries do not consume unrelated worktree traffic;
- removed ephemeral worktrees do not remove their ledger history; and
- unsupported client hook surfaces are explicit capability gaps.

Acceptance evidence:

- two concurrent child worktrees with distinct source mutations and command failures;
- deterministic event ownership after worktree teardown;
- WAL contention and retry tests;
- no cross-branch verification-at-HEAD false positives;
- measured capture coverage before and after the implementation.

Rollback: disable child enrichment and retain parent-only recording with an explicit degraded
coverage report.

## Workstream C5 / Task 241: Quiet Witness Shipping Interface

Make the deterministic witness the canonical local pre-delivery command.

Required behavior:

- one-screen default output under the C2 budget;
- stable exit classes for pass, fail, unsupported, and not-derivable-in-CI;
- branch/worktree-specific scope and ledger filtering;
- scope mapping, diff accounting, test-deletion escalation, verification-at-HEAD, task-flip
  containment, and native-CI delegation;
- a full delivery report artifact suitable for a PR body or CI attachment; and
- no LLM call or prose-string reconciliation.

Acceptance evidence:

- integration into a real dispatch-wave shipping step;
- at least one passing PR and seeded failures for stale verification, out-of-scope diff, test
  deletion, and stranded done flip;
- local and CI honesty tests;
- latency and output-size measurements.

Rollback: return to the existing witness command and manual shipping checklist.

## Workstream C6 / Task 242: Installer Decomposition - Managed Update Slice

Extract managed-asset planning, rendering, and update-safety logic from
`scripts/_aegis_installer.py` and its packaged mirror without changing generated behavior.

Required behavior:

- one authoritative implementation with explicit compatibility adapters;
- byte-identical generated assets unless an intentional fixture says otherwise;
- semantic local-divergence detection remains fail-closed;
- source-root and packaged operation remain equivalent;
- no migration or broad module rewrite.

Acceptance evidence:

- golden install/update plans for Codex, HP-Fetcher, and Blog fixtures;
- live-versus-packaged parity;
- generated-byte checks;
- safe update, manual review, unsafe overwrite, and rollback cases;
- installer-line-count and changed-surface measurements.

Rollback: revert the extraction commit; no target-repository migration is allowed.

## Cross-Cutting Task 244: Derivable Upstream Source Closeout

Close the self-hosting lifecycle gap exposed by Task 236: after the sole completed tracking folder
was archived, the upstream source checkout's guard could not find it because this checkout
intentionally has no installed-target `.aegis/state/current-work.json`.

Required behavior:

- an upstream source checkout may resolve one completed tracker from repository evidence without
  installed runtime state;
- derivation requires a task-bearing branch, a done Taskmaster task, one unambiguous matching
  `-COMPLETED` archive, and task/tracker identity parity;
- ambiguous archives, non-done tasks, ID mismatches, and paths outside the archive fail closed;
- installed targets continue to use the existing current-work state contract; and
- the next kickoff can start without first repairing or pretending that the completed folder is
  still active.

Acceptance evidence:

- focused guard, readiness, kickoff, archive, CI-clean-checkout, and next-task handoff tests;
- live archive of a completed upstream planning task without fabricated `.aegis/state`;
- a clean CI checkout where the completed archive is derivable; and
- rollback to the current sole-completed-`ACTIVE` compatibility posture.

Rollback: retain one completed tracker under `active/` as the explicitly documented compatibility
state; do not create synthetic installed-target state.

## Workstream C7 / Task 243: PR-4 Evidence Refresh

Refresh the replacement parity matrix after C1-C6 are dogfooded.

Required evidence:

- HP-Fetcher post-update capsule, ledger, status-budget, and legacy-residue snapshot;
- Blog PRs 7-24, including merged-state, denial, recovery, dependency remediation, controlled
  auto-merge, and Task 64 semantic-manifest policy evidence;
- the first ordinary timestamp-only autonomous-delivery canary;
- worktree/subagent capture coverage and attribution results;
- unique-content comparison between generated and human legacy surfaces;
- interrupted-session and removed-worktree recovery;
- positive and negative witness cases; and
- an explicit lifecycle for advisory-era pending events.

For every parity row, record:

- current job;
- replacement owner;
- proof result;
- dogfood references;
- unique content still present only in the legacy surface;
- rollback path;
- final `keep`, `shadow`, `demote`, or `retire` state; and
- explicit Task 210 go/no-go.

Acceptance evidence:

- matrix schema/guard tests;
- negative fixtures for missing proof, placeholder dogfood, missing rollback, and unsupported
  client coverage;
- no row changes state solely because its replacement code exists.

Rollback: revert matrix decisions; no runtime retirement occurs in this workstream.

## Dependency Graph

The intended sequence is:

```text
237 truthful guidance ----+
238 context budgets ------+--> 241 quiet witness ----+
239 capture audit -> 240 attribution ----------------+--> 243 parity refresh -> 210 PR-4
237 + 238 + 240 -----------> 242 installer slice ----+
244 source closeout ----------------------------------+
```

C1 and C2 may be implemented independently. C3 must precede C4. C5 depends on C2 and C4 so
its output and branch filtering use the converged contracts. C6 depends on the user-facing and
recorder behavior being characterized. C7 depends on every preceding workstream.

Task 210 depends directly on Task 243. Task 243 transitively requires Tasks 237-242 and Task 244,
while Tasks 242 and 244 retain Task 235's managed-update divergence guard as an explicit
prerequisite. C7 is the final evidence gate; it may conclude that no parity row is ready for
retirement.

## Standing Metrics

Every implementation task records:

- default output bytes and lines;
- governance tool calls as a percentage of total tool calls;
- p50 and p95 hook latency where measurable;
- parent versus child event coverage;
- unattributed and duplicate event counts;
- false-block and would-block counts;
- witness pass/fail/unsupported counts;
- repair and manual-review activations; and
- rollback result.

Program targets:

- advisory manual-governance calls below 5% of tool calls;
- zero interior advisory blocks;
- default command output at or below 8 KiB and 60 lines;
- 100% capture for supported child mutation and failure fixtures;
- zero cross-worktree attribution errors;
- zero PR-4 row transitions without complete proof and rollback.

## Explicit Non-Goals

- No hash chain for the single-owner ledger.
- No Aegis-built OS sandbox or policy language.
- No PR-3 narration unless deterministic fields demonstrably lose required intent.
- No broad event-sourced workflow rewrite.
- No strict-mode reactivation in HP-Fetcher.
- No pending-event drain, Task 80 repair, or legacy-artifact deletion.
- No big-bang installer rewrite.
- No PR-4 runtime retirement in Tasks C1-C7.

## Task 210 Entry Gate

Task 210 may begin only when:

1. Tasks 237-244 are done;
2. the updated parity matrix contains at least one evidence-backed `demote` or `retire` row;
3. every changed row has a tested rollback;
4. worktree/subagent coverage is either implemented or explicitly unsupported and excluded from
   claims;
5. the witness has both positive and negative real-project evidence;
6. advisory pending events have a documented lifecycle; and
7. upstream source closeout works without a stale active projection or fabricated target state;
   and
8. Task 210 is still implemented as small reversible per-surface changes.

If no row qualifies, Task 210 remains blocked. A successful convergence program is allowed to
conclude that no legacy surface should yet be retired.
