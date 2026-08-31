# Gas City Workflow plugin

Version `0.6.1` packages the common lifecycle, cross-project continuity audit, continuous
project-isolated Obsidian projections, and frozen report-only evidence reviews without copying
project state into prompts or widening permissions.

- `skills/gas-city-workflow/SKILL.md` is the small routing skill.
- `scripts/project_context.py` emits the live read-only context capsule.
- `scripts/workflow.py` executes journaled `begin`, `resume`, `recover`, `attach`, `checkpoint`,
  `verify`, `publish`, and `finish` transitions.
- `scripts/continuity.py` captures one immutable cross-project observation and renders identical
  machine and human Current/Next/Blocked/orphan views.
- `scripts/build_obsidian_registry.py` deterministically projects that same validated project
  registry into the continuous Obsidian reconciler configuration.
- `config/projects.json` binds established canonical roots, explicit host rig roots, and
  exceptional worktree-root overrides.
- `config/root-policy.json` is the single canonical/retired-root contract consumed by context and both user-level agent guards.
- `.gas-city-workflow.json` descriptors onboard future projects without changing plugin code.
- `adapters/` keeps Codex execution and Fable read-only review on the same contract.
- `skills/gas-city-evidence-workflow/` and `scripts/evidence/` provide the generic shadow-review
  contract while projects retain their own builders, prompts, rubrics, and report schemas.
- `scripts/codex_hook_trust.py` owns the bounded Codex JSON-RPC hook-trust transaction separately
  from the provider/agent installer.
- `scripts/install_root_policy.py` transactionally installs the shared evaluator into the user
  runtime, merges one exact PreToolUse registration into Codex and Claude, marks only the legacy
  Codex project entry untrusted, and repoints only Claude's Aegis source to the canonical checkout.

The context capsule derives the canonical checkout from Git common-directory truth. Linked worktrees must be direct children of the reported `workspace.worktree_root`; source work from arbitrary or preserved legacy roots fails closed.

The retired-root guard is user-level rather than project-local, so it still loads when the retired
project is deliberately untrusted. It blocks mutation-capable tools whenever the current Git
common directory is `/home/loucmane/codex`, including linked worktrees, while leaving read-only
inspection available. The installer preserves exact backups and modes, validates both adapters
against the same policy, trusts only the exact Codex user hook through the supported app-server
transaction, compares the historical checkout and worktree inventory before/after, and rolls back
every managed user file on failure. It never edits or deletes the historical checkout.

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

The evidence workflow similarly cannot grant dispatch or calculate a domain verdict. It binds
tracked project assets and external inputs, audits blind bundles and exact report directories,
validates evidence-only reports, and enforces seal/readback/dispatch/release ordering. Only
`mode=shadow` exists in v1. See `references/evidence-profile-contract.md`.

The continuity workflow is read-only. It de-duplicates shared Bead stores by rig, derives active
initiative scope from Beads, and checks Aegis, Git/worktrees, open PRs, lifecycle transactions,
managed-signing receipts, structured follow-ups, and Obsidian coverage. A future project can be
included with a validated local descriptor through repeatable `snapshot --project-root`; the
auditor never scans arbitrary directories. See `references/continuity-contract.md`.

The Obsidian registry is generated from that same project registry; it is never maintained as a
second hand-written project list. Each registered project owns only
`GasCity/<project-id>/Aegis`, and the global `GasCity/Continuity` dashboard is derived from the
auditor's machine report rather than independently reclassifying work. Generate and validate the
tracked registry with:

```bash
python3 plugins/gas-city-workflow/scripts/build_obsidian_registry.py --write --validate-roots
python3 plugins/gas-city-workflow/scripts/build_obsidian_registry.py --check --validate-roots
```

The installed user timer reconciles every enabled project and the dashboard. A changed projection
is atomically replaced, gated, reloaded once in the live Obsidian app, and read back. A
byte-identical cycle performs only the managed-note read; it does not reload Obsidian. Missing
direct project parents may be created only beneath the declared managed vault root. The installer
quiesces the timer before capture and restores its files, private state, managed output trees,
service result, and timer state exactly on failure. A registry entry binds the host's absolute
`rig_root`; the repository-local descriptor remains portable and never guesses that host path.
Adding a valid descriptor plus its reviewed host registry entry is therefore sufficient to
generate the same lifecycle for a future project without another daemon or agent memory.

For blind report lanes, `config/evidence-reviewer/` defines one generic rig-scoped Sol reviewer
whose work directory is `/home/loucmane/gascity/evidence-runs`, whose additional writable-root
list is empty, and whose prompt forbids project/Git/vault/host/network inspection. Preview the
bounded host install with:

```bash
python3 plugins/gas-city-workflow/scripts/install_evidence_reviewer.py
```

`--apply` is a separate live configuration mutation. It requires every registered rig suspended
and zero running agent sessions. On a fresh install it atomically installs the provider and two
agent files; on an append-forward repair it requires those installed bytes to remain exact. In
both modes it transactionally ensures the exact work directory is trusted in the attended Codex
`config.toml`, using an owned marker block while preserving all unrelated bytes and the original
file mode. It also verifies the byte-exact Gas City hook manifest under that root, lists the four
resolved hooks through Codex's app-server API, and upserts only those four runtime hashes through
one version-bound `config/batchWrite`. It then re-lists the hooks and requires every one to be
trusted. Arbitrary, extra, modified, differently sourced, or differently commanded hooks remain
blocked; the hook-trust bypass flag is never used. The transaction records mode-0600 before/after
evidence, validates the resolved provider, agent, prompt, project trust, and hook trust, reloads
only when Gas City configuration changed, preserves the controller epoch, and restores every
mutated surface byte-exact on failure. Conflicting entries, canonical-path aliases, malformed
TOML, unrelated nonblank config-byte or semantic changes, and managed-block drift fail closed.
The same transaction installs one project-local Codex exec-policy file containing only five
absolute control prefixes: claim, bead show/update/close, and drain acknowledgement. It validates
every allowed prefix and a negative lifecycle/routing/mail/molecule/restart/shell corpus through
`codex execpolicy check`, refuses unrelated rule files, and removes the file and newly created
rules directory on rollback. The broader Gas City worker policy is never installed for this lane.
Codex may normalize an adjacent blank separator while inserting its own tables; the exact prior
file is still preserved for rollback. Installation does not
authorize routing, rig resume, or evidence dispatch; a fresh managed reviewer session remains the
required proof that startup reaches its instructions without a prompt.

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
