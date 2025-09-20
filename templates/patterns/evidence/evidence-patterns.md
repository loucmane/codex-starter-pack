---
id: evidence-collection-patterns
type: pattern
category: evidence
title: Evidence Collection Patterns
pattern_type: operational
complexity: moderate
dependencies:
  - patterns/selection/tool-selection.md
related:
  - patterns/evidence/validation-patterns.md
  - patterns/evidence/proof-patterns.md
version: 1.0.0
status: stable
---

# Evidence Collection Patterns

## Pattern Description
Methods and approaches for collecting evidence to support claims about code, architecture, or system behavior. These patterns ensure assertions are backed by verifiable proof from the codebase.

## Pattern Structure
1. Identify claim requiring evidence
2. Determine evidence type needed
3. Select appropriate search strategy
4. Collect evidence from sources
5. Verify evidence validity
6. Cite evidence in response

## When to Use
- Making assertions about the codebase
- Claiming system behavior or design
- Describing architecture patterns
- Stating implementation details
- Answering "how does X work" questions

## When NOT to Use
- Discussing hypothetical scenarios
- Proposing new designs
- General programming concepts
- User-provided information

## Evidence Types

### Code Evidence
- **Direct code**: Actual implementation
- **Imports/Dependencies**: Usage proof
- **Function calls**: Invocation evidence
- **Variable usage**: Data flow proof
- **Comments**: Developer intent

### Structural Evidence
- **File organization**: Directory structure
- **Module boundaries**: System organization
- **Package structure**: Dependency layout
- **Config files**: System configuration

### Behavioral Evidence
- **Test cases**: Expected behavior
- **Error handling**: Failure modes
- **Logs**: Runtime behavior
- **Documentation**: Intended usage

## Evidence Collection Strategies

### Direct Search Strategy
For specific claims:
1. Extract key terms from claim
2. Search for exact matches
3. Verify context is correct
4. Collect file:line references

Example:
```
Claim: "The system uses JWT authentication"
Search: "jwt", "jsonwebtoken", "JWT"
Evidence: auth.js:45 - `const jwt = require('jsonwebtoken')`
```

### Pattern Search Strategy
For architectural claims:
1. Identify pattern signatures
2. Search for pattern markers
3. Collect multiple examples
4. Build pattern proof

Example:
```
Claim: "The app follows MVC pattern"
Search: "Controller", "Model", "View" in filenames
Evidence: 
  - controllers/UserController.js
  - models/User.js
  - views/UserView.jsx
```

### Dependency Analysis Strategy
For technology claims:
1. Check package.json/requirements
2. Search for imports
3. Find usage examples
4. Verify active use

Example:
```
Claim: "The app uses Redis for caching"
Evidence:
  - package.json: "redis": "^4.0.0"
  - cache.js:3 - `const redis = require('redis')`
  - cache.js:23 - `client.set(key, value)`
```

## Evidence Check Pattern

### Trigger Detection
**Signals that need evidence**:
- "The system..."
- "It uses..."
- "The code..."
- "The architecture..."
- "It implements..."
- "The app has..."

### Process
1. **Flag**: Set NEED_EVIDENCE = true
2. **Search**: Use appropriate tools
   - Code search: Serena tools
   - File search: Glob
   - Text search: Grep
3. **Collect**: Gather specific references
4. **Verify**: Confirm evidence supports claim
5. **Cite**: Include file:line references

### Evidence Quality Levels

#### High Quality Evidence
- Direct code references
- Multiple corroborating sources
- Recent and active code
- With file:line citations

#### Medium Quality Evidence
- Configuration files
- Single source references
- Indirect indicators
- Comments or documentation

#### Low Quality Evidence
- File naming patterns only
- Old or commented code
- Third-party dependencies
- Assumptions from structure

## Architecture Claim Pattern

### Special Requirements
Architecture claims need multi-source evidence:

1. **Documentation Evidence**
   - README files
   - Architecture docs
   - Design documents
   - Comments

2. **Structure Evidence**
   - Directory organization
   - Module separation
   - Layer boundaries
   - Package structure

3. **Implementation Evidence**
   - Actual code patterns
   - Class/function organization
   - Data flow patterns
   - Communication patterns

### Process
1. Search for architecture documentation
2. Analyze directory structure
3. Find pattern implementations
4. Collect interface definitions
5. Verify layer separation
6. Cite all evidence types

## Common Evidence Patterns

### Technology Stack Evidence
```
Claim: "Uses React with TypeScript"
Evidence needed:
- package.json dependencies
- .tsx file extensions
- React imports
- TypeScript config
```

### Design Pattern Evidence
```
Claim: "Implements Observer pattern"
Evidence needed:
- Subscribe/unsubscribe methods
- Event emitter usage
- Listener registration
- Event dispatching
```

### Integration Evidence
```
Claim: "Integrates with Stripe"
Evidence needed:
- Stripe SDK import
- API key configuration
- Payment endpoints
- Webhook handlers
```

## Evidence Citation Format

### Standard Citation
```
Evidence: [description] (file:line)
Example: JWT authentication implemented (auth/jwt.js:45-67)
```

### Multiple Citations
```
Evidence found in:
- User model definition (models/User.js:12)
- Auth middleware (middleware/auth.js:23-45)
- Login endpoint (routes/auth.js:67)
```

### No Evidence Found
```
Could not find evidence for [claim].
Searched for: [search terms]
Need to verify: [what to check]
```

## Anti-Patterns to Avoid

1. **Claiming without searching**: Always search first
2. **Vague citations**: Always include specific locations
3. **Old evidence**: Verify evidence is current
4. **Single source**: Seek multiple sources for big claims
5. **Assumption chains**: Don't build claims on assumptions

## Examples

### Good Evidence Collection
```
User: "Does the app use MongoDB?"
Process:
1. Check package.json → "mongoose": "^6.0.0" ✓
2. Search for connection → db/connect.js:5 ✓
3. Find model definitions → models/*.js files ✓
Response: "Yes, the app uses MongoDB via Mongoose (package.json:15, db/connect.js:5-12)"
```

### Poor Evidence Collection
```
User: "What database does it use?"
Wrong: "It probably uses PostgreSQL" (no evidence)
Right: "Let me check..." [searches] "Found PostgreSQL connection in db/config.js:8"
```

## Related Patterns
- [Validation Patterns](validation-patterns.md) - Validating evidence
- [Proof Patterns](proof-patterns.md) - Proof requirements
- [Tool Selection](../selection/tool-selection.md) - Choosing search tools

## Handler References
[Handler: evidence-check migrated to handlers/operators/validation/evidence-checker.md]
[Handler: architecture-claim migrated to handlers/operators/analysis/architecture-analyzer.md]