# Task 254 — Strict Codex hook-trust portability

Task 254 extends merged Task 253 by persisting the complete no-bypass hook-trust review contract in
the tracked `codex.hook_trust` foundation-manifest gate. The exact values are
`.codex/hooks.json`, `/hooks`, `exact_hook_definition`, and `bypass_allowed: false`; both root and
packaged schemas enforce them.

Strict verification uses that tracked contract as authority. Ignored install-report data is only
supplemental diagnostics and cannot make invalid tracked guidance pass. Actual Codex trust remains
client/session-local and hash-bound; repository state explicitly does not assert it. A changed hook
definition requires renewed `/hooks` review.

Verification completed: focused tests 166 passed/1 opt-in skip; full suite 2,059 passed/4 opt-in
skips; clean secondary-worktree strict verification and closeout dry-run pass without an install
report. `/tmp/blog-task42` reproduced the old single-gate failure, then passed with zero required
failures under Task 254 while its dirty status and 1,031 Git-visible records remained byte-identical.

Remaining work is workflow closure, protected PR/CI delivery, and safe primary-main synchronization.
Preserve primary checkout drift and do not claim client-local hook trust.
