# Timestamp Validation Gate (Draft)

## Goal
Ensure every timestamp logged in sessions/work-tracking uses the current local time command (`date "+%Y-%m-%d %H:%M %Z"`) instead of manual entry.

## Requirements
1. **Command Capture**
   - Before writing any timestamped entry, run the date command and paste output verbatim.
   - Guard verifies recent command evidence in session log (command + output).
2. **Behavior Update**
   - Extend `templates/behaviors/timestamps/before-adding.md` to reference the enforced command usage.
   - Behavior blocks entries lacking the command output.
3. **Guard Check**
   - `codex-guard` inspects session/work-tracking diffs for timestamp lines.
   - Confirms preceding lines cite the `date` command output within same entry.
4. **Plan Integration**
   - Add checklist item: "Timestamp sourced from `date` command" in tracker.
   - Plan template references timestamp gate when documenting verification.
5. **Automation Consideration**
   - Optional helper (`scripts/codex-task timestamp stamp`) to run command and insert formatted output.
6. **Evidence**
   - Session log stores command + output (S:W:H:E evidence).
   - Serena memory/hand-off includes timestamp gate confirmation.

## Open Questions
- Should guard enforce timezone or allow overrides with justification?
- How to treat legacy entries created before this gate? (Proposal: allow but warn.)

## Next Steps
1. Review draft with loucmane.
2. Update timestamp behavior + guard once plan compliance work lands.
3. Implement optional helper if desired.


## Execution Tasks (Draft)
- **TaskMASTER Task Proposal**
  - Task: "Implement timestamp validation gate"
    - Subtask 1: Finalize timestamp gate design
    - Subtask 2: Update behavior `timestamps/before-adding.md`
    - Subtask 3: Extend `codex-guard` timestamp checks
    - Subtask 4: Add optional helper script (`codex-task timestamp stamp`)
    - Subtask 5: Update tracker checklist, plan template, and documentation
    - Subtask 6: Validate with guard and capture evidence

> Note: Use double quotes in commit messages (see templates/conventions/git/commit-format.md).
