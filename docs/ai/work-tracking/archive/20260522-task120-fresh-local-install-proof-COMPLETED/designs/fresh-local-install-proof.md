# Fresh Local Install Proof Design

## Boundary

Task 120 proves Aegis can be used from a local artifact before any TestPyPI or PyPI publishing.

Allowed sources:

- Local wheel built from this repository during Task 120.
- Local source path only as a secondary development fallback if the wheel path exposes a blocker.

Forbidden sources:

- TestPyPI.
- PyPI.
- `twine upload`.
- Registry installs of `aegis-foundation`.
- Manual `.mcp.json` edits as the happy path.

## Proof Shape

1. Build a local wheel and certification report under this task's evidence folder.
2. Create a brand-new target project under `/tmp`, with no existing Aegis files.
3. Generate the native Claude MCP registration payload from the local wheel.
4. Execute project-scoped `claude mcp add` from the fresh target when available.
5. Start the MCP server from the wheel and verify it reports package assets, not the source checkout.
6. Install Aegis into the target using the local artifact command path.
7. Verify installed files, readiness before and after kickoff, pending S:W:H:E tracking, protected-path guards, strict verification, and closeout.
8. Capture a Claude live-test prompt that asks a fresh Claude session to make a small app change through Aegis instead of direct unmanaged edits.

## Fresh Target

The target is intentionally outside `/home/loucmane/codex` so generated runtime state cannot accidentally rely on the source checkout. Runtime target files must not contain `/home/loucmane/codex`, `AEGIS_SOURCE_ROOT`, source-checkout `PYTHONPATH`, TestPyPI, or PyPI references except where a report explicitly records the local wheel command used for this proof.
