#!/usr/bin/env bash
# Claude Stop hook. Non-blocking reminder for dirty workflow state.

set -u

cat >/dev/null

REPO_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cd "$REPO_ROOT" 2>/dev/null || exit 0

if [ -f ".claude/.no-handoff-nudge" ]; then
    exit 0
fi

STATUS="$(git status --porcelain 2>/dev/null || true)"
if [ -z "$STATUS" ]; then
    exit 0
fi

DIRTY_WORKFLOW="$(printf '%s\n' "$STATUS" | sed -E 's/^...//' | grep -E '^(sessions/|plans/|docs/ai/work-tracking/|\.taskmaster/)' || true)"
DIRTY_OUTSIDE_CLAUDE="$(printf '%s\n' "$STATUS" | sed -E 's/^...//' | grep -Ev '^(\.claude/|$)' || true)"
ACTIVE_COUNT=0
if [ -d "docs/ai/work-tracking/active" ]; then
    ACTIVE_COUNT="$(find docs/ai/work-tracking/active -maxdepth 1 -type d -name '*-ACTIVE' | wc -l | tr -d ' ')"
fi

if [ -n "$DIRTY_WORKFLOW" ]; then
    COUNT="$(printf '%s\n' "$DIRTY_WORKFLOW" | grep -c . || true)"
    printf '[handoff-nudge] %s dirty workflow-state file(s). Run /plan-sync and /guard before handoff or compaction.\n' "$COUNT" >&2
    exit 0
fi

if [ -n "$DIRTY_OUTSIDE_CLAUDE" ] && [ "${ACTIVE_COUNT:-0}" -eq 0 ]; then
    COUNT="$(printf '%s\n' "$DIRTY_OUTSIDE_CLAUDE" | grep -c . || true)"
    printf '[handoff-nudge] %s dirty non-.claude file(s) but no ACTIVE work-tracking folder. Run /kickoff or stop before mutating project state.\n' "$COUNT" >&2
    exit 0
fi

exit 0
