# Decisions

- 2026-05-07 — Remove `templates/PROJECT-BLOG.md` from the portable template set instead of allowlisting the security finding or rewriting only one import example. This clears the baseline by removing stale content, not by weakening Task 18 scanner behavior.
- 2026-05-07 — Keep this task narrowly scoped to PROJECT-BLOG removal and direct references. Broader monolith/root-template cleanup remains out of scope.
- 2026-05-07 — Update the scanner module fixture from `PROJECT-BLOG.md` to `USER-GUIDE.md` because PROJECT-BLOG is no longer part of the canonical monolith detection list. This preserves the test's intent without retaining stale product content as canonical.
