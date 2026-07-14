# Task 249 Fix pre-adapter Codex manifest update migration – Implementation Notes

## Completed Workstreams
- **Apply ordering:** move managed `install(..., apply=True)` ahead of
  `runtime_update(..., apply=True)` after preview safety has passed.
- **Failure reporting:** if install refuses, report it without claiming runtime apply; if
  runtime later refuses, retain both applied-install and refused-runtime evidence.
- **Parity:** apply the same change to source and packaged installer copies and compare bytes.
- **Regression:** generate Blog-shaped pre-adapter manifests from current Codex-only and
  multi-agent installs; prove migration, current-schema output, and second-preview idempotence.
- **Safety:** prove a divergent unowned hook remains byte-identical and prevents manifest or
  runtime writes; prove direct runtime update remains strict.
- **Dogfood:** replay update apply against a disposable snapshot of the active Blog checkout.
