# Performance Baseline

**Generated**: 2026-04-25 13:54 CEST

## Commands
- `git ls-files`
- `rg --files templates scripts tests`
- `python3 scripts/template-ssot-scanner/scanner.py --base /home/loucmane/codex --out /tmp/task1-template-scan-results.json --no-checkpoints`

## Results
| Command | Elapsed | Max RSS |
|---------|---------|---------|
| `git ls-files` | 0.00s | 4352 KB |
| `rg --files templates scripts tests` | 0.00s | 4352 KB |
| `scanner.py --no-checkpoints` | 1.62s | 24812 KB |

## Evidence Files
- `perf-git-ls-files.txt`
- `perf-rg-files.txt`
- `perf-scanner-run.txt`

## Interpretation
Inventory commands are effectively instantaneous at the current repository size. The scanner run is still lightweight when checkpoints are disabled: under 2 seconds wall time and under 25MB RSS for the current repository. The main performance risk is not CPU or memory, but unbounded generated checkpoint volume when checkpointing is enabled.
