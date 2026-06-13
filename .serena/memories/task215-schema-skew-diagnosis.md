# Task 215 — Verify schema-skew self-diagnosis (2026-06-13)

HP-Coach reported `aegis verify --strict` rejecting the manifest `runtime` field.
DIAGNOSIS CORRECTED: current codex source validates HP-Coach's real manifest clean;
the rejection came from a STALE MCP/CLI bundle resolving its own old packaged schemas
as source root. No schema content change needed.

Fix: `_manifest_schema_failure_message` in scripts/_aegis_installer.py, wired at both
manifest_schema gate fail sites (status() id=manifest_schema, verify()
gate_id=aegis.manifest_schema). Behavior: always append "[validated with schemas from
<source_root>]"; when the target's installed mirror differs from the validator's copy
AND accepts the manifest → explicit "validator runtime is STALE — update/re-register
the Aegis runtime (aegis runtime update / repoint MCP)" message. Mirror missing,
identical, or also-rejecting → plain failure (no false skew claims).

Tests: tests/meta_workflow_guard/test_manifest_schema_skew.py (5).

Companion backlog item: TM 216 (closeout evidence/pending-tracking loop) — the bigger
design rework from the same HP-Coach report; accepted as written (generate-don't-assert
surfaces, self-writes don't re-arm, read-only Bash doesn't enqueue, stable evidence
keys, one-shot convergent closeout).
