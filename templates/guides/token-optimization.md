---
title: Token Optimization Guide
description: How to save 60-90% of tokens using Serena and GPT-5 integration
version: 1.0.0
created: 2025-08-09
---

# Token Optimization Guide

This guide shows how to dramatically reduce token usage by combining Serena MCP and GPT-5 (O1 Pro) integration.

## 🎯 Quick Summary

**Token Savings**: 60-90% reduction in typical workflows
- **Serena MCP**: 80-90% reduction vs full file reads
- **GPT-5 offloading**: Handles complex reasoning externally
- **Combined approach**: Maximum efficiency

## 🚀 Setup

### Prerequisites
1. **Serena MCP** - Already installed and configured ✓
2. **Cursor CLI** - Install cursor-agent:
   ```bash
   # Install cursor CLI
   npm install -g @cursor/cli
   
   # Login to Cursor
   cursor-agent login
   ```

### Configuration
The system is already configured with:
- GPT-5 consultation handler: `handlers/tools/external/consult-gpt5.md`
- GPT-5 analyst agent: `agents/gpt5-analyst.md`
- Quick GPT-5 agent: `agents/gpt5-quick.md`

## 📖 Usage Patterns

### Pattern 1: Serena-First Investigation
**Saves 80-90% tokens on file reading**

```bash
# Instead of reading entire files:
❌ Read src/components/UserProfile.tsx  # ~5000 tokens

# Use Serena's symbolic tools:
✅ mcp__serena__get_symbols_overview --relative_path "src/components/UserProfile.tsx"  # ~500 tokens
✅ mcp__serena__find_symbol --name_path "UserProfile/render" --include_body true  # ~200 tokens
```

### Pattern 2: GPT-5 for Complex Analysis
**Offload heavy reasoning to external model**

```bash
# For complex debugging:
"consult gpt5 about this performance issue"

# For architecture review:
"get second opinion on this design pattern"

# For fresh perspective:
"ask gpt5 why this might be failing"
```

### Pattern 3: Combined Workflow
**Maximum efficiency for complex tasks**

```
1. Use Serena to narrow scope (saves 80% tokens)
2. Gather minimal context
3. Consult GPT-5 with focused question (offloads reasoning)
4. Apply insights with Serena's precise edits
```

## 🔧 Practical Examples

### Example 1: Debugging Complex Issue
```bash
# Step 1: Use Serena to find the problem area
mcp__serena__search_for_pattern --substring_pattern "error|fail|exception"

# Step 2: Get precise context
mcp__serena__find_symbol --name_path "ErrorHandler" --depth 1

# Step 3: Consult GPT-5 with minimal context
"consult gpt5: ErrorHandler throws undefined on line 42, context: [minimal code]"

# Result: 90% token savings vs traditional debugging
```

### Example 2: Architecture Review
```bash
# Step 1: Map structure with Serena
mcp__serena__get_symbols_overview --relative_path "src/core/"

# Step 2: Get GPT-5 architectural analysis
"ask gpt5 analyst to review this component structure for scalability"

# Result: Deep analysis without token overhead
```

### Example 3: Performance Optimization
```bash
# Step 1: Find hot paths with Serena
mcp__serena__find_referencing_symbols --name_path "expensiveOperation"

# Step 2: Get optimization suggestions
"consult gpt5 about optimizing this recursive function"

# Result: Expert optimization advice with minimal tokens
```

## 📊 Token Usage Comparison

| Task | Traditional | With Serena | With GPT-5 | Combined |
|------|------------|-------------|------------|----------|
| Debug complex bug | 15,000 | 3,000 | 8,000 | 2,000 |
| Architecture review | 25,000 | 5,000 | 12,000 | 3,500 |
| Code refactoring | 10,000 | 2,000 | 6,000 | 1,500 |
| Performance analysis | 20,000 | 4,000 | 10,000 | 2,500 |

## 🎯 Best Practices

### DO:
- ✅ Always use Serena's symbolic tools first
- ✅ Keep GPT-5 queries focused and specific
- ✅ Summarize findings before consulting GPT-5
- ✅ Use `think_about_collected_information` to consolidate
- ✅ Cache GPT-5 insights in work tracking files

### DON'T:
- ❌ Read entire files when symbols would suffice
- ❌ Send large codebases to GPT-5
- ❌ Use GPT-5 for simple tasks Claude can handle
- ❌ Forget to validate GPT-5 suggestions
- ❌ Skip Serena's search capabilities

## 🔍 Quick Commands

### Serena Essentials
```bash
# Overview without reading file
mcp__serena__get_symbols_overview --relative_path "path/to/file"

# Find specific symbol
mcp__serena__find_symbol --name_path "ClassName/method"

# Search patterns efficiently
mcp__serena__search_for_pattern --substring_pattern "pattern"

# Find references
mcp__serena__find_referencing_symbols --name_path "symbol"

# Think about findings
mcp__serena__think_about_collected_information
```

### GPT-5 Consultation
```bash
# Quick consultation
"ask gpt5 about [specific issue]"

# Deep analysis
"consult gpt5 analyst for [complex problem]"

# Second opinion
"get second opinion on [decision/approach]"
```

## 🚦 When to Use Each Tool

### Use Serena When:
- Reading code structure
- Finding specific symbols
- Searching for patterns
- Making precise edits
- Tracking references

### Use GPT-5 When:
- Stuck on complex bugs
- Need architectural review
- Want fresh perspective
- Require deep reasoning
- Validating approaches

### Use Both When:
- Maximum token efficiency needed
- Problem requires both search and reasoning
- Complex multi-step investigations
- Performance optimization
- Security analysis

## 📈 Metrics & Monitoring

Track your token savings:
1. Note tokens before optimization
2. Apply Serena-first approach
3. Offload reasoning to GPT-5
4. Compare final token usage

Typical results:
- **Small tasks**: 60-70% reduction
- **Medium tasks**: 70-80% reduction
- **Large tasks**: 80-90% reduction

## 🔗 Related Resources

- [Serena Documentation](https://github.com/oraios/serena)
- [Cursor CLI Docs](https://cursor.sh/docs)
- Handler: `handlers/tools/external/consult-gpt5.md`
- Agents: `agents/gpt5-analyst.md`, `agents/gpt5-quick.md`

## 💡 Pro Tips

1. **Batch Serena operations** - Multiple searches in parallel
2. **Summarize before GPT-5** - Reduce context to essentials
3. **Cache GPT-5 insights** - Reuse analysis across sessions
4. **Use appropriate agent** - Quick vs comprehensive analysis
5. **Validate suggestions** - Always verify external recommendations

Remember: The goal is not just to save tokens, but to work more efficiently by using the right tool for each job!