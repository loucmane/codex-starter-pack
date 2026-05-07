---
id: cannot-proceed
title: Enforcement Mechanisms
type: engine-component
status: stable
priority: critical
dependencies:
  - templates/conventions/
  - templates/workflows/
  - templates/TOOLS.md
  - templates/BEHAVIORS.md
  - behavioral-hooks
exports:
  - enforcement-gates
  - natural-execution
  - cannot-proceed-rules
---

# ENFORCEMENT MECHANISMS

## Cannot Proceed Without Gates

These enforcement gates create hard stops that prevent protocol violations:

1. **File Edit** → Convention check first
   - MUST read existing file before editing
   - MUST check templates/conventions/ for file-specific rules
   - MUST validate naming conventions
   - Gate: Edit tool fails without prior Read

2. **Implementation** → Workflow loaded
   - MUST find and load relevant workflow handler
   - MUST follow handler Process steps in order
   - MUST validate each step completion
   - Gate: No code written without workflow context

3. **Tool Use** → Correct tool verified
   - MUST check tool selection matrix
   - MUST use Serena for code search, Grep for text
   - MUST use appropriate tool for file type
   - Gate: Tool selection validated before execution

4. **Claims** → Evidence gathered
   - MUST provide file paths and line numbers
   - MUST show actual code/output as proof
   - MUST verify claims with tool outputs
   - Gate: No assertions without evidence

5. **Commits** → Format and execution mode validated
   - MUST use `direct-git-execution` when Git/GitHub work is delegated and auth is available
   - MUST use `full-gac-command` only when the user explicitly asks for "the gac"
   - MUST use `message-payload-only` only for message-only requests
   - MUST use `auth-refresh-required` when SSH/GPG cache is expired
   - MUST check conventional commit types and include scope when applicable
   - Gate: Commit rejected if format or execution mode is invalid

6. **Timestamps** → Actual time checked (date command)
   - MUST run date command for current time
   - MUST use actual output, never estimate
   - MUST format consistently (HH:MM)
   - Gate: No timestamp without date command

## Natural Execution

Instead of "I should check templates", these become "I cannot proceed without checking" - making template usage automatic and unavoidable.

### The Transformation

**OLD WAY**: "Check templates" → Often skipped
**NEW WAY**: "Cannot proceed without templates" → Always happens

Like syntax checking - I can't write invalid code, and now I can't skip template checks.

### Implementation

Each gate is implemented through:
- **Tool constraints**: Tools fail without prerequisites
- **Handler dependencies**: Steps require prior validations
- **Behavioral hooks**: Actions trigger automatic checks
- **Protocol echoes**: Must state protocol to proceed

### Self-Reinforcing System

The enforcement mechanisms are self-reinforcing:
- To state a protocol, must find it first
- To find it, must read the template
- To proceed, must satisfy the gate
- Gates create natural workflow compliance

## Progress Log

- **2026-04-22 16:00** — [S:20260422|W:task91-standardize-template-metadata|H:templates/engine/enforcement/cannot-proceed.md|E:templates/metadata/template-metadata-policy.json] Added canonical metadata during the Task 91 engine-module standardization slice
