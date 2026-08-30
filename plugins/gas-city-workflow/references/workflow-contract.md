# Gas City Workflow Contract

## Authority layers

1. The project-local `AGENTS.md` / `CLAUDE.md` defines repository rules.
2. Gas City Beads is the sole active work ledger.
3. Aegis plans, sessions, trackers, and S:W:H:E records are evidence and readiness controls, not a second task ledger.
4. Operator authorization remains separate for lifecycle, signing, publication, privileged mutation, deployment, and destructive actions.

The plugin adds no shell allowlists, writable roots, groups, capabilities, MCP write methods, or service access. Its context command only reads files and runs read-only Git queries. Its lifecycle command uses only the caller's existing repository and ledger authority; it never treats successful orientation or a bead status as authority for routing, rig lifecycle, signing, publication, privileged mutation, or deployment.

## Cold start

Run:

```bash
python3 <PLUGIN_ROOT>/scripts/project_context.py --root /absolute/project/root
```

The result binds repository identity, exact rig, canonical checkout, approved linked-worktree root, branch/head/cleanliness, current plan/session pointers, ACTIVE trackers, adapter instructions, and literal Beads read commands. Stop if the root is not an exact Git worktree root, registry/descriptor identity is ambiguous, the current worktree is outside the approved root, or authority is not `beads`.

## Lifecycle transitions

Run `workflow.py begin --root <canonical-root> --bead <id>` instead of remembering the
worktree/kickoff/claim/readiness sequence. The transition journal lives under the repository's Git
common directory at `.git/gas-city-workflow/transactions/<bead>.json`, outside individual linked
worktrees. It binds the exact project, rig, branch, worktree, and starting commit and advances only
through `planned → worktree-created → scaffolded → claimed → ready`.

- `begin` creates or safely adopts the exact derived worktree and starts the evidence workflow.
- `resume` derives the active bead from `sessions/state.json` when `--bead` is omitted and verifies
  or completes the same transaction.
- `recover` is the explicit operator-facing synonym for append-forward recovery after a proven
  pre-mutation failure or complete rollback.
- `attach` adds one already-declared blocking dependency to the current source-work context. It
  keeps the primary Aegis session, tracker, and branch, records the dependency separately under
  `attached_bead_ids` while preserving the one-item authoritative `bead_ids` field,
  claims the dependency idempotently, and journals the attachment. It refuses unrelated beads;
  do not open a second Aegis context while the parent source change is still active.
- `checkpoint`, `verify`, `publish`, and `finish` run their bounded checks and append results to
  the same transition journal.

The journal is evidence, not authority. A partial or contradictory filesystem, Git, bead, or
scaffold state blocks instead of being guessed away. Existing unscaffolded worktrees can only be
fast-forwarded when clean and ancestor-related; once scaffolded, their task branch is never moved
by lifecycle replay.

Projects whose canonical checkout is deliberately dirty or parked on a long-lived branch may
declare a validated `base_ref` in the registry or local descriptor. `begin` resolves the immutable
starting commit from that ref instead of canonical `HEAD`, without checking out, cleaning, or
otherwise mutating the canonical workspace. Refresh a remote-tracking ref before `begin` when the
task explicitly requires the newest remote default branch.

For `beads-with-frozen-legacy-evidence` projects only, `begin` preserves unrelated ACTIVE folders
that are tracked and byte-unchanged at the selected base commit. They remain historical inputs,
not the current task. A new or modified unrelated ACTIVE folder still blocks. Modern Aegis
profiles retain the one-ACTIVE-folder rule.

Projects without an installed Aegis foundation use the canonical Gas City Operations
`codex-task wizard kickoff --target-dir <worktree>` adapter. The executable is shared, but the
adapter validates the selected Git worktree root and writes every session, plan, tracker, and
plan-sync artifact beneath that target. Cross-project Taskmaster kickoff is forbidden. Installed
Aegis projects continue to use `aegis kickoff`.

## Workspace placement

The Git common directory is the source of truth for the canonical checkout. By default, linked worktrees must be direct children of a sibling `<canonical-name>-worktrees` directory. For example, `/home/loucmane/gas-city-ops` uses `/home/loucmane/gas-city-ops-worktrees`.

The central registry may declare an absolute `worktree_root` only for projects whose established layout cannot use that convention. The context capsule blocks arbitrary and legacy worktree locations before source readiness. Do not select a worktree root from remembered paths, available sandbox roots, or caller-provided convenience paths.

## Future-project onboarding

Prefer a project-local `.gas-city-workflow.json` so onboarding travels with the repository:

```json
{
  "schema": "gas-city-workflow.project.v1",
  "id": "example",
  "repository": "owner/example",
  "rig": "example",
  "workflow_authority": "beads",
  "workflow_profile": "beads-with-aegis-evidence"
}
```

Validate it against `config/project-descriptor.schema.json`, commit it through the repository’s normal review path, register/provision the rig separately, and run the context command with `--check`. A descriptor-only project derives its worktree root from the canonical checkout. Add a matching registry entry only when the host needs an explicit canonical-root binding or worktree-root override. A descriptor does not create a rig, grant permissions, or install infrastructure.

## Shared agent roles

- Codex: executing/orchestrating lane, subject to repository and operator gates.
- Fable: independent read-only reviewer by default. It consumes the same context capsule and repository instructions; it does not need broader filesystem or command permissions to review.
- Managed workers: bounded by their explicit contract and the project’s runtime policy.

Caller identity is never authorization. Frozen request content, exact paths/digests, repository state, and the operator’s scoped authority remain the decision inputs.
