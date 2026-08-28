#!/usr/bin/env bash
# Compatibility entrypoint. Canonical policy lives in aegis_foundation.gate.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SOURCE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
ROOT=""
ARGS=("$@")
for ((index = 0; index < ${#ARGS[@]}; index++)); do
  if [ "${ARGS[$index]}" = "--root" ] && [ $((index + 1)) -lt ${#ARGS[@]} ]; then
    ROOT="${ARGS[$((index + 1))]}"
    break
  fi
done
if [ -z "$ROOT" ]; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi
ROOT="$(cd "$ROOT" && pwd -P)"

if [ -x "$ROOT/.aegis/bin/aegis" ]; then
  exec "$ROOT/.aegis/bin/aegis" gate readiness --adapter claude "${ARGS[@]}"
fi

if [ -f "$SOURCE_ROOT/aegis_foundation/gate/readiness.py" ]; then
  export PYTHONPATH="$SOURCE_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  exec python3 -B -m aegis_foundation.gate.readiness --adapter claude "${ARGS[@]}"
fi

if python3 -c 'import aegis_foundation.gate.readiness' >/dev/null 2>&1; then
  exec python3 -B -m aegis_foundation.gate.readiness --adapter claude "${ARGS[@]}"
fi

echo "BLOCKED | canonical Aegis readiness runtime is missing"
exit 2
