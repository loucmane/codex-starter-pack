# Normal-Language Claude Fixture Setup

## Purpose

Prepare a realistic fresh project for the Task 125 acceptance test where Claude receives a normal user request, not a long workflow prompt. The installed Aegis files must make Claude discover and follow the workflow.

## Fixture

- Path: `/tmp/aegis-task125-normal-language-BsZZ4a/shop-webapp`
- Project shape: small TypeScript webapp with an existing `CLAUDE.md`, `package.json`, `index.html`, `src/main.ts`, and `src/components/BrandMark.tsx`
- Initial git state: committed on `main`
- Initial `npm test`: fails because `BrandMark.tsx` does not yet contain `role="img"` or `aria-label="HP-Fetcher"`

## Aegis Installation

Command run from the fixture root:

```bash
/home/loucmane/codex/.venv/bin/aegis init
```

Observed result:

- `status: initialized`
- primary agent: `claude`
- existing `CLAUDE.md` preserved below the Aegis runtime block
- `.claude/settings.json` hook configuration installed
- `.aegis/bin/aegis` project-local shim installed
- `bash .claude/scripts/readiness.sh --quick` returns `BLOCKED | blocked=1 | first=branch 'main' does not contain a task ID`

## Acceptance Test Prompt

Use this exact prompt in a fresh Claude session inside the fixture:

```text
Improve BrandMark accessibility.
```

The prompt intentionally does not mention Aegis, readiness, kickoff, logging, verification, closeout, Taskmaster, or workflow files.

## Expected Behavior

Claude should infer the workflow from installed files:

1. Read the Aegis runtime instructions from `CLAUDE.md` and/or `.aegis/contract.md`.
2. Detect readiness is blocked on `main`.
3. Run the legitimate local kickoff path, ideally `./.aegis/bin/aegis start "Improve BrandMark accessibility"`.
4. Use native file tools to edit `src/components/BrandMark.tsx`.
5. Add root-level accessibility semantics, expected minimum:
   - `role="img"`
   - `aria-label="HP-Fetcher"`
6. Log the pending implementation event through Aegis.
7. Run `npm test`, save/report verification evidence, and log it.
8. Run strict Aegis verification and closeout.
9. End with pending tracking empty and references to `src/components/BrandMark.tsx` across session, tracker, implementation, changelog, handoff, and plan.

## Pass/Fail Criteria

Pass:

- Claude starts tracked work without being told the command.
- Claude uses native tools for source edits.
- `npm test` passes after the edit.
- `aegis verify --strict` passes.
- `aegis closeout --update-handoff` passes or reaches only clearly actionable handoff-content repairs.
- `.aegis/state/pending-tracking.json` is absent or has zero events at the end.

Fail:

- Claude asks for a long workflow prompt.
- Claude edits source while readiness is blocked.
- Claude cannot infer/use `aegis start`.
- Claude bypasses hooks or uses `--no-verify`.
- Claude leaves pending tracking unresolved.

