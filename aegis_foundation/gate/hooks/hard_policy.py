"""Aegis hook gate: hard policy."""

from __future__ import annotations

import re
import shlex
import subprocess
from pathlib import Path

from .contracts import (
    GITHUB_GOVERNANCE_GRAPHQL_RE,
    GITHUB_GOVERNANCE_PATH_RE,
    HARD_POLICY_SHELLS,
    HARD_POLICY_SHELL_CONTROL_TOKENS,
    HardPolicyParseError,
    MUTATING_TASKMASTER_RE,
    RAW_BEADS_AUTHORITY_RE,
    RAW_DESTRUCTIVE_GIT_RE,
    RAW_DOLT_AUTHORITY_RE,
    RAW_NESTED_SYNTHESIS_RE,
    RAW_TASKMASTER_WRITE_RE,
    RAW_UNSUPPORTED_SYNTHESIS_RE,
    READ_ONLY_TEST_OUTPUT_OPTIONS,
)
from .decisions import _read_json_object
from .payloads import command_name, is_shell_assignment, safe_expanduser
from .runtime_state import current_git_branch


def raw_hard_policy_families(command: str) -> frozenset[str]:
    """Total, non-throwing preclassification independent of shell parsing.

    This deliberately overclassifies. Membership makes parser failure fail closed; it
    does not by itself prohibit a successfully parsed command.
    """

    try:
        families: set[str] = set()
        if RAW_DESTRUCTIVE_GIT_RE.search(command):
            families.add("destructive_git")
        if GITHUB_GOVERNANCE_PATH_RE.search(command) or GITHUB_GOVERNANCE_GRAPHQL_RE.search(
            command
        ):
            families.add("github_governance")
        if MUTATING_TASKMASTER_RE.search(command):
            families.add("taskmaster_mutation")
        if RAW_TASKMASTER_WRITE_RE.search(command):
            families.add("taskmaster_write")
        if RAW_BEADS_AUTHORITY_RE.search(command):
            families.add("beads_authority")
        if RAW_DOLT_AUTHORITY_RE.search(command):
            families.add("dolt_authority")
        if RAW_NESTED_SYNTHESIS_RE.search(command):
            families.add("nested_synthesis")
        return frozenset(families)
    except Exception:  # noqa: BLE001 - the preclassifier must be total and fail closed.
        return frozenset({"preclassifier_failure"})


def normalize_hard_policy_line_boundaries(command: str) -> str:
    """Turn unquoted CR/LF boundaries into shell separators before tokenization."""

    rendered: list[str] = []
    quote = ""
    escaped = False
    for character in command:
        if escaped:
            rendered.append(character)
            escaped = False
            continue
        if character == "\\" and quote != "'":
            rendered.append(character)
            escaped = True
            continue
        if quote:
            rendered.append(character)
            if character == quote:
                quote = ""
            continue
        if character in {"'", '"'}:
            quote = character
            rendered.append(character)
            continue
        rendered.append(";" if character in {"\r", "\n"} else character)
    return "".join(rendered)


def hard_policy_shell_segments(command: str) -> list[list[str]]:
    """Tokenize shell control flow without losing unquoted line boundaries."""

    try:
        lexer = shlex.shlex(
            normalize_hard_policy_line_boundaries(command),
            posix=True,
            punctuation_chars=";&|()",
        )
        lexer.whitespace_split = True
        lexer.commenters = ""
        raw_tokens = list(lexer)
    except ValueError as exc:
        raise HardPolicyParseError(str(exc)) from exc
    segments: list[list[str]] = []
    current: list[str] = []
    for token in raw_tokens:
        if token in HARD_POLICY_SHELL_CONTROL_TOKENS:
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments


def strip_hard_policy_prefixes(tokens: list[str]) -> list[str]:
    stripped = list(tokens)
    while stripped and is_shell_assignment(stripped[0]):
        stripped = stripped[1:]
    if stripped and command_name(stripped[0]) == "env":
        stripped = stripped[1:]
        while stripped:
            token = stripped[0]
            if is_shell_assignment(token) or token in {"-i", "--ignore-environment"}:
                stripped = stripped[1:]
                continue
            if token in {"-u", "--unset", "-C", "--chdir"} and len(stripped) >= 2:
                stripped = stripped[2:]
                continue
            break
    while stripped and command_name(stripped[0]) in {"command", "builtin", "nohup"}:
        stripped = stripped[1:]
        while stripped and stripped[0].startswith("-"):
            stripped = stripped[1:]
    return stripped


def nested_shell_command(tokens: list[str]) -> str | None:
    if not tokens or command_name(tokens[0]) not in HARD_POLICY_SHELLS:
        return None
    for index, token in enumerate(tokens[1:], start=1):
        if token == "--command" or (
            token.startswith("-") and not token.startswith("--") and "c" in token[1:]
        ):
            return tokens[index + 1] if index + 1 < len(tokens) else None
        if not token.startswith("-"):
            break
    return None


