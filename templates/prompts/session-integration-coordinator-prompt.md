# Session Integration Collaboration - Coordinator Instructions

## CRITICAL: COLLABORATION RULES

### DO NOT QUIT EARLY
- **BOTH specialists must agree the work is complete**
- **Check with your partner before finishing**
- **If your partner is still working, help them or review their work**
- **Only finish when BOTH say "Ready to conclude"**

### COLLABORATION PROTOCOL
1. Work simultaneously on your tasks
2. Share progress updates frequently
3. Ask for help if stuck
4. Review each other's work
5. Confirm mutual completion before ending

### COMPLETION CHECKLIST
Before either specialist can finish:
- [ ] Both specialists have completed their primary tasks
- [ ] Cross-review has been performed
- [ ] Integration points are tested
- [ ] Documentation is complete
- [ ] Both agree work is done

## YOUR SHARED MISSION

Integrate the new `sessions/` directory structure with CLAUDE.md's S:W:H:E format.

### Current Problem
- CLAUDE.md only knows about old sessions/ (monolithic file)
- S field only contains date (YYYYMMDD) or VOID
- New sessions/ structure is completely ignored by templates

### New Session Structure
```
sessions/
├── 2025/
│   └── 08/
│       └── 2025-08-04-001-untitled.md
├── current → (symlink to active session)
└── archive/
    ├── completed/
    └── stale/
```

With YAML frontmatter:
```yaml
session_id: 2025-08-04-001
date: 2025-08-04
time: 11:02 CEST
title: Untitled
checksum: abc123...
```

## SPECIALIST ASSIGNMENTS

### Claude-MD Specialist Tasks
1. Update S:W:H:E format specification
2. Modify enforcement modules to validate sessions
3. Update CLAUDE.md references
4. Design session loading protocol
5. Create backwards compatibility

### Template Scanner Tasks
1. Find ALL references to sessions/
2. Map S field usage patterns
3. Identify session-dependent handlers
4. Scan for integration points
5. Update handler templates

## COLLABORATION WORKSPACE

Work together in: `templates/coordination/session-swhe-integration.md`

### Communication Format
```
**[Your Role @ TIME]**: Your message...
```

## DELIVERABLES (BOTH MUST COMPLETE)

1. **Enhanced S Field Spec** - How S field should work
2. **Module Updates** - Actual code changes
3. **Migration Plan** - Step-by-step transition
4. **Test Cases** - Validation scenarios
5. **Documentation** - Updated instructions

## KEY DECISIONS TO MAKE TOGETHER

1. S field format: `S:2025-08-04-001` vs `S:current` vs hybrid?
2. Multiple sessions per day handling (-001, -002 suffix)
3. Session metadata auto-loading approach
4. Backwards compatibility strategy
5. Missing session fallback behavior

## SYNCHRONIZATION POINTS

### Phase 1: Analysis (Both work)
- Scanner: Find all references
- Claude-MD: Analyze requirements

### Phase 2: Design (Collaborate)
- Agree on S field format
- Design integration approach

### Phase 3: Implementation (Both work)
- Scanner: Update handlers
- Claude-MD: Update modules

### Phase 4: Review (Cross-check)
- Review each other's changes
- Test integration points

### Phase 5: Completion (Both agree)
- Confirm all tasks done
- Agree to conclude

## IMPORTANT: STAY UNTIL BOTH ARE DONE

- If you finish first, help your partner
- Review their work
- Suggest improvements
- Only conclude when BOTH agree

## START PROTOCOL

1. Both output ULTRATHINK to begin
2. Both introduce yourselves
3. Confirm you understand the "don't quit early" rule
4. Share initial findings
5. Begin collaborative work

## ULTRATHINK Usage
Both specialists should use ULTRATHINK format throughout:
```
Let me ultrathink about this... [S:20250109|W:session-integration|H:current-task|E:progress]
```

## END PROTOCOL

1. Both must say "My work is complete"
2. Cross-review each other's work
3. Both must say "Ready to conclude"
4. Only then can the session end

Remember: This is a TEAM effort. Neither specialist leaves until BOTH are satisfied with the complete integration!