# Compound Bash Evidence Normalization

## Problem

HP-Coach Task 73 closeout failed after meaningful implementation and verification evidence had been logged. The failing gates were `closeout.evidence.session`, `closeout.evidence.tracker`, `closeout.evidence.implementation`, and `closeout.evidence.changelog`.

The proximate cause was plan-table evidence parsing, not mutation classification:

- `aegis log` writes evidence into the plan table through `_markdown_table_cell`.
- Shell pipelines are escaped as `&#124;` so the markdown table remains well formed.
- `_split_evidence_tokens` split the plan evidence cell on every semicolon.
- The escaped pipe entity itself contains a semicolon, so `cmd\`... | tail ...\`` became fragments such as `cmd\`... &#124` and `tail ...`.
- Python snippets with semicolons inside `cmd\`...\`` evidence had the same failure mode.
- Closeout then required those fragments to appear on every evidence surface, and `handoff repair` could not converge.

## Fix

Keep the S:W:H:E pending-tracking model unchanged. Instead, canonicalize required closeout evidence when reading the plan table:

- split evidence cells only on separators outside backticked command spans;
- do not split the semicolon that closes HTML entities such as `&#124;`;
- unescape `&#124;` back to `|` for canonical evidence tokens;
- preserve `cmd\`...\`` command evidence syntax instead of stripping the trailing backtick;
- when checking a surface, accept either the canonical evidence token or its markdown-table-escaped form.

This keeps closeout strict about real required evidence while preventing markdown escaping from manufacturing false requirements.

## Safety Boundary

The change does not make compound Bash commands read-only and does not hide mutations:

- post-tool tracking still records unknown or mutating Bash payloads as pending S:W:H:E events;
- mutating compound commands remain evidence-bearing events;
- the closeout change only affects how already-logged plan evidence is parsed and matched across surfaces.

## Regression Coverage

Added tests cover:

- tokenizer behavior for escaped pipes and shell semicolons inside `cmd\`...\`` evidence;
- end-to-end `repair_handoff` plus `closeout --dry-run` convergence with piped implementation and verification command evidence;
- negative tracking behavior proving a mutating compound Bash payload still creates a pending tracking event.
