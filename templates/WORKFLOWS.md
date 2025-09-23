
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.
# Universal Development Workflows

**Status**: ✅ MODULARIZED - All workflow components have been extracted to `templates/workflows/`

> **Migration Complete**: This file now serves as an index to the modular workflow system.
> - **Handlers**: Migrated to `templates/handlers/`
> - **Workflows**: Modularized in `templates/workflows/`
> - **Date**: 2025-08-08

## 📁 Module Organization

### Core Components
- **[ULTRATHINK Reference](workflows/core/ultrathink-reference.md)** - Foundation of all workflows
- **[Universal Flight Protocol](workflows/protocols/universal-flight.md)** - Pre/during/post checks

### Workflow Patterns
- **[Task Management](workflows/patterns/task-management.md)** - TodoWrite patterns
- **[Multi-Agent Orchestration](workflows/patterns/multi-agent-orchestration.md)** - Specialist deployment

### Session & Memory
- **[Session Lifecycle](workflows/session/lifecycle.md)** - sessions/ management
- **[Context Compaction](workflows/session/compaction.md)** - Handling long contexts
- **[Serena Patterns](workflows/memory/serena-patterns.md)** - Memory management

### Analysis & Testing
- **[Evidence Gathering](workflows/analysis/evidence-gathering.md)** - Evidence-based analysis
- **[Simulation Testing](workflows/testing/simulation-testing.md)** - Test workflows
- **[Test Checkpoints](workflows/testing/test-checkpoints.md)** - User testing
- **[Subagent Testing](workflows/testing/subagent-simulation.md)** - Specialist simulation

### Templates & Examples
- **[Behavioral Templates](workflows/templates/behavioral-templates.md)** - Common sequences
- **[Intent Handlers](workflows/handlers/intent-handlers.md)** - User intent routing
- **[Common Workflows](workflows/examples/common-workflows.md)** - Real examples

### Guides
- **[Common Mistakes](workflows/guides/common-mistakes.md)** - What to avoid

## 🚀 Quick Start

### For New Sessions
1. Start with [Session Lifecycle](workflows/session/lifecycle.md)
2. Follow [Universal Flight Protocol](workflows/protocols/universal-flight.md)
3. Use [Task Management](workflows/patterns/task-management.md) for todos

### For Development Work
1. Check [Intent Handlers](workflows/handlers/intent-handlers.md) for routing
2. See [Common Workflows](workflows/examples/common-workflows.md) for patterns
3. Apply [Behavioral Templates](workflows/templates/behavioral-templates.md)

### For Testing
1. Create [Test Checkpoints](workflows/testing/test-checkpoints.md)
2. Run [Simulation Testing](workflows/testing/simulation-testing.md)
3. Deploy [Subagent Testing](workflows/testing/subagent-simulation.md) if needed

## 🔍 Finding Specific Workflows

### By Task Type
- **Starting work**: See [Intent Handlers](workflows/handlers/intent-handlers.md#start-new-work)
- **Managing tasks**: See [Task Management](workflows/patterns/task-management.md)
- **Ending session**: See [Session Lifecycle](workflows/session/lifecycle.md#end-of-session)

### By Problem
- **Context too long**: See [Context Compaction](workflows/session/compaction.md)
- **Need evidence**: See [Evidence Gathering](workflows/analysis/evidence-gathering.md)
- **Common errors**: See [Common Mistakes](workflows/guides/common-mistakes.md)

## 📚 See Also

- **[CONVENTIONS.md](CONVENTIONS.md)** - Git aliases and code standards
- **[TOOLS.md](TOOLS.md)** - MCP tool configurations
- **[CLAUDE-NEW.md](CLAUDE-NEW.md)** - Quick navigation hub
- **[Registry](registry/index.md)** - Modular handler registry
- **[BUILDING-BETTER.md](BUILDING-BETTER.md)** - How to evolve this system

---

*Original 2,943-line workflow document has been modularized for better maintainability and navigation.*