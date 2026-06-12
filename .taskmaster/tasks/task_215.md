# Task ID: 215

**Title:** Verify schema-skew self-diagnosis

**Status:** in-progress

**Dependencies:** None

**Priority:** medium

**Description:** From HP-Coach closeout report 2026-06-12: a stale MCP/CLI bundle rejected the manifest 'runtime' field with a bare jsonschema error (Additional properties are not allowed) even though current schemas support it and the installed mirror in the target repo was newer than the validator's packaged copy. NOT a schema-content bug (current source validates the same manifest clean — verified). Fix: schema-validation failures in verify/doctor must report the resolved source_root + installer_version they validated with, cross-check the target's mirrored schema, and when the mirror is newer than the validator's copy, replace the error with an explicit 'validator runtime is stale — re-register/update your Aegis CLI/MCP' message. Regression test: stale-schema source root + newer mirror => skew message, not bare validation error.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
