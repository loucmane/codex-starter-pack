# Blog Legacy-Shadow S:W:H:E Dogfood - 2026-07-09

## Scope

Target repository: `/home/loucmane/dev/blog`

Target commit before the run: `7a3de4f8eca708755a1618c88c096416588a1c84`

Observation: `obs-20260709-201621-sota-magazine-revival-dogfood`

Goal: verify that a newly installed, Codex-primary multi-agent repository can retain the
legacy session/plan/work-tracking surfaces while generating their S:W:H:E history from the
passive ledger.

The target started clean on `main`, in advisory enforcement mode, with no ledger database,
no current work, and no legacy session/plan/work-tracking surfaces.

## Results

- `aegis ledger project-sweh --active --dry-run` refused to invent missing legacy surfaces.
- A bounded observation created one session, one plan, and six work-tracking markdown files.
- `aegis scope set ... --project-sweh` appended a passive scope event and projected it into
  all eight existing surfaces.
- Existing template and human-readable content remained outside the generated marker block.
- A repeated dry-run reported `changed: false` across all eight surfaces.
- Observation stop passed without `--allow-dirty`, reported zero unexpected changes, and
  archived the work-tracking folder from `-ACTIVE` to `-COMPLETED`.
- Projection remained idempotent after archival and resolved the archived paths from
  `.aegis/state/current-work.json`.
- The final ledger was a 28 KiB SQLite database with two scope events.
- Doctor reported 22 required checks passing, zero required failures, and one warning for
  the intentionally advisory enforcement mode.

The archived target surfaces are:

- `sessions/2026/07/2026-07-09-001-obs-20260709-201621-sota-magazine-revival-dogfood.md`
- `plans/2026-07-09-observe-sota-magazine-revival-dogfood.md`
- `docs/ai/work-tracking/archive/20260709-observe-sota-magazine-revival-dogfood-COMPLETED/`

## Defects Found And Fixed

### Agent-scoped client reload

The first `aegis observe start` was blocked because the target still carried a Claude
client-reload marker. The marker declared `agent: claude`, but the caller was positively
identified as Codex through `CODEX_THREAD_ID`.

The reload barrier is now agent-scoped:

- matching Claude and unknown callers remain blocked;
- Codex may continue past a Claude-only marker;
- the marker remains on disk until a real Claude PreToolUse hook clears it;
- `next`, `status`, and `doctor` report `required_for_other_agent` with
  `blocks_invoking_agent: false` for Codex.

### Scope identity

The first projected scope event rendered `S:unknown` because `aegis scope set` did not attach
the active envelope's session identity. Scope recording now reads the current-work envelope
and records:

- the active session filename stem as `session_id`;
- a stable task or observation `work_id`;
- the detected agent identity;
- declared path globs as event paths.

The append-only ledger intentionally retains the first malformed event. The second event in
the dogfood projection demonstrates the corrected identity:

```text
[S:2026-07-09-001-obs-20260709-201621-sota-magazine-revival-dogfood W:observe-sota-magazine-revival-dogfood H:scope ...]
```

### Truly read-only projection

The first idempotence check failed in the sandbox because `open_ledger()` initialized SQLite
tables and WAL state even though projection only needed to read. Ledger backends now support
`read_only=True`:

- SQLite opens in read-only mode and rejects append attempts;
- when a sandbox cannot open SQLite's shared-memory sidecar, reads fall back to an immutable
  snapshot;
- JSONL read-only mode does not create a shard directory and rejects append attempts;
- `project-sweh` always opens the ledger read-only.

The same unprivileged dry-run then succeeded and reported `changed: false`.

### Observation authority label

Post-run guidance initially labeled the observation as
`taskmaster:obs-20260709-...` because generic task-ID detection ran before the observation-mode
check. Observation mode now takes precedence and reports `observation-session` as its current
authority.

## Residual Findings

- Automatic projection is currently integrated only with the explicit scope boundary.
  Witness, delivery, merge, verification, and observation-stop projection remain future
  boundary integrations.
- The Codex CLI path now supplies invocation identity. MCP registrations still need an
  explicit per-client identity before they can safely apply the same exception.
- Doctor proposes a cosmetic `normalize_plan_table` repair for `plan-step-emergency` even
  though the strict plan-table check passes. It was not applied during this run.
- The target's tracked dogfood files are intentionally left uncommitted for review. No
  product source or Taskmaster state was changed.

## Verdict

The legacy-shadow model works in a clean, newly installed repository. Passive ledger truth
can update the old human-readable surfaces without per-mutation `aegis log` calls, preserve
their existing content, survive observation archival, and remain idempotent. The run also
proved that dogfood needs to include bootstrap and sandbox behavior, not only projection
rendering: both defects appeared before or around the first useful event and are now covered
by regression tests.
