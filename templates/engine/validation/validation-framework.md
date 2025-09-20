---
name: validation-framework
type: enforcement
priority: critical
version: 1.0.0
dependencies:
  - enforcement-check
  - ultrathink-protocol
  - swhe-format
---

# Validation Framework

## Purpose
Define and enforce validation rules for ULTRATHINK protocol compliance across all modules.

## Validation Pipeline

### Stage 1: Pre-Execution Validation
**Timing:** Before any development work begins
**Enforcement:** HARD BLOCK (exit code 2)

```yaml
validators:
  - name: CLAUDE_MD_CHECK
    required: true
    validates:
      - "CLAUDE.md was consulted"
      - "Enforcement check module loaded"
      - "Development mode detected"
    on_failure: 
      action: block
      message: "Must process through CLAUDE.md first"
  
  - name: DEVELOPMENT_TRIGGER
    required: true
    validates:
      - "User request contains development signals"
      - "State file flags development mode"
    on_failure:
      action: continue  # Not a dev request
```

### Stage 2: Protocol Compliance
**Timing:** At response generation
**Enforcement:** HARD BLOCK

```yaml
validators:
  - name: ULTRATHINK_PRESENCE
    required: true
    pattern: "Let me ultrathink about this..."
    location: "Start of response"
    on_failure:
      action: block
      message: "ULTRATHINK protocol statement required"
      
  - name: SWHE_FORMAT
    required: true
    pattern: '\[S:(\d{8})\|W:([^|]+)\|H:([^|]+)\|E:([^\]]+)\]'
    validates:
      - "S: Valid session ID (YYYYMMDD)"
      - "W: Non-empty work context"
      - "H: Valid handler or 'searching'"
      - "E: Evidence or 'pending'"
    on_failure:
      action: block
      message: "Invalid S:W:H:E format"
      
  - name: HANDLER_VALIDATION
    required: true
    validates:
      - "Handler exists in REGISTRY.md"
      - "Handler appropriate for work type"
      - "Handler loaded before use"
    on_failure:
      action: block
      message: "Invalid or missing handler"
```

### Stage 3: Evidence Gathering
**Timing:** During work execution
**Enforcement:** WARNING → BLOCK

```yaml
validators:
  - name: EVIDENCE_TRAIL
    required: true
    validates:
      - "File paths for all changes"
      - "Line numbers for edits"
      - "Operation summaries"
      - "Error messages if encountered"
    format:
      file_paths: "/absolute/path/to/file"
      line_numbers: "L10-25"
      operations: "created|modified|deleted"
      status: "success|failed|partial"
    on_failure:
      action: warning_then_block
      warning_message: "Evidence incomplete"
      block_after: 2  # Block after 2 warnings
      
  - name: SEARCH_EVIDENCE
    required: when_handler_searching
    validates:
      - "Registry search performed"
      - "Search results shown"
      - "Handler selected from results"
    on_failure:
      action: block
      message: "Must show registry search when H:searching"
```

### Stage 4: Completion Verification
**Timing:** At response completion
**Enforcement:** VALIDATION + METRICS

```yaml
validators:
  - name: COMPLETION_CHECK
    required: true
    validates:
      - "All E field steps completed"
      - "Success criteria met"
      - "Status indicator present"
    status_formats:
      - '(\d+)/(\d+)"(complete|done)"'
      - 'status:(success|completed)'
      - '✓|✗|⚠️'
    on_failure:
      action: log_and_warn
      message: "Work may be incomplete"
      
  - name: HANDLER_COMPLETION
    required: true
    validates:
      - "Handler steps followed"
      - "Handler outputs produced"
      - "Handler validation passed"
    on_failure:
      action: warning
      message: "Handler protocol incomplete"
```

## Module Integration

### How Modules Export Validators

Each module can export custom validators:

```markdown
---
name: my-handler
validators:
  - name: CUSTOM_CHECK
    type: pre_execution
    function: validate_prerequisites
    on_failure: block
  - name: OUTPUT_FORMAT
    type: completion
    pattern: 'specific-output-pattern'
    on_failure: warning
---
```

### Validation Functions

Modules can define validation functions:

```python
def validate_prerequisites(context):
    """
    Check if prerequisites are met
    Returns: (is_valid, error_message)
    """
    if not context.has_file('.env'):
        return False, "Missing .env file"
    return True, None

def validate_output_format(output):
    """
    Validate output matches expected format
    """
    pattern = r'Result:\s+\{.*\}'
    if not re.search(pattern, output):
        return False, "Output missing Result: block"
    return True, None
```

## Enforcement Mechanisms

### 1. Hook-Based Enforcement
```python
# In enhanced_enforcement.py
class ModuleValidator:
    def load_module_validators(self, module_path):
        """Load validators from module frontmatter"""
        # Parse module YAML frontmatter
        # Extract validator definitions
        # Return validator list
        
    def apply_validators(self, context, stage):
        """Apply all validators for given stage"""
        validators = self.get_validators_for_stage(stage)
        for validator in validators:
            result = validator.validate(context)
            if not result.is_valid:
                return self.handle_failure(validator, result)
```

### 2. State-Based Enforcement
```json
{
  "validation_state": {
    "current_stage": "protocol_compliance",
    "validators_passed": [
      "CLAUDE_MD_CHECK",
      "DEVELOPMENT_TRIGGER",
      "ULTRATHINK_PRESENCE"
    ],
    "validators_failed": [],
    "warnings_issued": 0,
    "blocks_triggered": 0
  }
}
```

