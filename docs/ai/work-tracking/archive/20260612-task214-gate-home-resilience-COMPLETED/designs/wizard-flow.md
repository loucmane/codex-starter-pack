# Task 214 — Gate home-resilience: design scope

Date: 2026-06-12. Trigger: HP-Coach dogfood incident — PreToolUse hook in Claude
Code's sandboxed bash environment (no HOME, no passwd entry) hit
`RuntimeError: Could not determine home directory` and the gate failed closed,
hard-blocking a tasks.json write despite advisory enforcement, with no traceback.

## Decisions
1. **Ledger path resolution never raises RuntimeError**: `_state_base` fallback chain
   XDG_STATE_HOME → HOME env → `Path.home()` (wrapped) → `$TMPDIR/aegis-state-<uid>`.
   A degraded environment still records somewhere deterministic.
2. **`safe_expanduser`** in gate_lib: unexpandable `~` returns the literal path —
   safe because a `~`-prefixed literal never matches repo-relative protected or
   workflow-owned paths. Applied at all four expanduser sites.
3. **Advisory contract holds under infra failure**: `degraded_pretooluse_fallback`
   in advisory mode records a `degraded_advisory_allow` event (action_class
   `mutation_or_unsafe`, traceback included) and allows with a loud
   DEGRADED-ADVISORY stderr line. Strict mode keeps failing closed — that spine is
   untouched — but now prints the full traceback for diagnosis.
4. **Diagnosability**: degraded events gain a `traceback` field; the strict block
   message includes the traceback. Any recurrence self-identifies its call site.

## Boundary
Claude-owned scripts + assets mirrors + tests only. No Codex-owned paths. HP-Coach
picks the fix up via its next `aegis install --apply` run after merge.

## Repro honesty
The exact unwrapped call site in HP-Coach's stack was not reproducible locally
(env -u HOME is insufficient: the pwd-database fallback resolves home; the sandbox
lacks both). Tests simulate the condition via monkeypatched `pathlib.Path.home` and
a `sitecustomize.py` PYTHONPATH injection in a full subprocess run.
