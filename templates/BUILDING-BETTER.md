# Building Better: System Extension Guide

This file has been modularized. All integration guides are now in `templates/integration/`

## 📁 Module Organization

### Development Guides
- [Creating Handlers](integration/guides/creating-handlers.md) - Complete handler creation guide
- [Extending Templates](integration/guides/extending-templates.md) - Template system extension
- [Adding Agents](integration/guides/adding-agents.md) - New agent integration
- [System Integration](integration/guides/system-integration.md) - Overall integration guide

### Cross-System Integration  
- [MCP Integration](integration/cross-system/mcp-integration.md) - MCP tool integration
- [Tool Integration](integration/cross-system/tool-integration.md) - Adding and using tools
- [Agent Coordination](integration/cross-system/agent-coordination.md) - Multi-agent patterns

### Composition Patterns
- [Workflow Composition](integration/composition/workflow-composition.md) - Complex workflows
- [Handler Chaining](integration/composition/handler-chaining.md) - Chain handlers effectively
- [Pattern Composition](integration/composition/pattern-composition.md) - Combine patterns

### Best Practices
- [Handler Design](integration/best-practices/handler-design.md) - Design principles
- [Template Design](integration/best-practices/template-design.md) - Template best practices
- [Integration Patterns](integration/best-practices/integration-patterns.md) - Integration tips

### Architecture Documentation
- [System Architecture](integration/architecture/system-architecture.md) - Overall system design
- [Handler Architecture](integration/architecture/handler-architecture.md) - Handler system design
- [Template Architecture](integration/architecture/template-architecture.md) - Template system design

## 🚀 Quick Start

1. **New to handler creation?** Start with [Creating Handlers](integration/guides/creating-handlers.md)
2. **Designing handlers?** Review [Handler Design](integration/best-practices/handler-design.md)
3. **Need examples?** Check existing handlers in `templates/handlers/`
4. **System overview?** Read [System Architecture](integration/architecture/system-architecture.md)

## 📚 Learning Path

### For Handler Developers
1. [Creating Handlers](integration/guides/creating-handlers.md)
2. [Handler Design](integration/best-practices/handler-design.md)
3. [Handler Chaining](integration/composition/handler-chaining.md)
4. [Handler Architecture](integration/architecture/handler-architecture.md)

### For System Architects
1. [System Architecture](integration/architecture/system-architecture.md)
2. [Template Architecture](integration/architecture/template-architecture.md)
3. [Integration Patterns](integration/best-practices/integration-patterns.md)
4. [Pattern Composition](integration/composition/pattern-composition.md)

### For Template Extenders
1. [Extending Templates](integration/guides/extending-templates.md)
2. [Template Design](integration/best-practices/template-design.md)
3. [System Integration](integration/guides/system-integration.md)
4. [Workflow Composition](integration/composition/workflow-composition.md)

## 🔄 Migration Notice

### What Changed
- All detailed content moved to modular files in `integration/`
- This file now serves as an index and navigation hub
- Content organized by category for better discovery
- Each module has complete YAML frontmatter

### Handler Migration
All handlers previously in this file have been migrated to:
- `templates/handlers/triggers/` - User-activated handlers
- `templates/handlers/orchestrators/` - Coordination handlers  
- `templates/handlers/operators/` - Technical operation handlers

See the [migration mapping](../../agent-outputs/template-migrator/migration-mapping.md) for details.

## 📖 Key Concepts

### Handler Roles
- **Triggers**: Respond to user commands
- **Orchestrators**: Coordinate complex workflows
- **Operators**: Perform specific technical tasks

### Domains
- **development**: Code implementation
- **git**: Version control
- **search**: Finding code/patterns
- **debug**: Problem investigation
- **test**: Testing and validation
- **docs**: Documentation
- **workflow**: Process management

## 🎯 Meta-Process

This modular structure itself demonstrates the evolution of the template system:
1. Started as monolithic CLAUDE.md (1400+ lines)
2. Split into template files
3. Handlers extracted to folders
4. Guides modularized into integration/

Each phase improved maintainability, discoverability, and extensibility.

---

*For the original monolithic content, see version history. The journey from monolithic to modular is documented in [System Architecture](integration/architecture/system-architecture.md).*

