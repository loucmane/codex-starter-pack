# Decisions

- 2026-06-15 — Derive the brief from `state` via a `CONTINUATION_BRIEF_BY_STATE` table rather
  than threading per-field args through the ~16 `_workflow_guidance_payload` call sites. Every
  state gets a coherent brief with one constructor edit; matches the TM 188 design intent
  ("optional params, only emitted when set") while avoiding per-site churn.
- 2026-06-15 — Encode the post-closeout delivery states (`delivery_pending`,
  `delivery_unknown`, `closeout_passed`) as **confirmation-gated** instead of lifting the
  dynamic `push_branch`/`open_pr` action into `next_safe_action`. Presenting a
  boundary-crossing git op as the "safe" next step would contradict the contract's
  never-auto-merge/push invariant.
- 2026-06-15 — `aegis next` now defaults to a concise human summary (`format_next_summary`);
  `--json` preserves the full payload. Safe because no runtime consumer parses `aegis next`
  stdout as JSON — the MCP server and `codex-task` call `next_action()` in-process.
- 2026-06-15 — Cleaned `tasks.json` `generate` churn (223-line int→string `id` reformat) by
  restoring HEAD format and surgically flipping only 188→done / 189→done in raw text. Avoids
  a 466-line noise diff; the prior session resolved the same churn the same way. (Override of
  the "never manually edit tasks.json" convention, scoped to status fields only.)
- 2026-06-15 — Deferred residual #2 (doctor-derived safe-repair vs manual-review as distinct
  `next_action` states) to a new follow-up, **TM 225**. That classification lives in
  doctor/repair and is a larger change than the brief; keeping this PR tight.
- 2026-06-15 — Left `task_188.md` at its pre-existing `pending` skew (json says `done`):
  `generate-one` refuses while the current task file is dirty, and 188 is outside TM 189's plan
  scope. To be resynced on a clean tree post-merge.
