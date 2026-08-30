---
name: gas-city-workflow
description: Orient and execute repository work in Gas City, HPFetcher, Blog, or a descriptor-onboarded future project using Beads as authority, Aegis as evidence, exact rig scoping, and existing permission boundaries. Use for project cold starts, continuing work, choosing or inspecting beads, planning implementation, coordinating Codex with read-only Fable review, or onboarding a new Gas City-managed project. Do not use for unrelated repositories or to grant permissions, resume rigs, deploy, mutate keys, or bypass operator gates.
---

# Gas City Workflow

Start from live state, never memory.

1. Run `python3 <PLUGIN_ROOT>/scripts/project_context.py --root <project-root>` and stop if it blocks.
2. Read the project’s `AGENTS.md` and `CLAUDE.md`; the project-local instructions override generic examples.
3. Treat the capsule’s `workflow.authority`, exact `project.rig`, and `workspace` policy as binding. The canonical checkout is `workspace.canonical_root`; create linked worktrees only as direct children of `workspace.worktree_root`. Never choose a worktree location from memory or filesystem writability.
4. Use the capsule’s literal `gc --city ... --rig ... bd` command shape for Beads reads.
5. Inspect `bd ready` and then the selected bead. Creating, updating, or closing a bead is ledger work; it does not authorize route, resume, worker dispatch, push, merge, install, restart, signing, or deployment.
6. Run the project’s reported readiness entrypoint when present. Stop on BLOCKED or `CLOSEOUT_PENDING`; reconcile through the supported project workflow rather than editing state files.
7. Make source changes in an isolated `codex/<bead>-<slug>` branch/worktree under the reported worktree root, preserve unrelated changes, and record focused tests and evidence.
8. Codex is the executor by default. Fable is read-only unless the operator explicitly changes that role; Fable may inspect and return PASS/HOLD but does not grant authority.
9. Before handoff, re-read the bead, Git state, readiness, plan/session/tracker parity, and any live state actually changed.

For onboarding and boundary details, read `<PLUGIN_ROOT>/references/workflow-contract.md`.
