# Legacy-Shadow S:W:H:E Projection Contract

Task: TM-233

Status: design prerequisite for TM-210 (`Capsule PR-4: retirement`). This document defines
how the old workflow scaffolding and the new capsule/ledger/witness stack coexist. It does not
authorize retirement or deletion of any legacy surface.

## Decision

Keep the old sessions, plans, trackers, handoffs, implementation logs, decisions, and changelog
surfaces during the transition, but change their role:

- The passive ledger remains the source of machine evidence.
- The capsule remains the primary current-state orientation surface.
- Taskmaster, git, PR metadata, CI, and witness remain delivery/current-truth authorities.
- Legacy work-tracking files remain human-readable projections, historical records, and
  shadow hardening oracles.

The old S:W:H:E shape is preserved, but it must be produced from ledger-backed projections at
workflow boundaries instead of requiring a manual `aegis log` after every mutation.

## Non-Goals

- Do not restore log-after-every-mutation blocking.
- Do not drain advisory-era pending events as if they were strict-mode debt.
- Do not overwrite human-authored history in old workflow files.
- Do not delete or archive Task 80 residue in HP-Fetcher as part of this task.
- Do not make old current-work, plans, sessions, or active-folder metadata equal authority when
  they disagree with Taskmaster, git, and capsule truth.

## Authority Model

| Question | Primary authority | Legacy role |
| --- | --- | --- |
| What branch/HEAD are current? | Git | none |
| What changed? | Git + passive ledger | tracker/implementation may explain why |
| What task is done/pending? | Taskmaster | current-work is fallback and conflict evidence |
| What work is active? | scope record + branch + Taskmaster + capsule | current-work and active folders are compatibility fallback |
| What tests are valid at HEAD? | verification ledger + CI + witness | closeout report is historical support |
| What did we decide and why? | decisions/tracker/handoff + optional PR-3 narration | legacy remains valuable |
| Can this merge? | witness + CI + protected branch policy | closeout is supporting evidence |
| What happened historically? | ledger + legacy projections | legacy remains readable context |

When Taskmaster, git, and capsule agree against a legacy current-work surface, current truth uses
Taskmaster/git/capsule. The legacy mismatch is still recorded as a shadow finding.

## Projection Model

S:W:H:E updates become derived projections from selected ledger events:

```text
ledger events -> projection planner -> generated S:W:H:E sections -> legacy files
```

Projection targets:

- `sessions/*.md`
- `plans/*.md`
- `TRACKER.md`
- `IMPLEMENTATION.md`
- `CHANGELOG.md`
- `DECISIONS.md`
- `HANDOFF.md`

The projection engine must preserve human-authored content and only write inside generated
sections with stable markers.

Required marker shape:

```markdown
<!-- AEGIS:BEGIN generated-sweh-projection -->
...
<!-- AEGIS:END generated-sweh-projection -->
```

Files without the markers must not be rewritten wholesale. The first projection may append a new
generated section at the nearest established local section boundary, but it must not delete or
reflow existing prose.

## Projection Granularity

Project high-signal events, not every raw tool call.

Boundary triggers:

- session start or resume
- explicit scope/plan change
- task status change
- verification command outcome
- witness or pre-delivery check
- PR created, updated, merged, or closed
- risk-register change
- explicit `aegis ledger project-sweh` projection command

Low-level tool events stay in the ledger unless they support a higher-level summary.

Implemented command surface:

```bash
aegis ledger project-sweh --target-dir . --output docs/ai/work-tracking/active/<folder>/TRACKER.md
aegis ledger project-sweh --target-dir . --active
aegis scope set <task-id> <glob>... --project-sweh
```

`--output` updates one named legacy markdown surface. `--active` resolves existing legacy
surfaces from `.aegis/state/current-work.json` and projects the same ledger slice into the
active session file, active plan file, and existing work-tracking markdown files. Both modes
write only inside the generated marker block. `scope set --project-sweh` is the first
boundary integration: it records the scope event in the passive ledger, then projects existing
active legacy surfaces as a follow-up view update. Projection is skipped if no legacy surfaces
exist.

## S:W:H:E Entry Shape

Projected entries should remain recognizable to existing workflow readers:

```markdown
- [S:<session> W:<work> H:<handler> E:<evidence>] <past-tense summary>
```

Rules:

