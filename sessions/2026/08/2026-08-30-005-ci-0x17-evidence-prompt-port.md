---
session_id: 2026-08-30-005
date: 2026-08-30
time: 22:50 CEST
title: Bead ci-0x17 - Port evidence-reviewer prompt repair to canonical source
---

# Session 2026-08-30-005 — Bead ci-0x17

Operator CODEX POST-CLOSE REVIEW ordered the durable closeout of the hpf-fk02
evidence-reviewer prompt/policy repair: port the live-installed prompt
(c13b5834…) byte-for-byte into canonical source (was f52ae745…), add the
prompt-policy agreement tests and worker-equivalent control smoke, merge under
the standing evidence-gated delivery policy, then apply only the merge-bound
installer with byte-agreement and idempotence proofs.

## Closeout

- Archived work-tracking folder: `docs/ai/work-tracking/archive/20260830-ci-0x17-evidence-prompt-port-COMPLETED`

## Progress

- **[22:50]** — [S:20260830|W:ci-0x17-evidence-prompt-port|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M %Z"`] Confirmed current timestamp as `2026-08-30 22:50 CEST`
- **[22:50]** — [S:20260830|W:ci-0x17-evidence-prompt-port|H:plugins/gas-city-workflow/config/evidence-reviewer/prompt.template.md|E:sha256:c13b5834251f98234f2e] Ported the live-installed evidence-reviewer prompt repair byte-for-byte into canonical source per the operator CODEX POST-CLOSE REVIEW
- **[22:52]** — [S:20260830|W:ci-0x17-evidence-prompt-port|H:pytest|E:tests/evidence_reviewer/test_prompt_policy_agreement.py] Added hermetic prompt-policy agreement tests plus worker-equivalent control smoke; 4/4 passing locally with the live installation present
- **[22:55]** — [S:20260830|W:ci-0x17-evidence-prompt-port|H:git|E:commit:95bcfb02;pr:operations-328] Signed commit pushed; PR 328 opened under the evidence-gated delivery policy at ops origin/main tip 03609690
- **[23:03]** — [S:20260830|W:ci-0x17-evidence-prompt-port|H:scripts/codex-task|E:docs/ai/work-tracking/archive/20260830-ci-0x17-evidence-prompt-port-COMPLETED/TRACKER.md] Scaffolded, recorded, and reconciled the completed work-tracking bundle for bead ci-0x17
