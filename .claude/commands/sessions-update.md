---
description: Append a S:W:H:E entry to the active session.
allowed-tools: Bash
argument-hint: --work <W> --handler <H> --evidence <E> --note <text>
---

Run:

```bash
python3 scripts/codex-task sessions update $ARGUMENTS
```

Verify the evidence path exists before running. Pair meaningful session entries with `/work-tracking-update`.
