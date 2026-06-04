# Task ID: 160

**Title:** Harden shadow accumulation evidence validation

**Status:** done

**Dependencies:** 158 ✓, 159 ✓

**Priority:** high

**Description:** Close the post-Task-158 measurement-layer gaps before any shadow evidence consumer or enablement work is added.

**Details:**

Scope: delegate shadow-layer Taskmaster authority checks to the authoritative Taskmaster state validator instead of a weaker local JSON-only check; malformed JSON, schema-invalid statuses, duplicate IDs, and empty task lists must produce clean refusal with no would_apply evidence and no uncaught exception. Add a state.json content contract for shadow cascade validation: state.json remains optional as a path delta, but if it changes, only approved Taskmaster bookkeeping changes are accepted; meaningful mutations such as currentTag, branchTagMapping, or unexpected authority-affecting keys must refuse with state_json_unexpected_mutation. Add defense-in-depth so build_shadow_accumulation_report forces would_apply=[] when valid_for_shadow=false, is covered by no-consumer/no-agent-reachable tests, and workflow permission/report-output policy is explicit. Non-goals: no apply, no enable, no Taskmaster status mutation, no in-repo shadow ledger, no broadening beyond merged_but_not_done/git_ancestor evidence. Tests: add malformed/invalid Taskmaster fixtures, state.json meaningful-mutation negative tests, false-context accumulation tests, and keep all Task 144-158 safety tests green.

**Test Strategy:**

No test strategy provided.
