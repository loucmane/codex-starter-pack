---
description: Run Claude readiness and stop on BLOCKED.
allowed-tools: Bash
---

Run:

```bash
if [ -x ./.aegis/bin/aegis ]; then
  ./.aegis/bin/aegis gate readiness --adapter claude --target-dir .
else
  python3 -m aegis_foundation.cli gate readiness --adapter claude --target-dir .
fi
```

If the state is `BLOCKED`, do not mutate files, memory, Git, Taskmaster, GitHub, or MCP state. Summarize the blocked checks and the required repair path.
