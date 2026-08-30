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
- 2026-08-30 — A project can legitimately retain unrelated historical ACTIVE folders. Lifecycle
  commands must select the current folder by bead identity and refuse zero or multiple matches;
  global single-folder assumptions turn durable history into an agent-memory dependency.
- 2026-08-30 — Cross-project closeout can reuse the canonical transactional archive safely when it
  treats legacy `.aegis` state as frozen evidence. The archive may update only the selected tracker,
  its bound plan/session references, and the transaction journal.
- 2026-08-30 — Codex project trust and Codex hook trust are independent startup gates. A worker can
  enter the reviewed project root yet still stop before instructions on changed/new hooks. Durable
  unattended startup therefore must bind the manifest bytes, validate resolved hook metadata, and
  install the exact runtime hashes through Codex's supported versioned config API; a bypass flag is
  neither durable trust nor an acceptable repair.

- 2026-08-30 — _Pending_ — document new findings here.
- 2026-08-30 — Archive preconditions were satisfied and the completed bundle was preserved.
