# Public Aegis Adoption Flow

Aegis should feel like a normal project tool from the outside. The low-level install and kickoff commands remain available for debugging, but the public path is:

```bash
aegis mcp register claude
cd /path/to/project
aegis init
aegis start "Improve BrandMark accessibility"
```

## Command Roles

| Command | Role |
|---|---|
| `aegis mcp register claude` | Registers the Aegis MCP server with Claude using the native `claude mcp add` path. Defaults to package mode, user scope, project-local uv cache/tool dirs, and `--default-target-dir .`. |
| `aegis init` | Installs the Aegis runtime into the current project with conservative defaults: generic profile, Claude primary adapter, Claude hooks, managed `CLAUDE.md` merge, and standard verification. |
| `aegis start "<task title>"` | Allocates a local Aegis task id, derives a slug, creates the task branch, session, plan, work-tracking folder, current-work state, and readiness evidence. |

## Normal Claude Use

After `aegis init`, a fresh Claude session should not need a large workflow prompt. The installed `CLAUDE.md`, `.aegis/contract.md`, and hooks tell Claude to:

1. Run readiness/status/next.
2. If no current work exists, infer a short task title from the user request and run `aegis start "<task title>"`.
3. Log scope before source edits.
4. Use native tools for source reads, edits, tests, and git inspection.
5. Let hooks create pending S:W:H:E tracking after mutations.
6. Clear pending tracking with `aegis log --pending-id current --plan-step auto --plan-status completed`.
7. Run task verification, strict Aegis verification, closeout preflight, and final closeout before reporting completion.

When the workflow state looks inconsistent, the normal recovery path is:

1. Run `aegis doctor` to classify the state without changing files.
2. Review the repair plan.
3. Run `aegis repair --apply` only for safe mechanical drift such as missing current symlinks, expected directories, absent managed runtime files, or executable bits.
4. Continue with normal verification and closeout gates.

## Advanced Equivalents

The public commands delegate to the established primitives:

| Public command | Advanced equivalent |
|---|---|
| `aegis init` | `aegis inspect` -> `aegis plan-install --primary-agent claude --agent claude` -> `aegis install --primary-agent claude --agent claude --apply` -> `aegis verify` |
| `aegis start "<title>"` | `aegis kickoff --task <id> --slug <slug> --title "<title>"` after allocating a local id in `.aegis/state/local-tasks.json` |
| `aegis mcp register claude` | `aegis mcp execute-registration --client claude --scope user --source-mode package` |

Use advanced commands for debugging, pinned versions, wheel/source testing, or externally managed task ids.

## Acceptance Bar

The flow is done only when behavior proves it:

- Fresh and existing target projects install with `aegis init`.
- Existing `CLAUDE.md` content is preserved under the Aegis managed block.
- No `.bak`, `.orig`, or backup sidecar files are created.
- Projects without Taskmaster or Serena can start local work with `aegis start`.
- Claude can receive a normal request like `Improve BrandMark accessibility` and follow installed Aegis files/hooks without a large checklist prompt.
- Pending tracking, strict verification, closeout, and handoff pass mechanically.
- Doctor and repair can diagnose and recover safe mechanical state drift without overwriting project files or clearing unlogged work.
