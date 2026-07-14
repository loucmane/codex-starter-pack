# Shared Codex Hook Bootstrap Hardening

## Incident

Codex Stop hooks repeatedly invoked an absolute command rooted at
`/home/loucmane/codex/.claude/scripts/`. While the tracked `gate_lib.py` was transiently
unavailable, every invocation failed before Aegis could evaluate policy or emit structured
evidence. Projects sharing equivalent legacy hook definitions inherited the mutable source
checkout as a runtime availability dependency.

The incident was not a committed deletion. The live and packaged `gate_lib.py` files are
present and byte-identical on current `main`; Git history contains modifications but no
committed removal. The failure class is therefore bootstrap coupling and partial-runtime
exposure, not missing product logic.

## Existing Architecture

Current generated Codex hooks resolve the target repository root with
`git rev-parse --show-toplevel`. Installed shell hooks are rendered as small dispatchers that
prefer the target-local `.aegis/bin/aegis hook <phase>` command and retain a sibling-runtime
fallback. Codex-only and multi-agent installs both receive the shared hook runtime.

The affected source checkout instead has an untracked, pre-adapter `.codex/hooks.json` whose
commands name mutable source wrapper paths directly. That operator-owned file is preserved and
must not be hot-edited by this task.

## Required Invariants

1. Generated project hooks contain no absolute Aegis source-checkout path.
2. Hook execution begins at a stable target-local bootstrap under the target Git root.
3. The bootstrap validates the complete phase-specific runtime before delegation.
4. PreToolUse never fails open when policy cannot be evaluated.
5. PostToolUse, lifecycle, SessionStart, and Stop failures are bounded, concise, and
   non-recursive; one invocation produces at most one actionable diagnostic.
6. Hook stdin is consumed exactly once and canonical exit/output semantics are preserved.
7. A managed update cannot expose a mixed old/new bootstrap and runtime set.
8. Exact known legacy Aegis handlers may be adopted or migrated; unknown/custom hooks remain
   untouched and force manual review before any write.
9. Codex-only, multi-agent, subdirectory, and linked-worktree installs behave identically.
10. Live source assets, packaged assets, schemas, manifests, contracts, and tests agree.

## Implementation Seam

Keep hook definitions declarative and target-local. Harden the stable dispatcher/shim and the
managed-update materialization transaction rather than teaching every hook event a separate
recovery path. Phase behavior belongs in the authoritative hook runtime; bootstrap behavior is
limited to locating it, validating it, delegating stdin, and returning a deterministic result.

Legacy migration must compare parsed command semantics against a finite set of known Aegis
forms. Matching must include phase, target path, invoking agent, and handler shape. A merely
similar shell command is project-owned and cannot be rewritten automatically.

## Verification Matrix

- Healthy target-local runtime with the central source checkout present and absent.
- Missing shim, wrapper, gate library, and phase dependency combinations.
- Mutation-capable PreToolUse versus passive PostToolUse/Stop/lifecycle behavior.
- Two independently installed projects while the source `gate_lib.py` is unavailable.
- Codex-only and multi-agent install/update, second-run idempotence, and linked worktrees.
- Exact legacy-handler migration and divergent custom-handler refusal before writes.
- Source/package parity and unchanged hook trust/client-reload guidance.
- Output-size and invocation-count assertions preventing recursive or repeated diagnostics.

## Rollback

Rollback is a reviewed revert of the Task 252 implementation commit. Existing recognized
project hooks remain target-local; unknown hooks are never rewritten. No target project needs
manual queue draining, task repair, or enforcement-mode changes. The primary source checkout's
untracked `.codex/hooks.json` remains outside the patch throughout.
