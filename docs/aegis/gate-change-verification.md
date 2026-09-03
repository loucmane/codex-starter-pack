# Gate and installer change verification

Focused RED/GREEN tests shorten implementation feedback; they are not publication
evidence for shared gate, parser, installer, or managed-asset changes. The full
downstream surface must pass on the same final candidate:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/claude_adapter tests/meta_workflow_guard
python3 scripts/aegis-refresh-managed-update-goldens --check
python3 scripts/codex-guard validate --include-untracked
git diff --check
```

Hosted required CI still runs the repository-wide matrix. Local success never
waives exact-head/base, signature, required-CI, mergeability, or review-thread rules.

## Packaged copies and deterministic fixtures

Keep the explicit `tests/meta_workflow_guard/test_assets_scripts_parity.py` mirrors
byte-identical, including `codex-guard` and `_aegis_installer.py`. Consumers install
these packaged copies; testing only the development copy does not prove delivery.

After a reviewed asset change, run:

```sh
python3 scripts/aegis-refresh-managed-update-goldens
```

The command prints re-derived fixture JSON from the real installer in temporary
synthetic projects. Apply that output to
`tests/fixtures/aegis/managed-update-golden-plans.json` and review the diff. It keeps
the project-owned file seeds and expected modification sets fixed, refuses unsafe
operations or changed modification scope, and recalculates only plan summaries
and operation digests. Never invent expected hashes or run this against a real
HPFetcher/Blog checkout. A second `--check` must pass without edits.

## Observation audit output is not a permission exemption

Observation start binds the exact gate-decision log's existence, length, and digest.
Closeout accepts only complete, schema-valid appended JSONL records while preserving
the bound prefix. Symlinks, special files, deletion, truncation, prefix rewriting,
malformed/duplicate fields, and incomplete writes fail closed. Reads are bounded to
16 MiB; exceeding that limit requires explicit diagnosis, not automatic deletion.
Unrelated reports and source edits remain unexpected changes. Legacy observation
baselines receive no implicit new exemption.

This is audit-integrity classification, not cryptographic proof of the writer and
not an authorization mechanism. It does not widen shell environment or command
allowlists. Fresh-session acceptance after merge-bound activation must include
observation start/stop plus positive bootstrap and adversarial refusal cases.

## Coordinator concurrency

External source-work bindings are not native worker claims or distributed leases.
One coordinator per Bead is an operator constraint; no concurrent routing, closure,
or ownership write is allowed. Fresh readbacks and the per-common-directory lock
detect observed drift but cannot eliminate the Beads API race. Atomic expected-digest
updates are tracked by `ga-gurw` and require separate implementation and proof.
