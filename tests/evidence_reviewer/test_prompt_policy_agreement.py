"""Evidence-reviewer prompt <-> policy agreement (canonical + installed).

Guards the defect that failed lane 1 of run hpf-fk02-batch17-shadow-20260830-001:
the all-agents native-command-path fragment steers bead operations to direct
`bd`, which the reviewer's Codex control policy does not allowlist, so the
command runs inside the workspace-write sandbox and loses Dolt access.

The canonical checks run everywhere (CI-hermetic). Installed-artifact checks
skip when the host does not carry the live installation.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

CANONICAL = (
    Path(__file__).resolve().parents[2]
    / "plugins/gas-city-workflow/config/evidence-reviewer/prompt.template.md"
)
INSTALLED = Path("/home/loucmane/gascity/city/agents/evidence-reviewer/prompt.template.md")
RULES = Path(
    "/home/loucmane/gascity/evidence-runs/.codex/rules/"
    "gas-city-evidence-reviewer-control.rules"
)
GC = "/home/loucmane/gascity/bin/gc"
BD = "/home/loucmane/gascity/bin/bd"
REQUIRED_FORMS = (
    f"{GC} hook --claim --json",
    f"{GC} bd show",
    f"{GC} bd update",
    f"{GC} bd close",
    f"{GC} runtime drain-ack",
)


def _command_forms(text: str) -> list[list[str]]:
    return [m.group(1).split() for m in re.finditer(r"`(/home/loucmane/gascity/bin/[^`]+)`", text)]


def test_canonical_prompt_pins_exact_allowlisted_forms() -> None:
    text = CANONICAL.read_text(encoding="utf-8")
    assert "overrides generic command guidance" in text
    assert "native-command-path" in text
    for form in REQUIRED_FORMS:
        assert form in text, f"canonical prompt missing exact allowlisted form: {form}"


def test_canonical_prompt_never_instructs_direct_bd() -> None:
    text = CANONICAL.read_text(encoding="utf-8")
    for m in re.finditer(r"`(/home/loucmane/gascity/bin/bd[^`]*)`", text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line = text[line_start : text.find("\n", m.end())]
        assert "never" in line.lower() or "superseded" in line.lower(), (
            f"canonical prompt instructs direct bd outside prohibition/override context: {line!r}"
        )


@pytest.mark.skipif(not INSTALLED.exists(), reason="live installation absent")
def test_installed_prompt_matches_canonical_byte_for_byte() -> None:
    assert INSTALLED.read_bytes() == CANONICAL.read_bytes()


@pytest.mark.skipif(not RULES.exists(), reason="installed policy absent")
def test_prompt_forms_covered_by_installed_policy_prefixes() -> None:
    rules_text = RULES.read_text(encoding="utf-8")
    prefixes = [
        [p.strip().strip('"') for p in m.group(1).split(",") if p.strip()]
        for m in re.finditer(r"pattern\s*=\s*\[([^\]]*)\]", rules_text)
    ]
    assert prefixes, "installed policy rules file empty"
    for pref in prefixes:
        assert pref[0] != BD, "policy must not allowlist direct bd for this agent"
    for form in _command_forms(CANONICAL.read_text(encoding="utf-8")):
        if form[0] != GC:
            continue
        assert any(
            form[: len(p)] == p or p[: len(form)] == form for p in prefixes
        ), f"prompt form not covered by any installed policy prefix: {' '.join(form)}"