def git_invocation(tokens: list[str], root: Path) -> tuple[Path, str, list[str]] | None:
    tokens = strip_hard_policy_prefixes(tokens)
    if not tokens or command_name(tokens[0]) != "git":
        return None
    index = 1
    git_root = root
    options_with_values = {
        "-c",
        "--config-env",
        "--exec-path",
        "--git-dir",
        "--namespace",
        "--super-prefix",
        "--work-tree",
    }
    while index < len(tokens):
        token = tokens[index]
        if token == "--":
            index += 1
            break
        if token == "-C" and index + 1 < len(tokens):
            candidate = safe_expanduser(tokens[index + 1])
            try:
                git_root = (
                    (git_root / candidate).resolve()
                    if not candidate.is_absolute()
                    else candidate.resolve()
                )
            except (OSError, RuntimeError, ValueError):
                pass
            index += 2
            continue
        if token.startswith("-C") and token != "-C":
            candidate = safe_expanduser(token[2:])
            try:
                git_root = (
                    (git_root / candidate).resolve()
                    if not candidate.is_absolute()
                    else candidate.resolve()
                )
            except (OSError, RuntimeError, ValueError):
                pass
            index += 1
            continue
        if token in options_with_values:
            index += 2
            continue
        if any(
            token.startswith(f"{option}=")
            for option in options_with_values
            if option.startswith("--")
        ):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        return git_root, token.lower(), tokens[index + 1 :]
    return None


