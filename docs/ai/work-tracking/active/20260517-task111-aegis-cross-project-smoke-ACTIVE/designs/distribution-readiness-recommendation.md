# Aegis Distribution Readiness Recommendation

## Summary

Task 111 proves that Aegis is ready for packaging/distribution design, but not yet ready to be published as a standalone installer without an explicit invocation contract.

The new smoke harness verifies the current architecture:

- CLI/library core remains the source of truth.
- MCP wrapper preserves core classifications and safety semantics.
- Cross-project target repositories are isolated under pytest `tmp_path`.
- Realistic target shapes can install and verify without clobbering user files.
- Safety failures produce structured reports rather than partial silent mutation.

## Evidence

| Evidence | Result |
| --- | --- |
| `tests-2026-05-17-aegis-cli-smoke.txt` | `60 passed` after adding CLI target-shape smoke coverage. |
| `tests-2026-05-17-aegis-mcp-equivalence.txt` | `62 passed` after adding MCP equivalence coverage. |
| `tests-2026-05-17-aegis-safety-smoke.txt` | `65 passed` after adding safety/negative smoke coverage. |

## What Is Ready

- Aegis can be installed into empty, Python/library, web/app, and docs-heavy target repositories through the CLI path.
- Aegis MCP tools can inspect, plan, install, verify, and expose resources while preserving source-of-truth installer semantics.
- Planning/dry-run paths are no-mutation paths.
- MCP mutating tools require explicit `apply` or acknowledgement gates.
- User files in target repositories are preserved.
- Partial/conflicting installs refuse predictably.
- Failed apply cleanup removes newly-created files without deleting pre-existing user files.

## Remaining Gap

The remaining blocker is not installer correctness; it is distribution ergonomics.

Today, usage still assumes this source repository is available and commands are invoked as:

```bash
python3 scripts/codex-task aegis ...
python3 scripts/aegis-mcp-server ...
```

That is acceptable for local development and MCP configuration inside this repo, but it is not a stable external invocation contract for other projects.

## Recommended Next Task

Create Task 112: **Aegis Packaging and Invocation Contract**.

Recommended scope:

- Define how external projects invoke Aegis without cloning or depending on this repo layout.
- Choose the initial supported invocation forms, likely one or more of:
  - local checkout path for development,
  - `uvx`/package entrypoint,
  - `pipx` install,
  - generated MCP server config snippet,
  - Codex/Claude adapter-specific command wrappers.
- Add tests that install/invoke Aegis from a temporary external project using the chosen contract.
- Keep CLI/library core as source of truth and keep MCP as wrapper.
- Document upgrade/rollback boundaries that should become a later task rather than expanding Task 112 too far.

## Non-Recommendations

- Do not make the MCP server the only installation path.
- Do not publish before the invocation contract is tested in temp external projects.
- Do not add a second installer implementation for packaging.
- Do not solve update/rollback in the same task unless the invocation contract is already stable.

## Suggested Task 112 Acceptance

- A fresh external temp project can invoke Aegis through the selected packaged/dev entrypoint.
- The entrypoint can run inspect, plan-install, install, verify, and MCP server startup without source-repo-specific assumptions leaking into the target project.
- Existing Task 111 smoke tests still pass.
- Documentation includes copy/pasteable commands for first adoption.
