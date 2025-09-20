# Claude Execution Engine - Modular Components

This directory contains the modularized components of the Claude AI Execution Engine, extracted from the monolithic CLAUDE.md file for better maintainability and organization.

## Directory Structure

```
templates/engine/
├── README.md                    # This file
├── verify-phase1.sh            # Phase 1 verification script
│
├── core/                       # Core engine components (Phase 3)
│   ├── execution-engine.md    # Lines 1-17 from CLAUDE.md
│   ├── enforcement-check.md   # Lines 9-17 from CLAUDE.md
│   ├── ultrathink-protocol.md # Lines 19-46 from CLAUDE.md
│   └── pre-ultrathink.md      # Lines 37-46 from CLAUDE.md
│
├── activation/                 # Context activation (Phase 2)
│   ├── context-aware.md       # Lines 48-93 from CLAUDE.md
│   ├── mode-detection.md      # Lines 50-56 from CLAUDE.md
│   └── triggers/              # Trigger types
│       ├── explicit.md        # Lines 58-70 from CLAUDE.md
│       ├── implicit.md        # Lines 71-80 from CLAUDE.md
│       ├── behavioral.md      # Lines 81-86 from CLAUDE.md
│       └── protocol-echo.md   # Lines 87-91 from CLAUDE.md
│
├── execution/                  # Execution mechanics (Phase 2)
│   ├── swhe-format.md         # Lines 99-135 from CLAUDE.md
│   ├── handler-validation.md  # Lines 110-120 from CLAUDE.md
│   └── evidence-based.md      # Lines 122-132 from CLAUDE.md
│
├── navigation/                 # Navigation and routing
│   ├── common-flows.md ✓      # Lines 218-256 from CLAUDE.md (Phase 1)
│   ├── template-protocol.md   # Lines 159-195 from CLAUDE.md (Phase 2)
│   └── handler-loading.md     # Lines 165-180 from CLAUDE.md (Phase 2)
│
├── structure/                  # System structure documentation
│   └── template-system.md ✓   # Lines 258-307 from CLAUDE.md (Phase 1)
│
├── enforcement/                # Enforcement mechanisms (Phase 3)
│   ├── cannot-proceed.md      # Lines 308-319 from CLAUDE.md
│   └── natural-execution.md   # Lines 297-310 from CLAUDE.md
│
├── examples/                   # Practical examples
│   └── practical.md ✓         # Lines 321-362 from CLAUDE.md (Phase 1)
│
└── fallbacks/                  # Error handling (Phase 2)
    └── error-handling.md       # Lines 364-436 from CLAUDE.md
```

## Migration Status

### Phase 1 - Low Risk (COMPLETE ✓)
- [x] `examples/practical.md` - Practical execution examples
- [x] `navigation/common-flows.md` - Common request routing flows  
- [x] `structure/template-system.md` - Template system architecture

### Phase 2 - Medium Risk (PENDING)
- [ ] `activation/` - Context-aware activation system
- [ ] `execution/` - Development mode execution
- [ ] `navigation/template-protocol.md` - Template navigation protocol
- [ ] `fallbacks/` - Error handling and fallbacks

### Phase 3 - High Risk (PENDING)
- [ ] `core/` - Critical execution engine components
- [ ] `enforcement/` - Enforcement mechanisms

## Module Format

Each module follows this standard format:

```yaml
---
id: unique-module-id
type: engine-component
dependencies:
  - list of required modules
  - or template files
exports:
  - list of exported functions
  - or patterns
---

# Module Title

Module content...
```

## Integration with CLAUDE.md

The main CLAUDE.md file references these modules using HTML comments:

```markdown
<!-- Module: Description of module -->
<!-- Import: templates/engine/path/to/module.md -->
See `templates/engine/path/to/module.md` for details
```

## Usage

These modules are automatically loaded by the Claude execution engine when processing requests. The modular structure allows for:

1. **Better maintainability** - Each component has a single responsibility
2. **Easier updates** - Changes to one module don't affect others
3. **Clear dependencies** - YAML frontmatter shows what each module needs
4. **Improved testing** - Individual modules can be validated independently

## Testing

Run the verification script to ensure all modules are properly structured:

```bash
chmod +x templates/engine/verify-phase1.sh
templates/engine/verify-phase1.sh
```

## Next Steps

1. Complete Phase 2 medium-risk extractions
2. Test handler discovery through module references
3. Validate ULTRATHINK protocol execution
4. Complete Phase 3 high-risk core component extraction
5. Update all cross-references in template system

---
*Last Updated: 2025-08-07*
*Phase 1 Complete*