---
id: session-resolver
title: Session Resolution Engine
type: engine-component
status: stable
priority: critical
dependencies:
  - sessions/ directory structure
  - sessions/ (legacy compatibility)
exports:
  - resolve-session
  - get-current-session
  - validate-session-id
  - detect-session-format
---

# Session Resolution Engine

## Start here

- Canonical reference for sessions. Other docs should link to this page.
- Validate `sessions/current` points to a valid file:
```bash
test -L sessions/current && test -f "$(readlink -f sessions/current)" && echo OK || echo "sessions/current missing or invalid"
```
- Create a new session (recommended script, when available): `scripts/session/start.sh` and end with `scripts/session/end.sh`.
- Anchors you may need next: `#sessions-current`, `#session-id`, `#start-end`, `#common-errors`.

## Purpose
Resolves session references from S field to actual session files, supporting both legacy sessions/ and new sessions/ directory structure.

## Auto-Detection Logic

### Format Detection
The resolver automatically detects the S field format:
- `current` → CURRENT format (sessions/current symlink)
- `VOID` → VOID format (needs resolution)
- `YYYY-MM-DD-NNN` → FULL_ID format (exact session)
- `YYYYMMDD` → DATE_LEGACY format (backwards compatible)
- `YYYY-MM-DD` → DATE_ISO format (ISO date)

### Detection Rules
```
If S:current → read sessions/current symlink
If S:2025-08-04-001 → find exact session file
If S:20250804 → find latest session for that date
If S:2025-08-04 → find latest session for ISO date
If S:VOID → check current, else guide to create
```

## Resolution Protocol

### 1. Parse S Field Value
```markdown
Input: S field value from ULTRATHINK
Process:
  - Detect format using pattern matching
  - Validate format is recognized
  - Prepare search parameters
Output: Format type and search criteria
```

### 2. Locate Session File
```markdown
Priority Order:
  1. Check sessions/current (for 'current')
  2. Search sessions/YYYY/MM/ for exact match
  3. Find latest session for date-based formats
  4. Fall back to sessions/ if exists
  5. Return VOID with creation instructions
```

### 3. Load Session Data
```yaml
Extract from session file:
  session_id: YYYY-MM-DD-NNN
  metadata:
    date: YYYY-MM-DD
    time: HH:MM ZONE
    checksum: sha256
    title: Session Title
  content: Session body text
  source: sessions|legacy
```

### 4. Return Structured Data
```json
{
  "session_id": "2025-08-04-001",
  "path": "sessions/2025/08/2025-08-04-001-untitled.md",
  "format": "FULL_ID",
  "metadata": {
    "date": "2025-08-04",
    "time": "11:02 CEST",
    "checksum": "abc123...",
    "title": "Untitled"
  },
  "content": "## Session: 2025-08-04...",
  "source": "sessions"
}
```

## Compatibility Features

### sessions/ Synchronization
- **On Write**: Update sessions/ when sessions/current changes
- **On Read**: Check sessions/ before sessions/
- **Migration**: Gradual transition without breaking changes

### Validation Rules
1. **Session ID Format**: Must match YYYY-MM-DD-NNN pattern
2. **YAML Frontmatter**: Must be valid YAML with required fields
3. **Checksum**: Verify if present (non-blocking if fails)
4. **Symlink**: Verify sessions/current points to valid session

## Error Handling

### Missing Session
```markdown
If no session found:
  1. Check if sessions/ directory exists
  2. Guide to create new session
  3. Suggest using start-session handler
  4. Return VOID state for proper initialization
```

### Invalid Format
```markdown
If format unrecognized:
  1. Log the invalid format
  2. Attempt legacy sessions/
  3. Guide to proper format
  4. Return error with suggestions
```

### Multiple Matches
```markdown
If multiple sessions for date:
  1. Sort by sequence number (NNN)
  2. Return latest (highest NNN)
  3. Log all matches found
  4. Optionally list alternatives
```

## Concurrent Sessions Policy

- Multiple same-day sessions are supported via the `YYYY-MM-DD-NNN` sequence. Example: `2025-08-13-001`, `2025-08-13-002`.
- Exactly one session is considered active at a time via the `sessions/current` symlink.
- To switch active sessions safely (no rm*):
  ```bash
  ln -sfn "sessions/YYYY/MM/YYYY-MM-DD-NNN-title.md" sessions/current
  test -L sessions/current && readlink -f sessions/current
  ```
- Recommended metadata in each session frontmatter:
  - `status: active|paused|archived`
  - When starting a new same-day session, set previous to `paused` and point `sessions/current` to the new one.
- Optional state helper (for UIs/agents): `sessions/state.json`
  ```json
  {
    "current": "YYYY-MM-DD-002-...md",
    "paused": ["YYYY-MM-DD-001-...md"],
    "updated_at": "2025-08-13T12:34:56Z"
  }
  ```
- Resolution rules remain unchanged:
  - `S:current` follows the symlink
  - `S:YYYY-MM-DD-NNN` targets the exact session
  - `S:YYYYMMDD` picks the latest (highest NNN) for that date

## Usage in swhe-format.md

### Integration Point
```markdown
In swhe-format.md, update S field processing:

1. Import session-resolver
2. Replace direct sessions/ reference with:
   `session_data = resolve-session(s_value)`
3. Use session_data.session_id for S field
4. Handle session_data.source for compatibility
```

### Example Usage
```markdown
# Original
S: Session ID from sessions/

# Updated
S: Session ID via session-resolver
  - Resolves from sessions/current or sessions/
  - Auto-detects format
  - Returns structured data
```

## Migration Path

### Phase 1: Parallel Operation
- Both sessions/ and sessions/ work
- Resolver handles both transparently
- No handler changes required

### Phase 2: Gradual Updates
- Update handlers to use sessions/
- sessions/ becomes read-only mirror
- Deprecation warnings added

### Phase 3: Full Migration
- sessions/ removed
- All handlers use sessions/
- Resolver simplified to sessions-only

## Testing Protocol

### Test Cases
1. **Current Session**: S:current → sessions/current
2. **Specific Session**: S:2025-08-04-001 → exact file
3. **Date Legacy**: S:20250804 → latest for date
4. **Void State**: S:VOID → creation flow
5. **Fallback**: No sessions/ → sessions/
6. **Multiple Daily**: Multiple -NNN → latest

### Validation Tests
- Invalid session IDs rejected
- Corrupted YAML handled gracefully
- Missing symlink detected
- Performance with many sessions

## Success Criteria
- ✓ All S field formats supported
- ✓ Zero breaking changes initially
- ✓ Transparent migration path
- ✓ Performance maintained
- ✓ Error handling comprehensive

## Progress Log

- **2026-04-22 16:00** — [S:20260422|W:task91-standardize-template-metadata|H:templates/engine/core/session-resolver.md|E:templates/metadata/template-metadata-policy.json] Added canonical metadata during the Task 91 engine-module standardization slice
