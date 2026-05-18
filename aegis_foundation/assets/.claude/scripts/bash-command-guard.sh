#!/usr/bin/env bash
# Claude Bash command guard for protected-path write bypasses.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/gate_lib.py" bash
