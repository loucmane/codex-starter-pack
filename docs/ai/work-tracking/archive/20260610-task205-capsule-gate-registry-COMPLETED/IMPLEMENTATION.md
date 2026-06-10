# Task 205 Capsule PR-1d: gate registry and verification classification – Implementation Notes

## What was built
- `.aegis/brief.json` ships as a seed-once installer asset, new kind `config`
  (foundation-manifest schema enum extended in both copies): created when missing,
  classified skip/owner-maintained on upgrade in plan_install, and never overwritten by
  install's write loop. Default: empty gates/source_roots, thresholds, redact_extra,
  archive_keep 20, inject true — pattern VALUES stay per-repo configuration.
- Command normalization + matching in gate_lib (both copies): segments split on shell
  control operators; env-assignment prefixes stripped; redirect tokens dropped including
  bare `>` operators consuming their target token; adjacent `cd X` + command pairs
  re-joined so cd-prefix patterns match alongside `-C`/`--dir` variants. Matching is
  exact equality on normalized forms.
- Recorder verification classification: matched Bash commands (PostToolUse AND
  PostToolUseFailure) become event_type `verification` with extra
  {package, gate, exit_class via outcome, commit (HEAD short)}; brief.json
  `redact_extra` feeds the ledger's redaction patterns.
- Scope records (spec 2.1): first recorded mutation on a branch appends ONE scope event
  (task id inferred from the task-NN branch convention; path_globs default to
  source_roots; gates default to all registered; needs_confirmation when uninferable).
  The SYNC posttooluse hook emits ONE failure-proof additionalContext nudge per branch
  suggesting `aegis scope set`, suppressed forever after nudge or confirmation.
- `aegis scope set <task-id> [globs...]` CLI appends the confirmed scope record.

## Verification
- 26 new tests: 8 invocation-variant matches (cd-prefix, -C, --dir, env prefix, pipes,
  redirects incl. bare `>` target), 6 non-matches, verification pass/fail classification
  with commit, redact_extra, scope inference/once-per-branch/ambiguous/read-only-skip,
  scope set CLI, nudge once + suppression-after-confirmation, seed-once plan
  classification, config kind. Two PR-1b tests updated for the new scope rows.
- Full suite 1247 passed / 4 env-gated skips.
