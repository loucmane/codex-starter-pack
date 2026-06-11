# Task ID: 211

**Title:** Capsule falsifier: replay-cold-start A/B harness

**Status:** in-progress

**Dependencies:** 195 ✓

**Priority:** high

**Description:** Authentic, cost-measuring falsifier for the Session Zero Capsule (supersedes the synthetic cohort, which a 30-agent workflow proved can only fire a KILL, never authorize a KEEP). Replay REAL historical cold-start points (committed SHA + the task that was next, sourced from this repo's kickoff history and HP-Coach incidents): for each point, two git worktrees at the SHA — capsule-on (real SessionStart injection) vs AEGIS_CAPSULE=off control — run a fresh headless 'claude -p "continue, orient, take the next concrete step"' k times per arm with identical allowed-tools. Mechanically extract from each transcript: tool-calls-to-first-meaningful-action (first mutation outside .aegis/ and ~/.claude, the spec section 7 metric) and correctness vs what actually happened next. Include a fresh-null scenario (clean state, capsule must give ~0 edge or the harness is capsule-shaped and void); blind the scorer to arm; pre-register keep/kill thresholds. Reuses the #195 replay philosophy extended from gate-decisions to cold-start trajectories. A KEEP here authorizes building PR-3/PR-4; the owner's interleaved real-use A/B remains gold-standard confirmation.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
