# Decisions

- 2026-06-02 — Keep default reconcile output observational. Add candidate data
  only behind an explicit `--preview-candidates` / `preview_candidates=true`
  switch so routine agent reconciliation does not emit action-shaped guidance.
- 2026-06-02 — Name the section `mutation_candidate_preview` and records
  `mutation_candidate`, not `proposed_action`. Every candidate carries
  `executable: false`, `apply_path_exists: false`, and
  `blocked_reason: report-only per Task 147 contract`.
- 2026-06-02 — Include excluded findings in the preview as contract exclusions,
  phrased as manual-only boundaries rather than TODOs. This makes the
  auto/manual boundary explicit without inviting agents to work through an
  action list.
- 2026-06-02 — Treat predicted blast-radius paths as non-authoritative. The
  preview names likely Taskmaster files for operator review, while Task 145's
  side-effect oracle remains the authority for actual mutation blast radius at
  apply time.