### 3. Progressive Enforcement
```yaml
enforcement_levels:
  - level: 0
    name: "Natural Conversation"
    validators: []
    
  - level: 1
    name: "Development Mode"
    validators: [ULTRATHINK_PRESENCE, SWHE_FORMAT]
    
  - level: 2
    name: "Strict Mode"
    validators: [ALL]
    
  - level: 3
    name: "Audit Mode"
    validators: [ALL]
    additional: [TRACE_LOGGING, SCREENSHOT_CAPTURE]
```

## Validation Criteria

### For ULTRATHINK Format
```python
def validate_ultrathink(content):
    checks = {
        "statement_present": "Let me ultrathink" in content,
        "at_start": content.strip().startswith("Let me ultrathink"),
        "followed_by_swhe": "[S:" in content[:200],
        "proper_case": "ultrathink" in content.lower()
    }
    
    failures = [k for k, v in checks.items() if not v]
    return len(failures) == 0, failures
```

### For S:W:H:E Components
```python
def validate_swhe_components(s, w, h, e):
    validations = {
        "session": {
            "check": lambda x: re.match(r'^\d{8}', x),
            "message": "Session must be YYYYMMDD format"
        },
        "work": {
            "check": lambda x: x and x not in ['null', 'undefined', 'TODO'],
            "message": "Work context must be specified"
        },
        "handler": {
            "check": lambda x: x and (x in VALID_HANDLERS or x == 'searching'),
            "message": "Handler must be valid or 'searching'"
        },
        "evidence": {
            "check": lambda x: x and (x == 'pending' or '/' in x or '"' in x),
            "message": "Evidence must show progress or completion"
        }
    }
    
    for component, validator in validations.items():
        value = locals()[component]
        if not validator["check"](value):
            return False, validator["message"]
    
    return True, "Valid"
```

## Testing Validators

### Unit Tests
```python
def test_ultrathink_validator():
    valid_response = "Let me ultrathink about this... [S:20250808|W:test|H:test|E:done]"
    invalid_response = "Here's the solution..."
    
    assert validate_ultrathink(valid_response)[0] == True
    assert validate_ultrathink(invalid_response)[0] == False
```

### Integration Tests
```python
def test_full_pipeline():
    # Simulate development request
    set_development_mode(True)
    
    # Test blocked response
    response = generate_response_without_ultrathink()
    validated = enforce_validation_pipeline(response)
    assert "BLOCKED" in validated
    
    # Test valid response
    response = generate_response_with_ultrathink()
    validated = enforce_validation_pipeline(response)
    assert "BLOCKED" not in validated
```

## Metrics & Monitoring

### Tracked Metrics
```json
{
  "validation_metrics": {
    "total_validations": 1000,
    "passed": 850,
    "warnings": 100,
    "blocks": 50,
    "by_validator": {
      "ULTRATHINK_PRESENCE": {
        "checked": 1000,
        "passed": 900,
        "failed": 100
      },
      "SWHE_FORMAT": {
        "checked": 900,
        "passed": 850,
        "failed": 50
      }
    },
    "common_failures": [
      {
        "validator": "SWHE_FORMAT",
        "reason": "Missing handler",
        "count": 30
      }
    ]
  }
}
```

### Performance Targets
- Validation latency: <50ms total
- Memory usage: <10MB
- CPU usage: <5% during validation
- Cache hit rate: >90% for handler lookups

## Integration Points

### With Hooks
- `user_prompt_submit.py`: Detect development mode
- `enhanced_enforcement.py`: Apply validation pipeline
- `pre_tool_use.py`: Block tools without validation
- `stop.py`: Collect final metrics

### With Modules
- Load validator exports from frontmatter
- Apply module-specific validation rules
- Chain validators in pipeline
- Report validation results

### With State Management
- Track validation state across conversation
- Persist warning counts
- Remember completed validations
- Reset on new session

## Error Recovery

### Validation Failure Recovery
```python
def recover_from_validation_failure(failure_type):
    recovery_strategies = {
        "missing_ultrathink": provide_ultrathink_template,
        "invalid_swhe": provide_swhe_examples,
        "missing_handler": suggest_registry_search,
        "incomplete_evidence": request_evidence_update
    }
    
    strategy = recovery_strategies.get(failure_type)
    if strategy:
        return strategy()
    return provide_general_help()
```

### Graceful Degradation
- If validator crashes → log and continue
- If state corrupted → reset to defaults
- If handler not found → suggest alternatives
- If metrics fail → disable metrics, continue validation

## Future Enhancements

### Planned Features
1. **Machine Learning Validation**: Learn patterns from successful validations
2. **Custom Validator Plugins**: Allow user-defined validators
3. **Visual Validation UI**: Show validation status in real-time
4. **Distributed Validation**: Validate across multiple agents
5. **Blockchain Evidence**: Immutable evidence trail

### Extension Points
- Custom validator types
- External validation services
- Webhook notifications
- CI/CD integration
- IDE plugin support

---

## Summary

This validation framework provides:
- **Multi-stage validation pipeline** with hard blocks
- **Module-specific validators** that integrate seamlessly
- **State tracking** across conversation turns
- **Performance monitoring** and metrics
- **Graceful error handling** and recovery

The framework ensures 100% technical enforcement of ULTRATHINK protocol through actual code barriers, not just documentation.