# Findings

- 2026-06-13 — _Pending_ — document new findings here.



## Progress Log

- **2026-06-13 15:26** — [S:20260613|W:task216-closeout-convergence|H:docs/findings|E:tests/fixtures/replay/hpcoach-2026-06.jsonl] Replay corpus independently corroborated the churn fix: FP baseline 9->8 — corpus entry E04a (read-only jq/ls compound blocked while readiness BLOCKED, a real HP-Coach friction case) is now correctly allowed. Lock updated deliberately; E04a pinned as improvement.
- **2026-06-13 15:49** — [S:20260613|W:task216-closeout-convergence|H:docs/findings|E:tests/claude_adapter/test_pending_tracking_churn.py] Adversarial diff-review workflow (5 agents) caught 5 critical gate-bypass escapes in the churn fix BEFORE merge: (1) bundled short clusters sed -ni/sort -uo/yq -Pi; (2) GNU long forms sed --in-place/sort --output[=FILE]; (3-4) positional-output writers uniq IN OUT and xxd -r IN OUT that no flag guard can catch; (5) MOST SERIOUS: compound bypass where a sanctioned logging/aegis command chained with a real mutation (codex-task plan sync; rm -rf src) excluded the whole payload — a core-invariant break, also pre-existing in the aegis-log/bootstrap exclusions. Fixes: cluster-aware command_has_write_flag with long --flag=value; removed uniq/xxd from read-only set; whole-payload-AND for bash_has_trusted_aegis_subcommand/_nested and bash_is_codex_task_logging (sanctioned segment excludes only when every other segment is read-only incl. redirect detection). All escapes verified closed, legit exclusions preserved; 252 affected-suite tests green.


