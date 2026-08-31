# Decisions

- 2026-08-31 — Use the native Beads hierarchy grammar
  `namespace-token(.positive-integer)*` on every lifecycle validator. This admits real
  children while rejecting empty segments, zero segments, alphabetic pseudo-children,
  slashes, and traversal-like values.
- 2026-08-31 — Centralize relationship classification in `workflow_common` and consume it
  from both begin and attach. Known informational types are non-blocking; missing or unknown
  types remain blocking so schema drift fails closed.
- 2026-08-31 — Keep source and packaged Aegis script copies byte-identical and cover both
  public validator entrypoints with focused regression tests.
