# PR Scope 288 Gate Hard-Policy Parser - Implementation Notes

## Test-first sequence

The shared JSON corpus and its two consumers were committed before the implementation.
Against the vulnerable baseline, the new selection produced 32 failures and 12 passing
controls. The implementation was added only after that red evidence existed.

## Gate behavior

- Raw input is normalized and preclassified without execution.
- Hard-policy eligibility is established before shell parsing.
- Parser failure in an eligible context denies unconditionally.
- Newline/CR separation and sensitive concealment forms are handled fail closed.
- Legitimate non-sensitive heredoc and substitution controls remain permitted.
- RFC3339 expiry values use aware datetime parsing rather than lexical comparison.
- Mutation classification uses a small explicit read-only allowlist and a conservative
  mutating default.

The live and packaged gate files remain byte-identical.

## Preserved boundaries

The implementation changed no Taskmaster state, primary-checkout file, Gas City runtime,
provider credential, GitHub App credential, worker, or project task authority.
