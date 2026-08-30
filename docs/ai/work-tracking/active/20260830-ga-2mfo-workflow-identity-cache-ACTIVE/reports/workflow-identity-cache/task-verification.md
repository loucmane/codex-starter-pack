# ga-2mfo task verification

## Workflow identity and cache repair

- `tests/meta_workflow_guard/test_gas_city_workflow_plugin.py`
  - PASS: 8 focused tests.
- `python3 scripts/validate_codex_plugin.py plugins/gas-city-workflow`
  - PASS.
- Canonical `/home/loucmane/gas-city-ops` and registered linked-worktree contexts
  - PASS; preserved legacy `/home/loucmane/codex/...` context refused.
- Signed source head `d1fbb19979675d12a7ce464b2e3969de94173682`
  - Merged by PR #312 as `accfe9b0ab267e83488036f0d34ad18611fa9ce5` with byte-identical tree `9544034910de64793da2dde5c4db84b272fc6ad7`.
- Locked managed `gascity` import cache
  - Restored at cache key `954ed14987da288bfb98feee4cdab5043a44de1a8a9cf47afaaa0ce6e438fd5f`, exact locked commit `17bf05ccfc05ea9f4f0f4827f8ea3a9198bd6e28`.
  - `pack.toml`, `packs.lock`, and `city.toml` remained byte-identical.
- Canonical explicit `gc --city /home/loucmane/gascity/city --rig gascity bd ready`
  - PASS.

## Transactional source-closeout recovery

- `tests/meta_workflow_guard/test_source_checkout_closeout.py` and `tests/meta_workflow_guard/test_codex_task.py`
  - PASS: 253 tests.
- Packaged runtime, release distribution, invocation contract, and installer suites
  - PASS: 185 tests; 3 explicitly optional smoke tests skipped.
- Python compilation, Ruff with the repository's pre-existing `codex-task` E402 exception, `git diff --check`, and packaged `codex-task` byte parity
  - PASS.
- Recovery guarantees
  - Matching recovered source current-work retires only after terminal archive verification.
  - Interrupted closeout replay and already-completed archive repair are idempotent.
  - Installed, malformed, symlinked, tampered, and differently scoped state is preserved and refused.

## Remaining acceptance work

- Merge the signed source-closeout recovery change after hosted CI passes.
- Repair the preserved `ga-2mfo` closeout through the supported completed-archive path.
- Prove source lifecycle `IDLE`, readiness/guard PASS, close `ga-hd6c` and `ga-2mfo` with evidence, and publish their terminal Obsidian projections.
