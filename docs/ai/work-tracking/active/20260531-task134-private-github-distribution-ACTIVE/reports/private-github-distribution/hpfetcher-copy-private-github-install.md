# HPFetcher Copy Private GitHub Install Smoke

## Source And Target

Real project source, read-only:

```text
/home/loucmane/dev/hpfetcher
```

Safe copied target:

```text
/tmp/aegis-task134-hpfetcher-copy
```

Copy command excluded `.git`, `node_modules`, `.next`, `dist`, `build`, `.venv`, and `__pycache__`. The copied target size was `726M`.

Private GitHub source:

```text
git+ssh://git@github.com/loucmane/codex-starter-pack.git@feat/task-134-private-github-distribution
```

Resolved commit during smoke:

```text
5afc9752494ee5812fca8169da75a2420d89e27f
```

## Preservation Baseline

Before install, the copied `CLAUDE.md` hash was:

```text
63f75e68a4a22d8e1374415a886f85a3babedb97d945e8fc834120b30037e5f4
```

The copied project did not have an existing `AGENTS.md`.

## Install Command

```bash
env UV_CACHE_DIR=/tmp/uv-cache-task134-private UV_TOOL_DIR=/tmp/uv-tools-task134-private \
  uvx --from git+ssh://git@github.com/loucmane/codex-starter-pack.git@feat/task-134-private-github-distribution \
  aegis init --target-dir . --primary-agent multi --agent claude --agent codex
```

## Result

PASS. Aegis installed from the private GitHub source into the copied HPFetcher project.

Observed install summary:

- 31 creates
- 1 modify (`CLAUDE.md`)
- 0 conflicts
- 0 manual reviews
- standard install verification passed with 10 checks, 0 required failures, 1 unsupported policy-only check

`CLAUDE.md` preservation was confirmed by the installed file containing:

```text
<!-- AEGIS:BEGIN claude-runtime -->
...
## Existing Project Instructions
...
HP-Coach: a coaching tool for the Swedish högskoleprov (HP).
```

`AGENTS.md` was created because no existing `AGENTS.md` was present in the copied source. It records:

```text
Primary agent: `multi`
Enabled adapters: `claude, codex`
```

The expected Claude reload barrier was created:

```text
.aegis/state/client-reload-required.json
status: required
method: installed_claude_pretooluse_hook
```

This is correct for a copied real project with the Claude adapter enabled; the current session must stop before source edits, project verification, Taskmaster mutation, `aegis.start`, `aegis.kickoff`, `aegis.verify`, or `aegis.closeout`.

## Doctor

Command:

```bash
env UV_CACHE_DIR=/tmp/uv-cache-task134-private UV_TOOL_DIR=/tmp/uv-tools-task134-private \
  uvx --from git+ssh://git@github.com/loucmane/codex-starter-pack.git@feat/task-134-private-github-distribution \
  aegis doctor --target-dir .
```

Result:

```text
Aegis doctor: healthy (installed_no_current_work)
Checks: 11 total, 0 required failures, 0 warnings
Repair plan: 0 safe, 0 manual-review
```

## Verdict

PASS for copied-real-project private GitHub install acceptance. The real HPFetcher checkout was not mutated. Aegis preserved existing `CLAUDE.md` content under the managed runtime block, created `AGENTS.md` because none existed, reported the expected Claude restart hard stop, and doctor was healthy.
