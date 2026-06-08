# Task ID: 177

**Title:** Add Aegis dynamic runtime dispatch and update flow

**Status:** in-progress

**Dependencies:** None

**Priority:** high

**Description:** Split Aegis bootstrap from runtime so downstream projects can update gate/readiness/runtime fixes without full scaffold reinstall.

**Details:**

Implement stable installed hook dispatchers that call the project-local .aegis/bin/aegis hook entrypoints; add hook pretooluse/posttooluse/stop/readiness runtime commands; add runtime status/update commands that record source-root mode, commit, and relevant dirty state in .aegis/runtime.env and foundation-manifest.json; preserve fail-closed mutation behavior and existing hook semantics; keep reinstall required only for bootstrap/settings changes; validate with installer, MCP, hook, and downstream-style update tests.

**Test Strategy:**

No test strategy provided.

## Subtasks

### 177.1. Extract hook runtime entrypoints

**Status:** done
**Dependencies:** None

Move gate and readiness execution behind Aegis runtime commands.

**Details:**

Add aegis hook pretooluse, posttooluse, stop, and readiness entrypoints that call importable Python runtime code. Keep existing hook behavior equivalent while making the runtime callable through the project-local Aegis shim.

### 177.2. Install dispatcher hooks and runtime pointer

**Status:** done
**Dependencies:** None

Convert installed Claude hooks into stable dispatchers and record the selected runtime source.

**Details:**

Replace copied hook logic in installed assets with tiny scripts that invoke ./.aegis/bin/aegis hook <phase>. Add .aegis/runtime.env and a manifest runtime block recording mode, source_root, commit, and update timestamp. Reinstall should be required only when dispatcher/settings shape changes.

### 177.3. Add runtime status and update commands

**Status:** done
**Dependencies:** None

Expose an explicit non-reinstall update path for downstream projects.

**Details:**

Implement aegis runtime status and aegis runtime update --apply. Validate source-root shape, record current git commit, report relevant dirty runtime paths, update .aegis/runtime.env and the manifest runtime block only, and refuse broken runtime roots. Keep update scoped away from sessions, plans, and work-tracking.

### 177.4. Preserve fail-closed and backward-compatible hook behavior

**Status:** done
**Dependencies:** None

Make dispatcher runtime failures safe and keep existing installs migration-safe.

**Details:**

PreToolUse must fail closed for mutation-class actions when the runtime cannot load, while retaining existing safe read-only behavior where applicable. Stop hook must not create infinite loops or branch-name deadlocks. Existing copied hook installs should remain supported or migration-safe until dispatcher installs are in place.

### 177.5. Test downstream runtime update without scaffold reinstall

**Status:** done
**Dependencies:** None

Prove runtime behavior can update without rewriting installed scaffold.

**Details:**

Add tests for installed dispatcher scripts, aegis hook entrypoints, runtime status/update, manifest and runtime.env updates, broken source-root failure, no scaffold or session rewrite on runtime update, and an HP-Coach-style flow where install-once plus runtime update exposes new gate behavior without reinstall.
