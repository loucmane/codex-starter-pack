# Findings

- 2026-06-03 — CI previously validated only GitHub Actions context proof while the full Taskmaster sacrificial cascade ran locally. Task 152 closes that environment gap by provisioning the pinned Taskmaster CLI in CI before pytest.
- 2026-06-03 — Under `task-master-ai@0.43.1`, `.taskmaster/state.json` is part of the status-cascade delta even when it already exists. The file is created from absence or rewritten from a pre-existing baseline, so Task 152 records it as part of the dynamic blast radius in both branches.
- 2026-06-03 — Toolchain evidence must be comparable, not just descriptive. A future apply path must treat Taskmaster version/source, provisioning-lock, Node/Python, or runner identity mismatch as stale cascade evidence that requires re-validation.
