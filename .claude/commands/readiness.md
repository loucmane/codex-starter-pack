---
description: Run Claude readiness and stop on BLOCKED.
allowed-tools: Bash
---

Run:

```bash
bash .claude/scripts/readiness.sh
```

If the state is `BLOCKED`, do not mutate files, memory, Git, Taskmaster, GitHub, or MCP state. Summarize the blocked checks and the required repair path.
