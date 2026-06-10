#!/usr/bin/env bash
# Aegis Session Zero Capsule injection (capsule PR-2b). Synchronous: stdout enters
# model context. Must never fail a session start.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/gate_lib.py" sessionstart || true
exit 0
