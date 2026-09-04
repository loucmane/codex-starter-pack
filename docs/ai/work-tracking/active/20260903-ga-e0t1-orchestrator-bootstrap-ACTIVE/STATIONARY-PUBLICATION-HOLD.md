# ga-fjoi — source PASS, publication preflight HOLD

## Observed boundary

Fable's independent R5 source review is accepted and all 22 frozen source hashes
are unchanged. Supported workflow verification, source guard, generated consumer
golden parity and drift check pass. Canonical Operations and remote main remain
`3641fa7aa11c9713da3dac3c075f50caee547ed8`; canonical checkout is clean.
Signing-readiness check reported cached and ready without a prompt; no signing
operation was attempted in this continuation.

One supported publication-preflight attempt was made:

```text
python3 plugins/gas-city-workflow/scripts/workflow.py publish --root /home/loucmane/gas-city-ops-worktrees/ga-e0t1-orchestrator-bootstrap
exit=2
gas-city-workflow: BLOCKED: external source workflow has unresolved unattached dependencies
```

This is a pre-mutation refusal in the first ownership check, before publication
journal recording or clean/signed-head inspection. No Git push, merge, activation,
new client or live Bead-note retry occurred. Source remains uncommitted and open.

## Cause confirmed from code and fresh Beads

`workflow.py::_publish` requests `check_active_ownership(...,
dependencies_complete=True)`. `workflow_ownership.py::check_active_ownership`
normally permits already-attached primary dependencies during source work, but
empties that allowed set when `dependencies_complete=True`. Its error text still
says "unattached" even for a correctly attached active repair.

Fresh primary ga-e0t1 readback has exactly two blocking prerequisites:
ga-t469 is closed PASS; ga-fjoi is in progress. The ready workflow journal and
active plan both bind ga-fjoi as attached, and both Beads carry the verified
external-coordinator binding. Supported `workflow.py verify` passed this binding
on 2026-09-04T15:06:55Z. Thus the failure is not an absent attachment, ownership
drift, native assignment, or unknown prerequisite.

ga-fjoi's acceptance requires merged delivery, activation and an unchanged
canonical Fable seat coordinating two synthetic worktrees. Closing it before
publication would falsely claim that unperformed acceptance. Removing its
blocking edge or calling Git publication directly would evade the existing gate.
None was attempted.

## Narrow proposed disposition, not implemented

Separate **candidate delivery** from **task acceptance/closeout** in the supported
workflow. A reviewed candidate-publication path should retain exact project,
branch, worktree, live ownership, attached-journal parity, guard, clean signed
head, CI/base and review checks, while allowing only its already-attached,
externally owned repair Bead to remain in progress for post-merge acceptance.
Unattached blockers and conflicting/assigned/routed ownership must still refuse.
`finish` must continue requiring every blocking prerequisite to be completed.

Regression evidence must prove that narrow positive case and all negative cases,
and verify no new dispatch, source-edit, signing or native-permission approval.
Independent review remains required before runtime activation. The existing
22-file candidate needs no alteration to its reviewed source-only loading checks.

The operator's last exact authorization preserved every other permission check.
Consequently this continuation does not silently change the publication gate or
claim that the review itself authorizes the additional transition semantics.
Pending a bounded disposition, preserve the candidate, all histories and evidence;
do not replay the refused live note, rewrite archives, or close either Bead PASS.
