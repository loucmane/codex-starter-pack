# Task 160 Design Notes

## Scope
- Harden post-merge shadow accumulation evidence before any consumer or enablement work.
- Keep the apply line closed: no apply, no enable, no Taskmaster status mutation, no in-repo shadow ledger.

## Safety Model
- Taskmaster authority is delegated to the authoritative `_taskmaster_state` validator.
- Shadow accumulation must not record `would_apply` evidence unless the context is valid for post-merge shadow.
- Optional `.taskmaster/state.json` membership is not enough. If the file changes, the content must fit the managed bookkeeping contract.
- CI accumulation artifacts live outside the governed repo and the real accumulation step is wrapped by the whole-tree oracle.

## Verification Focus
- Invalid Taskmaster authority fixtures: malformed JSON, invalid status, duplicate ID, and empty task list.
- State-file semantic negatives: active tag drift and branch mapping rewrite.
- False shadow contexts: refused-only report, no sacrificial validation, no `would_apply`.
- CI workflow contract: job-level read-only permissions, runner-temp artifact path, zero repo deltas.
