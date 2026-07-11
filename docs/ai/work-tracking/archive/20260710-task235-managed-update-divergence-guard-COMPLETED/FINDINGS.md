# Findings

- 2026-07-11 - Task 235 was complete in Taskmaster and implementation evidence, but its work-
  tracking directory remained under `active/`. The Task 236 kickoff correctly required the stale
  projection to be archived; no Task 235 runtime or verification result changed.

- 2026-07-10 — Manifest ownership was path-only. A target could commit a hardened managed
  governance asset and still receive a `safe_to_apply=true` overwrite because the updater had
  no record of the bytes Aegis originally installed.
- 2026-07-10 — The existing manifest schema already allowed an optional checksum, so the fix
  requires no schema-version break. New installs can adopt byte baselines incrementally.
- 2026-07-10 — Legacy source-backed assets can recover their prior expected bytes safely with
  `git show <runtime.source_commit>:<source-path>`; no historical installer code needs to be
  executed.
- 2026-07-10 — `project_update --apply` advances runtime metadata before reinstalling assets.
  It must retain the original manifest for classification or a legacy baseline silently changes
  from the installed commit to the new commit mid-operation.
- 2026-07-10 — The completed-archive implementation from `loucmane/blog` is otherwise byte-compatible
  with upstream. Promoting it canonically makes the live blog guard a skip on the retry.
