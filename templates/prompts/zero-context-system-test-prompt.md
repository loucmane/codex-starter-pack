# Codebase Operational Analysis

## Assignment

You've been asked to audit how the AI assistant in this codebase is configured to operate. Approach this as if you know nothing about the system and must discover everything through investigation.

## Primary Questions to Answer

1. **How does the AI decide what to do when given a request?**
   - Find and document the decision flow
   - Identify configuration files
   - Map the execution path

2. **What must happen before the AI executes any task?**
   - Look for prerequisites
   - Find any required preliminary steps
   - Document any "pre-flight" checks

3. **Are there specific formats or patterns the AI must follow?**
   - Search for format specifications
   - Look for template structures
   - Identify any syntax requirements

4. **What happens if something goes wrong?**
   - Find error handling mechanisms
   - Document fallback strategies
   - Test recovery procedures

## Practical Tests

Execute these tests and document EVERYTHING that should happen:

### Test 1: Simple Request
**Input**: "Write a function to calculate fibonacci"
- Find what controls this execution
- Document each step that should occur
- Note any special formatting in the response

### Test 2: Complex Request  
**Input**: "Debug why my app crashes on startup"
- Trace the complete workflow
- Identify all components involved
- Document any protocols followed

### Test 3: Vague Request
**Input**: "Help"
- See how ambiguity is handled
- Find clarification mechanisms
- Document the resolution process

### Test 4: System Check
**Input**: "Run tests"
- Identify how commands are processed
- Find the handler selection mechanism
- Document the execution format

## Investigation Methods

Use these approaches:

1. **File System Exploration**
   ```
   - Look in .claude/ directory
   - Check for templates/ folder
   - Find any .md files with configurations
   - Search for "engine", "protocol", "execution"
   ```

2. **Content Search**
   ```
   - grep for "must", "required", "enforce"
   - Search for "protocol", "format", "before"
   - Look for "CRITICAL", "IMPORTANT", "WARNING"
   - Find patterns with special characters like [, ], :, |
   ```

3. **Dependency Tracing**
   ```
   - Start from main configuration files
   - Follow imports and references
   - Map module relationships
   - Identify critical paths
   ```

4. **Reverse Engineering**
   ```
   - Find example handlers
   - Trace back to their triggers
   - Identify the routing mechanism
   - Understand the selection logic
   ```

## Red Flags to Look For

Be alert for:
- Files marked as "critical" or "engine"
- Repeated patterns or formats
- Enforcement or validation code
- Special protocols or procedures
- Required preliminary steps
- Specific output formats

## Deliverables

### 1. System Map
Create a visual or textual map showing:
```
[Entry Point] → [Decision Logic] → [Execution] → [Output]
```
Include ALL intermediate steps discovered

### 2. Protocol Inventory
List every protocol, format, or pattern found:
- Name
- Purpose  
- Format specification
- When it's used
- How it's enforced

### 3. Test Results
For each test:
- Expected behavior (from docs)
- Actual behavior (from testing)
- Gaps or issues
- Evidence (file:line)

### 4. Critical Components
Identify and rank:
- Most important configuration files
- Key decision points
- Critical protocols
- Essential formats

### 5. Compliance Checklist
Create a checklist of everything the AI MUST do:
- [ ] Before starting work
- [ ] During execution
- [ ] When formatting output
- [ ] On error conditions

## Evaluation Focus

You will be evaluated on:
- Thoroughness of discovery
- Accuracy of findings
- Quality of evidence
- Completeness of testing
- Identification of critical components

## Starting Point

Begin by exploring:
1. The .claude/ directory structure
2. Any file with "engine" in the name
3. Template organization
4. Main configuration files

Document your investigation process so we can see how you discovered each component. Don't assume anything - verify everything through testing.

## Note

This is a blind assessment. Discover the system organically through investigation, not through hints or assumptions. Focus on what the AI MUST do, not what it CAN do.