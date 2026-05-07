---
id: create-commit-message
name: Create Commit Message
title: Create Commit Message
role: operator
type: operator
domain: git
stability: draft
status: draft
triggers:
  - "draft commit message"
  - "suggest commit"
  - "prepare gac"
  - "checkpoint"
  - "commit and push"
dependencies:
  - check-commit-msg
  - suggest-commit-type
tools:
  - AnalyzeDiff
  - Write
version: 1.0.0
---
> **Codex Note:** Regular Git/GitHub execution is the default when the user delegates Git work and auth is available. `gac` is a legacy/user convenience alias that Codex emits only when the user explicitly asks for "the gac" or chooses manual fallback after auth expiry.

#### Handler: create-commit-message {#create-commit-message}
**Purpose**: Compose or execute a conventional commit flow that reflects the validated plan scope, tracker updates, and supporting evidence.

**Inputs Required**:
- Current plan/tracker status (plan-step + checklist progress)
- Latest `git status -sb` / diff summary
- Evidence bundle locations (e.g., reports, session logs)

**Process**:
1. **Scope Confirmation**
   - Run `python3 scripts/codex-task plan sync` if not already captured.
   - Re-read tracker/session entries for the changes being committed.
2. **Determine Commit Type & Scope**
   - Use `suggest-commit-type` output (or conventions) to select the type (`feat`, `fix`, `docs`, etc.).
   - Derive an optional scope (e.g., `templates`, `guard`, `docs`).
3. **Summarize Work**
   - Extract key changes from the diff grouped by file area.
   - Map each change back to plan steps, tracker loglines, or evidence artifacts.
4. **Draft Commit Message**
   - Compose `type(scope?): summary` line (<= 72 chars summary).
   - Body: canonical `Summary:` block with `- ` bullets describing the concrete changes; include file references or evidence paths where helpful.
   - Footer (optional): reference Taskmaster task IDs or follow-up TODOs.
5. **Choose Response Mode**
   - `direct-git-execution`: if the user asked Codex to checkpoint, commit, push, create a PR, merge a PR, or otherwise delegated Git/GitHub execution, run regular `git add`, `git commit`, `git push`, and GitHub commands after gates pass.
   - `full-gac-command`: if the user explicitly asked for "the gac", return only the full `gac "..."` command.
   - `message-payload-only`: if the user asked for a commit message or validation only, return only the message payload.
   - `auth-refresh-required`: if regular Git/GitHub execution fails because SSH/GPG auth expired, ask the user to refresh auth and retry the same regular command path.
6. **Self-Check**
   - Ensure message matches conventions (`templates/conventions/git/commit-format.md`).
   - Pass to `check-commit-msg` for validation before handing to the user.

**Success Criteria**:
- Message reflects actual diff and documented evidence.
- Guard accepts format and rejects stale GAC-default guidance.
- Response mode matches the user request (`direct-git-execution`, `full-gac-command`, `message-payload-only`, or `auth-refresh-required`).
- In `direct-git-execution`, Codex completes the delegated Git/GitHub operation instead of handing back an alias command.

**Failure Modes & Recovery**:
- *Missing scope*: revisit tracker/plan to capture work correctly.
- *Summary too long*: rewrite to meet max length.
- *Unsupported type*: revisit `suggest-commit-type` guidance or conventions document.
- *Auth expired*: ask the user to refresh SSH/GPG cache and retry the same regular Git/GitHub command path; do not disable signing, use `--no-verify`, or fall back to GAC by default.

**Examples**:
- `docs(templates): document legacy → modular replacements`  
  ```
  - map legacy workflow anchors to templates/workflows/domain/
  - add inventory coverage for registry/matrix references
  - log plan sync + tracker updates for task 87 scope completion
  ```
- `feat(guard): enforce timestamp evidence capture`  
  ```
  - extend codex-guard timestamp gate coverage
  - add regression suite under tests/timestamp_guard/
  - update session lifecycle workflow references
  ```

**Related Handlers**:
- `check-commit-msg` – final validation
- `suggest-commit-type` – choose commit type
- `update-tracker` – ensure documentation alignment

**Evidence Expectations**:
- Updated tracker/session entries referencing this commit
- Guard/test logs stored under `reports/`
- Plan step marked completed where applicable

## Progress Log

- **2026-04-21 17:31** — [S:20260421|W:task91-standardize-template-metadata|H:templates/handlers/operators/git/create-commit-message.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `title`, `type`, and `status` metadata during the Task 91 handler-standardization slice
- **2026-05-07 13:55** — [S:20260507|W:task107-direct-git-execution-mode|H:templates/handlers/operators/git/create-commit-message.md|E:docs/ai/work-tracking/active/20260507-task107-direct-git-execution-mode-ACTIVE/TRACKER.md] Updated commit handler response modes so direct Git/GitHub execution is the default and GAC output is explicit-request only
