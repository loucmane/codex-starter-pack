# Findings

- 2026-06-04 — The pre-Task-160 shadow authority check was weaker than the authoritative Taskmaster state model: invalid statuses, duplicate IDs, and empty task lists could bypass the local parser or raise later. Delegation closes that seam.
- 2026-06-04 — The Task 158 state.json fix solved false refusal by making state-file membership optional, but without content validation it could also accept meaningful state mutations. Task 160 adds a semantic contract for that optional file.
- 2026-06-04 — `build_shadow_accumulation_report()` needed its own invalid-context guard. Relying only on upstream CI gating left future non-CI consumers with a way to carry action-shaped evidence from invalid shadow contexts.
