# Task ID: 182

**Title:** Allow fallback observation artifact root for legacy observation state

**Status:** done

**Dependencies:** 181 ✓

**Priority:** high

**Description:** Observation stop should treat the computed fallback artifact root as Aegis-owned even when an observation was started before artifact_root metadata existed, so collect-artifacts can close legacy active observations after moving known artifacts.

**Details:**

Update observation allowed-prefix computation to include the same fallback artifact root used by stop_observation. This keeps observations started before the observation_artifacts path existed from blocking on files that Aegis just collected into .aegis/reports/observations/<observation-id>/artifacts. Add a regression using legacy current-work metadata without paths.observation_artifacts or observation.artifact_root.

**Test Strategy:**

No test strategy provided.
