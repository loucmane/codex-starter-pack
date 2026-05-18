# Local MCP E2E Target Matrix

## Decision

Task 115 validates Aegis MCP behavior with generated throwaway projects, not checked-in demo
applications. The tests should create realistic target directories under pytest `tmp_path` and
drive the MCP tool/resource/prompt surface directly. This keeps the repository small while still
proving behavior across project shapes.

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
- `aegis.verify` refusal without `acknowledge_report_write=true`
- `aegis.verify` success with `acknowledge_report_write=true`
- `aegis://manifest/current`
- `aegis://contract/current`
- `aegis://install-plan/latest`
- `aegis://verification/latest`
- `aegis://managed-files`
- preservation of seed files byte-for-byte

Partial and conflict targets should prove structured safety behavior:

- partial targets return readable status/resource states without crashing
- conflict plans identify manual-review or overwrite-sensitive operations
- conflict installs are refused or leave conflicting files unchanged

## Fixture Strategy

Use pytest factory helpers in a focused test module. Generated fixtures are preferred over
committed sample projects because the release matrix cares about target shapes, not application
implementation depth. If a later task needs public examples, those should be separate examples
with their own documentation and maintenance burden.

## Acceptance Gate

Task 115 is complete only when local MCP E2E tests pass for generated targets and the handoff
states whether the MCP is ready for GitHub release-candidate artifact publication. PyPI remains
out of scope.