- `S` identifies the session or resume lineage when known.
- `W` identifies the task, scope record, branch, or PR.
- `H` identifies the logical handler (`edit`, `verify`, `witness`, `task-truth`,
  `delivery`, `risk`, `legacy-shadow`) rather than raw shell fragments.
- `E` references ledger event IDs, witness IDs, commit hashes, or report paths.
- Summaries are generated from normalized paths, outcomes, and existing narrative context.
- Raw command strings must not be rendered by default.
- Redacted command summaries may be shown only when needed for debugging.

## Legacy Shadow Findings

Old checks continue to run where useful, but each check must have a policy:

- `block`: may stop the action immediately.
- `warn`: appears in capsule/witness and records evidence, but does not block editing.
- `record-only`: records facts for later analysis.
- `disabled`: no longer runs.
- `replaced`: replacement owns the job; legacy may exist as generated/view-only output.

Initial policy guidance:

| Legacy check | Initial policy |
| --- | --- |
| current-work disagrees with Taskmaster/capsule | `warn` |
| `plans/current` stale | `warn` |
| `sessions/current` stale | `warn` |
| active folder count mismatch | `warn` |
| advisory pending queue non-empty | `warn` |
| missing legacy reports subdir | `record-only` |
| tracker/handoff exists | `record-only` |
| protected hook/settings/security path edited unexpectedly | `block` |
| destructive git command | `block` |
| secrets/exfiltration/prod deploy patterns | `block` |
| missing or stale verification at delivery | `block` in witness, not editing |

The policy table is conservative. Individual rows may change only with replay or dogfood
evidence and a PR-4 parity row.

## Advisory Pending Lifecycle

Advisory-era pending events are audit evidence, not strict-mode debt.

Required behavior:

- Keep advisory pending events queryable as evidence.
- Summarize or link them from capsule/projections when relevant.
- Do not hard-block the next strict-mode tool call merely because advisory-era events exist.
- If switching from advisory to strict, surface a reconciliation report first.
- Do not silently discard advisory-era events.

Strict-mode pending events may still retain stronger semantics, but they must be distinguishable
from advisory-era events.

## Idempotency And Safety

Projection must be deterministic and repeatable:

- A second projection over the same ledger range produces no duplicate S:W:H:E entries.
- Projection state records the last included ledger event per target surface.
- If projection state is missing, the engine can rebuild generated sections from ledger ranges.
- Human-authored content outside generated markers is never rewritten.
- Projection failures are warnings unless they affect a delivery witness requirement.
- Generated sections include enough evidence references to audit back to the ledger.

## HP-Fetcher Acceptance Fixture

Use `docs/aegis/hpfetcher-capsule-advisory-dogfood-2026-07-09.md` as the first downstream
fixture.

Acceptance expectations:

- Task 80 current-work residue becomes a legacy shadow warning, not current authority.
- Taskmaster/capsule truth remains primary for task status and next action.
- Advisory pending backlog is retained as audit evidence, not treated as strict debt.
- Old Task 80 tracker/handoff/plans remain readable historical context.
- Generated S:W:H:E projection does not overwrite existing Task 80 human-authored history.
- Stale verification remains a witness/delivery concern.

## Clean-Repository Acceptance Fixture

Use `docs/aegis/blog-legacy-shadow-sweh-dogfood-2026-07-09.md` as the first clean-install
fixture. It proves that projection can:

- refuse to invent absent legacy scaffolding;
- populate eight intentionally created session/plan/work-tracking surfaces;
- preserve template and human-readable content outside the marker block;
- remain idempotent before and after observation archival;
- operate through a truly read-only SQLite connection in a sandbox;
- close the observation without `--allow-dirty` or unexpected changes.

The fixture also preserves its first malformed `S:unknown` ledger event as evidence for the
scope-context fix instead of rewriting append-only history.

## PR-4 Implications

PR-4 should not remove old work-tracking surfaces merely because capsule exists. A safer
intermediate state is `demote`: old surfaces remain generated/view-only projections while the
capsule, ledger, and witness own current truth and delivery discipline.

Any PR-4 row that proposes `demote` or `retire` for a legacy surface must say whether a
S:W:H:E projection remains:

- required generated projection
- optional generated projection
- historical only
- retired

Rows that still need human-readable narrative should prefer generated projection or keep/shadow,
not deletion.
