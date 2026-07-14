# Decisions

- 2026-07-14 — Treat the tracked manifest gate, not the ignored install report, as release-verification evidence for Codex hook-trust guidance.
- 2026-07-14 — Accept exactly one gate whose complete semantics match the installer-generated contract; fail closed on absence, duplication, malformed verification metadata, or any semantic drift.
- 2026-07-14 — Keep hook trust manual and external to the repository. This change proves guidance reproducibly; it does not bypass `/hooks`, claim automated trust, or weaken enforcement.
- 2026-07-14 — Maintain byte-identical root and packaged installer assets and limit implementation changes to the approved two installer copies plus focused tests.
