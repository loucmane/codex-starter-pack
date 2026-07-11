# Task 236 Define Aegis usability convergence roadmap – Implementation Notes

## Planned Workstreams
- Task 237 - truthful, compact, mode-aware managed agent guidance.
- Task 238 - shared bounded-output contract for every agent-facing Aegis command.
- Task 239 - diagnostic worktree/subagent capture matrix and replay-safe fixture.
- Task 240 - evidence-selected worktree and parent/child attribution correction.
- Task 241 - quiet deterministic witness as the canonical pre-delivery interface.
- Task 242 - behavior-preserving extraction of the installer managed-update slice.
- Task 243 - refreshed PR-4 parity evidence and row-by-row go/no-go decisions.
- Task 244 - fail-closed completed-tracker derivation for the self-hosted upstream source checkout.

## Dependency Shape
- Tasks 237, 238, and 239 depend on this planning task.
- Task 240 depends on the Task 239 audit.
- Task 241 depends on Tasks 238 and 240.
- Task 242 depends on Tasks 235, 237, 238, and 240.
- Task 243 depends on Tasks 237-242 and Task 244.
- Task 210 now depends on Task 243 and cannot begin retirement before convergence evidence.

## Scope Boundary
- Task 236 changes planning, evidence, and Taskmaster metadata only.
- No gate, ledger, capsule, witness, installer, managed asset, or retirement runtime behavior is
  implemented here.
