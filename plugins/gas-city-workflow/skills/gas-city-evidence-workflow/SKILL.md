---
name: gas-city-evidence-workflow
description: Freeze and validate report-only, blind evidence-review runs for Gas City-managed projects. Use when asked to inspect batches or candidates with Sol/Fable reviewers, build blind bundles, run a shadow quality review, compare independent reviewer findings, or prove project outputs stayed unchanged. Do not use for authoritative project decisions, promotion, deployment, or ordinary source implementation.
---

# Gas City evidence workflow

Use the parent `gas-city-workflow` lifecycle first. The evidence run must have one live parent
bead in the project profile's declared rig and a clean `codex/<bead>-...` subject worktree.

Read [the evidence profile contract](../../references/evidence-profile-contract.md) before
creating a profile, request, authorization envelope, or controller event.

## Required sequence

1. Resolve project context and read the parent bead from its explicit rig.
2. Create or inspect the tracked project-owned profile and assets. Never place domain verdict
   logic in this plugin.
3. Create a fresh external run root, freeze request, and current authorization envelope. Use
   only `mode=shadow`; an authoritative mode is a hard error.
4. Freeze once with `freeze_evidence_run.py --request ... --profile ... --manifest ...`.
5. Run `validate_evidence_run.py` between freeze and bundle construction.
6. Run project-owned builders into exact fresh bundle directories. Audit every lane with
   `audit_blind_bundle.py --stage pre-dispatch`.
7. Have Fable review only its declared full-visibility inputs. Record `seal` on the parent bead,
   have Fable read that note back, then record `fable-readback`.
8. Only with independent route/lifecycle/worker authority, record `dispatch` and dispatch the
   bounded report-only lanes. A manifest or bead never grants dispatch.
9. Audit with `--stage post-collection`, then validate every report with
   `validate_review_report.py`.
10. Record `release` after collection. Run `compare_review_lanes.py`; it compares evidence and
    always leaves `domain_verdict` null.
11. Revalidate the manifest to prove authoritative outputs remain byte-identical. Prove zero
    worker/session/worktree residue, append the closeout pointer to the parent bead, and use the
    normal lifecycle finish transition.

## Stop rules

Stop on digest drift, dirty subject state, project/rig mismatch, unresolvable parent bead,
expired authorization, existing run id, unexpected bundle/output files, Git metadata, symlinks,
special files, forbidden content, report identity/schema mismatch, broken event order,
authoritative-output drift, or any request for authoritative mode.

Repairs are append-forward: create a new run id, name the frozen predecessor in `supersedes`, and
bind its absolute manifest path in `supersedes_manifest`. Never rewrite, relocate, copy, or clean
earlier run evidence.
