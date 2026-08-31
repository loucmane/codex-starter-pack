# Bead ga-c8al Support hierarchical Bead IDs in transactional workflow lifecycle – Implementation Notes

## Planned Workstreams

- Extend transactional ID validation to native hierarchical IDs without admitting unsafe
  path characters or malformed segments.
- Align `scripts/codex-task`, Aegis installer source, and packaged assets to the same grammar.
- Classify blocking and informational Bead relationships once and use the shared result in
  both readiness and attach decisions.
- Prove RED failures first, then run the complete affected workflow/Codex/Aegis/parity suite.

## Verification

- RED: 5 workflow failures plus 2 downstream-validator failures reproduced.
- GREEN: 41 focused lifecycle/validator tests passed.
- Regression: 445 affected tests passed; one release-certification smoke remained skipped
  behind its existing `AEGIS_RUN_CERTIFICATION_SMOKE=1` opt-in.
- `git diff --check`: passed.
