# Gas City Workflow plugin

Version `0.2.0` packages the common lifecycle without copying project state into prompts or widening permissions.

- `skills/gas-city-workflow/SKILL.md` is the small routing skill.
- `scripts/project_context.py` emits the live read-only context capsule.
- `scripts/workflow.py` executes journaled `begin`, `resume`, `recover`, `checkpoint`,
  `verify`, `publish`, and `finish` transitions.
- `config/projects.json` binds established canonical roots and exceptional worktree-root overrides.
- `.gas-city-workflow.json` descriptors onboard future projects without changing plugin code.
- `adapters/` keeps Codex execution and Fable read-only review on the same contract.

The context capsule derives the canonical checkout from Git common-directory truth. Linked worktrees must be direct children of the reported `workspace.worktree_root`; source work from arbitrary or preserved legacy roots fails closed.

Start a bead from the canonical checkout with one command:

```bash
python3 plugins/gas-city-workflow/scripts/workflow.py begin \
  --root /home/loucmane/gas-city-ops \
  --bead ga-xxxx \
  --goal "Observable outcome"
```

`begin` validates project and rig identity, reads the bead and its dependencies, derives the
branch/worktree, creates or safely adopts it, creates the Aegis evidence scaffold, claims the
bead, runs readiness, and records every completed phase in a repository-local transaction
journal. `resume` and `recover` replay the same transition from live state; completed phases are
verified rather than repeated. The remaining commands record meaningful lifecycle checkpoints in
the same journal. None of them grants routing, rig lifecycle, signing, publication, privileged
mutation, or deployment authority.

Validate from the repository root:

```bash
python3 scripts/validate_codex_plugin.py plugins/gas-city-workflow
python3 plugins/gas-city-workflow/scripts/project_context.py \
  --root /home/loucmane/dev/blog --check
```

The bundled validator is CI-portable and enforces the stable manifest and skill-frontmatter
contract. The Codex `plugin-creator` validator remains an additional development-time check.

Installing or updating the plugin is a separate client-level action. The package itself contains no hooks, MCP server, app connector, or permission mutation.

After the Gas City Operations repository is present at its canonical path, register its tracked
marketplace and install the versioned plugin:

```bash
codex plugin marketplace add /home/loucmane/gas-city-ops
codex plugin add gas-city-workflow@gas-city-operations
```

The pre-rename checkout may be used for development validation, but it is not the canonical
marketplace path. Installing the plugin does not create a rig, edit a project, or widen Codex or
Fable permissions.
