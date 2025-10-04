# Session Continuation Regression Suite (Task 85)

## Test Coverage
- `check_metadata.py` (Python script) – verifies registry + metadata references for continuation validation behavior.
- `test_metadata.py` (pytest) – ensures metadata files remain in sync.
- `test_guard_stub.py` (pytest placeholder) – scaffolding for future guard simulations.

## Running Tests
```bash
python3 -m pytest tests/session_continuation
```

## Outstanding
- Replace placeholder guard tests with real guard simulations.
- Consider adding CI job once guard tests are in place.
