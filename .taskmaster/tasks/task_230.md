# Task ID: 230

**Title:** Computed capsule active-task orientation fields

**Status:** pending

**Dependencies:** None

**Priority:** medium

**Description:** Add deterministic computed-capsule fields for active Taskmaster task/subtask and next safe action, based on PR-3 narration gate evidence from 2026-07-06.

**Details:**

Extend the computed capsule, not PR-3 narration. The gate evidence showed stale current.json is correctly reported by brief --status, and a fresh computed capsule corrects branch/commit/task counts, but it does not name the active Taskmaster task, active subtask, or next safe action. Extend .claude/scripts/brief_lib.py and the asset copy so task_truth/rendered injection include active task id/title/status, active subtask when present, and a concise deterministic next_action sourced from Taskmaster/current branch/current workflow state. Do not add Stop checkpoints, SessionEnd distill, lazy narration, or LLM narration code in this task.

**Test Strategy:**

No test strategy provided.
