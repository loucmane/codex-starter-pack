# Derived Obsidian Vault Design

## Decision

Build a deterministic out-of-repository Obsidian projection as a disposable view over Aegis and
legacy evidence. Do not make Obsidian an authority, workflow engine, task tracker, or writeback
surface.

## Inputs

- read-only passive ledger events;
- current Git branch and HEAD;
- Taskmaster task/subtask records;
- bounded computed-capsule orientation fields;
- structural inventory of preserved legacy workflow Markdown.

## Outputs

- YAML-frontmatter Markdown nodes;
- path-qualified wikilinks;
- native `.base` table views;
- exact ownership/hash manifest;
- no `.obsidian/` configuration.

## Key Constraints

1. Default output lives beside the XDG ledger, never in the repository.
2. No raw commands or arbitrary ledger payloads are copied.
3. Low-level gate and mutation events do not create notes or freshness churn.
4. Existing output is replaceable only when its manifest and all hashes prove sole Aegis
   ownership.
5. Build stages and self-checks the full graph before atomic directory replacement.
6. Legacy prose stays in its source file; the vault records structure, digest, and links.
7. Every node class and total output has a hard ceiling.
8. No legacy runtime surface is retired in Task 243.

## Why This Complements S:W:H:E

The ledger is excellent at observed facts but weak at human rationale. Legacy plans, sessions,
trackers, decisions, findings, and handoffs contain thousands of human-authored lines that the
ledger cannot safely reconstruct. Obsidian contributes navigation and relationship discovery;
it does not make those narrative sources obsolete.

## Failure Policy

- Missing ledger: build the task/capsule/legacy view and report ledger absence.
- Invalid or unreadable ledger: fail; do not hide corruption as an empty history.
- Unknown/manual output: refuse and preserve every byte.
- Tampered generated output: refuse and report exact mismatches.
- Stage/check failure: preserve previous valid output.
- Limit exceeded: fail before replacement.
- Source changes during build: the next freshness check reports stale; source is never locked or
  modified.
