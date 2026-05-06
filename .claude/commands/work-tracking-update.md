---
description: Append a S:W:H:E entry to active work tracking.
allowed-tools: Bash
argument-hint: --document TRACKER --work <W> --handler <H> --evidence <E> --note <text>
---

Run:

```bash
python3 scripts/codex-task work-tracking update $ARGUMENTS
```

Use `--document TRACKER` for normal progress and `--document HANDOFF` for handoff-specific notes.
