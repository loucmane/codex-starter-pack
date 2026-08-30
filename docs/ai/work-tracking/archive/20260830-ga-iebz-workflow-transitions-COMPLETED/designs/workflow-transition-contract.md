# Memory-independent workflow transition contract

## Problem

The existing components are individually sound but require an agent to remember their
ordering. A fresh linked worktree must be kicked off before readiness can become READY,
while the routing skill currently says to run readiness first. The readiness renderer also
advertises `./.aegis/bin/aegis next`, although that untracked runtime is not present in a
fresh source worktree. This turns deterministic project state into conversational knowledge.

## Design

Expose one versioned workflow CLI with small phase modules:

- `begin`: derive project/bead/workspace state, create or reuse the exact worktree,
  scaffold source evidence, claim the bead, and require READY.
- `resume` / `recover`: inspect the transaction journal and live state, then complete only
  the next idempotent transition or refuse an ambiguous mismatch.
- `checkpoint`: synchronize plan/tracker state and return a fresh context capsule.
- `verify`: run the project readiness, guard, and Git-diff gates without publishing.
- `publish`: report the frozen signed-head/CI/merge contract; external publication remains
  separately authorized.
- `finish`: report and invoke the supported closeout sequence; bead close and Obsidian
  publication remain explicit terminal transitions.

The CLI is a router, not a second policy engine. It calls the existing project-context,
bead, Aegis/source-kickoff, readiness, guard, closeout, Git, and Obsidian surfaces. Skills
only point to this CLI and never duplicate lifecycle rules.

## Transaction model

`begin` writes a schema-versioned journal beneath the Git common directory so all linked
worktrees share one recovery record without adding source churn. The journal records the
immutable project identity, canonical and worktree roots, bead, slug, branch, base commit,
and completed phases. Each phase is derived again from live state before advancement.

Phases are:

1. `planned`
2. `worktree-created`
3. `scaffolded`
4. `claimed`
5. `ready`

Exact replay is idempotent. A different path, branch, base, bead, project, or source state
is a hard refusal. Recovery never deletes or resets an unexpected worktree.

## Source and installed targets

- An uninstalled source checkout uses its tracked `scripts/codex-task wizard kickoff`.
- An installed consumer uses the canonical Gas City Operations source runtime to call
  `scripts/codex-task aegis kickoff --target-dir ...`.
- Readiness is evaluated through tracked Python/source adapters, never an assumed local
  `.aegis/bin/aegis` shim.

## Performance boundary

Normal work pays for project/bead discovery plus the quick readiness gate. Full tests,
hosted CI, Obsidian publication, and live checks occur only at their existing publication
or closeout boundaries. No rig resume, dispatch, service mutation, deployment, key access,
or permission widening is introduced.

## Required fixtures

- fresh canonical project to READY;
- exact begin replay;
- interrupted phase recovery;
- branch/path/base mismatch refusal;
- descriptor-only future project using the derived sibling worktree root;
- installed-project kickoff backend;
- real `ga-k0ry` dry-run/bootstrap capsule;
- stable JSON output and zero policy duplication in the router skill.
