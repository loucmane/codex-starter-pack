# Bead ga-k9sd Beads-first workflow authority and reboot hardening – Implementation Notes

## Planned Workstreams
- Codex-facing beads-first guidance and explicit Taskmaster compatibility boundary.
- Read-only WSL reboot doctor, Windows bootstrap assets, focused regression tests, and operator runbook.
- Source-workflow support for `wizard kickoff --bead`, `Bead IDs` plan identity, and exact `codex/<bead>...` branch binding.
- Legitimate closeout of historical ACTIVE-folder residue and separate tracking of the missing override defect.
- Refresh exact staged tree and review package before any stable installation.

## Implemented on 2026-08-26
- Added the bead-native kickoff path to `scripts/codex-task` and its packaged mirror; the path creates plan/session/tracker state and makes no Taskmaster command.
- Added `Bead IDs` parsing and validation to `scripts/codex-guard` and its packaged mirror while retaining existing Task-ID behavior.
- Added red/green tests for parser, artifact generation, invalid bead IDs, branch validation, and packaged-script parity.
- Applied the supported command to `ga-k9sd`, replacing stale Task 288 current pointers with bead-bound artifacts.
- Added the exact `CODEX_WORK_TRACKING_FOLDER` selector promised by the multi-ACTIVE error; invalid, traversing, missing, and symlinked selections fail closed.
- Prevented parent `--include-untracked` validation from descending into nested Git repositories and taught the archive flow to preserve same-day tracker/document/memory continuity.



## Progress Log

- **2026-08-26 16:15** — [S:20260826|W:ga-k9sd-beads-first-guidance|H:claude-readiness:bead-native|E:.claude/scripts/readiness.sh] Added bead identity parsing and fail-closed source readiness while preserving the numeric Taskmaster compatibility path.
- **2026-08-26 17:14** — [S:20260826|W:ga-k9sd-beads-first-guidance|H:windows-bootstrap:principal-sid|E:tests/reboot_readiness/test_bootstrap_assets.py] Implemented canonical SID binding for the Windows scheduled-task verifier and kept the returned display-form user_id in the evidence contract.
- **2026-08-26 17:55** — [S:20260826|W:ga-k9sd-beads-first-guidance|H:windows-bootstrap:powershell51|E:scripts/windows/gas-city-wsl-bootstrap.ps1] Replaced ambient LASTEXITCODE capture with Start-Process -Wait -PassThru plus redirected stdout/stderr and removed unsupported ConvertFrom-Json -Depth.
- **2026-08-26 18:08** — [S:20260826|W:ga-k9sd-beads-first-guidance|H:windows-bootstrap:shared-custody|E:scripts/windows/install-gas-city-wsl-bootstrap.ps1] Changed installed bootstrap root to %USERPROFILE%\\.gas-city\\bootstrap and evidence root to %USERPROFILE%\\.gas-city\\reboot-readiness.
