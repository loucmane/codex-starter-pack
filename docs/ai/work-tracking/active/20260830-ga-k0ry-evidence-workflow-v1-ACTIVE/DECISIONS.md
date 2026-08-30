# Decisions

- 2026-08-30 — Ship four skill modes only: `freeze`, `shadow`, `adjudicate`, and `closeout`.
  `authoritative` hard-errors in v1; certification and profile authoring remain separate work.
- 2026-08-30 — Keep the generic layer in `plugins/gas-city-workflow`; keep the HPFetcher profile
  and bundle builders in `loucmane/hp-coach`; keep domain verdict scripts untouched.
- 2026-08-30 — Use one parent Bead for each evidence run. Lane executions remain bounded formula
  steps or process evidence, while repairs that outlive a run receive their own Beads.
- 2026-08-30 — Record both the sealed-review digest and release event on the parent Bead, require
  Fable readback before release, and label pre-release non-access as policy-only rather than a
  cryptographic guarantee.
- 2026-08-30 — Auto-trust only the four hooks resolved from the byte-verified canonical evidence
  manifest. Use `config/read` + `hooks/list` + one version-locked `config/batchWrite` + immediate
  `hooks/list` readback. Extra or altered hooks remain blocked, and the trust-bypass CLI flag is
  forbidden.

- 2026-08-30 — _Pending_ — capture decisions with context.
