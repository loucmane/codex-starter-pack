# Task ID: 179

**Title:** Add safe Aegis bootstrap upgrade for managed adapter files

**Status:** done

**Dependencies:** None

**Priority:** high

**Description:** Allow existing Aegis installs to refresh managed adapter and bootstrap files without manual deletion when those files are recorded as Aegis-owned in the installed manifest.

**Details:**

Classify existing files listed in the manifest managed_files as safe managed upgrades when they differ from current expected content, unless the path is explicitly customized or otherwise unsafe. Preserve manual-review for unknown user files and customized files. Validate against an HP-Coach style install where .claude scripts, .aegis/bin/aegis, schemas, and foundation manifest differ from the new dispatcher runtime assets.

**Test Strategy:**

No test strategy provided.
