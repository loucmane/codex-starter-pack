# Task ID: 162

**Title:** Build replayable precision corpus for shadow apply

**Status:** done

**Dependencies:** 161 ✓

**Priority:** high

**Description:** Construct the precision-evidence path for shadow apply using replayable real-git synthetic fixtures, reviewed labels, toolchain-bound expected outcomes, and pre-registered precision bars. Evidence-only and default-off.

**Details:**

Scope: create a replayable labeled precision corpus for the narrowed shadow-apply candidate path. Materialize cases as real synthetic git histories, not mocked merge booleans. Cover merge topology including fast-forward or ancestor-style, true merge, squash, and deleted-branch or unknown cases; cover state.json branches absent, legacy tag, and steady state; cover proof source git_ancestor and excluded github_pr_merged as a negative. Store reviewed ground-truth labels as fixtures with expected would_apply, refusal reason, or manual/unknown result, including auto/manual boundary cases. Replay the real shadow pipeline over the corpus and recompute per finding_kind plus proof_source precision metrics: TP, FP, FN, and auto-to-manual boundary leaks. Register the bar before measurement: zero false positives, zero boundary leaks, and at least N true positives for every auto-eligible pair. The precision artifact must be physically distinct from the operational ledger and cascade smoke, and must be toolchain-version-keyed so a task-master-ai or runner/toolchain bump invalidates expected outcomes. Classify all evidence streams: operational accumulation is operational-only when empty, cascade validation is synthetic smoke and precision_observation false, and only the precision corpus can provide precision evidence. Non-goals: no apply, no enable, no MCP apply tool, no agent-reachable mutation, no Taskmaster status mutation against the governed repo.

**Test Strategy:**

No test strategy provided.
