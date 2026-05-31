# Public Aegis Adoption Flow

Aegis should feel like a normal project tool from the outside. The low-level install and kickoff commands remain available for debugging, but the public path is:

```bash
aegis mcp register claude
cd /path/to/project
aegis init
# restart Claude if init reports client_reload.required=true
aegis start "Improve BrandMark accessibility"
```

For projects that already use Taskmaster, replace the local `aegis start` step with Taskmaster discovery and explicit-id kickoff:

```bash
task-master next
task-master show <id>
aegis kickoff --task <id> --slug <slug> --title "<title>"
```

If the client has Taskmaster MCP available, the read-only discovery equivalents (`help`, `get_tasks`, `next_task`, `get_task`) may be used before kickoff even while readiness is `BLOCKED`. Taskmaster MCP mutations and unknown Taskmaster MCP tools remain blocked until Aegis kickoff makes readiness `READY`.

## Command Roles

| Command | Role |
|---|---|
| `aegis mcp register claude` | Registers the Aegis MCP server with Claude using the native `claude mcp add` path. Defaults to package mode, user scope, project-local uv cache/tool dirs, and `--default-target-dir .`. |
| `aegis init` | Installs the Aegis runtime into the current project with conservative defaults: generic profile, Claude primary adapter, Claude hooks, managed `CLAUDE.md` merge, and standard verification. |
| `aegis start "<task title>"` | Allocates a local Aegis task id, derives a slug, creates the task branch, session, plan, work-tracking folder, current-work state, and readiness evidence. |
| `aegis kickoff --task <id> ...` | Starts Aegis current work from an external numeric task id such as Taskmaster. It creates the same branch, session, plan, and work-tracking scaffold without allocating a local Aegis task. |

## Normal Claude Use

After `aegis init`, a fresh Claude session should not need a large workflow prompt. The installed `CLAUDE.md`, `.aegis/contract.md`, and hooks tell Claude to:

1. Run readiness/status/next.
2. If no current work exists and `.taskmaster/` has available numeric work, run `task-master next` and `task-master show <id>` or the read-only Taskmaster MCP discovery equivalents, then run `aegis kickoff --task <id> --slug <slug> --title "<title>"`.
3. If no Taskmaster numeric task is available, infer a short task title from the user request and run `aegis start "<task title>"`.
4. Log scope before source edits.
5. Use native tools for source reads, edits, tests, and git inspection.
6. Let hooks create pending S:W:H:E tracking after mutations.
7. Clear pending tracking with `aegis log --pending-id current --plan-step auto --plan-status completed`.
8. Run task verification, strict Aegis verification, closeout preflight, final closeout, and one read-only `aegis doctor` health check before reporting completion.
9. If Taskmaster is in use, mark the Taskmaster task done only after Aegis closeout and doctor pass.
10. Refresh Taskmaster generated task files after marking done. Use the project helper when present; otherwise run broad `task-master generate` deliberately and report it.

For MCP clients, the standalone public path is `aegis.init apply=true` followed by a Claude restart when `client_reload.required=true`, then `aegis.start apply=true` or Taskmaster-backed `aegis.kickoff apply=true`. In Taskmaster projects, `aegis.next` should recommend `task-master next/show` or Taskmaster MCP equivalents plus `aegis.kickoff apply=true` with the Taskmaster numeric id. `aegis.plan_install` and `aegis.install` remain advanced/debug equivalents once `aegis.init` exists.

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
- Projects with an available Taskmaster numeric task use `task-master next/show` and explicit `aegis kickoff`; `aegis start` must not allocate a competing local task.
- Claude can receive a normal request like `Improve BrandMark accessibility` and follow installed Aegis files/hooks without a large checklist prompt.
- First-time Claude installs report the required restart before source edits, and post-restart sessions proceed through `aegis next`.
- Pending tracking, strict verification, closeout, and handoff pass mechanically.
- Taskmaster completion happens after Aegis closeout and read-only doctor, not before.
- Doctor and repair can diagnose and recover safe mechanical state drift without overwriting project files or clearing unlogged work.
