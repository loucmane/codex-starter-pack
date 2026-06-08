# Findings - Task 180

- 2026-06-08 — HP-Coach observation dogfood produced known browser/screenshot byproducts that could not be cleaned by the agent while observation mode was active, because raw cleanup is correctly blocked and clean `observe stop` refuses dirty state.

Observation mode correctly permits dev servers and browser/screenshot tooling, but those tools may create repo-local byproducts such as root-level screenshots and `.playwright-mcp/`.

The current exit path is incomplete:

1. `aegis observe stop` refuses dirty state.
2. Raw cleanup commands such as `rm` are blocked while observation is active.
3. The only available in-agent escape is `observe stop --allow-dirty`.

The desired upstream fix is a sanctioned `observe stop --collect-artifacts` path that collects only known, newly-created observation artifacts while continuing to block source, Taskmaster, protected, pre-existing, symlink-escaping, or unknown changes.
