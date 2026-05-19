# Local MCP E2E Target Matrix

## Decision

Task 115 validates Aegis MCP behavior with two layers:

1. Generated throwaway projects under pytest `tmp_path` for fast CI-friendly regression coverage.
2. Concrete checked-in fixture projects under `tests/fixtures/aegis-target-projects/`, copied into temporary target directories for local-wheel MCP stdio smoke validation.

The fixture projects are test inputs, not maintained demo applications. This keeps the repository
small while making the "new project" and "already-started project" validation easy to inspect.

Task 115 also validates the positive installed-project workflow path. Aegis must not require
Taskmaster or Serena to reach `READY`; those integrations are optional accelerators. The portable
minimum is:

1. Installed Aegis runtime and Claude hook files.
2. Git branch containing a task/work id.
3. Aegis-native current work state in `.aegis/state/current-work.json`.
4. `sessions/current`, `plans/current`, and one active work-tracking folder aligned to the same id.
5. Rich generated workflow files: session, plan, tracker, findings, decisions, implementation notes, changelog, handoff, designs directory, and reports directory.
6. Plan/tracker checklist alignment.

## Target Shapes

| Target | Purpose | Seed Files |
| --- | --- | --- |
| Empty project | Prove first install into a new repository | `.gitkeep` or empty directory |
| Python app | Prove safe install beside Python packaging files | `pyproject.toml`, `README.md`, `src/example_app/__init__.py` |
| Web app | Prove safe install beside frontend app files | `package.json`, `src/main.ts`, `index.html` |
| Backend server | Prove safe install beside API/server code | `pyproject.toml`, `app/main.py`, `tests/test_health.py` |
| Docs-heavy project | Prove safe install beside existing docs | `docs/index.md`, `docs/architecture.md`, `README.md` |
| Partial Aegis install | Prove status/resources explain incomplete state | `.aegis/foundation-manifest.json` or `.aegis/contract.md` only |
| Conflict target | Prove install does not silently overwrite managed files | pre-existing managed file with non-Aegis content |

## Concrete Fixture Matrix

| Fixture | Project Type | Lifecycle | Purpose |
| --- | --- | --- | --- |
| `python-new` | Python | New | Prove Aegis can install beside a freshly created Python package shell |
| `python-started` | Python | Already started | Prove existing Python source and tests remain unchanged |
| `web-new` | Web app | New | Prove Aegis can install beside a freshly created frontend shell |
| `web-started` | Web app | Already started | Prove existing frontend entrypoint files remain unchanged |
| `backend-new` | Backend server | New | Prove Aegis can install beside a freshly created backend service shell |
| `backend-started` | Backend server | Already started | Prove existing backend app and health test files remain unchanged |

## MCP Operations

Each happy-path target should exercise:

- server creation with an explicit packaged/source root and target directory
- tool discovery for every V1 tool name
- resource and prompt discovery
- `aegis.inspect`
- `aegis.status`
- `aegis.plan_install`
- `aegis.install` refusal without `apply=true`
- `aegis.install` success with `apply=true`
- `aegis.kickoff` refusal without `apply=true`
- `aegis.kickoff` success with `apply=true`
- `aegis.verify` refusal without `acknowledge_report_write=true`
- `aegis.verify` success with `acknowledge_report_write=true`
- `aegis://work/current`
- `aegis://manifest/current`
- `aegis://contract/current`
- `aegis://install-plan/latest`
- `aegis://verification/latest`
- `aegis://managed-files`
- preservation of seed files byte-for-byte
- installed readiness reaching `READY` without `.taskmaster/` or `.serena/`
- packaged workflow templates installed under `.aegis/templates/workflow/`
- generated session, plan, tracker, findings, decisions, implementation, changelog, and handoff content containing the same core sections used by this repository's workflow

Partial and conflict targets should prove structured safety behavior:

- partial targets return readable status/resource states without crashing
- conflict plans identify manual-review or overwrite-sensitive operations
- conflict installs are refused or leave conflicting files unchanged

## Fixture Strategy

Use pytest factory helpers in a focused test module. Generated fixtures are preferred over
committed sample projects because the release matrix cares about target shapes, not application
implementation depth. If a later task needs public examples, those should be separate examples
with their own documentation and maintenance burden.

For the second layer, commit minimal fixture templates under `tests/fixtures/` and copy them into
`tmp_path` before mutation. The local-wheel MCP stdio smoke must run against the copied targets, not
the fixture templates themselves.

## Optional Integration Strategy

Options considered:

| Option | Summary | Decision |
| --- | --- | --- |
| Taskmaster-required | Keep readiness dependent on `.taskmaster/tasks/tasks.json` and make every installed project initialize Taskmaster | Rejected. It makes Aegis non-portable and forces a specific planning tool into every downstream project. |
| Serena-required | Require `.serena/` or Serena MCP memory for continuity before READY | Rejected. Memory is continuity only, not workflow evidence, and should never be a gate dependency. |
| Aegis-native minimum with optional integrations | Use `.aegis/state/current-work.json` plus session/plan/work-tracking files as the portable authority; validate Taskmaster only when no Aegis current-work state exists or current-work explicitly marks Taskmaster required; use Serena only when available | Chosen. This keeps the gate mechanical across projects while still allowing richer integrations in this source repo without making stale optional integrations block downstream projects. |
| MCP-only bootstrap | Require MCP `aegis.kickoff` for all kickoff operations | Rejected as the only path. MCP is useful, but the CLI must also work for projects and agents without MCP configured. |

The implemented design adds `aegis kickoff` and MCP `aegis.kickoff`. The Claude PreToolUse gate
allows this single bootstrap operation while readiness is `BLOCKED`; other hookable mutations remain
blocked until kickoff creates the aligned workflow state.

## Workflow Scaffold Template Strategy

Options considered:

| Option | Summary | Decision |
| --- | --- | --- |
| Hardcode kickoff document bodies in Python | Simple to implement, but hides the workflow contract in code and makes drift from this repository likely | Rejected |
| Install template docs but keep kickoff hardcoded | Gives agents something to read, but does not force generated scaffolding to follow the templates | Rejected |
| Package templates and render them during kickoff | Keeps source templates auditable, ships them into target projects, and makes generated workflow files reproducible | Chosen |

The implemented design stores source templates in `templates/aegis/workflow/`, packages the same files in
`aegis_foundation/assets/templates/aegis/workflow/`, installs them into target projects under
`.aegis/templates/workflow/`, and renders them from both CLI and MCP kickoff. Tests assert the generated
session, plan, tracker, findings, decisions, implementation, changelog, and handoff files contain required
sections rather than merely existing.

## Acceptance Gate

Task 115 is complete only when local MCP E2E tests pass for generated targets, the default installed-target
runtime matrix proves MCP install creates the Aegis/Claude files and the installed gate plus CLI kickoff can
scaffold and run real task output, local-wheel MCP stdio smoke passes for the concrete Python/web/backend
fixture matrix, `aegis kickoff` proves the installed target can move from `BLOCKED` to `READY` without
Taskmaster or Serena, the generated workflow scaffold is template-backed and content-verified, and the
handoff states whether the MCP is ready for GitHub release-candidate artifact publication. PyPI remains out
of scope.
