"""Regression coverage for semantic Aegis acceptance assertions."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.meta_workflow_guard.aegis_acceptance_assertions import (
    assert_brandmark_accessibility_semantics,
    assert_plan_step_evidence,
    assert_web_cart_button_semantics,
    assert_workflow_evidence,
    parse_plan_table,
    parse_swhe_entries,
)


def test_parse_swhe_entries_and_plan_table() -> None:
    entries = parse_swhe_entries(
        "- [S:20260527|W:task42-add-cart-button|H:claude:Edit|E:src/main.ts] changed source\n"
        "- [S:20260527|W:task42-add-cart-button|H:aegis:verify|E:.aegis/reports/verification-report.json]"
    )
    assert [(entry.work, entry.handler, entry.evidence) for entry in entries] == [
        ("task42-add-cart-button", "claude:Edit", "src/main.ts"),
        ("task42-add-cart-button", "aegis:verify", ".aegis/reports/verification-report.json"),
    ]

    plan_text = """
| Step ID | Description | Evidence | Status |
| --- | --- | --- | --- |
| plan-step-implement | Make source change | starter; src/main.ts | completed |
| plan-step-verify | Verify source change | .aegis/reports/verification-report.json | completed |
"""
    steps = parse_plan_table(plan_text)
    assert steps["plan-step-implement"].evidence == "starter; src/main.ts"
    assert_plan_step_evidence(plan_text, plan_step="plan-step-verify", evidence="verification-report.json", status="completed")


def test_workflow_evidence_helper_reads_structured_surfaces(tmp_path: Path) -> None:
    work_root = tmp_path / "docs/ai/work-tracking/active/20260527-task42-add-cart-button-ACTIVE"
    work_root.mkdir(parents=True)
    session = tmp_path / "sessions/2026/05/session.md"
    session.parent.mkdir(parents=True)
    token = "[S:20260527|W:task42-add-cart-button|H:claude:Edit|E:src/main.ts]"
    for path in (
        session,
        work_root / "TRACKER.md",
        work_root / "IMPLEMENTATION.md",
        work_root / "CHANGELOG.md",
        work_root / "HANDOFF.md",
    ):
        path.write_text(f"- {token} Changed source\n", encoding="utf-8")

    current_work = {
        "task": {"id": "42", "slug": "add-cart-button"},
        "paths": {
            "session": "sessions/2026/05/session.md",
            "work_tracking": "docs/ai/work-tracking/active/20260527-task42-add-cart-button-ACTIVE",
        },
    }
    entries = assert_workflow_evidence(
        tmp_path,
        current_work,
        handler="claude:Edit",
        evidence="src/main.ts",
        surfaces=["session", "tracker", "implementation", "changelog", "handoff"],
    )
    assert len(entries) == 5


@pytest.mark.parametrize(
    "source",
    [
        """
const app = document.querySelector("#app")!;
const label = ["Add", "to", "cart"].join(" ");
const button = document.createElement("button");
button.textContent = label;
app.appendChild(button);
""",
        """
const target = document.body;
const button = document.createElement("button");
const label = "Add" + " to " + "cart";
button.append(label);
target.append(button);
""",
        """
const app = document.querySelector("#app")!;
app.innerHTML = '<button type="button">Add to cart</button>';
""",
    ],
)
def test_web_cart_button_semantics_accepts_idiomatic_variants(source: str) -> None:
    evidence = assert_web_cart_button_semantics(source)
    assert evidence.label_line > 0


@pytest.mark.parametrize(
    "source",
    [
        """
// Add to cart
const app = document.querySelector("#app")!;
app.textContent = "ready";
""",
        """
const unused = "Add to cart";
const app = document.querySelector("#app")!;
const button = document.createElement("button");
app.appendChild(button);
""",
        """
const button = document.createElement("button");
button.textContent = "Add to cart";
""",
    ],
)
def test_web_cart_button_semantics_rejects_comments_dead_literals_and_unattached_buttons(source: str) -> None:
    with pytest.raises(AssertionError):
        assert_web_cart_button_semantics(source)


@pytest.mark.parametrize(
    "source",
    [
        """
export function BrandMark(): HTMLElement {
  const mark = document.createElement("span");
  mark.setAttribute("role", "img");
  mark.setAttribute("aria-label", "HP-Fetcher");
  return mark;
}
""",
        """
export function BrandMark(): HTMLElement {
  const template = document.createElement("template");
  template.innerHTML = '<span role="img" aria-label="HP-Fetcher"><span aria-hidden="true">[</span>HP-Fetcher</span>';
  return template.content.firstElementChild as HTMLElement;
}
""",
    ],
)
def test_brandmark_accessibility_semantics_accepts_equivalent_implementations(source: str) -> None:
    assert assert_brandmark_accessibility_semantics(source, label="HP-Fetcher")


def test_brandmark_accessibility_semantics_rejects_dead_markup() -> None:
    with pytest.raises(AssertionError):
        assert_brandmark_accessibility_semantics(
            """
const dead = '<span role="img" aria-label="HP-Fetcher">HP-Fetcher</span>';
export function BrandMark(): HTMLElement {
  return document.createElement("span");
}
""",
            label="HP-Fetcher",
        )
