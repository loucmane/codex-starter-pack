# Decisions

- 2026-06-10 — Implemented only strict/advisory modes for this task. Replay integration, hash chaining, policy versioning, and additional lifecycle modes remain out of scope.
- 2026-06-10 — Kept the state file absent-by-default strict, so installed projects do not change behavior until an operator explicitly runs `aegis enforce --mode advisory`.
- 2026-06-10 — Used JSONL gate decisions rather than markdown narration for advisory records, making the output replay-corpus friendly while preserving existing S:W:H:E tracking.
