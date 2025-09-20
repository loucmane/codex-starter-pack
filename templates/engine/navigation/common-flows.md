---
id: common-request-flows
type: engine-component
dependencies:
  - templates/REGISTRY
  - templates/handlers
  - tools/search/serena-guide
  - tools/search/grep-patterns
exports:
  - development-flow
  - problem-solving-flow
  - search-flow
  - git-flow
---

# Common Request Flows

## "Work on X" → Development Flow
```
1. Search REGISTRY: "start-new-work"
2. Find: Handler link [start-new-work](handlers/triggers/development/start-new-work.md)
3. Load using one of:
   - Direct: Read --file_path "templates/handlers/triggers/development/start-new-work.md"
   - Search: mcp__serena__search_for_pattern --substring_pattern "id: start-new-work" --relative_path "templates/handlers/"
4. Execute: Create work folder, initialize todos, begin implementation
```

## "Fix bug Y" → Problem Solving Flow
```
1. Search REGISTRY: "fix-bug"
2. Find: Handler link [fix-bug](handlers/triggers/debug/fix-bug.md)
3. Load using one of:
   - Direct: Read --file_path "templates/handlers/triggers/debug/fix-bug.md"
   - Search: mcp__serena__search_for_pattern --substring_pattern "id: fix-bug" --relative_path "templates/handlers/"
4. Execute: Evidence gathering → root cause → fix → test
```

## "Find Z" → Search Flow
```
1. Search REGISTRY: "search-code" or "find-symbol"
2. Find: Tool selection matrix
3. Load: Appropriate search handler
4. Execute: Use Serena for code, Grep for text
```

## "Commit changes" → Git Flow
```
1. Search REGISTRY: "commit-changes"
2. Find: Handler link [commit-changes](handlers/operators/git/commit-changes.md)
3. Load using one of:
   - Direct: Read --file_path "templates/handlers/operators/git/commit-changes.md"
   - Search: mcp__serena__search_for_pattern --substring_pattern "id: commit-changes" --relative_path "templates/handlers/"
4. Execute: Check conventions → create message → commit
```