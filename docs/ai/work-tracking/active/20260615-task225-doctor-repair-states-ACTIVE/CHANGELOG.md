# Task 225 Surface doctor safe-repair vs manual-review states in aegis next – Changelog

- 2026-06-15 20:11 CEST — Initialized active work-tracking folder.
- 2026-06-15 — Added `_repair_plan_split` (single-sourced safe/manual classify) and a
  severity-gated repair branch to `next_action` emitting `safe_repair_available` /
  `manual_review_repair`, with `CONTINUATION_BRIEF_BY_STATE` entries; assets re-mirrored; new
  `test_repair_next_states.py`. Design + adversarial-review workflows run; review-found major
  bug (cosmetic-action resurrection) fixed + regression-tested. Closes TM 189 residual #2.
