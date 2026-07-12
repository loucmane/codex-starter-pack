# Task 238 Universal Context-Budget Contract

Status: binding implementation design

Date: 2026-07-12

## Problem

Agent-facing command output is itself an LLM input. A command that emits thousands of
event IDs, paths, checks, findings, or repair candidates consumes context before the
agent can act. HP-Fetcher demonstrated the failure directly: advisory pending state
turned a read-only status request into thousands of lines even though the operator only
needed exact counts, a few representative samples, the evidence location, and one next
action.

Task 238 changes rendering, not detection or stored truth. Full internal payloads,
state files, and report artifacts remain authoritative. No pending event is drained,
deleted, rewritten, or hidden from intentional full-detail inspection.

## Modes

| Mode | CLI | Maximum | Collection sample | Purpose |
| --- | --- | --- | --- | --- |
| default | no detail flag | 60 lines and 8 KiB UTF-8 | 5 items | Safe for automatic agent invocation |
| verbose | `--verbose` | 120 lines and 32 KiB UTF-8 | 20 items | Bounded diagnosis without context flooding |
| all | `--all` | no renderer cap | complete | Explicit operator/debug intent only |

`--verbose` and `--all` are mutually exclusive. `--json` selects representation, not
detail. Default JSON is bounded; `--all --json` returns the complete legacy payload.
Agent guidance must never recommend `--all` as its default next action.

MCP tools expose the same modes as `detail=default|verbose|all`. The cap applies to
the complete MCP success/error envelope after transport serialization, not merely to
the nested core report. MCP metadata uses a flatter representation so FastMCP's
pretty JSON cannot turn a compact payload into more than 60 lines.

## Bounded JSON Compatibility

The bounded projection preserves top-level scalar identity and status fields and samples
nested collections in place. It adds `_aegis_output`, containing:

- command and detail mode;
- configured and actual line/byte counts;
- exact collection counts by JSON path;
- exact category counts for recognized fields such as status, reason, event type,
  verdict, label, mode, hook, and tool name;
- bounded truncation records with total, shown, and omitted counts;
- full-detail artifact paths;
- one copyable next action when derivable; and
- an explicit `use --all` fallback for intentional full stdout.

Existing consumers that read top-level `status`, `installed`, `passed`, `summary`, or
identity values continue to work. Consumers that require complete lists must opt into
`--all --json` or read the linked artifact. The renderer must fall back to a minimal,
valid JSON envelope rather than emitting invalid or over-budget JSON.

## Bounded Text

Existing command-specific summaries remain the source of wording and verdict order. The
shared renderer enforces the hard cap and appends, within the cap:

- exact high-value counts;
- a truncation marker when output was sampled;
- full-detail artifact paths;
- one copyable next action; and
- the explicit `--all` escape hatch.

The renderer preserves the beginning of the command-specific summary because it carries
the command identity and primary verdict. It may omit repeated details, never the final
pass/fail class or the fact that truncation occurred.

## Artifact Ownership

- status and next: current-work, pending-tracking, manifest, verification, and closeout
  state already stored under `.aegis/`;
- readiness: Taskmaster, plan/session/current-work/tracker state named by the summary;
- doctor: the same installed-state sources, with complete stdout available only by
  explicit `--all --json` because doctor remains read-only;
- verify: `.aegis/reports/verification-report.json`;
- update: `.aegis/reports/update-report.json` when applied, plus install-plan and
  verification artifacts;
- witness: `.aegis/reports/witness-report.json`;
- replay: a full JSON report in the selected replay work directory;
- closeout: `.aegis/reports/closeout-report.json` when written; dry-run failures link
  their source evidence and support explicit `--all --json` without fabricating a report.

## Integration Boundary

The shared Python renderer lives in `aegis_foundation/output_budget.py`. Package CLI
handlers use it after the existing core functions have produced their full payloads.
Witness and replay keep complete report generation separate from stdout rendering.
Readiness uses a small adapter with the same numeric contract because the hook executes
as a standalone managed script in target repositories where importing the package is not
guaranteed. Source and packaged managed scripts remain byte-identical.

No detection function may receive a sampled payload. Sampling is a final presentation
step only. Exit codes are computed from the full payload before rendering.

## Acceptance And Falsifiers

Automated fixtures cover collection sizes 0, 10, 3,500, and 100,000. They assert exact
counts, category totals, truncation markers, valid JSON, line and byte limits, bounded
verbose behavior, and complete `--all` output. Failure fixtures prove that CI-facing
stdout stays bounded while the artifact retains every failure.

The HP-Fetcher dogfood is read-only: capture before/after pending-state fingerprints,
run status with the Task 238 source renderer, assert one-screen output, and prove no
pending event or workflow state changed. Record latency, emitted bytes/lines, source
event count, governance calls, and rollback.

Failure conditions include invalid bounded JSON, an output over either default cap,
missing exact counts, absent truncation disclosure, loss of full artifact detail, an
implicit full-detail invocation, or any mutation of HP-Fetcher pending state.

## Rollback

Revert the CLI renderer integration and managed readiness/witness/replay presentation
changes. Full state and report artifacts are unchanged, so rollback needs no data
migration. The shared renderer module can be removed after callers are reverted.
