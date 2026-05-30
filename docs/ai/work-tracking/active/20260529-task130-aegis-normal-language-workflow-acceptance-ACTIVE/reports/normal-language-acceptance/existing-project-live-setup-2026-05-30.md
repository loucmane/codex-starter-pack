# Task 130 Existing-Project Claude Live Test Setup

Date: 2026-05-30

## Target

```text
/tmp/aegis-task130-existing-project-pE84A7/hpfetcher-synthetic
```

## Shape

- Existing synthetic frontend project with a baseline git commit on `main`.
- Existing project `CLAUDE.md` with source layout and development rules.
- Existing component structure:
  - `app/src/components/BrandMark.tsx`
  - `app/src/components/DesktopNav.tsx`
  - `app/src/App.tsx`
  - `app/src/styles/brand.css`
- Existing docs at `docs/architecture.md`.
- Existing `.mcp.json` points the `aegis` MCP server at the local checkout under `/home/loucmane/codex`.
- No Aegis runtime installed yet.
- No Taskmaster or Serena.

## Baseline

Initial commit:

```text
823d520 chore: create existing project fixture
```

Initial project verification fails, as expected:

```text
npm run verify
```

Output:

```json
{
  "rootSpan": true,
  "hasRoleImg": false,
  "hasLabel": false,
  "hidesDecorativeAccent": true
}
```

The fixture already hides the decorative accent with `aria-hidden`; the task is to make the BrandMark root announce as a single `HP-Fetcher` image label.

## Prompt

Open a fresh Claude client in the target folder, approve the project MCP server, then use this normal prompt:

```text
Improve the BrandMark accessibility so screen readers announce it as HP-Fetcher. Use the project workflow and close it out when done.
```

## Pass Criteria

- Claude uses MCP `aegis.init` or public CLI `aegis init`, preserving the existing project `CLAUDE.md` under the Aegis managed block.
- Claude starts local tracked work with `aegis.start`, not explicit numeric `aegis.kickoff`.
- Claude logs scope before source edits.
- Claude uses native source-editing tools for `app/src/components/BrandMark.tsx`.
- Claude makes a semantic accessibility fix so `npm run verify` passes.
- Claude logs the implementation pending event with `pending_event_id=current`.
- Claude writes and logs task verification evidence.
- Claude runs strict Aegis verification and logs the strict verification pending event.
- If closeout readiness reports handoff semantic gaps, Claude uses `aegis.handoff_repair apply=true`.
- Claude does not directly edit `HANDOFF.md`, `IMPLEMENTATION.md`, or `CHANGELOG.md`.
- Final closeout passes with pending tracking empty.

## Evidence To Capture After Run

- Final branch name.
- Final `npm run verify` result.
- `.aegis/reports/verification-report.json` summary.
- `.aegis/reports/closeout-report.json` summary.
- Whether `.aegis/state/pending-tracking.json` is absent or has zero events.
- Whether existing `CLAUDE.md` content was preserved.
- Whether workflow surfaces contain a handoff repair event if handoff repair was needed.
