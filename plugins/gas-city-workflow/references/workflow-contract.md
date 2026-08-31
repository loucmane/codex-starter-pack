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

Before registry or descriptor resolution, the context command applies `config/root-policy.json` to
the Git common directory. `/home/loucmane/codex` is preserved historical evidence, not a source
root; its main checkout and all of its linked worktrees fail with the canonical replacement path.
The same evaluator is installed as one user-level Codex and Claude PreToolUse hook, preventing a
cold-start agent from mutating the historical root even before it remembers to run context. Project
trust is defense in depth only; the hook is the active mutation boundary. Canonical IDLE and active
task states use the same identity contract and remain valid.

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

Validate it against `config/project-descriptor.schema.json`, commit it through the repository’s
normal review path, register/provision the rig separately, and run the context command with
`--check`. A descriptor-only project derives its worktree root from the canonical checkout. The
host registry entry must declare the absolute `rig_root` used for Beads export; `rig_root` is
deliberately excluded from descriptor parity because repository descriptors must remain portable.
The host registry may also bind an explicit canonical root or exceptional worktree root. A
descriptor does not discover a rig, guess a store path, grant permissions, or install
infrastructure.

For Codex, onboarding is not complete until the exact generated project hooks are loaded and
trusted in the client-local trust store. Run `managed_delegation_canary.py check` and one fresh
`apply --run-id ...` from the clean canonical Gas City Operations source after any managed-hook
release. The canary uses a synthetic descriptor-managed repository, never invokes a native
delegation tool, and must prove all of the following in one transaction: exact Aegis hook
enumeration, exact-hash trust through the supported app-server API, a tier-C
`native_delegation_requires_gas_city` denial, unrelated local-read non-interference, and
byte/mode/owner-exact restoration of the user config. A remembered `/hooks` click or a source-only
unit test is not live enforcement evidence. Then run `trust-project --project-root <canonical>
--run-id ...` for each installed project. That transaction retains only the exact managed-hook
hashes after a denial/allow proof and a byte-identical second application; it restores the entire
starting config on any failure.

## Shared agent roles

- Codex: executing/orchestrating lane, subject to repository and operator gates.
- Fable: independent read-only reviewer by default. It consumes the same context capsule and repository instructions; it does not need broader filesystem or command permissions to review.
- Managed workers: bounded by their explicit contract and the project’s runtime policy.

Caller identity is never authorization. Frozen request content, exact paths/digests, repository state, and the operator’s scoped authority remain the decision inputs.

## Delegation authority

Managed-project delegated work is created from a Bead through a reviewed `gc sling` route. The
shared project PreToolUse gate mechanically denies Claude `Agent`/`Task` and Codex native
create/resume tools before provider work starts. `SubagentStart` is retained only for lifecycle
evidence because it cannot block creation. A route refusal or unavailable Gas City lifecycle is a
stop condition, never permission to fall back.

An exceptional native request requires `.gas-city-delegation-exceptions.json` conforming to the
installed Aegis schema. Authorization binds the exact request digest, project, adapter, normalized
tool, `codex/*` branch, Bead, and review evidence. The complete file must be tracked and clean at
HEAD and byte-identical on the project's canonical reviewed base. Session, caller,
agent identity, advisory mode, and ordinary break-glass tokens cannot satisfy or relax it.
