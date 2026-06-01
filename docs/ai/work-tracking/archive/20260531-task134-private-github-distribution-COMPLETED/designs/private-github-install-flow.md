# Task 134 Private GitHub Install Flow Design

## Objective
Make the private GitHub repository install path a first-class Aegis distribution mode so a new machine can use Aegis without PyPI/TestPyPI and without a local source checkout.

## Non-Goals
- Do not publish to PyPI or TestPyPI.
- Do not mutate the real HPFetcher checkout directly.
- Do not replace package, pinned package, wheel, source checkout, or public GitHub registration modes.
- Do not make `.mcp.json` or manual Codex config edits the happy path; native `claude mcp add` and `codex mcp add` stay primary.

## Command Contract
The private happy path should work from any machine with GitHub SSH access and `uvx`:

```bash
uvx --from git+ssh://git@github.com/loucmane/codex-starter-pack.git@main \
  aegis mcp register claude --source-mode private-github --github-ref main

uvx --from git+ssh://git@github.com/loucmane/codex-starter-pack.git@main \
  aegis mcp register codex --source-mode private-github --github-ref main
```

Those commands install only enough Aegis to register the native MCP server. The registered MCP server should itself run through:

```bash
uvx --from git+ssh://git@github.com/loucmane/codex-starter-pack.git@main \
  aegis-mcp-server --default-target-dir . --transport stdio
```

After registration, Claude and Codex should discover the Aegis MCP tools and follow the existing workflow:

1. `aegis.inspect` / `aegis.status` / `aegis.next`
2. `aegis.init` or `aegis.install apply=true`
3. hard stop and client reload when Claude hooks are newly installed
4. `aegis.start` or Taskmaster-backed `aegis.kickoff`
5. native source edits and project tests
6. `aegis.log`, strict `aegis.verify`, `aegis.closeout`, read-only `aegis.doctor`

## Implementation Shape
- Add a `private-github` registration source mode that defaults to the repository SSH URL.
- Normalize SSH-style private GitHub inputs into `git+ssh://...` specs accepted by `uvx --from`.
- Keep `github` mode as the public HTTPS default for backward compatibility.
- Document exact new-machine commands for Claude and Codex.
- Add focused tests that prove command generation, fake native registration, and verification understand the private source spec.

## Acceptance Evidence
- Unit coverage for `private-github` source mode and SSH URL normalization.
- CLI coverage for `aegis mcp generate-registration --source-mode private-github`.
- Documentation coverage asserting the private GitHub commands are present.
- A saved `/tmp` smoke report for generated commands and, if credentials allow, real private-repo `uvx` startup.
- A copied real-project acceptance report using a tmp copy, never the real HPFetcher path.
