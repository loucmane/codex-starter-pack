# ga-fjoi R7 — authorized cache-association correction

The operator approved correcting the mode-0755-only association after the R6
actual-worktree inventory HOLD. That finding, previous source reviews, signed
R6 publication evidence and failed attempts remain preserved unchanged.

Only three R6 source files change: runtime cache association, its contract and
regression tests. The 20 other source files are byte-identical. The executable
delta removes only the duplicate extensionless `100755` restriction; source
Git-object bytes/mode verification and every other runtime function remain exact.

RED: 8 failed / 57 passed, reproducing the single association defect. Focused
GREEN: 111 passed. Final frozen full regression: **2,766 passed, 21 existing skips,
zero failures/errors** (2,787 cases; 603.55 seconds). The earlier partial run and
denied retry remain preserved. The operator explicitly permitted declared test
dependencies only in disposable `/tmp` virtualenvs; the unchanged full suite then
passed, including the previously blocked packaging case. No test was disabled,
edited or newly skipped. Lint, golden parity and workflow verification PASS.

Real read-only cache classification: candidate 95/95 and canonical 108/108 PASS.
Both formerly rejected cache files, their mode-0644 sources and all canonical
cache/config baselines remain unchanged. Full integrity correctly refuses the
uncommitted candidate; it is not replaced by this classification-only diagnostic.

Review packet: `reports/ga-fjoi-cache-association-r7-review.md`.
Proof receipt: `3388528834b72c6e7f6f2ea5f22afe8fdff29a3af4bee23931f5b83b7c0cb2ba`.
Three-file delta patch: `26dd46537127b2f00bdfb13b51c83b1cb871cf8b3901d31146ef303a8bb14fbb`.
Test/authority receipt: `reports/ga-fjoi-cache-association-r7-verification-HOLD.json`.
Raw JUnit evidence is preserved both at original paths and as lossless compressed
report copies. Scope resolution: `STATIONARY-R7-TEST-AUTHORIZATION.md`.
Final source-verification receipt:
`reports/ga-fjoi-cache-association-r7-final-verification.json`, SHA-256
`354d00b005ee8e17943b7cc1e954431cf86dbe0efaa6de8b42ce0ac7f9e131a7`.
Final JUnit SHA-256:
`cbc90230bf859dc0d2c264f7e1b9880af7d4809912cb492249b3d496471fbc4c`.
All 23 frozen source hashes and protected canonical inputs remain unchanged.

PR #376 remains draft at R6 head `64e4bf13f6b48bc73e87305626a912c9a0a46497`;
its green hosted CI does not validate R7. No R7 commit, activation, live Bead-note
retry, Fable invocation, rig action or protected-project change. Independent R7
review precedes delivery/activation. Both Beads stay open for live acceptance.
