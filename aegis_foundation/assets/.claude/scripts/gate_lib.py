from __future__ import annotations

import os
import sys

# Defense in depth: prevent cache reads as well as writes before runtime imports.
# This does not replace or relax any runtime integrity/approval check.
sys.dont_write_bytecode = True
sys.pycache_prefix = os.devnull
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["PYTHONPYCACHEPREFIX"] = os.devnull

from pathlib import Path  # noqa: E402 - cache isolation precedes runtime imports.


def _candidate_source_roots() -> list[Path]:
    script = Path(__file__).resolve()
    target = script.parents[2]
    candidates = [target / ".aegis" / "runtime" / "python", target]
    runtime_env = target / ".aegis" / "runtime.env"
    try:
        lines = runtime_env.read_text(encoding="utf-8").splitlines()
    except OSError:
        lines = []
    for line in lines:
        if line.startswith(("AEGIS_SOURCE_ROOT=", "source_root=")):
            candidates.append(Path(line.split("=", 1)[1]).expanduser())
    value = os.environ.get("AEGIS_SOURCE_ROOT")
    if value:
        candidates.append(Path(value).expanduser())
    return candidates


os.environ["AEGIS_HOOK_SCRIPT_DIR"] = str(Path(__file__).resolve().parent)
for _candidate in _candidate_source_roots():
    _resolved = _candidate.resolve()
    if (_resolved / "aegis_foundation" / "gate" / "hooks").is_dir():
        sys.path.insert(0, str(_resolved))
        break

try:
    from aegis_foundation.gate import hooks as _runtime
except Exception as _exc:  # fail closed for mutation-capable hook phases
    _phase = sys.argv[1] if len(sys.argv) > 1 else ""
    print(f"Aegis canonical hook runtime is unavailable: {_exc}", file=sys.stderr)
    raise SystemExit(2 if _phase in {"pretooluse", "path", "bash", "configchange"} else 0)

for _name in _runtime.__all__:
    globals()[_name] = getattr(_runtime, _name)

if __name__ == "__main__":
    raise SystemExit(_runtime.main())
