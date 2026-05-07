# Compatibility Mapping Validation

**Date**: 2026-05-07
**Task**: 13 - Implement Compatibility Mapping Table

## Focused Tests

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_template_registry.py -q
```

Result:

```text
8 passed
```

## Runtime Smoke Check

Command:

```bash
python3 - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, 'scripts')
from template_registry import TemplateRegistry
registry = TemplateRegistry(repo_root=Path('.'))
for query in ['templates/REGISTRY.md', 'templates/WORKFLOWS.md', 'templates/BUILDING-BETTER.md']:
    result = registry.resolve(query)
    print(query, '=>', result.status, result.source, result.path)
print('target issues', registry.compatibility_map.validate_targets(Path('.').resolve()))
PY
```

Result:

```text
templates/REGISTRY.md => redirect compatibility templates/registry/index.md
templates/WORKFLOWS.md => redirect compatibility templates/workflows/
templates/BUILDING-BETTER.md => redirect compatibility templates/integration/best-practices/
target issues []
```

## Notes

The compatibility mapping remains part of the template registry runtime. Existing registry callers keep using `TemplateRegistry.resolve()`, while the mapping data now lives in a versioned JSON table under `templates/registry/compatibility-map.json`.

