# 2026-06-10 Task 203 Capsule PR-1b kickoff

PR-1a (task 202) merged as 3b45955 (GitHub PR #200); envelope archived; TM 202 done.

Task 203 = capsule PR-1b: async record hooks per AEGIS_CAPSULE_SPEC.md sections 1.1/1.2/2.
Scope pinned in designs/record-hooks-scope.md: five touchpoints (settings renderer
exec-form async entries, ledger-record.sh bootstrap, aegis hook dispatcher choices,
gate_lib `record` routing with always-exit-0 recorder, manifest managed_files for
ledger_lib + ledger-record.sh), event classification (mutation/tool_failure/delivery/
task_truth), payload-fixture prerequisite (tests/fixtures/hook_payloads/ captured live
via temporary settings.local.json), .gitignore hygiene rider. Existing synchronous
hooks untouched until PR-4. Live acceptance (events appear in HP-Coach, nothing blocks)
runs in HP-Coach after merge via plan-install + install --apply.

Enforcement remains advisory (owner-set). Commits --no-gpg-sign (no tty).
