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

The result binds repository identity, exact rig, branch/head/cleanliness, current plan/session pointers, ACTIVE trackers, adapter instructions, and literal Beads read commands. Stop if the root is not an exact Git worktree root, registry/descriptor identity is ambiguous, or authority is not `beads`.

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

Validate it against `config/project-descriptor.schema.json`, commit it through the repository’s normal review path, register/provision the rig separately, and run the context command with `--check`. A descriptor does not create a rig, grant permissions, or install infrastructure.

## Shared agent roles

- Codex: executing/orchestrating lane, subject to repository and operator gates.
- Fable: independent read-only reviewer by default. It consumes the same context capsule and repository instructions; it does not need broader filesystem or command permissions to review.
- Managed workers: bounded by their explicit contract and the project’s runtime policy.

Caller identity is never authorization. Frozen request content, exact paths/digests, repository state, and the operator’s scoped authority remain the decision inputs.
