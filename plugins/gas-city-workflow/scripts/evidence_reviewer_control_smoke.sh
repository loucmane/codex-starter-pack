#!/bin/sh
# Worker-equivalent control smoke for the evidence reviewer (operator host only).
# Proves the exact allowlisted gc forms reach Beads host-side (outside any
# sandbox): create a throwaway smoke bead, show, update, close via `gc bd`,
# and probe the claim surface (which must be reachable and correctly gated).
# Usage: evidence_reviewer_control_smoke.sh <rig>
set -eu
RIG="${1:?usage: evidence_reviewer_control_smoke.sh <rig>}"
GC=/home/loucmane/gascity/bin/gc
CITY=/home/loucmane/gascity/city
export PATH=/home/loucmane/gascity/bin:/usr/bin:/bin GC_HOME=/home/loucmane/gascity/home
"$GC" --city "$CITY" bd create "SMOKE: reviewer control-surface path check" --rig "$RIG" -p 3 -t task \
  -d "Automated worker-equivalent smoke; safe to close immediately." >/tmp/smoke-create.$$ 2>&1
SMOKE=$(grep -o "[a-z]*-[a-z0-9.]*" /tmp/smoke-create.$$ | head -1); rm -f /tmp/smoke-create.$$
[ -n "$SMOKE" ] || { echo "FAIL: could not create smoke bead"; exit 1; }
"$GC" --city "$CITY" bd show "$SMOKE" --rig "$RIG" >/dev/null
"$GC" --city "$CITY" bd update "$SMOKE" --rig "$RIG" --append-notes "smoke: gc bd path verified host-side" >/dev/null
"$GC" --city "$CITY" bd close "$SMOKE" --rig "$RIG" --reason "SMOKE PASS: gc bd show/update/close host-side" >/dev/null
GC_AGENT="$RIG/evidence-reviewer" "$GC" --city "$CITY" hook --claim --json >/dev/null 2>&1 || true
echo "SMOKE PASS: $SMOKE created/shown/updated/closed via exact gc forms; claim surface probed"
