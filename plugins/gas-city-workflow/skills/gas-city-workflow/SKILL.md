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
6. For new source work, run `python3 <PLUGIN_ROOT>/scripts/workflow.py begin --root <canonical-root> --bead <id> --goal <outcome>`. For interrupted work, run `workflow.py resume --root <worktree>`; use `recover` only after the prior failure is understood. These commands derive the branch/worktree, create or verify the Aegis scaffold, claim the bead, and run readiness transactionally. Do not repeat their individual mutations by hand.
7. During implementation use `checkpoint`; before handoff use `verify`; after an exact signed clean commit use `publish`; and after accepted publication use `finish`. Stop on BLOCKED or `CLOSEOUT_PENDING`; reconcile through the supported project workflow rather than editing state or journal files.
8. Make source changes only in the derived `codex/<bead>-<slug>` branch/worktree, preserve unrelated changes, and record focused tests and evidence.
9. Codex is the executor by default. Fable is read-only unless the operator explicitly changes that role; Fable may inspect and return PASS/HOLD but does not grant authority.
10. Before handoff, re-read the bead, Git state, workflow journal, readiness, plan/session/tracker parity, and any live state actually changed.

For onboarding and boundary details, read `<PLUGIN_ROOT>/references/workflow-contract.md`.
