#!/usr/bin/env bash
# Claude path guard for protected Aegis/Codex-owned surfaces.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/gate_lib.py" path
