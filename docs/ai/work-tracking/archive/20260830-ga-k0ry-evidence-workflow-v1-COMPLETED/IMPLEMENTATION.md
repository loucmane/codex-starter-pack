# Evidence workflow v1 implementation

## Generic surface

- Added strict `gas-city-evidence-run.v1` JSON Schema.
- Added the `gas-city-evidence-workflow` skill and project profile contract.
- Added exactly five executable commands: freeze, validate, bundle audit, report validation, and
  lane comparison.
- Kept `mode=shadow` structural. The generic comparator emits `domain_verdict: null` and cannot
  replace project quality logic.
- Added an optional validated project `base_ref`; HPFetcher now derives new task worktrees from
  `refs/remotes/origin/main` without touching its dirty, parked canonical checkout.
- Added target-aware lightweight lifecycle scaffolding for projects without an installed Aegis
  foundation. The canonical `codex-task` validates the foreign Git root, writes only beneath that
  worktree, forbids cross-project Taskmaster kickoff, and exposes target-aware plan sync.
- Added profile-native readiness for frozen-legacy projects. It binds the transition journal,
  exact bead branch, selected base ancestry, current plan/session, and one matching tracker while
  tolerating only unrelated trackers that are tracked and byte-unchanged at the selected base.
- Made lightweight checkpoint and finish resolve the exact bead-scoped ACTIVE folder instead of
  relying on a single-active-folder memory convention. Cross-project finish reuses the canonical
  transactional archive engine while preserving unrelated historical trackers and frozen `.aegis`
  state; same-repository source closeout remains unchanged.

## Frozen bindings

The manifest binds the parent bead, project and rig, clean subject repository/branch/commit/tree,
profile, request, authorization envelope, prompts, rubrics, schemas, bundle builders, external
inputs, Fable inputs, candidates, lane directories, and authoritative outputs. The validator
recomputes every binding and refuses drift.

The authorization envelope is an audit artifact only. Its exact report write roots and explicit
exclusions are checked, but current dispatch and lifecycle authority remain external gates.

## Fail-closed fixtures

Focused fixtures cover clean freeze/validation plus refusal on overwrite, external/profile drift,
authoritative mode, repair without `supersedes`, dirty source, project/rig mismatch, blind-bundle
leakage, Git/symlink content, undeclared output, candidate mismatch, malformed event chains, and
interrupted closeout. Seal → Fable readback → dispatch → release is digest-chained and strictly
ordered.

Validation evidence:

- Codex plugin validator: PASS.
- Evidence and plugin focused tests: 16 passed; lifecycle/plugin base-ref regression: 28 passed.
- Cross-project lifecycle proof: HPFetcher `hpf-nqzf` reached journal phase `ready` from exact main
  `5415f14f...` in its isolated worktree while the dirty canonical checkout remained untouched.
- Target-aware helper regression: 246 combined `codex-task` and workflow-transition tests passed.
- Packaged `codex-task` parity and all focused lifecycle/evidence regressions: 272 passed.
- Complete repository regression with network available for isolated editable-install fixtures:
  2,322 passed and 21 explicitly skipped.
- Optional `ruff` command was unavailable in the environment; Python compilation and repository
  guard checks remain required before commit.

## Pilot-discovered confinement repair

The first immutable pilot manifest froze successfully before dispatch, but its report roots were
under the operations scratchpad while the managed HPFetcher Sol worker is intentionally writable
only beneath the HPFetcher worktree root. No route, session, or worker mutation occurred.

Repairs now accept a required absolute `supersedes_manifest` only when `repair=true`. The
successor manifest binds that predecessor file's SHA-256 and revalidates its run identity. This
allows a repair to move to an already-approved output root without copying, relocating, or
rewriting old evidence and without widening a worker sandbox. Legacy non-repair manifests remain
valid and must omit the new field. Focused coverage proves cross-root repair, predecessor digest
drift refusal, and backward-compatible validation of run 001.

## Pilot-discovered Codex hook trust repair

Run 004 proved project trust alone is insufficient for unattended reviewer startup: Codex also
requires explicit trust for each project hook hash. The worker stopped at the review prompt before
claim, bundle access, report creation, or subject mutation, and the immutable run plus stop evidence
remain preserved.

The append-forward repair keeps the provider/agent install separate from a dedicated
`codex_hook_trust.py` transaction. It binds the canonical hook manifest byte-for-byte, validates
exactly four resolved project hooks through `hooks/list`, obtains the user-config version through
`config/read`, and writes only those four current hashes through one optimistic
`config/batchWrite`. It immediately re-lists and requires `trusted`, rejects changed commands,
sources, identities, extras, load diagnostics, or unrelated nonblank/semantic config changes, and
retains the installer's exact backup/rollback boundary. A disposable copy of the real Codex config
proved untrusted-to-trusted migration and byte-idempotent reapplication; 56 focused workflow tests,
Ruff, plugin validation, and diff checks pass. The live migration remains a separate gate.

