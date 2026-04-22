---
id: error-to-recovery-matrix
title: Error to Recovery Matrix
type: decision-matrix
category: recovery
status: stable
usage: Maps error patterns to recovery actions and prevention strategies
version: 1.0.0
---

# Error → Recovery Matrix

Provides immediate actions and recovery paths for common error patterns.

## Input
Error pattern or failure type

## Output
Immediate action, recovery path, and prevention strategy

## Matrix

| Error Pattern | Immediate Action | Recovery Path | Prevention |
|--------------|------------------|---------------|------------|
| Handler not found | Search broader terms | Check templates/patterns/ | Update registry |
| File not found | Verify path exists | Search for file | Use absolute paths |
| Symbol not found | Try substring match | Use search_pattern | Check file first |
| Test failure | Read full error | Fix implementation | Run before commit |
| Build failure | Check recent changes | Revert if needed | Test locally |
| Type mismatch | Find type definition | Fix or cast | Use strict types |
| Import error | Check file location | Fix import path | Use aliases |
| Permission denied | Check file perms | Request access | Validate early |
| Syntax error | Find exact location | Fix syntax | Use linter |
| Network timeout | Retry with backoff | Check connection | Add timeouts |
| Memory exceeded | Reduce scope | Process in chunks | Monitor usage |
| Git conflict | Review changes | Merge carefully | Pull often |
| Database lock | Wait and retry | Kill long queries | Use transactions |
| Rate limited | Add delay | Implement backoff | Cache results |
| Version mismatch | Check requirements | Update deps | Pin versions |
| Missing dependency | Install required | Check package.json | Document deps |
| Circular reference | Map the cycle | Break dependency | Design better |
| Stack overflow | Find recursion | Add base case | Limit depth |
| Deadlock | Analyze locks | Restart service | Order locks |
| Data corruption | Restore backup | Validate data | Add checksums |

## Recovery Strategies

### Immediate Response
1. **Stop**: Don't make problem worse
2. **Assess**: Understand the failure
3. **Document**: Record what happened
4. **Communicate**: Inform if needed

### Investigation Steps
1. Check recent changes
2. Review error messages
3. Search for similar issues
4. Test in isolation
5. Verify assumptions

### Recovery Actions

#### For Code Errors
- Revert to working state
- Fix incrementally
- Test each change
- Document solution

#### For System Errors
- Restart affected services
- Clear caches if relevant
- Check system resources
- Monitor after fix

#### For Data Errors
- Verify backups exist
- Test recovery process
- Validate restored data
- Implement safeguards

## Common Recovery Patterns

### Build/Deploy Failures
```
1. Check CI/CD logs
2. Identify failing step
3. Run locally to reproduce
4. Fix and test
5. Re-run pipeline
```

### Performance Issues
```
1. Profile to find bottleneck
2. Measure baseline
3. Implement fix
4. Measure improvement
5. Monitor in production
```

### Security Issues
```
1. Isolate affected systems
2. Assess exposure
3. Apply patches
4. Review for similar issues
5. Update security practices
```

## Fallback Decision Tree

```
No handler match?
├─ Is it development work? → Use start-new-work as default
├─ Is it a search? → Check tool selection matrix
├─ Is it file operation? → Check special files rules
├─ Is it unclear? → Ask: "What specifically would you like me to do?"
└─ Still stuck? → Document gap and request guidance
```

## Prevention Checklist

### Before Changes
- [ ] Backup critical files
- [ ] Verify test coverage
- [ ] Check dependencies
- [ ] Review conventions
- [ ] Plan rollback strategy

### During Changes
- [ ] Test incrementally
- [ ] Commit working states
- [ ] Document decisions
- [ ] Monitor resources
- [ ] Validate assumptions

### After Changes
- [ ] Run full test suite
- [ ] Check for regressions
- [ ] Update documentation
- [ ] Review performance
- [ ] Plan monitoring

## Escalation Path

1. **Level 1**: Try immediate action
2. **Level 2**: Follow recovery path
3. **Level 3**: Check similar issues
4. **Level 4**: Request expert help
5. **Level 5**: Document for future

## Progress Log

- **2026-04-22 15:52** — [S:20260422|W:task91-standardize-template-metadata|H:templates/matrices/recovery/error-to-recovery.md|E:templates/metadata/template-metadata-policy.json] Added canonical `title` and `status` metadata during the Task 91 matrices-family standardization slice
