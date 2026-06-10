# 2026-06-10 Task 209 Capsule PR-3.5 kickoff

PR-2b merged (bbcbcef); capsule loops complete in codex. Task 209 = delivery witness v0
pulled AHEAD of PR-3 narration (its proves-useful gate needs falsifier evidence; deps
rewired 209->207). witness_lib.py: 4 deterministic local checks (scope mapping, diff
accounting + test-deletion escalation, verification-pass-at-HEAD from ledger, done-flip
containment); CI mode finding: ledger does not travel to CI, so --ci runs git-derivable
checks and marks check 3 not_derivable_in_ci — spec-revision note. aegis-witness.yml
added; required-check flip is the owner's branch-protection action.
