# Findings

- 2026-08-31 — The transactional workflow parser was repaired in `ga-c8al`, but the real hierarchical transaction exposed five legacy consumers outside that parser: source readiness/current-plan validation, installed gate branch inference, delivery witness inference, delivery-policy branch validation, and closeout active-folder inference.
- 2026-08-31 — The defect survived the earlier test suite because workflow transition tests mocked readiness. The repair adds a real `readiness.sh` hierarchical-Bead fixture and a cross-surface parity test rather than another isolated parser test.
- 2026-08-31 — Native generated Bead branches use an alphanumeric base token with numeric dotted descendants. Direct Bead validation remains the broader existing safe grammar; branch inference deliberately models the unambiguous native generated form.
