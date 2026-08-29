# Decisions

- 2026-08-28 — Use repository-enabled merge commits — the former squash requirement
  was impossible under current GitHub settings and caused the fully authorized PR #295
  executor to fail HTTP 405.
- 2026-08-28 — Cap supported Python at `<3.15` while testing 3.11-3.14 — an explicit
  support window is more honest than an open-ended lower bound that CI cannot prove.
- 2026-08-28 — Keep Taskmaster as conditional compatibility only — Beads own lifecycle
  truth, while legacy cascade/precision evidence runs only when relevant.
- 2026-08-28 — Pin all third-party actions by full SHA and project dependencies by
  `uv.lock`; human-readable release comments do not carry authority.
- 2026-08-28 — Add Dependency Review to the delivery-policy evidence set and Dependabot
  for both Actions and `uv`; repository-level protection settings remain a distinct,
  evidence-backed external mutation.
- 2026-08-29 — Archived through the supported archive helper; no evidence was deleted.
