"""Semantic assertions for Aegis target-project acceptance tests."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


_IDENTIFIER = r"[A-Za-z_$][\w$]*"


@dataclass(frozen=True)
class SwheEntry:
    session: str
    work: str
    handler: str
    evidence: str


@dataclass(frozen=True)
class PlanStep:
    step_id: str
    description: str
    evidence: str
    status: str


@dataclass(frozen=True)
class WebCartButtonEvidence:
    strategy: str
    display: str
    label_line: int
    append_line: int | None = None


_SWHE_RE = re.compile(
    r"\[S:(?P<session>[^\]|]+)\|W:(?P<work>[^\]|]+)\|H:(?P<handler>[^\]|]+)\|E:(?P<evidence>[^\]]+)\]"
)


def parse_swhe_entries(text: str) -> list[SwheEntry]:
    """Return structured S:W:H:E records from a workflow markdown surface."""

    return [
        SwheEntry(
            session=match.group("session"),
            work=match.group("work"),
            handler=match.group("handler"),
            evidence=match.group("evidence"),
        )
        for match in _SWHE_RE.finditer(text)
    ]


def parse_plan_table(text: str) -> dict[str, PlanStep]:
    """Parse the Aegis plan table into records keyed by plan step id."""

    rows: dict[str, PlanStep] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("|-"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 4 or cells[0] == "Step ID":
            continue
        if not cells[0].startswith("plan-step-"):
            continue
        rows[cells[0]] = PlanStep(
            step_id=cells[0],
            description=cells[1],
            evidence=cells[2],
            status=cells[3],
        )
    return rows


def assert_swhe_entry(text: str, *, work: str, handler: str, evidence: str) -> SwheEntry:
    entries = parse_swhe_entries(text)
    for entry in entries:
        if entry.work == work and entry.handler == handler and entry.evidence == evidence:
            return entry
    found = ", ".join(f"W={entry.work} H={entry.handler} E={entry.evidence}" for entry in entries)
    raise AssertionError(
        f"missing S:W:H:E entry W={work} H={handler} E={evidence}; found: {found or '<none>'}"
    )


def assert_plan_step_evidence(
    plan_text: str,
    *,
    plan_step: str,
    evidence: str,
    status: str,
) -> PlanStep:
    steps = parse_plan_table(plan_text)
    step = steps.get(plan_step)
    if step is None:
        raise AssertionError(f"missing plan step {plan_step}; found: {sorted(steps)}")
    if evidence not in step.evidence:
        raise AssertionError(f"plan step {plan_step} does not reference evidence {evidence!r}: {step.evidence!r}")
    if step.status != status:
        raise AssertionError(f"plan step {plan_step} status {step.status!r} != {status!r}")
    return step


def assert_workflow_evidence(
    target: Path,
    current_work: dict,
    *,
    handler: str,
    evidence: str,
    surfaces: Iterable[str],
) -> list[SwheEntry]:
    """Assert workflow markdown surfaces contain the expected semantic evidence entry."""

    paths = current_work["paths"]
    work = f"task{current_work['task']['id']}-{current_work['task']['slug']}"
    work_root = Path(paths["work_tracking"])
    surface_rel_paths = {
        "session": Path(paths["session"]),
        "tracker": work_root / "TRACKER.md",
        "findings": work_root / "FINDINGS.md",
        "decisions": work_root / "DECISIONS.md",
        "implementation": work_root / "IMPLEMENTATION.md",
        "changelog": work_root / "CHANGELOG.md",
        "handoff": work_root / "HANDOFF.md",
    }

    entries: list[SwheEntry] = []
    for surface in surfaces:
        rel_path = surface_rel_paths[surface]
        text = (target / rel_path).read_text(encoding="utf-8")
        entries.append(assert_swhe_entry(text, work=work, handler=handler, evidence=evidence))
    return entries


def assert_web_cart_button_semantics(source: str, *, label: str = "Add to cart") -> WebCartButtonEvidence:
    evidence = find_web_cart_button_semantics(source, label=label)
    if evidence is None:
        raise AssertionError(
            "source does not create and attach a button whose rendered text semantically resolves "
            f"to {label!r}; comments and unused string literals do not count"
        )
    return evidence


def find_web_cart_button_semantics(source: str, *, label: str = "Add to cart") -> WebCartButtonEvidence | None:
    code = _strip_js_comments(source)
    constants = _collect_string_constants(code)
    html_evidence = _find_inner_html_button(source, code, constants, label)
    if html_evidence is not None:
        return html_evidence

    for match in re.finditer(
        rf"\b(?:const|let|var)\s+(?P<name>{_IDENTIFIER})\s*=\s*document\.createElement\(\s*['\"]button['\"]\s*\)",
        code,
    ):
        name = match.group("name")
        label_match = _find_button_label_assignment(code, name, constants, label)
        if label_match is None:
            continue
        append_match = re.search(rf"\.(?:appendChild|append|replaceChildren)\(\s*{re.escape(name)}\b", code)
        if append_match is None:
            continue
        return WebCartButtonEvidence(
            strategy="dom-button",
            display=f"{name}@{_line_number(source, match.start())}",
            label_line=_line_number(source, label_match.start()),
            append_line=_line_number(source, append_match.start()),
        )
    return None


def assert_brandmark_accessibility_semantics(source: str, *, label: str) -> str:
    code = _strip_js_comments(source)
    constants = _collect_string_constants(code)

    for match in re.finditer(
        rf"\b(?:const|let|var)\s+(?P<name>{_IDENTIFIER})\s*=\s*document\.createElement\(\s*['\"]span['\"]\s*\)",
        code,
    ):
        name = match.group("name")
        role_re = rf"{re.escape(name)}\.setAttribute\(\s*['\"]role['\"]\s*,\s*['\"]img['\"]\s*\)"
        label_re = rf"{re.escape(name)}\.setAttribute\(\s*['\"]aria-label['\"]\s*,\s*(?P<expr>[^)]+)\)"
        label_match = re.search(label_re, code)
        if re.search(role_re, code) and label_match and _expr_resolves_to(label_match.group("expr"), constants, label):
            if re.search(rf"\breturn\s+{re.escape(name)}\b", code):
                return f"imperative-span:{name}"

    for match in re.finditer(r"\.innerHTML\s*=\s*(?P<expr>.*?);", code, re.S):
        html = _evaluate_js_string_expr(match.group("expr"), constants)
        if html and _html_tag_has_accessible_label(html, tag="span", label=label):
            if "firstElementChild" in code or "firstChild" in code:
                return "template-innerHTML"

    if re.search(rf"return\s*\(?\s*<span\b(?=[^>]*\brole=['\"]img['\"])(?=[^>]*\baria-label=['\"]{re.escape(label)}['\"])", code):
        return "jsx-span"

    raise AssertionError(f"source does not return a BrandMark span with role='img' and aria-label={label!r}")


def _strip_js_comments(source: str) -> str:
    result: list[str] = []
    i = 0
    quote: str | None = None
    while i < len(source):
        char = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if quote:
            result.append(char)
            if char == "\\" and i + 1 < len(source):
                i += 1
                result.append(source[i])
            elif char == quote:
                quote = None
            i += 1
            continue
        if char in {"'", '"', "`"}:
            quote = char
            result.append(char)
            i += 1
            continue
        if char == "/" and nxt == "/":
            while i < len(source) and source[i] != "\n":
                result.append(" ")
                i += 1
            continue
        if char == "/" and nxt == "*":
            result.extend("  ")
            i += 2
            while i < len(source) - 1 and not (source[i] == "*" and source[i + 1] == "/"):
                result.append("\n" if source[i] == "\n" else " ")
                i += 1
            if i < len(source) - 1:
                result.extend("  ")
                i += 2
            continue
        result.append(char)
        i += 1
    return "".join(result)


def _collect_string_constants(code: str) -> dict[str, str]:
    constants: dict[str, str] = {}
    assignment_re = re.compile(rf"\b(?:const|let|var)\s+(?P<name>{_IDENTIFIER})\s*=\s*(?P<expr>[^;\n]+);")
    for _ in range(3):
        changed = False
        for match in assignment_re.finditer(code):
            value = _evaluate_js_string_expr(match.group("expr"), constants)
            if value is not None and constants.get(match.group("name")) != value:
                constants[match.group("name")] = value
                changed = True
        if not changed:
            break
    return constants


def _find_inner_html_button(
    source: str,
    code: str,
    constants: dict[str, str],
    label: str,
) -> WebCartButtonEvidence | None:
    for match in re.finditer(r"\.innerHTML\s*=\s*(?P<expr>.*?);", code, re.S):
        html = _evaluate_js_string_expr(match.group("expr"), constants)
        if html and _html_tag_has_text(html, tag="button", label=label):
            line = _line_number(source, match.start())
            return WebCartButtonEvidence(strategy="innerHTML-button", display=f"innerHTML@{line}", label_line=line)
    return None


def _find_button_label_assignment(
    code: str,
    name: str,
    constants: dict[str, str],
    label: str,
) -> re.Match[str] | None:
    assignment_re = re.compile(
        rf"{re.escape(name)}\.(?:textContent|innerText|text)\s*=\s*(?P<expr>[^;\n]+)"
    )
    for match in assignment_re.finditer(code):
        if _expr_resolves_to(match.group("expr"), constants, label):
            return match

    append_re = re.compile(rf"{re.escape(name)}\.(?:append|replaceChildren)\(\s*(?P<expr>[^)]+)\)")
    for match in append_re.finditer(code):
        if _expr_resolves_to(match.group("expr"), constants, label):
            return match
    return None


def _expr_resolves_to(expr: str, constants: dict[str, str], expected: str) -> bool:
    value = _evaluate_js_string_expr(expr, constants)
    return value is not None and _normalize_text(value) == _normalize_text(expected)


def _evaluate_js_string_expr(expr: str, constants: dict[str, str]) -> str | None:
    expr = expr.strip()
    if not expr:
        return None
    if expr in constants:
        return constants[expr]
    literal = _string_literal_value(expr)
    if literal is not None:
        return literal

    join_match = re.fullmatch(r"\[(?P<items>.*)\]\.join\(\s*(?P<sep>.*?)\s*\)", expr, re.S)
    if join_match:
        sep = _evaluate_js_string_expr(join_match.group("sep"), constants)
        if sep is None:
            return None
        item_values = [_evaluate_js_string_expr(item, constants) for item in _split_top_level(join_match.group("items"), ",")]
        if item_values and all(value is not None for value in item_values):
            return sep.join(value for value in item_values if value is not None)

    parts = _split_top_level(expr, "+")
    if len(parts) > 1:
        values = [_evaluate_js_string_expr(part, constants) for part in parts]
        if all(value is not None for value in values):
            return "".join(value for value in values if value is not None)

    return None


def _string_literal_value(expr: str) -> str | None:
    expr = expr.strip()
    if len(expr) < 2 or expr[0] not in {"'", '"', "`"} or expr[-1] != expr[0]:
        return None
    quote = expr[0]
    body = expr[1:-1]
    escaped = False
    for char in body:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == quote:
            return None
    return body.replace(r"\'", "'").replace(r'\"', '"').replace(r"\`", "`").replace(r"\n", "\n")


def _split_top_level(expr: str, separator: str) -> list[str]:
    parts: list[str] = []
    start = 0
    quote: str | None = None
    depth = 0
    i = 0
    while i < len(expr):
        char = expr[i]
        if quote:
            if char == "\\":
                i += 2
                continue
            if char == quote:
                quote = None
            i += 1
            continue
        if char in {"'", '"', "`"}:
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == separator and depth == 0:
            parts.append(expr[start:i].strip())
            start = i + 1
        i += 1
    parts.append(expr[start:].strip())
    return parts


def _html_tag_has_text(html: str, *, tag: str, label: str) -> bool:
    for match in re.finditer(rf"<{tag}\b[^>]*>(?P<body>.*?)</{tag}>", html, re.I | re.S):
        body = re.sub(r"<[^>]+>", " ", match.group("body"))
        if _normalize_text(body) == _normalize_text(label):
            return True
    return False


def _html_tag_has_accessible_label(html: str, *, tag: str, label: str) -> bool:
    tag_re = re.compile(rf"<{tag}\b(?P<attrs>[^>]*)>", re.I | re.S)
    for match in tag_re.finditer(html):
        attrs = match.group("attrs")
        if re.search(r"\brole\s*=\s*['\"]img['\"]", attrs) and re.search(
            rf"\baria-label\s*=\s*['\"]{re.escape(label)}['\"]", attrs
        ):
            return True
    return False


def _normalize_text(text: str) -> str:
    return " ".join(text.split()).casefold()


def _line_number(source: str, index: int) -> int:
    return source.count("\n", 0, index) + 1
