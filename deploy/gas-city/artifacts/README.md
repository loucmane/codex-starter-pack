# Build inputs (not committed)

Materialize only checksum-verified Linux AMD64 binaries here before building:

- `gc` — 1.3.5, SHA-256 from `runtime-lock.json`
- `bd` — 1.1.0, SHA-256 from `runtime-lock.json`
- `dolt` — 2.2.0, SHA-256 from `runtime-lock.json`
- `codex` and its adjacent runtime resources — official Linux x64 0.144.4
  package, archive SHA-256 `9a4a45314e80b53c4761b80067e3a68c2302f9a9026059b5f54f22dec8f34323`
  and binary SHA-256 `2b3edc9cdfd1717fba3dbc92817205a8a2c7511d459e456d4817eeff6f78ed7a`
- `claude` — subscription-capable CLI 2.1.210, binary SHA-256
  `e7d2ceb53ed4c2ced1fe7fc1c6331c98dc5f7b4c9b2722d9c5fa3dd5dff6f719`
- `aegis-runtime.whl` — deterministic offline runtime built only from the
  exact Aegis CLI/core modules and packaged assets enumerated by the builder.
  Rebuild it
  with `PYTHONDONTWRITEBYTECODE=1 deploy/gas-city/bin/build-aegis-runtime` and
  require the printed SHA-256 to match `runtime-lock.json`. The worker extracts
  it without pip, package-index access, or runtime dependency resolution.

The build must stop if any pinned infrastructure, provider, or helper checksum
differs. Both resulting image IDs and all model observations stay runtime
evidence until the canaries prove them; they must not be guessed or committed
as receipts.
