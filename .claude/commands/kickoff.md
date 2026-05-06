---
description: Start a Taskmaster-backed Claude/Codex workflow session.
allowed-tools: Bash
argument-hint: --task <id> --slug <slug> --title <title> --goal <text>...
---

Run:

```bash
python3 scripts/codex-task wizard kickoff $ARGUMENTS
```

After it succeeds, run `/readiness` and report the session, plan, and ACTIVE work-tracking folder paths. Do not use `--force` unless the user explicitly authorizes it.
