# Decisions

- 2026-06-05 — Use `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` as the Task 163 transition strategy instead of bumping JavaScript action major versions. This validates the GitHub Actions Node 24 runtime before the 2026-06-16 default switch while preserving `upload-artifact@v4` path behavior for `$RUNNER_TEMP/aegis-shadow/` evidence artifacts.
- 2026-06-05 — Keep Taskmaster CLI execution on `node-version: "22"` in `actions/setup-node@v4`; the GitHub JavaScript-action runtime and the Taskmaster toolchain runtime are separate surfaces.