## ULTRATHINK Integration {#ultrathink-integration}

This file participates in the ULTRATHINK system:

### VOID Resolution
- **S = VOID** → See [resolve-session-void](CONVENTIONS.md#resolve-session-void)
- **W = VOID** → See [resolve-work-void](WORKFLOWS.md#resolve-work-void)
- **H = VOID** → See [resolve-handler-void](REGISTRY.md#resolve-handler-void)

### Integration Handler Requirements
Cross-system integration handlers in this file manage transitions between different parts of the template system, ensuring valid [S:W:H] context is maintained.

## 🎯 The Journey {#the-journey}

### From Chaos to Clarity {#from-chaos-to-clarity}

The Claude Template System emerged from a 1400+ line monolithic CLAUDE.md file that had grown organically. The journey to modular clarity taught us valuable lessons about documentation evolution.

### Key Evolutionary Steps {#key-evolutionary-steps}

1. **Recognition** - "This is too big to navigate"
2. **Analysis** - Content mapping revealed natural categories
3. **Experimentation** - Tried different organizational approaches
4. **Refinement** - User feedback drove improvements
5. **Integration** - Unified disparate ideas into cohesive system

## 📚 Lessons Learned {#lessons-learned}

### 1. User Reality Drives Design {#user-reality-drives-design}

**Initial Assumption**: AI handles everything autonomously
**Reality Check**: User performs testing, needs interaction points
**Evolution**: Added explicit testing checkpoints throughout workflow

This teaches us: Always validate assumptions against actual usage patterns.

### 2. Progressive Complexity {#progressive-complexity}

**Initial Design**: Complex scoring system (1-5 complexity ratings)
**User Feedback**: "Why not make delegation the default?"
**Evolution**: Natural value-based decisions, progressive enhancement

This teaches us: Start with the advanced pattern if it's actually simpler.

### 3. Context Window as Feature {#context-window-as-feature}

**Initial Concern**: Delegation wastes context
**Realization**: Fresh context per specialist improves quality
**Evolution**: Delegation-first approach optimizes context usage

This teaches us: Constraints can become advantages with right framing.

### 4. Natural Language Over Formulas {#natural-language-over-formulas}

**Initial**: `if (complexity > 3) { deploy_specialist() }`
**Evolution**: "This needs UI expertise" → Deploy UI specialist
**Result**: More intuitive, flexible, learnable system

This teaches us: Human-readable patterns beat algorithmic ones.

## 🔄 Evolution Patterns {#evolution-patterns}

### Pattern 1: Extraction and Enhancement {#extraction-and-enhancement}

When extracting content from monolithic docs:

1. **Map Everything First**
   - Create content-mapping.md
   - Identify natural categories
   - Note cross-references needed

2. **Extract Verbatim**
   - Copy content exactly first
   - Preserve all information
   - Maintain formatting

3. **Enhance Thoughtfully**
   - Add organization only where helpful
   - Improve examples based on learning
   - Integrate new insights naturally

### Pattern 2: Feedback Integration {#feedback-integration}

When users provide feedback:

1. **Listen for Underlying Need**
   - "Why are we doing X?" often means "Y would be better"
   - Example: "Why sequential?" led to discovering testing needs

2. **Prototype Quickly**
   - Show how it would work
   - Get confirmation before full implementation
   - Iterate based on response

3. **Document the Why**
   - Capture reasoning for future understanding
   - Helps others learn from journey
   - Prevents regression

### Pattern 3: Unification Over Addition {#unification-over-addition}

When adding new features:

1. **Seek Integration**
   - Can this enhance existing patterns?
   - Example: Orchestration became part of standard workflow

2. **Avoid Modal Thinking**
   - Not "orchestration mode" vs "normal mode"
   - Instead: Progressive enhancement within one flow

3. **Simplify Activation**
   - From: Complex commands and modes
   - To: Natural progression based on task needs

## 🛠️ Improvement Framework {#improvement-framework}

### How to Evolve the System {#how-to-evolve-system}

1. **Identify Pain Points**
   ```yaml
   Questions to Ask:
     - What takes too long to find?
     - What requires too much context?
     - What patterns repeat unnecessarily?
     - Where do users get confused?
   ```

2. **Propose Solutions**
   ```yaml
   Evaluation Criteria:
     - Does it simplify usage?
     - Does it preserve all capabilities?
     - Is it discoverable?
     - Can it be explained simply?
   ```

3. **Test with Examples**
   ```yaml
   Validation Steps:
     - Try the new pattern on real tasks
     - Compare before/after workflow
     - Get user feedback
     - Measure actual improvement
   ```

4. **Document Changes**
   ```yaml
   Required Documentation:
     - What changed and why
     - Migration path from old pattern
     - New examples
     - Updated cross-references
   ```

## 🎯 Meta-Patterns {#meta-patterns}

### The Pattern of Patterns {#pattern-of-patterns}

Good patterns share characteristics:

1. **Natural Language** - Describable without formulas
2. **Progressive** - Simple case simple, complex case possible
3. **Discoverable** - Users find them without instruction
4. **Composable** - Work together without conflict
5. **Memorable** - Stick after single exposure

### Documentation Principles {#documentation-principles}

1. **Show, Don't Tell**
   - Examples > Explanations
   - Real workflows > Abstract concepts

2. **Organize by Usage**
   - Group by when/how used
   - Not by technical category

3. **Cross-Reference Liberally**
   - No dead ends
   - Multiple paths to same info

4. **Evolve Continuously**
   - Documentation is living
   - Capture learnings immediately
   - Preserve iteration history (append, don't overwrite)
   - Track what didn't work and why

## 🚀 Future Evolution Ideas {#future-evolution-ideas}

### Potential Improvements {#potential-improvements}

1. **Smart Parallel Processing**
   - Track subtask dependencies automatically
   - Identify parallelization opportunities
   - Maintain quality through testing checkpoints

2. **Learning System**
   - Track pattern success rates
   - Personalize to user preferences
   - Suggest optimizations

3. **Template Generation**
   - Auto-generate from patterns
   - Project-specific customization
   - Version management

### How to Contribute Improvements {#how-to-contribute}

1. **Document Current Pain**
   - What specific task is difficult?
   - How long does it take?
   - What would ideal look like?

2. **Prototype Solution**
   - Create minimal example
   - Test on real scenario
   - Measure improvement

3. **Share Learning**
   - Update relevant template file
   - Add to EVOLUTION.md
   - Create memory for context

## 📊 Success Metrics {#success-metrics}

### How We Know It's Better {#how-we-know-better}

1. **Time to Task** - How quickly can someone start working?
2. **Error Rate** - How often do mistakes happen?
3. **Discovery** - Can users find what they need?
4. **Adoption** - Do people actually use the patterns?
5. **Evolution** - Does system improve over time?

### Current State (After Phase 3) {#current-state}

- ✅ Modular structure implemented
- ✅ User testing integrated
- ✅ Natural delegation patterns
- ✅ Unified workflow achieved
- 🔄 Ready for real-world testing

## 🔍 Meta-Process for Meta-Process {#meta-process-for-meta-process}

Even this document should evolve. When improving it:

1. **Add Real Examples** - From actual system evolution
2. **Capture Failures** - What didn't work and why
3. **Link Changes** - To specific commits/sessions
4. **Stay Concrete** - Avoid abstract meta-discussion

## Cross-System Integration Handlers {#cross-system-integration-handlers}

These handlers manage interactions between different parts of the template system.

### Handler Interconnections {#handler-interconnections}

#### Handler: workflow-to-tool {#workflow-to-tool}
**Triggers**: Workflow step requires specific tool
**Target Pattern**: Tool needed within workflow context
**Pre-conditions**: 
- Active workflow in progress
- Tool requirement identified
**Process**:
1. Identify required tool capability
2. Route to TOOLS.md tool selection
3. Execute tool with workflow context
4. Return results to workflow
**Success**: Tool completes, workflow continues
**Failure**: Suggest alternative tools or manual steps
**Examples**:
- Bug fix workflow needs search → Routes to search-code handler
- Refactoring needs symbol analysis → Routes to find-references

#### Handler: tool-to-convention {#tool-to-convention}
**Triggers**: Tool usage must follow conventions
**Target Pattern**: Convention check needed before tool use
**Pre-conditions**: 
- Tool selected for use
- Conventions apply to operation
**Process**:
1. Identify applicable conventions
2. Route to CONVENTIONS.md checks
3. Validate tool parameters
4. Execute with convention compliance
**Success**: Tool runs with proper conventions
**Failure**: Show convention violations, correct and retry
**Examples**:
- Git commit → Check commit message conventions
- File naming → Validate naming standards

#### Handler: convention-to-workflow {#convention-to-workflow}
**Triggers**: Convention violation requires workflow
**Target Pattern**: Fix process needed for violation
**Pre-conditions**: 
- Convention violation detected
- Workflow exists for correction
**Process**:
1. Identify violation type
2. Route to correction workflow
3. Guide through fix process
4. Verify convention compliance
**Success**: Violation corrected via workflow
**Failure**: Manual intervention needed
**Examples**:
- Wrong timestamp format → Route to timestamp workflow
- Missing evidence → Route to evidence gathering

### State Management Handlers {#state-management-handlers}

#### Handler: save-context {#save-context}
**Triggers**: "save state", "checkpoint progress", switching tasks
**Target Pattern**: Current state needs preservation
**Pre-conditions**: 
- Active work in progress
- State worth preserving
**Process**:
1. Gather current context (todos, files, decisions)
2. **PRIMARY**: Update work tracking files
3. **FALLBACK**: Create memory snapshot
4. Mark resumption point
**Success**: State saved for easy resume
**Failure**: Partial save with warnings
**Examples**:
- Before switching tasks → Save to handoff.md
- Mid-session checkpoint → Update tracker.md

#### Handler: restore-context {#restore-context}
**Triggers**: "resume work", "continue from", "pick up where"
**Target Pattern**: Previous state to restore
**Pre-conditions**: 
- Saved state exists
- No conflicting active work
**Process**:
1. **PRIMARY**: Read work folder files
2. Load todos and progress
3. Restore file context
4. Show last actions
**Success**: Context restored, ready to continue
**Failure**: Partial restore, need user guidance
**Examples**:
- "continue yesterday's work" → Load from work folder
- "resume feature X" → Restore full context

#### Handler: switch-context {#switch-context}
**Triggers**: "work on something else", "switch to", "pause this"
**Target Pattern**: Change from one context to another
**Pre-conditions**: 
- Current context active
- Target context identified
**Process**:
1. Execute save-context for current
2. Clear active todos
3. Load target context
4. Confirm switch complete
**Success**: Clean context switch
**Failure**: Rollback to previous context
**Examples**:
- "switch to bug fix" → Save feature, load bug context
- "work on PR instead" → Full context swap

## Creating and Managing Handlers {#creating-handlers}

This section contains guides for creating new handlers and maintaining handler documentation standards.

### Handler Documentation Format Standard {#handler-documentation-standard}

Every handler MUST include these 8 sections in this exact order:

```markdown
#### Handler: handler-name {#handler-name}
**Triggers**: Comma-separated list of exact phrases that activate this handler
**Target Pattern**: What the handler extracts or acts upon from user input
**Pre-conditions**: 
- Bulleted list of conditions that must be true
- Before this handler can execute successfully
**Process**:
1. Numbered steps the handler follows
2. Each step should be clear and actionable
3. Include specific tools or templates used
4. Show routing logic if applicable
5. End with concrete outcome
**Success**: What happens when handler completes successfully
**Failure**: What happens when handler cannot complete
**Examples**:
- Input phrase → Expected outcome
- Another example → Another outcome
```

#### Documentation Best Practices {#documentation-best-practices}

**DO:**
- ✅ Keep triggers realistic - what users actually say
- ✅ Make process steps concrete and actionable
- ✅ Include tool names when tools are used
- ✅ Show routing to templates/other handlers
- ✅ Make examples diverse to show handler range
- ✅ Use consistent formatting throughout

**DON'T:**
- ❌ Make triggers too abstract or technical
- ❌ Write vague process steps like "analyze the code"
- ❌ Skip pre-conditions - use "None" if none exist
- ❌ Write multi-line success/failure descriptions
- ❌ Use different formatting styles

### Handler Creation Guide {#handler-creation-guide}

#### When to Create a New Handler {#when-to-create}

Create a new handler when:
- Users repeatedly ask for something with no handler
- A common development task lacks a direct trigger
- Multiple users phrase the same need differently
- A workflow requires a specific entry point

#### Step-by-Step Creation Process {#creation-process}

1. **Identify the Need**
   - Verify no existing handler covers this need
   - Confirm users actually request this functionality
   - Ensure it would be used frequently
   - Check it's distinct from existing handlers

2. **Choose Handler Location**
   - **WORKFLOWS.md** - Development tasks, features, implementation
   - **TOOLS.md** - Tool selection and usage patterns
   - **CONVENTIONS.md** - Standards, validation, formatting
   - **PATTERNS.md** - Meta-routing, ambiguous requests
   - **BUILDING-BETTER.md** - Cross-system integration

3. **Write the Handler**
   - Follow the standard format exactly
   - Use realistic trigger phrases
   - Make process steps actionable
   - Include clear success/failure conditions

4. **Add to REGISTRY.md**
   ```markdown
   #### Handler: `handler-name` {#handler-name}
   - **Triggers**: Main trigger phrases
   - **Keywords**: [searchable, terms, discovery, words]
   - **Process**: One-line summary
   - **Location**: FILENAME.md#handler-name
   - **Template**: If routes to template, note here
   ```

5. **Test the Handler**
   - Test discovery via triggers
   - Verify anchor navigation works
   - Follow process steps manually
   - Confirm success/failure modes

6. **Integration**
   - Add cross-references from related handlers
   - Update routing handlers if needed
   - Add 5-10 discovery keywords
   - Document in CHANGELOG.md

#### Common Handler Patterns {#common-patterns}

**Feature Implementation:**
```markdown
#### Handler: implement-[feature] {#implement-feature}
**Triggers**: "implement X", "build Y feature", "add Z functionality"
**Target Pattern**: Feature specification
**Pre-conditions**: 
- Requirements clear
- Work folder exists
**Process**:
1. Break down into tasks
2. Create todos
3. Route to development workflow
**Success**: Feature implemented
**Failure**: Requirements unclear
```

**Tool Usage:**
```markdown
#### Handler: use-[tool] {#use-tool}
**Triggers**: "use X for Y", "run Z tool"
**Target Pattern**: Tool and purpose
**Pre-conditions**: 
- Tool available
- Purpose clear
**Process**:
1. Validate tool choice
2. Set parameters
3. Execute tool
4. Process results
**Success**: Tool completes task
**Failure**: Wrong tool for job
```

#### Validation Checklist {#validation-checklist}

Before committing your handler:
- [ ] Triggers are phrases users actually say
- [ ] Target pattern is clear
- [ ] Pre-conditions are verifiable
- [ ] Process steps are concrete
- [ ] Success/failure are single lines
- [ ] Examples show real usage
- [ ] Added to REGISTRY.md
- [ ] Keywords aid discovery
- [ ] Anchors work correctly
- [ ] No overlap with existing handlers
- [ ] Statistics updated
- [ ] Tests pass

### Enhanced Keywords Guide {#enhanced-keywords}

Keywords are critical for handler discovery. When adding keywords to REGISTRY.md:

1. **Think Like a User**
   - What words would they use?
   - Include common misspellings
   - Add domain-specific terms
   - Consider synonyms

2. **Keyword Categories**
   - **Action words**: create, build, make, implement
   - **Problem words**: bug, error, issue, broken
   - **Technical terms**: component, service, API, hook
   - **Emotional words**: stuck, confused, help, frustrated

3. **Keyword Density**
   - Aim for 5-10 keywords per handler
   - Balance specific and general terms
   - Include both technical and natural language

4. **Testing Keywords**
   - Search REGISTRY with each keyword
   - Verify handler appears in results
   - Check for keyword conflicts
   - Update if discovery fails

Remember: Handlers are only useful if users can find them!

## Key Takeaways {#key-takeaways}

1. **Listen to Users** - They know what works
2. **Evolution > Revolution** - Small improvements compound
3. **Simplicity Wins** - Complex systems fail
4. **Document Everything** - Future you will thank you
5. **Test Reality** - Assumptions kill good systems

---

Remember: The best system is one that improves itself through use. This document is the DNA for that evolution.