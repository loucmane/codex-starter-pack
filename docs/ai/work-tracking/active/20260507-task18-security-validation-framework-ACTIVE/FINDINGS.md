# Findings

- 2026-05-07 — Task 18 historical wording is broader than the current proven gap. Existing guard/scanner foundation already provides workflow validation, metadata-wrapped reports, scanner config, validation findings, and allowlist/blocklist pattern matching.
- 2026-05-07 — `task-master show 97` reports Task 97 as done and `python3 scripts/codex-task taskmaster health` reports zero invalid dependency refs, so the unchecked `97` marker in `.taskmaster/tasks/task_018.txt` is generated-file display drift rather than a dependency blocker.
- 2026-05-07 — Initial full-project security validation was too noisy because normal in-repo relative links were reported as path traversal candidates. The implementation now only reports traversal tokens that escape the project root or cannot be resolved safely, which reduced the baseline report from 203 findings to 1 finding.
- 2026-05-07 — Environment-variable references such as `process.env.API_KEY` are not inline secret material. The detector now treats environment references and obvious placeholders as safe while retaining literal-token detection.
