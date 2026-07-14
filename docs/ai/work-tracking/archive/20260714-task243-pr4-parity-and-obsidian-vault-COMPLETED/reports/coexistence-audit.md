# Passive Evidence And Legacy S:W:H:E Coexistence Audit

**Task**: 243.2
**Date**: 2026-07-14
**Repositories inspected**: Aegis source, Blog, HP-Fetcher
**Downstream repository mutations**: none
**Decision**: preserve both systems; do not execute Task 210 retirement

## Executive Decision

The capsule-era stack and the legacy S:W:H:E stack solve different parts of the workflow and
must coexist:

- the append-only ledger records observed machine facts with near-zero agent ceremony;
- the capsule computes current orientation from live sources;
- the witness proves deterministic delivery conditions at a boundary;
- legacy plans, sessions, trackers, handoffs, decisions, findings, and implementation notes
  preserve declared intent, human reasoning, progress narrative, and recovery context;
- the derived Obsidian vault links those sources without becoming authority or writing back.

The replacement question is therefore not “can the ledger delete the Markdown?” It is “which
facts should be machine-derived, and which narrative remains intentionally human-authored?” The
current evidence supports reducing duplicated ceremony and generating more mechanical sections,
but it does not support deleting, demoting, or ceasing validation of the legacy surfaces.

Task 210 is a **NO-GO** at this checkpoint. Task 243 does not implement retirement.

## Evidence Population

The same read-only vault builder was run against all three repositories, with disposable output
under `/tmp`. Every second build over an unchanged authoritative snapshot was a no-op.

| Fixture | Ledger rows | High-signal rows | Stable identity edges | Tasks + subtasks | Legacy documents | Human legacy lines |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Aegis source | 15,463 | 204 | 117 | 637 | 2,175 | 72,963 |
| Blog | 2,506 | 97 | 42 | 39 | 214 | 8,114 |
| HP-Fetcher | 45,473 | 1,047 | 1,573 | 367 | 33 | 3,948 |

The complete build measurements and snapshot digests are in
`reports/obsidian-vault/dogfood.md`. Blog was active during inspection, so its row is the exact
successful snapshot rather than a permanent append-only count.

## Unique Legacy Content

Generated Aegis marker blocks were excluded before counting human-authored nonblank lines. The
inventory records structure and digests; it does not copy legacy prose into the vault.

| Legacy kind | Aegis source human lines | Blog human lines | HP-Fetcher human lines | Content the passive stack does not replace |
| --- | ---: | ---: | ---: | --- |
| Changelog | 1,838 | 263 | 535 | Curated milestones, causal sequencing, and release narrative. |
| Decision | 1,457 | 368 | 41 | Alternatives, rationale, owner judgment, and trade-offs. |
| Implementation | 3,869 | 448 | 556 | Intended design, implementation reasoning, and durable technical explanation. |
| Other legacy documents | 26,743 | 1,704 | 29 | Contracts, research, reports, project-specific operating context, and historical evidence. |
| Plan | 15,024 | 1,831 | 462 | Declared intent, ordered approach, expected evidence, and scope amendments. |
| Risk context | 5,605 | 1,574 | 827 | Findings, handoff context, unresolved risk, and owner-facing recovery guidance. |
| Session | 11,061 | 965 | 833 | Chronological reasoning, failed approaches, interruptions, and recovery context. |
| Tracker | 7,459 | 961 | 665 | Human progress narrative and checklist state; 1,653, 156, and 29 checkboxes respectively. |

These are not merely duplicate renderings of ledger rows. For example, the source corpus contains
15,024 plan lines and 11,061 session lines while its high-signal ledger projection contains only
204 events. The difference is intentional semantic content, not unexplained projection debt.

## Delivery And Recovery Dogfood

