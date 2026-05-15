# Decisions

- 2026-05-15 11:15 CEST — Implement Task 78 as a final-documentation map and guide-hub link only. Do not create duplicate architecture, operations, API, troubleshooting, disaster recovery, capacity, compliance, or handover documents when current canonical docs already exist.
- 2026-05-15 11:15 CEST — Keep final documentation repository-native and evidence-backed. The map may point to report packet generators and validation commands, but it must not claim hosted docs, external training, live monitoring, external compliance certification, or incident-management integrations.
- 2026-05-15 11:53 CEST — Use Markdown links for same-template-tree documentation references and literal code paths for repo-root/report artifacts in `templates/guides/reference/final-documentation-map.md` so the automatic reference-fix gate stays green.
