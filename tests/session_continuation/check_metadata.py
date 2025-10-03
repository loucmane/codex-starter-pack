#!/usr/bin/env python3
"""Sanity checks for continuation validation metadata wiring."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]

REGISTRY_TEXT = (ROOT / "templates" / "REGISTRY.md").read_text(encoding="utf-8")
OVERVIEW_TEXT = (ROOT / "templates" / "metadata" / "template-overview.md").read_text(encoding="utf-8")
SUMMARY_TEXT = (ROOT / "templates" / "metadata" / "template-summary.csv").read_text(encoding="utf-8")
GUARDS_TEXT = (ROOT / "templates" / "metadata" / "workflow-guards.json").read_text(encoding="utf-8")
PATTERNS_TEXT = (ROOT / "templates" / "registry" / "patterns" / "meta-routing.md").read_text(encoding="utf-8")

checks = {
    "registry": "Continuation Validation" in REGISTRY_TEXT,
    "overview": "continuation-validation.md" in OVERVIEW_TEXT,
    "summary": "templates/behaviors/session/continuation-validation.md" in SUMMARY_TEXT,
    "guards": "templates/behaviors/session/continuation-validation.md" in GUARDS_TEXT,
    "patterns": "continuation-validation" in PATTERNS_TEXT,
}

errors = [name for name, ok in checks.items() if not ok]

if errors:
    sys.stderr.write("Missing continuation metadata: " + ", ".join(errors) + "\n")
    sys.exit(1)

print("Continuation metadata checks passed.")
