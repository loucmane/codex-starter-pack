#!/usr/bin/env bash
# Claude ConfigChange guard.
# Prevents project hook configuration from being weakened in the running session.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/gate_lib.py" configchange
