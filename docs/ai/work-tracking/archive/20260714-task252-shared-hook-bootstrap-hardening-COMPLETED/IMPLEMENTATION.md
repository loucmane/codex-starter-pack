# Task 252 Harden Shared Codex Hook Bootstrap Against Mutable Runtime Outages – Implementation Notes

## Implemented Workstreams

### Target-local hook bootstrap
- Generated Codex registrations now invoke `$(git rev-parse --show-toplevel)/.aegis/bin/aegis hook <phase>` for every phase.
- The installed shim exports `AEGIS_TARGET_ROOT` and executes the target's managed `gate_lib.py` before consulting a source checkout or installed package.
- Required mutation-policy phases fail closed with exit 2 when local runtime bytes are missing. Passive phases return 0 so an evidence outage cannot wedge the client.
- Each missing phase emits one concise diagnostic until that phase successfully recovers; marker state lives under ignored `.aegis/state`.
- Hook execution uses `python3 -B` so linked worktrees stay byte-clean.

### Transactional managed installation
- Managed files use temp-file + `os.replace` atomic replacement and retain prior mode bits.
- Runtime dependencies install before the shim, dispatch wrappers install after the shim, and `.codex/hooks.json` / `.claude/settings.json` activate last; the manifest remains the final managed asset.
- Existing bytes and modes are snapshotted before apply. Any exception restores all modified managed/report paths independently of the failing write helper, then removes only newly created plan paths.
- Install reports expose deterministic rollback status, restored paths, cleanup results, and errors.

### Safe hook migration
- Exact known legacy absolute Aegis handlers and the prior Git-root dispatcher forms are structurally adopted.
- Project-owned hooks are preserved.
- Unknown Aegis-like commands remain manual-review and cannot be overwritten silently.
- One SessionStart handler now performs both capsule injection and lifecycle evidence; SubagentStart has a distinct `subagentstart` dispatcher alias to preserve one registration per lifecycle event.

### Runtime parity
- Live and packaged `gate_lib.py` are byte-identical.
- Live and packaged `_aegis_installer.py` are byte-identical.
- Direct CLI hook dispatch also resolves target-local runtime before source-root resolution.

## Scope Preserved
- The primary checkout's untracked `.codex/hooks.json`, `.aegis/`, `.agents/`, and `.codex/agents/` were not modified.
- Enforcement remains advisory.
- No Blog checkout or downstream project was updated.
