# Task 215 — Schema-skew self-diagnosis: design scope

Date: 2026-06-13. Trigger: HP-Coach closeout report — a stale MCP bundle rejected the
manifest `runtime` field with a bare jsonschema error. Diagnosis correction recorded:
current source validates the same manifest clean (verified against the live HP-Coach
manifest); the validator was the stale party, not the schema content.

## Decision
`_manifest_schema_failure_message` wraps both manifest_schema gate fail sites
(status() and verify()): always name the source root used; when the target's
installed schema mirror differs from the validator's copy AND accepts the manifest,
replace the bare error with an explicit "validator runtime is STALE — update or
re-register the Aegis runtime" message. Mirror-missing, mirror-identical, and
mirror-also-rejects cases stay plain failures (no false skew claims).

## Boundary
scripts/_aegis_installer.py + tests/meta_workflow_guard/test_manifest_schema_skew.py.
No schema content changes (already correct); no managed-script mirrors involved.