Blog PRs #7 through #24 provide a concentrated delivery corpus: 17 merged PRs and one closed
draft (#14). They cover documentation realignment, protected CI, controlled auto-merge,
canaries, closeout evidence, managed-runtime refresh, cross-agent skills, dependency security,
and a verification-only manifest policy. This validates passive delivery evidence and boundary
automation over many real merges, but it does not make their plans, sessions, task archives, or
decision records redundant.

Later source Tasks 237–252 add complementary evidence:

- Task 237 made installed guidance truthful and mode-aware.
- Task 238 bounded agent-facing command output.
- Tasks 239–240 improved worktree and child-agent attribution.
- Task 241 made the witness quiet and deterministic.
- Task 242 extracted safer managed updates.
- Tasks 244–245 made completed source state and delivery ordering derivable.
- Tasks 246–250 hardened evidence-gated autonomous delivery and the Codex adapter.
- Task 251 made advisory pending evidence non-blocking at delivery without deleting it.
- Task 252 hardened shared Codex hook bootstrap behavior.

This evidence justifies `shadow` for mechanical duplicate paths where passive capture now owns
the observed fact. It does not justify `demote` or `retire` for narrative or compatibility
surfaces.

## Cross-Repository Findings

### Aegis source

The source repository has the broadest narrative corpus and the most complete replacement
components. Its vault proves deterministic graph construction and surfaces 117 stable identity
edges, while preserving 72,963 human-authored legacy lines. Even here, Taskmaster, plans,
sessions, and archived work-tracking remain active inputs to delivery and recovery.

### Blog

Blog proves the model under fast real-world delivery. The ledger and witness captured merge and
policy facts; the legacy system retained product rationale, baseline findings, owner decisions,
and task recovery context. The 97 generated marker blocks coexist with 8,114 human lines. That is
successful augmentation, not replacement.

### HP-Fetcher

HP-Fetcher remains the strongest scale and failure-history fixture: 45,473 ledger rows, 1,573
stable identity edges, 470 tool failures, and the intentionally preserved stale Task 80 pointer.
The capsule can expose that contradiction without repairing it. The old surfaces still explain
why the state exists and what must not be destroyed. That combination is more useful than either
system alone.

## Authority And Lifecycle Contract

| Concern | Authoritative or preferred owner | Coexisting view or narrative |
| --- | --- | --- |
| Task status and dependencies | Current task authority, presently Taskmaster | Tracker and vault task links |
| Git branch, HEAD, diff, PR, and CI | Git and GitHub | Capsule, witness report, delivery evidence, vault links |
| Observed tool and mutation facts | Append-only Aegis ledger | Bounded evidence notes and generated S:W:H:E blocks |
| Current orientation | Computed capsule | Handoff and vault orientation note |
| Delivery eligibility | Deterministic witness and protected CI | Closeout report, handoff, and PR narrative |
| Declared intent and rationale | Plan, decisions, implementation notes, owner input | Capsule summary and vault links |
| Human progress and recovery context | Session, tracker, findings, handoff | Generated markers and capsule open loops |

No vault note is permitted to write back. No generated marker may overwrite marker-external human
content. Advisory pending evidence is preserved rather than drained, and strict enforcement may
still fail closed where its profile requires reconciliation.

## Risks That Remain

- The ledger still under-represents work performed by agents whose worktrees lack the managed
  adapter; Tasks 239–240 improve identity but do not eliminate all deployment gaps.
- Narrative provenance is structural rather than semantic: line counts and digests prove unique
  content exists, not that every sentence remains current.
- Task authority is due to migrate from Taskmaster to Gas Town later, but that migration is
  explicitly outside Task 243 and requires separate owner authorization.
- The derived vault is a disposable local view, not a synchronization mechanism, backup, or
  replacement database.
- Broad PR-4 removal would still create irreversible compatibility and recovery risk without a
  demonstrated benefit.

## Required Follow-Through

1. Keep the legacy system operational and truthful alongside the passive stack.
2. Prefer generated marker sections for machine-observed facts; preserve human-authored sections.
3. Keep agent-facing Aegis output bounded and the witness deterministic.
4. Continue worktree/adapter coverage dogfood across supported clients.
5. Treat any future per-surface demotion as a separate reversible decision with new evidence.
6. Do not begin Task 210 or Taskmaster-to-Gas-Town migration from this task.

## Conclusion

The coexistence model is working: the new stack lowers ceremony and improves factual continuity,
while the old stack preserves the intent and reasoning that passive observation cannot infer.
The Obsidian vault makes both easier to navigate, but deliberately owns neither. Every PR-4 row
therefore remains `keep` or `shadow`, and every row is a Task 210 `NO-GO` at this checkpoint.
