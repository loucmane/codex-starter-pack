# Findings

- 2026-07-13 — PR #264 proved a circular dependency: the required delivery job asks
  GitHub for clean mergeability while its own check is still pending. Current evidence
  evaluates `allow` immediately after the job completes, but the merge step has already
  been skipped.
- 2026-07-13 — `mergeable=true/state=blocked` distinguishes protection blocking from a
  content conflict, but does not itself prove the blocker is self-owned. Therefore it can
  support only a non-authorizing provisional decision followed by fresh full evaluation.
- 2026-07-13 — GitHub's required context can be made satisfiable without weakening branch
  protection by moving merge authority to a separate non-required job. The evaluator can
  finish read-only; only then can the executor observe clean mergeability.
- 2026-07-13 — The executor must recollect rather than consume evaluator artifacts. This
  closes head/base, review, workflow, inventory, and policy-state races between the two
  jobs and makes `provisional` incapable of authorizing a merge by construction.
- 2026-07-13 — The full meta-workflow suite passed 1,210 tests with four documented opt-in
  release/MCP smoke skips, so the split does not regress installer or legacy workflow
  contracts locally.
- 2026-07-13 — The first ordinary canary, PR #269 at exact head
  `2f01675029765e6e99a6a784ce9d397f1388dcdf`, reached four green required workflows,
  clean current base, complete one-file inventory, and zero review threads. Trusted run
  `29270554173` completed the evaluator but skipped the executor; PR #269 remained open
  and immediately reported `mergeable=true/state=clean` afterward.
- 2026-07-13 — The pre-remediation workflow did not persist evaluator decisions or
  reasons, so `state=unstable` during run `29270554173` is a bounded inference from the
  skipped executor plus post-run clean evidence, not direct telemetry. Confidence is
  medium: it is the only remaining non-attended gate consistent with the observed path,
  but the ephemeral input is unavailable. The fixture records that provenance rather
  than overstating certainty.
- 2026-07-13 — Extending the non-authorizing provisional class to `unstable` does not
  broaden merge authority. Any other failed gate still dominates, and the executor still
  recollects everything and requires a fresh `mergeable=true/state=clean` `allow` before
  calling the exact-head merge endpoint.
