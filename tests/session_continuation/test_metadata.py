from pathlib import Path

def test_registry_includes_continuation_behavior():
    registry = Path('templates/REGISTRY.md').read_text(encoding='utf-8')
    assert 'Continuation Validation Behavior' in registry

def test_workflow_guards_reference_behavior():
    guards = Path('templates/metadata/workflow-guards.json').read_text(encoding='utf-8')
    assert 'templates/behaviors/session/continuation-validation.md' in guards

def test_template_overview_lists_behavior():
    overview = Path('templates/metadata/template-overview.md').read_text(encoding='utf-8')
    assert 'Session Continuation Validation' in overview
