# Bead ga-ur1c.4 Enforce Gas City delegation in managed projects – Implementation Notes

## Implemented Workstreams

- Added `aegis_foundation/gate/hooks/delegation.py`, evaluated before ordinary hookability/readiness handling, so managed native-delegation requests fail closed even in advisory mode.
- Added one shared Claude/Codex matcher contract and installed the evaluator/schema through the self-contained Aegis hook runtime.
- Added canonical Git-root, descriptor, runtime-pointer, and generated user-registry resolution with remote identity and descriptor/registry parity checks.
- Added `.gas-city-delegation-exceptions.json` schema and runtime validation: exact project, adapter, normalized tool, payload digest, `codex/*` branch, Bead, canonical reviewed base, and bounded review evidence.
- Rewrote managed Claude orchestrator/executor/checker guidance to make Gas City Beads authoritative and provider-native fallback forbidden.
- Bumped `gas-city-workflow` to `0.7.0` and updated the shared adapter/workflow contract documentation.

## Verification Evidence

- Tests-only RED commit: `4bbeff920e947c2202ffa1d194c366c1196203ba`.
- `tests/claude_adapter`: 711 passed.
- `test_aegis_installer.py`: 158 passed, one opt-in certification smoke skipped by design.
- Codex hook/schema/plugin group: 45 passed.
- Managed-delegation focused suite: 21 passed.
- Real-root read-only proof resolved Gas City Operations, Gas City, HPFetcher, and Blog through the expected descriptor/registry identities without project mutation.
- Source/package installer, contract, and schema bytes are identical; `git diff --check` passes.
- Repository pre-commit passes all configured hooks: secret scan, guard validation, and strict drift check.
