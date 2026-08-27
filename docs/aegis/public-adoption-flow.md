# Public Aegis Adoption Flow

Aegis should feel like a normal project tool from the outside. The low-level install and kickoff commands remain available for debugging, but the public path is:

```bash
aegis mcp register claude
cd /path/to/project
aegis init
# restart Claude if init reports client_reload.required=true
aegis kickoff --bead ga-example --slug improve-brandmark-accessibility --title "Improve BrandMark accessibility"
```

The project work authority decides the kickoff form:

```bash
# Gas City beads (preferred external authority)
aegis kickoff --bead ga-example --slug <slug> --title "<title>"

# No external work ledger
aegis start "<title>"

# Historical numeric compatibility only
aegis kickoff --task <id> --slug <slug> --title "<title>"
```

Beads-first projects refuse `aegis start`, never allocate a duplicate local or Taskmaster task,
and do not register Taskmaster MCP. Historical Taskmaster repositories may retain their
numeric compatibility flow until separately migrated.

## Command Roles

| Command | Role |
|---|---|
| `aegis mcp register claude` | Registers the Aegis MCP server with Claude using the native `claude mcp add` path. Defaults to package mode, user scope, project-local uv cache/tool dirs, and `--default-target-dir .`. |
| `aegis init` | Installs the Aegis runtime into the current project with conservative defaults: generic profile, Claude primary adapter, Claude hooks, managed `CLAUDE.md` merge, and standard verification. |
| `aegis kickoff --bead <id> ...` | Starts current work from an authoritative Gas City bead and renders bead-native branch, session, plan, tracker, and current-work state. |
| `aegis start "<task title>"` | Allocates a local Aegis task id, derives a slug, creates the task branch, session, plan, work-tracking folder, current-work state, and readiness evidence. |
| `aegis kickoff --task <id> ...` | Historical numeric-task compatibility for a project that explicitly retains that authority. |

## Normal Claude Use

After `aegis init`, a fresh Claude session should not need a large workflow prompt. The installed `CLAUDE.md`, `.aegis/contract.md`, and hooks tell Claude to:

1. Run readiness/status/next.
2. Follow the declared work authority. In a beads-first project, inspect the exact bead and run `aegis kickoff --bead <id> ...`.
3. Use `aegis start` only when no external ledger is declared; use numeric kickoff only for an explicitly historical compatibility project.
4. Log scope before source edits.
5. Use native tools for source reads, edits, tests, and git inspection.
6. Let hooks create pending S:W:H:E tracking after mutations.
7. Clear pending tracking with `aegis log --pending-id current --plan-step auto --plan-status completed`.
8. Run task verification, strict Aegis verification, closeout preflight, final closeout, and one read-only `aegis doctor` health check before reporting completion.
9. Close or update the authoritative external work item only after Aegis closeout and doctor pass.
10. Build and gate the managed Obsidian projection at readiness, closeout, or publication boundaries when the project enables it.

For MCP clients, the public path is `aegis.init apply=true`, a client restart when required,
then `aegis.bead_kickoff apply=true` for beads-first work. `aegis.start` and legacy
`aegis.kickoff` remain available only for their declared authority modes.

Claude Code loads `.claude/settings.json` hooks at session start. If `aegis init` or `aegis install` creates or changes `.claude/settings.json` or `.claude/scripts/*`, Aegis writes `.aegis/state/client-reload-required.json`; while that marker exists, `aegis.start` and `aegis.kickoff` are refused. The agent must stop before source edits and ask the user to restart Claude in the project. After restart, the installed `PreToolUse` hook clears the marker, and `aegis next` resumes the normal workflow with active hooks.

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
- Beads-first projects use `aegis kickoff --bead`; `aegis start` must not allocate a competing local task.
- Historical numeric-task repositories may retain explicit `aegis kickoff --task` until migration.
- Claude can receive a normal request like `Improve BrandMark accessibility` and follow installed Aegis files/hooks without a large checklist prompt.
- First-time Claude installs report the required restart before source edits, and post-restart sessions proceed through `aegis next`.
- Pending tracking, strict verification, closeout, and handoff pass mechanically.
- External work-item completion happens after Aegis closeout and read-only doctor, not before.
- Doctor and repair can diagnose and recover safe mechanical state drift without overwriting project files or clearing unlogged work.
