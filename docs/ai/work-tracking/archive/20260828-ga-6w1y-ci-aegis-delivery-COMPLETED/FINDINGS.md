# Findings

- 2026-08-28 — `aegis.delivery-policy.json` and the autonomous executor require `squash`, while GitHub disables squash merges and permits merge commits. Run `33206478387` reached the final API call and failed HTTP 405 after its evidence checks passed.
- 2026-08-28 — Hosted CI installs floating project ranges instead of either committed lockfile, tests only Python 3.11/3.12 despite `requires-python >=3.11`, and provisions Taskmaster in every matrix job even for Beads-first changes.
- 2026-08-28 — Most workflows lack timeouts and concurrency cancellation; guard/delivery triggers duplicate work; external actions are tag-pinned rather than immutable full SHAs; witness permissions are implicit.
- 2026-08-28 — Repository action policy allows all actions without SHA enforcement, while Dependabot security updates, secret scanning, and push protection are disabled. Repository-setting changes must remain separate explicit external gates if the source workflow cannot enforce them directly.
- 2026-08-28 — Recent hosted CI median duration is 419 seconds. Optimization must preserve the exact-head guard, full Python coverage, and evidence artifacts rather than merely suppressing checks.
- 2026-08-29 — Archive preconditions were satisfied and the completed bundle was preserved.
