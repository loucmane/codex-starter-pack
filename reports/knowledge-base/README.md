# Knowledge Base Reports

This directory stores optional static knowledge-base index packets generated from canonical repository knowledge surfaces.

Generate the latest packet with:

```bash
python3 scripts/codex-task knowledge base \
  --report-file reports/knowledge-base/latest.json \
  --runbook-file reports/knowledge-base/latest.md
```

Generate a focused search packet with:

```bash
python3 scripts/codex-task knowledge base \
  --query "runtime contract" \
  --report-file reports/knowledge-base/runtime-contract.json \
  --runbook-file reports/knowledge-base/runtime-contract.md
```

The command indexes existing source-of-truth files across guides, workflow protocols, tool/report references, Taskmaster evidence, sessions, plans, work tracking, and Serena memories. It does not create hosted knowledge-base software, search services, LMS/video/Q&A systems, access-control systems, analytics backends, copy-export trees, or external integrations.
