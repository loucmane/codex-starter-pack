# ga-ur1c.6.4 live acceptance — 2026-09-01

## Source and installed binding

- Transaction repair: signed commit `3f57327a219a7236b2040cdd4638918acb0ed39c`, merged as
  `b3769f7e1910a8ec014d5bb47c603d5d0d7fd35e` by PR #356.
- Semantic post-cycle repair: signed commit `a27e67c222ed74081390a585a0f1d1020745c980`,
  merged as `8ac134e269ede170ec3536130f80ac0ae8d7ed68` by PR #357.
- Installed runtime: `4ffcdd401a575d4efdc95e9c108099eae44b017d0aea92c8b551fe8c3932cfb6`.
- Installed registry: `ab3b8a76dde4fcb369ab2057ddc881991b2e881b824d2e53b7f5fd4df0db5ee0`.
- Installed service: `9e3e9df1ec28706bc52d1b53c8f91e85b747018d44a97a80921bfcf398ba4814`.
- Installed timer: `85a227e0c406eb056e3982e2112a58a32720416f7776f4079a276e140f44e6e2`.
- Merge-bound installer `--check`: PASS.

The merge-bound transaction repair had already completed and the four installed assets matched the
reviewed source. A redundant byte-identical reinstall was refused before mutation; no workaround or
second transition was attempted. The semantic repair changes canonical dashboard capture scripts
referenced by the registry and does not change the packed installed runtime.

## Consecutive-cycle no-op proof

The scheduled timer advanced the dashboard audit clock from `2026-09-01T14:06:28Z` to
`2026-09-01T14:07:37Z`. Across those consecutive completed cycles:

| Projection | Files | Aggregate file manifest SHA-256 before/after |
|---|---:|---|
| Gas City Operations | 2,677 | `bf9855de498294d91b61b7e92fd92ca1ec3c35d6171674defc266ff5498f9b95` |
| Gas City | 250 | `a50e2923fd9cf6fc8aa9e7d77a57f7c1ad5d7072333ebbeb6d8446dd0bf76dee` |
| HPFetcher | 4,507 | `e5b8956cb5184f020a6d7aabcfc888d33b965165586bed5716e2700f99b08e43` |
| Blog | 1,499 | `11b4a97c64220e3569a94f4754598cd38f44ad79893697817432e52f0f6f46ee` |
| Continuity | 3 | `93bf448c8dd0a1f0534d8f60b838fb8561179c0f14752241361a56bfddab56c2` |

Every projection contained zero symlinks. Dashboard `snapshot_sha256` remained
`e352277de7e5bdd4deed3742c89b27926ac7b18c3938b31ba01b2cf3732212c0`; report SHA-256
remained `906d3b68d42f46462038c9f1908e1afb6339670e8ec35fec08dad004ab222409`; and
`refresh_attempted=false`. The serialized installed `check --require-live-index` returned `ok=true`
for all four projects and the continuity dashboard, with no problems and no refreshes.

## Non-interference

- Timer: enabled, active, waiting, result success.
- Service: inactive, dead, result success, `NRestarts=0`.
- WSL Obsidian: PID `3168034`, boot ID `ff4de3b9-89d2-46e1-8b7a-ac8758015c39`, kernel start
  tick `35154910`, cmdline SHA-256
  `adeab20e3516fa4c9a37c947d721233f9c64e6b4e200dd5aa96066cba62ca8ae`.
- Gas City controller remained PID `50582`; all four registered project rigs remained suspended;
  running agents remained zero.

## Regression and workflow checks

- Focused affected suite: `76 passed`.
- S:W:H:E guard: PASS.
- Work-tracking audit: PASS.
- Plan/tracker sync: PASS.
- Installed-byte check: PASS.

Result: PASS. The repaired cycle is serialized, rollback semantics are stable, terminal output is
byte-identical across consecutive cycles, and live Obsidian observation remains authoritative.
