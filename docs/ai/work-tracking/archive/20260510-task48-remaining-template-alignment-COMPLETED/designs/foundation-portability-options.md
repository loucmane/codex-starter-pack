# Foundation Portability Options

## Purpose

The portable foundation should be reusable across product sites, games, tools, documentation projects, and future repositories. This decision record compares delivery mechanisms and selects the direction that can be enforced and tested rather than remembered.

## Current Baseline

Already implemented:

- `.codex/config.toml` repo-structure contract.
- `python3 scripts/codex-task bootstrap init --target-dir <repo>`.
- `python3 scripts/codex-task sync plan --target-dir <repo>`.
- `templates/engine/core/portable-foundation-spec.md`.
- `templates/engine/validation/foundation-adoption-guide.md`.
- Cross-project fixture coverage for product-web, game/tool, docs-heavy, and utility/library shapes.
- Guard validation and work-tracking audit commands.

Current gap:

- The foundation has bootstrap and sync primitives, but it is not yet a polished installation/adoption product with a manifest, dry-run/doctor flow, upgrade contract, and clear optional wrappers.

## Options

| Option | Description | Strengths | Weaknesses | Decision |
| --- | --- | --- | --- | --- |
| A. Copyable template pack | Treat the repo as files to copy into each project. | Simple and transparent. | Manual, easy to drift, weak evidence, no upgrade path. | Reject as primary. |
| B. Repo-local CLI installer/adopter | Make `scripts/codex-task` the source of truth for install, adopt, doctor, dry-run, and sync behavior. | Testable in CI and temp repos; agent-agnostic; works offline; aligns with existing bootstrap/sync commands. | Requires CLI polish and manifest discipline. | Select as core. |
| C. MCP installer | Build an MCP server that installs/configures the foundation inside projects. | Good agent UX; can expose structured operations. | Depends on MCP availability before the foundation is installed; harder to use in CI; not agent-agnostic enough as the only source of truth. | Reject as primary; keep as optional wrapper. |
| D. Codex plugin/skill installer | Package the foundation as a Codex plugin or skill. | Strong Codex UX and distribution story. | Codex-specific; does not solve Claude/future-agent portability alone. | Optional wrapper after CLI core. |
| E. Hybrid CLI core plus MCP/plugin wrappers | CLI owns behavior and tests; MCP/plugin wrappers call the CLI. | Best balance: durable/testable core with good agent UX later. | Requires clear boundary so wrappers do not fork logic. | Selected direction. |

## Selected Direction

Use a hybrid architecture with the CLI as the enforceable source of truth:

```text
scripts/codex-task foundation|bootstrap|sync|doctor  -> source of truth
MCP server / Codex plugin / Claude command wrappers   -> optional adapters that call the CLI
tests with temp project fixtures                      -> acceptance gates
```

The MCP server idea is valid, but not as the first or only installer. MCP should be a control-plane adapter over a tested CLI, not the place where install semantics live.

## Proposed Task 46 Re-Scope

Task 46 should become the productization home for this direction:

**Title candidate**: Portable Foundation Installer and Adoption Contract

**Scope candidate**:

- Add a foundation asset manifest listing required, optional, generated, and repo-local files.
- Extend bootstrap/adoption commands with dry-run and doctor/report modes.
- Define install vs adopt vs upgrade behavior.
- Preserve existing files by default; require explicit force/update flags.
- Add tests using cross-project fixtures and temp repositories.
- Emit evidence suitable for CI and work-tracking.

## Non-Goals For Task 46

- Do not make MCP the only install path.
- Do not build a marketplace.
- Do not add template signing until distribution actually needs it.
- Do not implement autonomous cross-repo mutation; keep sync planning reviewable.

## Acceptance Direction

Task 46 should not be considered complete until a brand-new temp repo and an existing partial repo can both run:

```bash
python3 scripts/codex-task bootstrap init --target-dir <repo>
python3 scripts/codex-task <doctor-or-equivalent> --target-dir <repo>
python3 scripts/codex-guard validate --include-untracked
```

with clear reports and no unexpected clobbering.

## Progress Log

- **2026-05-10 16:00** — [S:20260510|W:task48-remaining-template-alignment|H:docs/design|E:docs/ai/work-tracking/active/20260510-task48-remaining-template-alignment-ACTIVE/designs/foundation-portability-options.md] Selected CLI-core plus optional MCP/plugin wrappers as the portable foundation installation direction.
