# Decisions - Task 180

- 2026-06-08 — Implement a sanctioned observation-stop collection path instead of allowing raw cleanup commands during observation.

Decision: implement a sanctioned observation-stop collection path instead of allowing `rm` during observation.

Rationale: observation mode should remain inspection-only. Aegis can safely classify and move known artifacts because it has the observation baseline and target-root confinement; a raw shell deletion permission would weaken the boundary.

## Prefer `--collect-artifacts`

Decision: expose the feature as `aegis observe stop --collect-artifacts`.

Rationale: screenshots and Playwright traces are useful audit evidence. Moving them under the observation report is safer and more useful than silently deleting them.
