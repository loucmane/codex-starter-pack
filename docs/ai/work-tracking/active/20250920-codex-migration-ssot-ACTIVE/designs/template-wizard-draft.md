# Interactive Template Wizard (Draft)

## Objective
Guide developers through template execution interactively, enforcing plan compliance and guard checks in real time.

## Features
- Command: `codex-template wizard --template <name>`
- Auto-fills S:W:H:E when context available.
- Validates each step (plan, timestamps, evidence) before continuing.
- Logs progress to plan/tracker automatically.

## Tasks
- Design wizard flow per template type.
- Build CLI interface (prompt + validation).
- Integrate with behaviors/guards (`codex-guard`).
- Provide undo/retry mechanics.
- Capture analytics for metrics dashboard.

## Open Questions
- How to support multi-template workflows.
- Accessibility of wizard (CLI vs. TUI).
- Fallback when plan tool unavailable.
