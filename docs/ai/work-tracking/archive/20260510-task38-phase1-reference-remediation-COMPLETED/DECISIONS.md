# Decisions

## 2026-05-10 — Apply only current safe-runner automatic reference updates

Decision: Task 38 will apply only current `update_reference` and `update_reference_scoped` recommendations generated under `scripts/template-ssot-scanner/output/data/` and executed through `scripts/template-ssot-scanner/apply_reference_fixes.py`.

Rationale: The fresh scanner run produced 141 automatic dry-run changes, plus broader manual-review and monolith-completion findings. The automatic changes are suitable for this Phase 1 reference-remediation task; broad section migration, circular dependency redesign, and orphan decisions are separate work and should not be bundled into a blind apply.

Evidence:
- `designs/phase1-reference-remediation-scope.md`
- `reports/phase1-reference-remediation/scanner-suite-2026-05-10.txt`
- `reports/phase1-reference-remediation/dry-run-regenerated-2026-05-10.txt`

## 2026-05-10 — Preserve Markdown link locality in remediation tooling

Decision: Reference remediation must preserve executable Markdown link semantics, not only scanner-normalized repo paths.

Rationale: The first full pytest run showed that root-style targets inserted into nested Markdown files broke local link resolution. The correct system fix is to make the safe runner emit source-relative Markdown link targets and make the scanner understand those local links.

Evidence:
- `reports/phase1-reference-remediation/tests-full-2026-05-10.txt` records the caught failure.
- `reports/phase1-reference-remediation/tests-reference-fixes-2026-05-10.txt` records focused regression coverage passing after the fix.
- `reports/phase1-reference-remediation/tests-full-final-2026-05-10.txt` records the final full test suite passing.
