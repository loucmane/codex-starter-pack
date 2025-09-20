---
id: context-to-mode-matrix
type: decision-matrix
category: routing
usage: Determines operational mode based on context signals
version: 1.0.0
---

# Context → Mode Matrix

Maps context signals to operational modes for appropriate behavior activation.

## Input
Context signals from user request or current activity

## Output
Mode to activate, expected behavior, and examples

## Matrix

| Context Signals | Mode | Behavior | Examples |
|----------------|------|----------|----------|
| "implement", "build", "fix" | Development Mode | Full template system | "implement search" |
| "test", "debug", "check" | Testing Mode | Evidence gathering | "test the feature" |
| "commit", "push", "PR" | Git Mode | Convention enforcement | "commit changes" |
| "search", "find", "where" | Search Mode | Tool selection matrix | "find the bug" |
| "how", "why", "explain" | Analysis Mode | Code examination | "how does it work" |
| "optimize", "improve" | Performance Mode | Profiling first | "optimize queries" |
| "secure", "vulnerability" | Security Mode | Threat analysis | "secure the API" |
| "deploy", "release" | Deployment Mode | Checklist execution | "deploy to prod" |
| "weather", "chat", general | Natural Mode | Skip all protocols | "how's the weather" |
| "document", "readme" | Documentation Mode | Markdown conventions | "document this" |
| "refactor", "clean up" | Refactoring Mode | Test preservation | "refactor auth" |
| "review", "feedback" | Review Mode | Critical analysis | "review my code" |
| "setup", "install" | Setup Mode | Environment check | "setup the project" |
| "monitor", "alert" | Monitoring Mode | Metrics focus | "monitor performance" |
| "rollback", "revert" | Recovery Mode | Safe procedures | "rollback deploy" |
| "plan", "design" | Planning Mode | Architecture focus | "plan the feature" |
| "profile", "benchmark" | Profiling Mode | Performance metrics | "profile the app" |
| "backup", "restore" | Maintenance Mode | Data safety | "backup database" |
| "migrate", "upgrade" | Migration Mode | Safe transitions | "migrate to v2" |
| "trace", "log" | Debugging Mode | Detailed logging | "trace the request" |

## Mode Characteristics

### Development Mode
- Full template system activated
- Work tracking enabled
- Convention enforcement strict
- Tool selection automatic

### Testing Mode
- Evidence gathering primary
- Test checkpoints created
- Validation emphasized
- User testing included

### Natural Mode
- All protocols skipped
- Natural conversation
- No template loading
- Direct responses

### Git Mode
- Convention strict enforcement
- Format validation required
- Commit message standards
- Branch management rules

## Mode Selection Rules

1. **Priority Order**: Most specific signal wins
2. **Multiple Signals**: Higher priority mode activates
3. **Default**: Natural mode when no signals detected
4. **Switching**: Explicit mode change requires confirmation

## Mode Transitions

- Natural → Development: Any dev keyword
- Development → Testing: Test command
- Testing → Git: Commit request
- Any → Natural: Explicit casual topic
- Emergency → Recovery: Error detection