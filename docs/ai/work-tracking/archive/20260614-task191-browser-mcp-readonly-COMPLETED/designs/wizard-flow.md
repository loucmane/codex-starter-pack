# Task 191 (rescoped) — browser-observation MCP read-only: design scope

Date: 2026-06-14. Rescoped residual after TM 216/#224 shipped the shell/git/taskmaster/aegis
read-only classification. Browser-observation MCP tools (chrome-devtools/playwright) were
classified as mutations (unknown MCP -> conservative), so they armed pending-tracking — the
churn source behind HP-Coach's playwright backlog (and what TM 221 had to clean at drain).

## Decision
In mcp_is_mutation, add a browser-namespace branch (before MCP_MUTATION_TOOL_RE): a
chrome-devtools/playwright tool is read-only w.r.t. the repo UNLESS it writes a repo path
(mcp_path_values non-empty, e.g. take_screenshot --filePath). So observation (snapshot, click,
navigate, console, evaluate, file_upload-which-reads) stops arming the queue, while a
screenshot/save to a repo path still tracks. payload_is_read_only derives from mcp_is_mutation,
so both agree. Complements TM 221 (which discards such events at drain) by preventing them
entering the queue at the source.

## Invariant
A browser call that writes a repo path stays a mutation (tracked). Conservative: ANY repo
path field present => treat as mutation. Non-browser MCP classification unchanged
(apply-gated aegis, taskmaster, unknown all as before).

## Boundary
.claude/scripts/gate_lib.py + assets mirror (byte-identical) + tests. No installer changes.