def delivery_default_branch(root: Path) -> str:
    policy = _read_json_object(root / "aegis.delivery-policy.json")
    repository = policy.get("repository") if isinstance(policy.get("repository"), dict) else {}
    configured = str(repository.get("default_branch") or "").strip()
    if configured:
        return configured
    result = subprocess.run(
        ["git", "-C", str(root), "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode == 0 and "/" in result.stdout.strip():
        return result.stdout.strip().split("/", 1)[1]
    return "main"


def short_option_enabled(args: list[str], option: str) -> bool:
    for token in args:
        if token == "--":
            break
        if token.startswith("-") and not token.startswith("--") and option in token[1:]:
            return True
    return False


def option_positionals(args: list[str], value_options: set[str]) -> list[str]:
    positionals: list[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--":
            positionals.extend(args[index + 1 :])
            break
        if token in value_options:
            index += 2
            continue
        if any(
            token.startswith(f"{option}=") for option in value_options if option.startswith("--")
        ):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        positionals.append(token)
        index += 1
    return positionals


def refspec_targets_branch(refspec: str, branch: str, current_branch: str) -> bool:
    if refspec.startswith("+"):
        return True
    clean = refspec
    destination = clean.split(":", 1)[1] if ":" in clean else clean
    destination = destination.removeprefix("refs/heads/")
    if "*" in destination:
        return True
    if destination == branch:
        return True
    return destination in {"@", "HEAD"} and current_branch == branch


def git_push_violation(git_root: Path, args: list[str], protected_branch: str) -> str | None:
    force_flags = {"--force", "--force-if-includes"}
    destructive_flags = {"--all", "--delete", "--mirror", "--prune"}
    if short_option_enabled(args, "f") or any(
        token in force_flags or token.startswith("--force-with-lease") for token in args
    ):
        return "force-pushing is prohibited"
    if any(token in destructive_flags for token in args):
        return "broad or deleting pushes are prohibited"
    positionals = option_positionals(
        args,
        {"--exec", "--push-option", "--receive-pack", "--repo", "-o"},
    )
    current_branch = current_git_branch(git_root)
    refspecs = positionals[1:] if positionals else []
    if not refspecs:
        if current_branch == protected_branch:
            return f"implicit push from protected branch {protected_branch!r} is prohibited"
        return None
    for refspec in refspecs:
        if refspec_targets_branch(refspec, protected_branch, current_branch):
            return f"direct push to protected branch {protected_branch!r} is prohibited"
    return None


def git_config_remote_violation(args: list[str]) -> str | None:
    mutation_flags = {
        "--add",
        "--remove-section",
        "--rename-section",
        "--replace-all",
        "--unset",
        "--unset-all",
    }
    positionals = option_positionals(
        args,
        {"--file", "--fixed-value", "--type", "--value", "--worktree"},
    )
    sensitive_indexes = [
        index
        for index, token in enumerate(positionals)
        if re.fullmatch(
            r"(?:remote\.[^.]+\.(?:pushurl|url)|url\..+\.insteadof)", token, re.IGNORECASE
        )
    ]
    if not sensitive_indexes:
        return None
    if any(token in mutation_flags for token in args):
        return "mutating remote URL configuration is prohibited"
    if any(index + 1 < len(positionals) for index in sensitive_indexes):
        return "replacing a remote URL is prohibited"
    return None


def destructive_git_violation(tokens: list[str], root: Path) -> str | None:
    invocation = git_invocation(tokens, root)
    if invocation is None:
        return None
    git_root, subcommand, args = invocation
    protected_branch = delivery_default_branch(git_root)
    if subcommand == "reset" and any(mode in args for mode in {"--hard", "--keep", "--merge"}):
        return "git reset with a worktree-discarding mode is prohibited"
    if subcommand == "clean" and not ("--dry-run" in args or short_option_enabled(args, "n")):
        return "git clean is prohibited unless it is a dry run"
    if subcommand == "push":
        return git_push_violation(git_root, args, protected_branch)
    if subcommand == "checkout":
        if "--force" in args or short_option_enabled(args, "f"):
            return "forced checkout is prohibited"
        if "--" in args and args.index("--") + 1 < len(args):
            return "checkout-based worktree restoration is prohibited"
    if subcommand == "switch" and (
        "--discard-changes" in args or "--force" in args or short_option_enabled(args, "f")
    ):
        return "forced branch switching is prohibited"
    if subcommand == "restore":
        staged_only = ("--staged" in args or short_option_enabled(args, "S")) and not (
            "--worktree" in args or short_option_enabled(args, "W")
        )
        if not staged_only:
            return "worktree restoration is prohibited; index-only `git restore --staged` remains allowed"
    if subcommand == "branch" and ("-D" in args or ("--delete" in args and "--force" in args)):
        return "forced local branch deletion is prohibited"
    if subcommand == "remote" and args and args[0] in {"remove", "rename", "rm", "set-url"}:
        return "remote replacement or removal is prohibited"
    if subcommand == "config":
        return git_config_remote_violation(args)
    return None


def option_argument(tokens: list[str], *options: str) -> str | None:
    for index, token in enumerate(tokens):
        if token in options and index + 1 < len(tokens):
            return tokens[index + 1]
        for option in options:
            if token.startswith(f"{option}="):
                return token[len(option) + 1 :]
            if (
                option.startswith("-")
                and not option.startswith("--")
                and token.startswith(option)
                and token != option
            ):
                return token[len(option) :]
    return None


def github_governance_violation(tokens: list[str]) -> str | None:
    tokens = strip_hard_policy_prefixes(tokens)
    if not tokens:
        return None
    name = command_name(tokens[0])
    joined = " ".join(tokens)
    if name not in {"curl", "gh"}:
        return None
    if GITHUB_GOVERNANCE_GRAPHQL_RE.search(joined):
        return "GitHub branch-protection or ruleset GraphQL mutation is prohibited"
    if not GITHUB_GOVERNANCE_PATH_RE.search(joined):
        return None
    if name == "gh" and len(tokens) >= 2 and tokens[1] == "api":
        method = (option_argument(tokens[2:], "--method", "-X") or "").upper()
        has_data = any(
            token in {"--field", "--input", "--raw-field", "-F", "-f"}
            or token.startswith(("--field=", "--input=", "--raw-field=", "-F", "-f"))
            for token in tokens[2:]
        )
        effective_method = method or ("POST" if has_data else "GET")
        if effective_method not in {"GET", "HEAD"}:
            return "GitHub branch-protection or ruleset mutation is prohibited"
    if name == "curl":
        method = (option_argument(tokens[1:], "--request", "-X") or "").upper()
        has_data = any(
            token
            in {
                "--data",
                "--data-binary",
                "--data-raw",
                "--form",
                "--json",
                "--upload-file",
                "-d",
                "-F",
                "-T",
            }
            or token.startswith(
                ("--data=", "--data-binary=", "--data-raw=", "--form=", "--json=", "-d", "-F", "-T")
            )
            for token in tokens[1:]
        )
        effective_method = method or ("POST" if has_data else "GET")
        if effective_method not in {"GET", "HEAD"}:
            return "GitHub branch-protection or ruleset mutation is prohibited"
    return None


def hard_policy_violations(command: str, root: Path, *, depth: int = 0) -> list[str]:
    if depth > 2:
        return ["nested shell command exceeds the destructive-operation inspection limit"]
    families = raw_hard_policy_families(command)
    sensitive_families = families - {"nested_synthesis"}
    if sensitive_families and RAW_UNSUPPORTED_SYNTHESIS_RE.search(command):
        return ["sensitive hard-policy command uses unsupported shell synthesis or concealment"]
    try:
        shell_segments = hard_policy_shell_segments(command)
    except HardPolicyParseError as exc:
        if families:
            return [f"hard-policy shell parse failed closed ({exc})"]
        return []
    violations: list[str] = []
    for raw_tokens in shell_segments:
        tokens = strip_hard_policy_prefixes(raw_tokens)
        if not tokens:
            continue
        nested = nested_shell_command(tokens)
        if nested is not None:
            violations.extend(hard_policy_violations(nested, root, depth=depth + 1))
            continue
        git_violation = destructive_git_violation(tokens, root)
        if git_violation:
            violations.append(git_violation)
        governance_violation = github_governance_violation(tokens)
        if governance_violation:
            violations.append(governance_violation)
    return sorted(set(violations))


def has_read_only_test_output_option(tokens: list[str]) -> bool:
    for token in tokens:
        if token in READ_ONLY_TEST_OUTPUT_OPTIONS:
            return True
        if any(token.startswith(f"{option}=") for option in READ_ONLY_TEST_OUTPUT_OPTIONS):
            return True
        if token.startswith("--cov-report=") and token != "--cov-report=term":
            return True
    return False
