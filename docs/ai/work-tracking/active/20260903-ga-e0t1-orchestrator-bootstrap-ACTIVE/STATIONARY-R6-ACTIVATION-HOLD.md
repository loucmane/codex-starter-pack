# ga-fjoi — R6 publication PASS; runtime-inventory compatibility HOLD

## Completed delivery preparation

Fable's independent R6 source PASS was recorded. All 23 reviewed source hashes
remain exact. Signed source commit `61da46d9b28621418a23aa8f2e67207552a1009a` has
tree `b847a0c55cd1aeedbb5324280d70827c95c80bf6`. The exact supported publication
invocation that previously refused now returns READY with ga-fjoi still open.
Result: `reports/ga-fjoi-r6-signed-publication.json`.

PR #376 is open. The repository's strict up-to-date requirement needed a signed
ancestry-only integration of exact main `3641fa7aa11c9713da3dac3c075f50caee547ed8`.
Preview and actual merge were conflict-free and byte-identical to the reviewed
tree. Final pushed head `64e4bf13f6b48bc73e87305626a912c9a0a46497` has parents
`61da46d9b28621418a23aa8f2e67207552a1009a` and that exact main. Both signatures
verify with FD5585922F5335BC378AD8D42ECF4432C7E7982D. Supported publication is READY
for the final head at 2026-09-04T15:57:44Z. Hosted CI run 33892509880 was running
when this new hold was identified; no merge or activation is permitted by green
CI alone while the finding below remains unresolved.

The first publication invocation was blocked before execution by tool review;
source inspection established its local-journal-only scope and the same command
was approved on reassessment. A compound push command was separately refused
before execution because of shell substitutions. After fresh exact-pin reads and
inspection of the supported feature-branch push grammar, the literal non-force
push was accepted. Neither case used a policy change, alternate tool or override.

## Additional pre-activation proof and finding

A read-only check loaded the candidate through its actual `.claude/scripts/gate_lib.py`
and called `coordination_runtime.reviewed_runtime(candidate, candidate)`. It refused:
`ValueError: runtime cache has no reviewed extensionless executable`.

Per-file read-only diagnosis identified exactly two of the candidate's 95 ignored
runtime files. Canonical Operations has 108 ignored runtime files and all satisfy
the candidate's cache-association check; canonical source has not been activated.

| Existing preserved cache | Exact tracked source | Git mode |
| --- | --- | --- |
| `scripts/__pycache__/template-metrics-dashboardcpython-312.pyc` | `scripts/template-metrics-dashboard` | `100644` |
| `scripts/__pycache__/template-monitoringcpython-312.pyc` | `scripts/template-monitoring` | `100644` |

Cache mtimes are 2026-09-03 16:58 CEST, predating this delivery turn. Cache SHA-256:
`e198f932d71c80bcd7bdcd50af5799a12962c0b8e94546b18432c100c5c870c5` and
`4b741655c70545e7f8c10af7420af352d60f6f6422e777ca4b81c10fbf9c1093` respectively.
Their source bytes and mode remain exact Git objects `aa22f4cbe1a5cd70ed6ccc8758cd23d282008210`
and `d48da01f5e3a95c23e4d682afb6d2206102e5a98`. No cache payload was executed or
unmarshalled; diagnostic hashing does not reintroduce cache-content approval.

`_preserved_cache` explicitly requires `record[0] == "100755"` for the extensionless
naming case. Python's `SourceFileLoader` does not require that mode. The existing
repository tests use that loader for these exact paths (for example,
`tests/meta_workflow_guard/test_template_metrics_dashboard.py:18-22`). The new cache
test only creates mode-0755 helpers, and its negative test deliberately refuses
a tracked mode-0644 extensionless file. Thus the unit tests encode an overstrict
association rule and miss the real worktree's legitimate pre-existing inputs.

## Proposed correction — not implemented

Review cache association against an exact tracked regular source file, without
inventing an execute-bit requirement for interpreter-loaded extensionless source.
Retain the full actual-source Git-object digest and Git-mode comparison in `_verify`,
mandatory source-only loading, exact null device, existing naming/path/symlink/
special-file/size/count checks and refusal for caches without tracked source.
Do not chmod the helpers, delete caches or inspect/unmarshal cache payloads to
make this pass. Add real SourceFileLoader-generated mode-0644 cache regression
coverage alongside mode-0755, missing-source and actual-mode-drift negatives.

This would change an additional mode restriction that the last specific operator
authorization required preserving. No source correction is silently applied.
Obtain the narrow disposition and independent review before activation. The R6
publication delta remains independently proven; this is a distinct source-only
runtime compatibility finding, not a failed publication or live mutation.

## Preserved state

Canonical main is still `3641fa7aa11c9713da3dac3c075f50caee547ed8` and clean.
The five protected configuration files match the previous baseline; all ignored
files are preserved. Supervisor PID1769/start210566291/NRestarts0 is unchanged;
all four project rigs are suspended, 0/17 agents and no native sessions.
The read-only baseline is `reports/ga-fjoi-r6-activation-before.json`.
ga-fjoi and ga-e0t1 stay in progress. No merge, activation, cache cleanup, file-mode
change, live Bead note, new Fable client, worker dispatch or HPFetcher/Blog write.
