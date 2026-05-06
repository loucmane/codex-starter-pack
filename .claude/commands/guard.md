---
description: Run the S:W:H:E guard.
allowed-tools: Bash
argument-hint: [--include-untracked]
---

Run:

```bash
python3 scripts/codex-guard validate ${ARGUMENTS:---include-untracked}
```

If it fails, report the exact file paths and missing fields. Do not auto-fix without an explicit instruction.
