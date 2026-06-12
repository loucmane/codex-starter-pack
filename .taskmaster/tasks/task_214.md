# Task ID: 214

**Title:** Gate resilience when home directory is unresolvable

**Status:** in-progress

**Dependencies:** None

**Priority:** medium

**Description:** Production bug from HP-Coach dogfood: PreToolUse gate failed closed with 'RuntimeError: Could not determine home directory' when hooks ran in a sandboxed env (no HOME, no passwd entry). Fix: ledger_lib.store_dir home fallback chain that raises LedgerError never RuntimeError; harden unwrapped expanduser sites in gate_lib; degraded fallback must honor advisory mode (record would_block + allow loudly, never hard-block on infra failure in advisory); capture full traceback in degraded details and events for diagnosability. Regression tests simulate Path.home() raising via sitecustomize PYTHONPATH injection.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
