# Session Continuation Regression Suite (Task 85)

## Planned Coverage
- `check_metadata.py` (python script) – verifies registry + metadata references for continuation validation behavior.
- Upcoming pytest suite (pending installation) – simulate guard failures for missing guard logs, tracker entries, and sessions/current link.

## Manual Run
```bash
python3 tests/session_continuation/check_metadata.py
```

## Outstanding
- Install pytest in environment to enable guard/unit tests.
- Add fixtures for guard simulation once pytest available.
