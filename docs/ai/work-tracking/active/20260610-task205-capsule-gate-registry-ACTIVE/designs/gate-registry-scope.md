# PR-1d scope — gate registry + verification classification + scope records

Binding contract: AEGIS_CAPSULE_SPEC.md sections 1.2 (row 1d), 2 (gate registry,
decided), 2.1 (scope records). Isolated on purpose: command normalization is the
subtle, riskier part.

## Deliverables

1. **`.aegis/brief.json` installed asset** with SEED-ONCE semantics: new asset
   kind `config` (foundation-manifest schema enum extended) — created when missing,
   NEVER overwritten on upgrade (plan classifies existing config as skip,
   owner-maintained). Default content: empty gates, empty source_roots, thresholds
   {branch_count 30, unignored_file_mb 5}, redact_extra [], archive_keep 20,
   inject true. Pattern VALUES are per-repo configuration (deployment docs), never
   hardcoded in Aegis.
2. **Command normalization + gate matching** in gate_lib: segments split on shell
   control operators, env-assignment prefixes stripped, redirect tokens stripped,
   whitespace collapsed; adjacent `cd X` + command segments joined so cd-prefix,
   `-C`, and `--dir` pattern variants of the same logical command all match their
   registered literal patterns. Matching is exact equality on normalized forms.
3. **Verification classification** in the recorder: a PostToolUse Bash event whose
   command matches a registered gate becomes event_type `verification` with extra
   {package, gate, exit_class, commit (HEAD short, best-effort)}. `redact_extra`
   from brief.json feeds the ledger's redaction patterns.
4. **Scope records (2.1)**: at the first recorded mutation on a branch, infer the
   task id from the branch name (feat/task-NN-* convention) and append ONE
   event_type `scope` record {task_id, path_globs (default source_roots), gates
   (default all registered), inferred: true}. If inference fails, the scope record
   carries needs_confirmation and the SYNC posttooluse hook emits ONE non-blocking
   additionalContext nudge per branch suggesting `aegis scope set <task-id>
   [globs...]` (wrapped fully in try/except — the sync path must never gain a
   failure mode). `aegis scope set` CLI appends a confirmed scope record.

## Out of scope
The witness that CONSUMES scope records (PR-3.5); aegis brief (2a); JSONL freeze.

## Merge gate (spec 1.2 row 1d)
Fixture suite incl. cd-prefix/`-C`/`--dir` invocation variants.
