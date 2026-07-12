# HP-Fetcher Read-Only Context-Budget Dogfood

Date: 2026-07-12 23:22 CEST

Task: 238

## Scope

Render the live HP-Fetcher `aegis status` payload through the Task 238 source
renderer without installing assets, applying an update, draining advisory pending
events, repairing workflow state, or changing Git state. The target remained
`/home/loucmane/dev/hpfetcher`; only the command's stdout was written to `/tmp`.

## Command Shape

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m aegis_foundation.cli \
  --source-root /home/loucmane/codex \
  status --target-dir /home/loucmane/dev/hpfetcher
```

Before and after the command, the observation calculated SHA-256 fingerprints for
the pending file, every file in `.aegis/state`, and the NUL-delimited Git porcelain
view. It also read the pending-event count with `jq`. No target file was opened for
write.

## Result

| Measurement | Result |
| --- | --- |
| Source pending events | 4,151 |
| Default stdout lines | 1 |
| Default stdout bytes | 4,307 |
| Renderer latency | 92.381 ms |
| Exact pending collection path | `$.workflow_guidance.details.pending_event_ids` |
| Exact pending count in metadata | 4,151 |
| Truncation records | 7 |
| Governance calls required by the dogfood | 1 read-only status invocation |
| Pending drain/repair/update calls | 0 |
| Copyable next action | `./.aegis/bin/aegis next --target-dir .` |

The renderer linked the full-detail sources:

- `.aegis/foundation-manifest.json`
- `.aegis/state/current-work.json`
- `.aegis/state/pending-tracking.json`
- `.aegis/reports/verification-report.json`
- `.aegis/reports/closeout-report.json`

## Non-Mutation Proof

| Fingerprint | Before | After | Equal |
| --- | --- | --- | --- |
| `.aegis/state` aggregate SHA-256 | `f79db27717d25e9d8a647f1dd438354b91d789b9f8174c4dbccb12a5ddd0cffc` | `f79db27717d25e9d8a647f1dd438354b91d789b9f8174c4dbccb12a5ddd0cffc` | yes |
| pending file SHA-256 | `e7d18e7442f269bfd8ae0b8e7bd5be48dac7a00e28416bce5010eca4753494ee` | `e7d18e7442f269bfd8ae0b8e7bd5be48dac7a00e28416bce5010eca4753494ee` | yes |
| pending event count | 4,151 | 4,151 | yes |
| Git porcelain SHA-256 | `fd5be320aa9a811e45d194262ea55a5b07066a994e094cfa7d6326707a074444` | `fd5be320aa9a811e45d194262ea55a5b07066a994e094cfa7d6326707a074444` | yes |

## Verdict

Pass. The live pathological payload fits the default 60-line/8-KiB contract,
preserves the exact 4,151-event cardinality, points to complete evidence, and does
not mutate or drain HP-Fetcher state.

## Rollback

No target rollback exists because the dogfood made no target change. Reverting Task
238's CLI renderer integration restores the prior stdout behavior while leaving the
underlying HP-Fetcher state and report files untouched.
