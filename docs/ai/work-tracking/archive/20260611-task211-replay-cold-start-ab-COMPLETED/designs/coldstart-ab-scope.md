# TM #211 scope — replay-cold-start A/B falsifier

Authentic, cost-measuring capsule falsifier. Supersedes the synthetic cohort (a 30-agent
workflow proved it is cost-blind: can fire a trustworthy KILL but never authorize a KEEP)
and the arbitrary 2026-06-24 date gate.

## Design
Replay REAL historical cold-start points (committed SHA + the work that was next).
Per point, two git worktrees at the SHA: capsule-on (real SessionStart injection) vs
AEGIS_CAPSULE=off control. Fresh `claude -p "continue, orient, take next step"` k times
per arm, identical allowed-tools. Measure tool-calls-to-first-meaningful-action (first
mutation outside .aegis/, sessions/, plans/, docs/ai/work-tracking/, ~/.claude — spec
section 7 metric) from each transcript, plus correctness vs what actually happened next.

Controls fixing the synthetic pilot's flaws: open-ended task (no capsule-shaping);
baseline forages the REAL tree (no strawman); cost measured from transcript (the
KEEP-authorizing dimension); a fresh-null scenario the capsule must NOT win (else the
battery is capsule-shaped and the run is void); the replay agent is a fresh claude -p
process that does not know it is in an experiment (genuine blind).

## Split
- Testable core (CI): transcript parser, meaningful-action detection, worktree
  reconstruction, paired-delta CI, decide() thresholds, fresh-null guard, report.
- Operator-only (AEGIS_RUN_COLDSTART_AB=1): run_live_ab fires real claude -p sessions.

## Pre-registered verdict (decide())
KEEP-ELIGIBLE iff decision recon delta >= 1.0 AND CI lower bound > 0 AND fresh-null
passes (|delta| <= 0.5). CI entirely <= 0 => KILL. Otherwise INCONCLUSIVE. A KEEP here
authorizes PR-3/PR-4; the owner's interleaved real-use A/B remains gold-standard.

## Next (operator)
Seed scenarios from today's kickoff SHAs + HP-Coach incidents; run run_live_ab with k>=3.
