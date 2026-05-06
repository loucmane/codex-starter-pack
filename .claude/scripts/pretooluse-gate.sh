#!/usr/bin/env bash
# Claude PreToolUse dispatcher.
# Calls readiness before hookable persistent mutations and then dispatches
# protected-path / Bash write-surface checks.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/gate_lib.py" pretooluse
