---
id: system-debug
title: System Debugging Protocol
type: engine-component
status: stable
---

# System Debugging Protocol

## Overview
Systematic approach to debugging template system failures and identifying root causes.

## Debugging Checklist

### If Something Goes Wrong
```
1. Check: Did I search REGISTRY first?
2. Check: Did I load the full handler?
3. Check: Did I skip any pre-conditions?
4. Check: Am I using the right tool?
5. If still broken: Document exact failure point
```

## Diagnostic Steps

### Level 1: Basic Checks
- **Registry Search**: Verify REGISTRY.md was consulted
- **Handler Loading**: Confirm complete handler loaded
- **Pre-conditions**: Check all requirements met
- **Tool Selection**: Validate correct tool used

### Level 2: Deep Analysis
- **Execution Path**: Trace exact steps taken
- **State Verification**: Check S:W:H:E values
- **Context Validation**: Verify work folder/session
- **Dependencies**: Confirm all dependencies available

### Level 3: System Investigation
- **Template Integrity**: Verify templates not corrupted
- **Path Resolution**: Check file paths are correct
- **Permission Issues**: Verify file access rights
- **Environment State**: Check system resources

## Common Issues & Solutions

### Handler-Related Issues
| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| "Can't find handler" | Registry search failed | Search variations, check templates/patterns/ |
| "Handler incomplete" | Partial handler loaded | Use similar handler as template |
| "Handler outdated" | Version mismatch | Check handler version field |
| "Handler conflict" | Multiple matches | Use most specific match |

### Tool-Related Issues
| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| "Wrong tool used" | Tool matrix not checked | Always check tool matrix first |
| "Tool not available" | Missing dependency | Check tool requirements |
| "Tool failed" | Parameter issue | Verify parameter format |
| "Tool timeout" | Performance issue | Retry with smaller scope |

### Convention-Related Issues
| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| "Convention violated" | Rules not checked | Stop and check templates/conventions/ |
| "Format invalid" | Wrong structure | Review format requirements |
| "Naming conflict" | Convention ignored | Follow naming standards |
| "State inconsistent" | Update missed | Sync state files |

### Uncertainty Issues
| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| "Not sure what to do" | Ambiguous request | Ask user for specific guidance |
| "Multiple options" | No clear path | Present options to user |
| "Missing context" | Incomplete information | Request additional details |
| "Conflicting requirements" | Logic issue | Clarify priorities |

## Debug Output Format

### Structured Debug Report
```
DEBUG REPORT
============
Timestamp: [ISO-8601]
Request: [Original user request]
Intent: [Detected intent]

Execution Trace:
1. [Step taken] → [Result]
2. [Step taken] → [Result]
3. [Step taken] → [FAILURE POINT]

Failure Analysis:
- Expected: [What should have happened]
- Actual: [What actually happened]
- Cause: [Root cause if known]

Context:
- Session: [S value]
- Work: [W value]
- Handler: [H value]
- Evidence: [E value]

Recovery Attempted:
- [Action 1]: [Result]
- [Action 2]: [Result]

Recommendation:
[Suggested fix or workaround]
```

## Debug Logging

### What to Log
- All handler searches and results
- Template loading attempts
- Tool invocations and parameters
- State changes
- Error messages
- Recovery attempts

### Log Entry Format
```
[LEVEL] [Timestamp] [Component] [Action] [Result]
  Context: S:W:H:E values
  Details: Additional information
  Error: If applicable
```

### Log Levels
- **ERROR**: System failure, cannot continue
- **WARN**: Issue encountered, degraded operation
- **INFO**: Normal operation, key decisions
- **DEBUG**: Detailed trace for investigation

## Root Cause Analysis

### Common Root Causes
1. **Missing Handler**: Request type not covered
2. **Ambiguous Intent**: Unclear user request
3. **Tool Limitation**: Tool cannot perform action
4. **State Corruption**: Invalid system state
5. **Convention Conflict**: Rules contradiction

### Investigation Method
```
1. Reproduce issue consistently
2. Isolate failing component
3. Check assumptions
4. Verify dependencies
5. Test alternatives
6. Document findings
```

## Performance Debugging

### Slow Operations
- Check search scope (too broad?)
- Verify file sizes (too large?)
- Review handler complexity (too many steps?)
- Check tool efficiency (better alternative?)

### Resource Issues
- Memory usage (large files?)
- File handles (leaks?)
- Network calls (timeouts?)
- CPU usage (infinite loops?)

## Prevention Through Debugging

### Learning from Failures
1. **Document**: Record all debugging sessions
2. **Pattern**: Identify recurring issues
3. **Improve**: Update handlers/conventions
4. **Test**: Verify fixes work
5. **Share**: Update documentation

### Proactive Debugging
- Add validation checks
- Improve error messages
- Create test cases
- Monitor performance
- Regular audits

## Quick Debug Commands

### Essential Checks
```bash
# Check handler exists
mcp__serena__search_for_pattern --substring_pattern "id: [handler-name]" --relative_path "templates/"

# Verify file structure
ls -la templates/handlers/

# Check recent changes
git status templates/

# Validate YAML frontmatter
grep -A 10 "^---" [handler-file]
```

## When All Else Fails

### Escalation Path
1. Document exact failure with debug report
2. Check if known issue in documentation
3. Try minimal working example
4. Ask for user guidance with options
5. Create work item for fix

### Recovery Mode
```
"I've encountered an issue with [specific problem].
 
What I tried:
- [Attempt 1]
- [Attempt 2]

Options:
1. [Alternative approach]
2. [Simplified version]
3. [Manual workaround]

Which would you prefer, or would you like me to try something else?"
```

## Progress Log

- **2026-04-22 16:00** — [S:20260422|W:task91-standardize-template-metadata|H:templates/engine/debugging/system-debug.md|E:templates/metadata/template-metadata-policy.json] Added canonical metadata during the Task 91 engine-module standardization slice
