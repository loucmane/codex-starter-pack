# System Patterns Library

This file has been modularized. All patterns are now in `templates/patterns/`

> ⚠️ **HANDLERS MIGRATED**: All handlers from this file have been migrated to `templates/handlers/`
> 
> **PATTERNS MODULARIZED**: All patterns have been extracted to `templates/patterns/`

## 📁 Module Organization

### Routing Patterns
- [Meta-Routing](patterns/routing/meta-routing.md) - High-level routing decisions and ULTRATHINK
- [Request Analysis](patterns/routing/request-analysis.md) - Request parsing and ambiguity resolution
- [Intent Detection](patterns/routing/intent-detection.md) - Understanding user intent

### Selection Patterns
- [Handler Selection](patterns/selection/handler-selection.md) - Choosing the right handler
- [Tool Selection](patterns/selection/tool-selection.md) - Tool choice patterns and matrix reference
- [Agent Selection](patterns/selection/agent-selection.md) - Selecting specialist agents

### Evidence Patterns
- [Evidence Collection](patterns/evidence/evidence-patterns.md) - Methods for gathering evidence
- [Validation](patterns/evidence/validation-patterns.md) - Validation approaches and methods
- [Proof Requirements](patterns/evidence/proof-patterns.md) - Standards for sufficient proof

### Work Tracking Patterns
- [Work Patterns](patterns/work-tracking/work-patterns.md) - Work organization and tracking
- [Progress Tracking](patterns/work-tracking/progress-patterns.md) - Measuring and reporting progress
- [Documentation](patterns/work-tracking/documentation-patterns.md) - Documentation creation patterns

### Session Patterns
- [Session Management](patterns/session/session-patterns.md) - Managing development sessions
- [State Tracking](patterns/session/state-patterns.md) - State management approaches
- [Continuation](patterns/session/continuation-patterns.md) - Resuming and continuing work

### Integration Patterns
- [Cross-System](patterns/integration/cross-system.md) - System integration patterns
- [Composition](patterns/integration/composition.md) - Combining patterns strategically

## 🔗 Shared Patterns

Some patterns are used across multiple systems and are stored in shared locations:
- [ULTRATHINK Format](shared/patterns/ultrathink-format.md) - Core ULTRATHINK protocol
- [Tool Selection Matrix](shared/tools/tool-selection-matrix.md) - Comprehensive tool mappings

## 📚 Quick Reference

### By Complexity
**Simple Patterns:**
- Tool Selection
- Time Capture
- Evidence Check

**Moderate Patterns:**
- Request Analysis
- Handler Selection
- Session Management

**Complex Patterns:**
- Meta-Routing
- Cross-System Integration
- Pattern Composition

### By Frequency of Use
**Most Used:**
- Tool Selection
- Handler Selection
- Work Patterns

**Frequently Used:**
- Evidence Collection
- Session Management
- Request Analysis

**Specialized:**
- Pattern Composition
- Cross-System Integration
- Agent Selection

## 🚀 Handler Migration Notice

All handlers previously in this file have been migrated to:
- `templates/handlers/triggers/` - User-triggered handlers
- `templates/handlers/orchestrators/` - Coordination handlers
- `templates/handlers/operators/` - Task execution handlers

For handler documentation, see: [REGISTRY.md](REGISTRY.md)

## 📖 Using This Library

1. **Browse patterns** by category above
2. **Each pattern** includes:
   - When to use/not use
   - Pattern structure
   - Examples
   - Related patterns
3. **Patterns are approaches**, not specific implementations
4. **Handlers implement** these patterns

---

*Last updated: 2025-08-08*
*Version: 2.0.0 (Modularized)*