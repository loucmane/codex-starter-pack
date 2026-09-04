"""Distinguish inert note words from executable synthesis, without granting writes."""

from pathlib import Path

import pytest

from aegis_foundation.gate.hooks.hard_policy import (
    hard_policy_violations,
    raw_hard_policy_families,
)
from test_pretooluse_gates import PRETOOLUSE, make_repo, payload, run_gate

SCOPED = (
    "/usr/bin/env GC_HOME=/home/loucmane/gascity/home "
    "PATH=/home/loucmane/gascity/bin:/usr/local/bin:/usr/bin:/bin "
    "/home/loucmane/gascity/bin/gc --city /home/loucmane/gascity/city "
    "--rig gascity bd update ga-fjoi --append-notes "
)


@pytest.mark.parametrize(
    "argument",
    [
        "'Source candidate ready; source guard passed; no source activation.'",
        '"Source candidate ready; source guard passed; no source activation."',
        "'Review the source; eval is documented, not executed.'",
        "'source'",
        '"eval"',
        "'The word source\nremains note text.'",
    ],
)
def test_quoted_note_keywords_are_not_executable(tmp_path: Path, argument: str) -> None:
    command = SCOPED + argument
    assert "beads_authority" in raw_hard_policy_families(command)
    assert hard_policy_violations(command, tmp_path) == []


@pytest.mark.parametrize(
    "prefix",
    ["", "A=value ", "env -u UNUSED ", "/usr/bin/env A=value ", "command -- ", "builtin "],
)
@pytest.mark.parametrize("name", ["source", "'source'", "eval", '"eval"', "."])
def test_executable_keywords_still_refuse(tmp_path: Path, prefix: str, name: str) -> None:
    command = SCOPED + "'evidence'; " + prefix + name + " 'bd update ga-fjoi'"
    assert hard_policy_violations(command, tmp_path)


@pytest.mark.parametrize(
    "command",
    [
        SCOPED + "'evidence'; bash -lc 'source /tmp/not-executed'",
        SCOPED + "'evidence'; bash -lc 'eval external-command'",
        "bash -lc \"bd update ga-fjoi --append-notes 'source code reviewed'\"",
    ],
)
def test_nested_shell_inspection_preserves_execution_context(tmp_path: Path, command: str) -> None:
    violations = hard_policy_violations(command, tmp_path)
    if command.startswith(SCOPED):
        assert violations
    else:
        assert violations == []


@pytest.mark.parametrize(
    "suffix",
    [
        '"$(source /tmp/not-executed)"',
        '"`eval external-command`"',
        "<(printf evidence)",
        ">(printf evidence)",
        "<<'EOF'\nevidence\nEOF",
        "'unterminated source",
        "'evidence'; python3 -c 'print(1)'",
        "'evidence'; 'python3' '-c' 'print(1)'",
        "'evidence'; bash -lc 'bash -lc \"source /tmp/not-executed\"'",
        "'evidence'; bash -lc 'source \"unterminated'",
        "'evidence'; if true; then source /tmp/not-executed; fi",
        "'evidence'; while false; do eval external-command; done",
        "'evidence'; sour\\ce /tmp/not-executed",
        "'evidence'; e\\val external-command",
        "'evidence'; bash -lc 'bash -lc \"bash -lc true\"'",
        "'evidence'; git reset --hard HEAD",
        "'evidence'; gh api --method DELETE repos/example/project/branches/main/protection",
    ],
)
def test_synthesis_malformed_and_hard_policy_still_refuse(tmp_path: Path, suffix: str) -> None:
    assert hard_policy_violations(SCOPED + suffix, tmp_path)


@pytest.mark.parametrize("argument", ["'source guard passed'", "'eval is only a word here'"])
def test_classifier_fix_does_not_grant_unready_mutations(tmp_path: Path, argument: str) -> None:
    repo = make_repo(tmp_path, ready=False)
    result = run_gate(PRETOOLUSE, repo, payload("Bash", command=SCOPED + argument))
    assert result.returncode == 2
    assert "unsupported shell synthesis" not in result.stderr
    assert '"permissionDecision": "allow"' not in result.stdout
    assert "readiness" in result.stderr.lower() or "blocked" in result.stderr.lower()


@pytest.mark.parametrize("suffix", ["'literal $(example)'", "'literal `example`'", "'literal <<'"])
def test_raw_operator_conservatism_is_not_relaxed(tmp_path: Path, suffix: str) -> None:
    # This repair narrows evaluator words only, not the existing expansion policy.
    assert hard_policy_violations(SCOPED + suffix, tmp_path)


@pytest.mark.parametrize("name", ["'source'", '"eval"', "sour\\ce", "e\\val", "."])
@pytest.mark.parametrize(
    "shape",
    [
        "if true; then {name} /tmp/not-executed; fi",
        "while false; do {name} /tmp/not-executed; done",
        "if false; then true; else {name} /tmp/not-executed; fi",
        "if false; then true; elif {name} /tmp/not-executed; then true; fi",
        "{{ {name} /tmp/not-executed; }}",
        "if true; then command -- {name} /tmp/not-executed; fi",
        "! {name} /tmp/not-executed",
    ],
)
def test_control_word_does_not_hide_executable_evaluator(tmp_path, name, shape):
    assert hard_policy_violations(SCOPED + "'evidence'; " + shape.format(name=name), tmp_path)


def test_quoted_control_and_evaluator_words_stay_inert_arguments(tmp_path):
    assert not hard_policy_violations(SCOPED + "'then eval source do elif else { !'", tmp_path)
