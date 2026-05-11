---
id: guide-index
type: user-guide
status: stable
audience: all-users
skill-level: all
title: Codex Foundation Guide Hub
description: Current guide hub for the portable Codex foundation, template system, and agent runtime workflows
---

# Codex Foundation Guide Hub

Use this page as the starting point for learning the current repository workflow. The current system is not only a Claude prompt collection; it is a portable Codex foundation with Taskmaster tasks, session logs, plans, work-tracking folders, guard validation, template metadata, and a Claude runtime adapter.

## Start Here

- [Foundation onboarding training](training/foundation-onboarding.md) - Hands-on training path for the current workflow.
- [Getting started with the Codex foundation](quickstart/getting-started.md) - Beginner path for task startup, continuation, work tracking, evidence, and Git defaults.
- [Portable foundation adoption guide](../engine/validation/foundation-adoption-guide.md) - How to apply the foundation to new and existing repositories.
- [Portable foundation specification](../engine/core/portable-foundation-spec.md) - Contract for portable sessions, plans, work tracking, and enforcement.

## Daily Workflow References

- [Common workflows](workflows/common.md) - Example-driven workflow patterns.
- [Trigger phrases](reference/triggers.md) - Request phrasing and workflow triggers.
- [Troubleshooting issues](troubleshooting/issues.md) - Common user-facing problems and recovery patterns.
- [Understanding ULTRATHINK](ultrathink/understanding.md) - Reasoning protocol background.
- [Token optimization](token-optimization.md) - Context and token-use guidance.
- [Foundation communication templates](communication/foundation-communication-templates.md) - Copy-ready repo-native communication payloads for PRs, task completion, incidents, milestones, and follow-up capture.

## System References

- [Taskmaster alignment workflow](../workflows/taskmaster/alignment.md) - Taskmaster, session, plan, and work-tracking alignment.
- [Work-tracking enforcement](../workflows/taskmaster/work-tracking-enforcement.md) - Active folder, tracker, archive, and guard rules.
- [Session lifecycle](../workflows/session/lifecycle.md) - Session start, continuation, closeout, and archival rules.
- [Claude runtime contract](../../.claude/engine/runtime-contract.md) - Claude-side readiness and PreToolUse gate contract.

## Learning Paths

### New Maintainer

1. Read [Foundation onboarding training](training/foundation-onboarding.md).
2. Read the [portable foundation adoption guide](../engine/validation/foundation-adoption-guide.md).
3. Walk through the hands-on exercises in a real Taskmaster task.
4. Confirm you can explain the evidence and archive closeout flow.

### Agent Runtime Reviewer

1. Read the [Claude runtime contract](../../.claude/engine/runtime-contract.md).
2. Review [Taskmaster alignment](../workflows/taskmaster/alignment.md).
3. Review [work-tracking enforcement](../workflows/taskmaster/work-tracking-enforcement.md).
4. Confirm mutation gates are backed by tests before trusting any new adapter behavior.

### Template Maintainer

1. Read the [portable foundation specification](../engine/core/portable-foundation-spec.md).
2. Review the [foundation adoption guide](../engine/validation/foundation-adoption-guide.md).
3. Use [foundation onboarding training](training/foundation-onboarding.md) as the operational checklist for task work.

## Progress Log

- **2026-04-21 17:59** — [S:20260421|W:task91-standardize-template-metadata|H:templates/guides/index.md|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Added canonical `status` metadata during the Task 91 guide-standardization slice
- **2026-05-08 16:49** — [S:20260508|W:task33-training-materials|H:templates/guides/index.md|E:docs/ai/work-tracking/active/20260508-task33-training-materials-ACTIVE/designs/training-materials-scope-reconciliation.md] Replaced stale guide hub links with current foundation, runtime, session, and work-tracking references
- **2026-05-08 17:25** — [S:20260508|W:task49-communication-templates|H:templates/guides/index.md|E:docs/ai/work-tracking/active/20260508-task49-communication-templates-ACTIVE/designs/communication-templates-scope-reconciliation.md] Added the foundation communication templates guide to the daily workflow references
- **2026-05-11 16:02** — [S:20260511|W:task32-documentation-suite|H:templates/guides/index.md|E:docs/ai/work-tracking/active/20260511-task32-documentation-suite-ACTIVE/designs/documentation-suite-scope-reconciliation.md] Updated the guide hub quickstart label to point at the current Codex foundation workflow rather than an older Claude-only guide.
