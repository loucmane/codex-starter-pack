#!/usr/bin/env python3
"""Run codex-guard validate with plan sync and capture continuation log."""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PLAN_SYNC = [sys.executable, str(ROOT / 'scripts' / 'codex-task'), 'plan', 'sync']
GUARD_CMD = [sys.executable, str(ROOT / 'scripts' / 'codex-guard'), 'validate', '--include-untracked']
LOG_DIR = ROOT / 'reports' / 'session-continuation'
LOG_DIR.mkdir(parents=True, exist_ok=True)

print('Running plan sync...')
result = subprocess.run(PLAN_SYNC, cwd=ROOT)
if result.returncode != 0:
    sys.exit(result.returncode)

print('Running guard validate...')
result = subprocess.run(GUARD_CMD, cwd=ROOT, capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)

log_name = f"guard-{datetime.now().strftime('%Y%m%d-%H%M%S')}-check.txt"
(LOG_DIR / log_name).write_text(result.stdout)

sys.exit(result.returncode)
