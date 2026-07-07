# Task 230 - Computed capsule active-task orientation fields

Date: 2026-07-07
Branch: feat/task-230-computed-capsule-orientation

Scope: add deterministic computed-capsule orientation fields only. The task extends `.claude/scripts/brief_lib.py` and the managed asset copy to expose `task_truth.active_task`, `task_truth.active_subtask`, `task_truth.next_action`, and `task_truth.orientation_source`, then renders them in capsule markdown/injection.

Important boundary: do not implement PR-3 narration, Stop checkpoints, SessionEnd distill, lazy LLM narration, or PR-4 surface retirement. This is the deterministic gap found by the PR-3 narration gate decision.

Current implementation state: helper parsing was added for branch task IDs, current-work fallback, Taskmaster in-progress fallback, active subtasks, pending subtasks, and deterministic next action strings. Focused tests were added in `tests/claude_adapter/test_brief_lib.py`; the live and asset brief_lib copies were synced.

Validation so far: `python3 -m pytest tests/claude_adapter/test_brief_lib.py tests/claude_adapter/test_capsule_injection.py` passed with 31 tests.