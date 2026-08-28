# Bead ga-iqbd Modularize Aegis workflow gate and retire Claude readiness monolith – Implementation Notes

## Implemented Workstreams

- Added the adapter-neutral readiness engine in `aegis_foundation/gate/{models,state,workflow,render,readiness}.py` and exposed it as `aegis gate readiness`.
- Split hook policy into focused modules under `aegis_foundation/gate/hooks/` for contracts, payloads, decisions, runtime state, hard policy, shell policy, evidence, tracking, lifecycle, and entrypoints.
- Replaced `readiness.sh` and `gate_lib.py` with thin compatibility launchers that load the canonical runtime and fail closed for mutation-capable phases.
- Switched installer closeout and hook readiness calls to the canonical Python evaluator instead of shelling through Claude's compatibility script.
- Kept live and packaged launchers byte-identical and updated current Claude guidance to use `aegis gate readiness`.
- Added architecture, parity, package, and release-artifact coverage, including enforceable module-size budgets.
- Added the manifest-managed `.aegis/runtime/python` gate snapshot and local-first dispatcher resolution, preserving hook/readiness operation when `runtime.env` points to an unavailable source checkout.
- Documented ownership, upgrades, rollback, and cross-adapter behavior in `docs/aegis/modular-workflow-gate.md`.
