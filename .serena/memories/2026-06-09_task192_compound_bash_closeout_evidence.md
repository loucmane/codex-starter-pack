# Task 192 — Compound Bash closeout evidence

Implemented markdown-aware closeout evidence parsing in `scripts/_aegis_installer.py` and mirrored it to `aegis_foundation/assets/scripts/_aegis_installer.py`.

Root cause: plan-table evidence escapes pipeline `|` characters as `&#124;`; `_split_evidence_tokens` split evidence cells on every semicolon, including the semicolon inside `&#124;`, and also split semicolons inside `cmd` evidence. Closeout then required fragments such as `tail -25` / encoded pipe fragments across all evidence surfaces, making `handoff repair` unable to converge.

Fix: split evidence only on separators outside backticked command spans, ignore semicolons closing HTML entities, unescape `&#124;` back to `|`, preserve `cmd\`...\`` evidence syntax, and match surfaces against either canonical evidence or the markdown-table escaped form.

Tests added in `tests/meta_workflow_guard/test_aegis_installer.py`: tokenizer coverage, end-to-end handoff repair + closeout dry-run convergence with compound Bash evidence, and negative pending-tracking coverage proving mutating compound Bash payloads still create pending S:W:H:E events.

Focused verification passed: 3 new tests, 6 closeout/handoff regression tests, and ruff on touched files.