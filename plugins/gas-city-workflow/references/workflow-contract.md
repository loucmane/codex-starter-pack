# Gas City Workflow Contract

## Authority layers

1. The project-local `AGENTS.md` / `CLAUDE.md` defines repository rules.
2. Gas City Beads is the sole active work ledger.
3. Aegis plans, sessions, trackers, and S:W:H:E records are evidence and readiness controls, not a second task ledger.
4. Operator authorization remains separate for lifecycle, signing, publication, privileged mutation, deployment, and destructive actions.

The plugin adds no shell allowlists, writable roots, groups, capabilities, MCP write methods, or service access. Its context command only reads files and runs read-only Git queries.

## Cold start

Run:

```bash
python3 <PLUGIN_ROOT>/scripts/project_context.py --root /absolute/project/root
```

The result binds repository identity, exact rig, canonical checkout, approved linked-worktree root, branch/head/cleanliness, current plan/session pointers, ACTIVE trackers, adapter instructions, and literal Beads read commands. Stop if the root is not an exact Git worktree root, registry/descriptor identity is ambiguous, the current worktree is outside the approved root, or authority is not `beads`.

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
