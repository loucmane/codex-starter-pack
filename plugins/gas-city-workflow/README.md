# Gas City Workflow plugin

Version `0.1.0` packages the common cold-start workflow without copying project state into prompts or widening permissions.

- `skills/gas-city-workflow/SKILL.md` is the small routing skill.
- `scripts/project_context.py` emits the live read-only context capsule.
- `config/projects.json` binds the three established projects.
- `.gas-city-workflow.json` descriptors onboard future projects without changing plugin code.
- `adapters/` keeps Codex execution and Fable read-only review on the same contract.

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
