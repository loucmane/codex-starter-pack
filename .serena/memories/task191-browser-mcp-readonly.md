# Task 191 (rescoped) — browser-observation MCP read-only (2026-06-14)

Rescoped residual of the original TM 191 after TM 216/#224 shipped the shell/git/taskmaster/
aegis read-only classification. Browser-observation MCP tools (chrome-devtools/playwright)
were classified as mutations (they hit the "unknown MCP -> conservative mutation" fallback in
mcp_is_mutation), so they ARMED pending-tracking — the churn source behind HP-Coach's
playwright backlog that TM 221 had to clean at drain.

## Fix (.claude/scripts/gate_lib.py + assets mirror)
mcp_is_mutation: added a browser-namespace branch BEFORE MCP_MUTATION_TOOL_RE —
`if "__chrome_devtools__" in normalized or "__playwright__" in normalized: return bool(mcp_path_values(payload.tool_input))`.
So a browser tool is read-only w.r.t. the repo UNLESS it writes a repo path (mcp_path_values
non-empty, e.g. take_screenshot --filePath/--path). Observation (snapshot, click, navigate,
console, evaluate, file_upload which only reads) → read-only; screenshot/save to a repo path →
mutation (tracked). payload_is_read_only derives from mcp_is_mutation so both agree.

This is the UPSTREAM complement to TM 221: 191 stops browser tools entering the queue; 221
discards any that do at drain. Non-browser MCP classification unchanged (apply-gated aegis,
taskmaster, unknown all as before).

Tests: tests/claude_adapter/test_browser_mcp_readonly.py (15). Mirror byte-identical.

See [[task221-drain-readonly-fix]], [[task216-closeout-convergence]]. Remaining backlog:
TM 220 (path-lost populate), TM 189 (continuation-brief residual), TM 223 (Codex-led
codex-guard/codex-task assets sync).
