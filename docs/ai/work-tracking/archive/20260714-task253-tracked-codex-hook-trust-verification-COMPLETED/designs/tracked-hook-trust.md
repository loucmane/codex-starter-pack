# Tracked Codex Hook-Trust Verification

## Failure Model

Strict verification previously derived Codex hook-trust guidance from `.aegis/reports/install-report.json`. That report is generated and intentionally ignored, so clean clones cannot reproduce the result even when every tracked managed asset is correct.

## Trusted Contract

The tracked foundation manifest contains one installer-generated `codex.hook_trust` gate. It is accepted only when all contract fields match exactly:

- optional policy gate scoped to the Codex adapter;
- `.codex/hooks.json` as the settings path;
- the canonical unsupported-reason text directing review through `/hooks`;
- manual verification with unsupported failure mode and no automated expected value.

The derived guidance fixes the review command to `/hooks`, the hash scope to the exact hook definition, and `bypass_allowed` to false.

## Fail-Closed Rules

Missing gates, duplicate gates, malformed verification metadata, or any semantic difference produce no guidance. The existing required `codex.hook_trust_guidance` strict check then fails. No repository content can assert external Codex trust or bypass manual review.

## Compatibility

Installer output remains unchanged except that the canonical unsupported reason is shared by generation and verification. Root and packaged installer assets remain byte-identical.

## Rollback

Revert the Task 253 commit. No migration or persistent state conversion is required.
