#!/usr/bin/env bash
# Aegis passive ledger recorder (capsule PR-1b). Async hook: must never block or fail.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/gate_lib.py" record || true
exit 0
