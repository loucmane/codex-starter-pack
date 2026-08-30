---
session_id: 2026-08-30-005
work_context: ci-0x17-evidence-prompt-port
handler_target: plugins/gas-city-workflow/config/evidence-reviewer
bead_ids: [ci-0x17]
attached_bead_ids: []
branch_policy: codex/ci-0x17-evidence-prompt-port
evidence_summary:
  - docs/ai/work-tracking/archive/20260830-ci-0x17-evidence-prompt-port-COMPLETED
  - plugins/gas-city-workflow/config/evidence-reviewer/prompt.template.md
  - tests/evidence_reviewer/test_prompt_policy_agreement.py
  - bead:ci-0x17
plan_version: v1
emergency_bypass: false
---

# Plan - Bead ci-0x17 Port evidence-reviewer prompt repair to canonical source

## Header
- **Session ID (S)**: 2026-08-30-005
- **Work Context (W)**: ci-0x17-evidence-prompt-port
- **Handler Target (H)**: plugins/gas-city-workflow/config/evidence-reviewer
- **Bead IDs**: ci-0x17
- **Branch Policy**: codex/ci-0x17-evidence-prompt-port
- **Evidence Summary (E)**: docs/ai/work-tracking/archive/20260830-ci-0x17-evidence-prompt-port-COMPLETED, plugins/gas-city-workflow/config/evidence-reviewer/prompt.template.md, tests/evidence_reviewer/test_prompt_policy_agreement.py, bead:ci-0x17
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID | Description | Evidence | Status |
|---|---|---|---|
| plan-step-scope | Confirm scope and operator authority for porting the live-installed evidence-reviewer prompt repair into canonical source (CODEX POST-CLOSE REVIEW: evidence run PASS, durable closeout HOLD; installed c13b5834 vs stale canonical f52ae745) | bead:ci-0x17; docs/ai/work-tracking/archive/20260830-ci-0x17-evidence-prompt-port-COMPLETED/FINDINGS.md | completed |
| plan-step-implement | Port the installed prompt byte-for-byte into canonical source and add prompt-policy agreement tests plus the worker-equivalent control smoke | plugins/gas-city-workflow/config/evidence-reviewer/prompt.template.md; tests/evidence_reviewer/test_prompt_policy_agreement.py; plugins/gas-city-workflow/scripts/evidence_reviewer_control_smoke.sh | completed |
| plan-step-verify | Prove tests pass (4/4 locally with live installation), signed commit pushed, PR opened under the evidence-gated delivery policy | commit:95bcfb02;pr:operations-328; docs/ai/work-tracking/archive/20260830-ci-0x17-evidence-prompt-port-COMPLETED/HANDOFF.md | completed |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `plugins/gas-city-workflow/config/evidence-reviewer/prompt.template.md`
- `tests/evidence_reviewer/`
- `plugins/gas-city-workflow/scripts/evidence_reviewer_control_smoke.sh`
- `docs/ai/work-tracking/archive/20260830-ci-0x17-evidence-prompt-port-COMPLETED`
- Primary bead `ci-0x17`

## Branch Policy
- Working branch: `codex/ci-0x17-evidence-prompt-port`

## Amendments & Versioning
- 2026-08-30 - Bead `ci-0x17` kickoff scaffolded through `codex-task work-tracking scaffold`; plan authored to bind the operator-ordered durable closeout of the hpf-fk02 prompt/policy repair.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review bead `ci-0x17` and the archived bundle `docs/ai/work-tracking/archive/20260830-ci-0x17-evidence-prompt-port-COMPLETED`.
  3. After the evidence-gated merge, apply only the merge-bound `install_evidence_reviewer.py` and prove byte agreement + idempotence.
  4. Run `python3 scripts/codex-task plan sync` after tracker updates.
