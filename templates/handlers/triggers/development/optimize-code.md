---
id: optimize-code
name: Optimize Code Performance
role: trigger
domain: development
stability: stable
triggers:
  - "optimize this"
  - "make faster"
  - "improve performance"
  - "optimize code"
dependencies: []
tools:
  - Read
  - Edit
  - Bash
  - mcp__serena__search_for_pattern
version: 1.0.0
---

# Optimize Code Performance Handler

## Purpose
Analyze code performance bottlenecks and implement optimizations to improve execution speed, memory usage, and overall efficiency.

## Target Pattern
Code sections, functions, or modules that need performance improvements.

## Pre-conditions
- Code exists and is accessible
- Performance concerns identified
- Baseline measurements possible

## Process

1. **Profile current performance**
   - Use profiling tools or manual timing
   - Identify CPU, memory, and I/O bottlenecks
   - Measure baseline performance metrics
   - Document current performance characteristics

2. **Identify bottlenecks**
   - Analyze algorithm complexity (time/space)
   - Review database queries and data access patterns
   - Check for unnecessary computations or redundant operations
   - Identify memory leaks or excessive allocations
   - Examine network requests and API calls

3. **Implement optimizations**
   - Algorithm improvements (better data structures, efficient algorithms)
   - Caching strategies (memoization, result caching)
   - Database optimization (query optimization, indexing)
   - Code refactoring (remove duplicates, optimize loops)
   - Lazy loading and deferred execution
   - Memory management improvements

4. **Measure improvements**
   - Re-run performance tests
   - Compare against baseline metrics
   - Validate functionality remains correct
   - Document performance gains achieved
   - Ensure no regressions introduced

## Success Criteria
- Measurable performance improvement demonstrated
- Code functionality preserved
- Performance gains documented with metrics
- No new bugs or regressions introduced

## Failure Modes
- **Premature optimization**: Optimizing without evidence of need
- **Breaking functionality**: Changes that introduce bugs
- **Micro-optimizations**: Focus on insignificant improvements
- **Over-engineering**: Complex solutions for simple problems

## Examples

### Example 1: Database Query Optimization
**Input**: "optimize this user lookup function"
**Process**: 
- Profile query execution time
- Add database indexes
- Optimize query structure
- Measure improvement

### Example 2: Algorithm Improvement
**Input**: "make this search faster"
**Process**:
- Analyze current O(n²) algorithm
- Implement binary search O(log n)
- Benchmark performance difference

### Example 3: Memory Optimization
**Input**: "improve performance of this data processing"
**Process**:
- Profile memory usage
- Implement streaming/chunked processing
- Reduce memory footprint
- Measure memory and speed improvements

## Integration Points

### With Testing Handlers
- Ensures optimizations don't break existing functionality
- Performance regression testing

### With Profiling Tools
- Uses system profiling tools via Bash
- Integrates with code analysis tools

### With Code Review
- Documents optimization rationale
- Reviews performance trade-offs

## Best Practices
- Always measure before optimizing
- Focus on significant bottlenecks first
- Maintain code readability
- Document optimization decisions
- Use appropriate profiling tools
- Test thoroughly after changes