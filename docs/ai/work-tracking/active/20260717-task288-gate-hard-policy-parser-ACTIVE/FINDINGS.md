# Findings

- 2026-07-17 — **Confirmed fail-open class** — Newline separation and concealment forms
  could hide sensitive command families from the previous parser path; parser exceptions
  could be interpreted as no violation.
- 2026-07-17 — **Test-first evidence** — The new shared selection failed 32 cases before
  implementation while 12 non-sensitive or existing-policy controls passed.
- 2026-07-17 — **Regression evidence** — After implementation, all 44 new cases, 222
  focused gate tests, 643 Claude-adapter tests, and 180 adjacent installer/release tests
  passed; three opt-in smoke tests remained intentionally skipped.
- 2026-07-17 — **Initial PR CI diagnosis** — Guard jobs lacked an ACTIVE tracker and witness
  could not map the original branch to a numeric scope. No failure implicated gate behavior.
- 2026-07-17 — **Taskmaster boundary** — Workflow metadata can satisfy guard/witness using
  a PR-scoped numeric identifier without creating or updating Taskmaster state.