## Pilot-discovered Codex control-policy repair

Run 005 lane 1 reached non-interactive startup but Codex correctly denied the absolute Gas City
claim command because the isolated evidence root had no project-local exec policy. The attempt
failed before claim, bundle access, report creation, or subject mutation; its transcript and stop
record remain immutable.

The attached `ga-wwmw` repair adds one dedicated five-rule profile for only the absolute claim,
bead show/update/close, and drain-ack prefixes. The evidence-reviewer installer validates the
source and installed copies with the real `codex execpolicy check` surface, including negative
lifecycle, routing, mail, molecule, restart, direct-`bd`, shell, and unrelated-command cases. It
refuses any unrelated entry in the dedicated rules directory, installs the exact file at mode
`0644`, records the absent/exact predecessor state, is byte-idempotent, and removes both the file
and a newly created rules directory on rollback. The broader 14-prefix worker policy remains out
of scope. The real read-only preview passed with policy SHA-256
`dc2e7ac6fc66714a73e482e50bdff7fb3fc77936c7bff8a76723a6caa4d3b67d`; 34 focused tests,
Ruff, plugin validation, and diff checks pass. Live migration remains separately ordered after
merge.

## Progress Log
- **2026-08-30 16:03 CEST** - [S:20260830|W:ga-k0ry-evidence-workflow-v1|H:plugins/gas-city-workflow/scripts/install_evidence_reviewer.py|E:bead:ga-25cw;tests:23-passed;install-plan:0bb089972880127b0e8b619fd35813945b69d9a990c1fef2030d0af7e3b05660] Attached blocking bead ga-25cw to the active ga-k0ry context, implemented a generic no-project-access evidence reviewer plus transactional installer and rollback, and matched the validated live candidate hashes without mutating Gas City.
- **2026-08-30 18:24 CEST** - [S:20260830|W:ga-k0ry-evidence-workflow-v1|H:codex:hooks/list+config/batchWrite|E:manifest:55e21a9d981805afb62da110b022bc847f7ad2b9a62bada45de95dbdfa472410;tests:56-passed] Replaced interactive hook memory with an exact, modular, supported-API trust transaction and proved it twice against a disposable copy of the real configuration.
- **2026-08-30 19:25 CEST** - [S:20260830|W:ga-k0ry-evidence-workflow-v1|H:plugins/gas-city-workflow/scripts/install_evidence_reviewer.py|E:bead:ga-wwmw;policy:dc2e7ac6fc66714a73e482e50bdff7fb3fc77936c7bff8a76723a6caa4d3b67d;tests:34-passed] Added the transactional five-prefix evidence-reviewer policy, real Codex positive/negative validation, exact rollback and idempotence coverage, and explicitly excluded the broader default profile.

## Pilot completion

- The merge-bound five-prefix reviewer policy was installed transactionally and proved by two
  non-interactive native claims. No broader worker policy was installed.
- Frozen run `hpf-nqzf-batch13-shadow-20260830-005` completed both report-only lanes. The
  blind-solver report is SHA-256
  `66aeac2db41ebbcf0e46eca510408df312ac74d8fe62698b5885a9e2afb3e7ff`; the adversarial-audit
  report is SHA-256 `32790a8c177a5750348615ff0ae7e26c24ef8cc5c9782738f453846a1fab7d76`.
- Release event SHA-256
  `ef110d77273dfceec56f17377737e2196e560073dd8d67680f33bd9f8e289500` binds the pre-worker
  Fable readback. Comparison SHA-256
  `2b505f349a8bdb0d7758748efb99326f0bb0583a1ad0745941f9cb74def6461a` remains evidence-only
  with `domain_verdict=null`.
- Final bundle audits and manifest validation proved the authoritative batch13 tree remained
  byte-identical. Both worker sessions drained; HPFetcher and every other project rig were
  suspended with zero session, process, or tmux residue.
- HPFetcher PR #367 merged signed head `7ee1f35a9260a27090720197b4487164b427df54` as
  `652d81e74bdde97c3735b63b09639db9aa3c3c84`; the merged tree is byte-identical to
  `c5c2450bae6db457c88df90d5a7b257c272a2355`.

- **2026-08-30 20:02 CEST** - [S:20260830|W:ga-k0ry-evidence-workflow-v1|H:evidence-workflow:closeout|E:bead:hpf-nqzf;run:hpf-nqzf-batch13-shadow-20260830-005;merge:652d81e74bdde97c3735b63b09639db9aa3c3c84] Completed the authorized shadow pilot, final validations, source publication, and zero-residue closeout without promotion, deployment, or authoritative-output mutation.
