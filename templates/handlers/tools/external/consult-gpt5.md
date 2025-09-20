---
name: consult-gpt5
version: 1.0.0
category: tools/external
description: Consult GPT-5 (O1 Pro) via cursor-agent for second opinions and deep analysis
triggers:
  - "ask gpt5"
  - "consult gpt5"
  - "get second opinion"
  - "need fresh perspective"
  - "complex debugging"
  - "architectural review"
dependencies: []
---

# Consult GPT-5 Handler

## Purpose
Get second opinions and deep analysis from GPT-5 (O1 Pro) through cursor-agent integration.

## When to Use
- Complex bugs that resist normal debugging
- Architectural decisions needing validation
- Performance optimization challenges
- Security vulnerability analysis
- Fresh perspective on stuck problems

## Execution Protocol

### 1. Gather Context
```bash
# Collect current findings
mcp__serena__think_about_collected_information

# Summarize the problem clearly
```

### 2. Choose Agent Type
- **For comprehensive analysis**: Use `gpt5-analyst` agent
- **For quick consultation**: Use `gpt5` agent

### 3. Deploy Agent
```bash
# For comprehensive analysis
Task --subagent_type gpt5-analyst --description "Deep analysis" --prompt "
Problem: [Describe the specific issue]
Current Findings: [What you've discovered]
Context: [Relevant code, errors, logs]
Question: [What specific insight you need]
"

# For quick consultation
Task --subagent_type gpt5 --description "Quick GPT-5 check" --prompt "
Issue: [Brief problem description]
Context: [Key details]
Need: [What you want GPT-5 to focus on]
"
```

### 4. Process Response
- Extract key insights
- Validate recommendations against project standards
- Identify actionable items
- Note any risks or considerations

## Token Optimization Tips

### Before Consulting GPT-5
1. **Use Serena first** to narrow down the problem area
2. **Summarize findings** concisely
3. **Be specific** about what you need
4. **Include only relevant** code snippets

### Context Preparation
```bash
# Use Serena's symbolic tools to get precise context
mcp__serena__find_symbol --name_path "ClassName/methodName" --include_body true

# Get overview without full file reads
mcp__serena__get_symbols_overview --relative_path "path/to/file.ts"

# Search for specific patterns
mcp__serena__search_for_pattern --substring_pattern "error pattern"
```

## Example Workflows

### Debugging Complex Issue
```
1. Use Serena to identify problem area (saves tokens)
2. Gather minimal but complete context
3. Consult GPT-5 with specific question
4. Apply insights back to codebase
```

### Architecture Review
```
1. Use Serena to map current structure
2. Prepare concise architecture summary
3. Ask GPT-5 for specific improvements
4. Validate suggestions against conventions
```

## Integration with Template System

This handler works with:
- [analyze-code.md](../analysis/analyze-code.md) - For initial analysis
- [debug-issue.md](../debugging/debug-issue.md) - For debugging workflow
- [optimize-performance.md](../optimization/optimize-performance.md) - For performance issues

## Token Savings Metrics

Typical token savings using this approach:
- **Serena symbolic search**: 80-90% reduction vs full file reads
- **GPT-5 for complex analysis**: Offloads heavy reasoning
- **Combined approach**: 60-70% total token reduction

## Remember
- Always use Serena's symbolic tools first
- Keep GPT-5 queries focused and specific
- Validate all suggestions against project conventions
- Document insights in work tracking files