# Findings

- 2026-07-11 - `_render_claude_entrypoint` currently emits the full strict ceremony loop,
  including per-mutation logging, handoff repair, closeout, and Taskmaster completion ordering,
  even for advisory deployments.
- 2026-07-11 - The current AGENTS and Codex managed blocks are shorter, but they do not tell the
  agent to inspect enforcement mode or describe advisory recording, capsule orientation, and
  witness delivery behavior.
- 2026-07-11 - Existing Claude and Agents entrypoints always merge into target content. Codex
  merges only before manifest ownership is recorded or when marked customized; a later clean
  update can select the upstream source `CODEX.md` instead of preserving current project bytes.
- 2026-07-11 - Canonical and packaged installer files are byte-identical before implementation,
  so Task 237 must preserve that invariant.
- 2026-07-11 - The continuation tests require every surface to retain a compact summary and the
  `.aegis/contract.md` pointer; the full strict continuation contract remains authoritative.
- 2026-07-11 - Initial isolated Blog dogfood exposed a markerless migration defect: the old
  manifest-owned Claude runtime was appended under `Existing Project Instructions`, preserving
  the strict ceremony Task 237 was meant to remove.
- 2026-07-11 - The Blog manifest checksum exactly matched the markerless `CLAUDE.md`. Using that
  ownership proof permits safe migration of the whole legacy runtime while preserving any file
  whose bytes diverged after owner customization.
- 2026-07-11 - Final isolated Blog dogfood produced 19/19/21-line Claude/Codex/Agents blocks,
  preserved Codex and Agents project bytes, remained advisory, and was idempotent on the second
  update preview.
- 2026-07-11 - Combined managed guidance fell from 6,939 to 4,220 bytes in Blog. The main saving
  is Claude's strict payload reduction; Codex and Agents intentionally gained missing mode
  semantics.
- 2026-07-11 - PR #259 full-suite CI found that source `CODEX.md` had one blank line between the
  rendered continuation summary and end marker. Fresh installs copied that byte, while the next
  plan rendered the canonical block without it, producing one spurious `modify` plus a manifest
  update on both Python 3.11 and 3.12.
