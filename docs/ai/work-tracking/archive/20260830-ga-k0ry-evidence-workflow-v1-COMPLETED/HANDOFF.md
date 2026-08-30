# Handoff — ga-k0ry evidence workflow v1

## Outcome

PASS. The generic shadow-only evidence workflow and the HPFetcher project profile are merged,
installed where required, and proven by frozen run
`hpf-nqzf-batch13-shadow-20260830-005`.

## Terminal evidence

- Operations policy repair: PR #326, merge `46ceead32d82582c955da6ff269ede0605f2a3aa`.
- Dedicated reviewer policy SHA-256:
  `dc2e7ac6fc66714a73e482e50bdff7fb3fc77936c7bff8a76723a6caa4d3b67d`.
- Frozen manifest SHA-256:
  `9cd4d9378dd7a3ca8aa01aef4511e698ce796098b1f43ea2efec360166cc3428`.
- Blind-solver report SHA-256:
  `66aeac2db41ebbcf0e46eca510408df312ac74d8fe62698b5885a9e2afb3e7ff`.
- Adversarial-audit report SHA-256:
  `32790a8c177a5750348615ff0ae7e26c24ef8cc5c9782738f453846a1fab7d76`.
- Release SHA-256:
  `ef110d77273dfceec56f17377737e2196e560073dd8d67680f33bd9f8e289500`.
- Evidence-only comparison SHA-256:
  `2b505f349a8bdb0d7758748efb99326f0bb0583a1ad0745941f9cb74def6461a`.
- HPFetcher PR #367: signed head `7ee1f35a9260a27090720197b4487164b427df54`, merge
  `652d81e74bdde97c3735b63b09639db9aa3c3c84`, tree
  `c5c2450bae6db457c88df90d5a7b257c272a2355`.

The comparison deliberately carries `domain_verdict=null`. No promotion, deployment, or
authoritative HPFetcher output changed. Both reviewer sessions drained, all four project rigs are
suspended, no Gas City session or tmux residue remains, and controller PID `50582` stayed stable.

## Closeout

Close `ga-k0ry` PASS after publishing this archive commit, then require the terminal deterministic
Obsidian projection and one subsequent no-op reconciliation.
- Archived on 2026-08-30 20:05 CEST — Folder moved to archive and tracker marked COMPLETED.
