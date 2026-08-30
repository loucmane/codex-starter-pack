# Findings

- 2026-08-30 — A frozen subject commit is insufficient: the manifest must also bind the profile,
  lane prompts/rubrics/schemas, bundle builders, and sorted external inputs because HPFetcher uses
  untracked copyright-controlled data under `data/parsed/`.
- 2026-08-30 — Blindness must be constructed as a closed bundle in an empty directory and audited
  mechanically. A checkout or worktree is never a blind input because Git history can recover
  intended keys and rationales.
- 2026-08-30 — The authorization envelope is an audit binding, not a trust root. Dispatch still
  requires live operator authority; an envelope can only prove that a run stayed within it.
- 2026-08-30 — Generic tools may validate structure, hashes, confinement, and cross-lane evidence,
  but may not reproduce HPFetcher aggregation, promotion, or adjudication semantics.

- 2026-08-30 — _Pending_ — document new findings here.
