#!/usr/bin/env python3
"""Security validation scanner for portable template/config files."""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from config.integration import ScannerConfigContext, create_scanner_config_context
from report_generator import save_scanner_report
from scan_core import collect_scannable_files, discover_config_dirs, relative_posix_path
from validation_interface import ValidationFinding, ValidationRule

SCANNER_NAME = "security_validator"
SCANNER_VERSION = "1.0.0"
DEFAULT_OUTPUT = Path(__file__).parent / "output/data/security_validation.json"

RULE_PATH_TRAVERSAL = "security_path_traversal"
RULE_TEMPLATE_INJECTION = "security_template_injection"
RULE_INLINE_SECRET = "security_inline_secret"

DEFAULT_RULES = {
    RULE_PATH_TRAVERSAL: ValidationRule(
        name=RULE_PATH_TRAVERSAL,
        category="security",
        severity="warning",
        threshold=0,
        enabled=True,
    ),
    RULE_TEMPLATE_INJECTION: ValidationRule(
        name=RULE_TEMPLATE_INJECTION,
        category="security",
        severity="warning",
        threshold=0,
        enabled=True,
    ),
    RULE_INLINE_SECRET: ValidationRule(
        name=RULE_INLINE_SECRET,
        category="security",
        severity="error",
        threshold=0,
        enabled=True,
    ),
}

TRAVERSAL_RE = re.compile(
    r"(?i)(?:\.\.[/\\]|%2e%2e(?:%2f|%5c|[/\\])|\.\.%2f|\.\.%5c)"
)
TRAVERSAL_TOKEN_RE = re.compile(
    r"(?i)([`'\"])(?P<quoted>[^`'\"]*(?:\.\.|%2e%2e)[^`'\"]*)\1|(?P<bare>[^\s,;)\]}]+(?:\.\.|%2e%2e)[^\s,;)\]}]*)"
)
TEMPLATE_EXPR_RE = re.compile(
    r"(?P<expr>\$\{\{[^\n]{0,240}?\}\}|\{\{[^\n]{0,240}?\}\}|<%=?[^\n]{0,240}?%>|\{%[^\n]{0,240}?%\})"
)
DANGEROUS_TEMPLATE_TERM_RE = re.compile(
    r"(?i)\b(?:env|secret|token|password|exec|eval|subprocess|os\.|process|constructor|import|open|system)\b|__"
)


@dataclass(frozen=True)
class SecretPattern:
    name: str
    regex: re.Pattern[str]
    secret_group: str | None = None


SECRET_PATTERNS = (
    SecretPattern(
        name="private_key_block",
        regex=re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    ),
    SecretPattern(
        name="aws_access_key_id",
        regex=re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    ),
    SecretPattern(
        name="github_token",
        regex=re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{36,255}\b"),
    ),
    SecretPattern(
        name="openai_key",
        regex=re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    ),
    SecretPattern(
        name="generic_secret_assignment",
        regex=re.compile(
            r"(?i)\b(?:api[_-]?key|token|secret|password|passwd|private[_-]?key)\b\s*[:=]\s*['\"]?(?P<secret>[A-Za-z0-9_./+=:@-]{16,})['\"]?"
        ),
        secret_group="secret",
    ),
)

PLACEHOLDER_MARKERS = (
    "example",
    "placeholder",
    "changeme",
    "change_me",
    "your_",
    "your-",
    "dummy",
    "fake",
    "redacted",
    "process.env",
    "env.",
    "xxxxx",
    "<",
    ">",
    "${",
    "{{",
)


class SecurityValidator:
    """Scan portable template/config files for local security-risk patterns."""

    def __init__(
        self,
        base_path: Path,
        *,
        config_context: ScannerConfigContext | None = None,
        config_path: Path | None = None,
        include_pattern: str | None = None,
        exclude_pattern: str | None = None,
        profile: str | None = None,
        environment: str | None = None,
        apply_environment_overrides: bool = False,
        environ: dict[str, str] | None = None,
    ) -> None:
        self.base_path = base_path.resolve()
        self.config_context = config_context or create_scanner_config_context(
            config_path,
            profile=profile,
            environment=environment,
            apply_environment_overrides=apply_environment_overrides,
            environ=environ,
        )
        self.file_config = self.config_context.file_discovery_config(
            self.base_path,
            include_pattern=include_pattern,
            exclude_pattern=exclude_pattern,
        )
        self.rules = self._resolve_rules(self.config_context)

    def validate(self) -> dict[str, Any]:
        """Return a deterministic security validation report."""
        files = self._collect_files()
        findings: list[ValidationFinding] = []

        for file_path in files:
            findings.extend(self._scan_file(file_path))

        finding_dicts = [finding.to_dict() for finding in sorted(findings, key=_finding_sort_key)]
        summary = _summarize_findings(finding_dicts)

        return {
            "security_validation_version": SCANNER_VERSION,
            "base_path": str(self.base_path),
            "config_source": self.config_context.source,
            "config_profile": self.config_context.profile,
            "config_environment": self.config_context.environment,
            "files_scanned": len(files),
            "rules": {
                name: {
                    "category": rule.category,
                    "severity": rule.severity,
                    "threshold": rule.threshold,
                }
                for name, rule in sorted(self.rules.items())
            },
            "summary": summary,
            "findings": finding_dicts,
        }

    def save(self, output_file: Path) -> dict[str, Any]:
        """Run validation and save a metadata-wrapped report."""
        start = time.perf_counter()
        report = self.validate()
        duration = time.perf_counter() - start
        save_scanner_report(
            data=report,
            output_file=output_file,
            scanner_name=SCANNER_NAME,
            version=SCANNER_VERSION,
            stats={
                "files_scanned": report["files_scanned"],
                "findings": report["summary"]["total_findings"],
                "errors": report["summary"]["severity_counts"].get("error", 0),
                "warnings": report["summary"]["severity_counts"].get("warning", 0),
            },
            duration_seconds=duration,
        )
        return report

    def _collect_files(self) -> list[Path]:
        roots = [self.base_path / "templates", *discover_config_dirs(self.base_path, self.file_config.config_dirs)]
        files: dict[str, Path] = {}
        for root in roots:
            if not root.exists():
                continue
            for file_path in collect_scannable_files(root, self.file_config):
                files[relative_posix_path(self.base_path, file_path)] = file_path
        return [files[key] for key in sorted(files)]

    def _scan_file(self, file_path: Path) -> list[ValidationFinding]:
        relative_path = relative_posix_path(self.base_path, file_path)
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="latin-1")

        findings: list[ValidationFinding] = []
        for line_number, line in enumerate(content.splitlines(), 1):
            findings.extend(self._path_traversal_findings(file_path, relative_path, line, line_number))
            findings.extend(self._template_injection_findings(relative_path, line, line_number))
            findings.extend(self._inline_secret_findings(relative_path, line, line_number))
        return findings

    def _path_traversal_findings(
        self,
        file_path: Path,
        relative_path: str,
        line: str,
        line_number: int,
    ) -> list[ValidationFinding]:
        rule = self.rules.get(RULE_PATH_TRAVERSAL)
        if rule is None or self._is_allowlisted(relative_path, RULE_PATH_TRAVERSAL):
            return []
        if not TRAVERSAL_RE.search(line):
            return []

        findings = []
        tokens = _extract_traversal_tokens(line)
        if not tokens:
            tokens = [TRAVERSAL_RE.search(line).group(0)]  # type: ignore[union-attr]

        for token in tokens:
            escapes_base = self._candidate_escapes_base(file_path, token)
            if escapes_base is False:
                continue
            if escapes_base is None and not _contains_encoded_traversal(token):
                continue
            column = max(line.find(token), 0) + 1
            findings.append(
                _finding(
                    rule,
                    "Potential path traversal reference",
                    source_file=relative_path,
                    line=line_number,
                    column=column,
                    rule_name=RULE_PATH_TRAVERSAL,
                    match_kind="path_traversal",
                    sample=_redact_sample(token),
                    escapes_base=escapes_base,
                )
            )
        return findings

    def _template_injection_findings(
        self,
        relative_path: str,
        line: str,
        line_number: int,
    ) -> list[ValidationFinding]:
        rule = self.rules.get(RULE_TEMPLATE_INJECTION)
        if rule is None or self._is_allowlisted(relative_path, RULE_TEMPLATE_INJECTION):
            return []

        findings = []
        for match in TEMPLATE_EXPR_RE.finditer(line):
            expr = match.group("expr")
            if not DANGEROUS_TEMPLATE_TERM_RE.search(expr):
                continue
            findings.append(
                _finding(
                    rule,
                    "High-risk template expression detected",
                    source_file=relative_path,
                    line=line_number,
                    column=match.start() + 1,
                    rule_name=RULE_TEMPLATE_INJECTION,
                    match_kind="template_expression",
                    sample=_redact_sample(expr),
                )
            )
        return findings

    def _inline_secret_findings(
        self,
        relative_path: str,
        line: str,
        line_number: int,
    ) -> list[ValidationFinding]:
        rule = self.rules.get(RULE_INLINE_SECRET)
        if rule is None or self._is_allowlisted(relative_path, RULE_INLINE_SECRET):
            return []

        findings = []
        seen_secret_values: set[str] = set()
        for pattern in SECRET_PATTERNS:
            for match in pattern.regex.finditer(line):
                secret_value = match.group(pattern.secret_group) if pattern.secret_group else match.group(0)
                if _looks_like_placeholder(secret_value):
                    continue
                if secret_value in seen_secret_values:
                    continue
                seen_secret_values.add(secret_value)
                findings.append(
                    _finding(
                        rule,
                        "Potential inline secret material detected",
                        source_file=relative_path,
                        line=line_number,
                        column=match.start() + 1,
                        rule_name=RULE_INLINE_SECRET,
                        match_kind=pattern.name,
                        sample=_redact_secret(secret_value),
                    )
                )
        return findings

    def _candidate_escapes_base(self, source_file: Path, token: str) -> bool | None:
        normalized = unquote(token.strip().strip("`'\"")).replace("\\", "/").split("#", 1)[0]
        if not normalized or "://" in normalized or normalized.startswith("mdc:"):
            return None
        if any(marker in normalized for marker in ("{", "}", "$", "*")):
            return None
        try:
            resolved = (source_file.parent / normalized).resolve(strict=False)
            resolved.relative_to(self.base_path)
            return False
        except ValueError:
            return True
        except OSError:
            return None

    def _is_allowlisted(self, relative_path: str, rule_name: str) -> bool:
        decision = self.config_context.pattern_matcher.decide(relative_path, "paths", rule_name)
        return decision.status == "allowed"

    @staticmethod
    def _resolve_rules(config_context: ScannerConfigContext) -> dict[str, ValidationRule]:
        configured_rules = config_context.validation_rules(enabled_only=False)
        rules: dict[str, ValidationRule] = {}
        for name, default_rule in DEFAULT_RULES.items():
            rule = configured_rules.get(name, default_rule)
            if rule.enabled:
                rules[name] = rule
        return rules


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan template/config files for local security validation findings.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --base /path/to/project
  %(prog)s --profile ci --output output/data/security_validation.json
        """,
    )
    parser.add_argument("--base", type=Path, default=Path.cwd(), help="Repository root to scan")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Metadata-wrapped JSON output path")
    parser.add_argument("--config", type=Path, default=Path(__file__).parent / "scanner_config.yaml")
    parser.add_argument("--profile", default=None, help="Named scanner config profile")
    parser.add_argument("--environment", default=None, help="Named scanner config environment overlay")
    parser.add_argument("--env-overrides", action="store_true", help="Apply CODEX_SCANNER_ environment overrides")
    parser.add_argument("--include", default=None, help="Optional include glob override")
    parser.add_argument("--exclude", default=None, help="Optional comma-separated exclude glob additions")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validator = SecurityValidator(
        args.base,
        config_path=args.config,
        include_pattern=args.include,
        exclude_pattern=args.exclude,
        profile=args.profile,
        environment=args.environment,
        apply_environment_overrides=args.env_overrides,
    )
    report = validator.save(args.output)
    summary = report["summary"]
    print(
        f"Security validation complete: {report['files_scanned']} files scanned, "
        f"{summary['total_findings']} findings"
    )
    print(f"Results saved to: {args.output}")
    return 0


def _extract_traversal_tokens(line: str) -> list[str]:
    tokens = []
    for match in TRAVERSAL_TOKEN_RE.finditer(line):
        token = match.group("quoted") or match.group("bare")
        if token:
            tokens.append(token.strip())
    return tokens


def _finding(
    rule: ValidationRule,
    message: str,
    *,
    source_file: str,
    line: int,
    column: int,
    rule_name: str,
    match_kind: str,
    sample: str,
    **extra_details: Any,
) -> ValidationFinding:
    details = {
        "rule_name": rule_name,
        "line": line,
        "column": column,
        "match_kind": match_kind,
        "sample": sample,
    }
    details.update({key: value for key, value in extra_details.items() if value is not None})
    return ValidationFinding(
        category=rule.category,
        severity=rule.severity,
        message=message,
        source_file=source_file,
        details=details,
    )


def _finding_sort_key(finding: ValidationFinding) -> tuple[Any, ...]:
    return (
        finding.source_file or "",
        finding.details.get("line", 0),
        finding.details.get("column", 0),
        finding.message,
        finding.details.get("match_kind", ""),
    )


def _summarize_findings(findings: list[dict[str, Any]]) -> dict[str, Any]:
    severity_counts = {"error": 0, "warning": 0, "info": 0}
    rule_counts: dict[str, int] = {}
    for finding in findings:
        severity = finding["severity"]
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        rule_name = finding.get("details", {}).get("rule_name", "unknown")
        rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1
    return {
        "total_findings": len(findings),
        "severity_counts": {key: count for key, count in severity_counts.items() if count},
        "rule_counts": dict(sorted(rule_counts.items())),
    }


def _redact_sample(value: str, *, max_length: int = 96) -> str:
    compact = " ".join(value.strip().split())
    if len(compact) <= max_length:
        return compact
    return f"{compact[: max_length - 3]}..."


def _redact_secret(value: str) -> str:
    compact = value.strip()
    if len(compact) <= 8:
        return "<redacted>"
    return f"{compact[:4]}...{compact[-4:]}"


def _looks_like_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in PLACEHOLDER_MARKERS)


def _contains_encoded_traversal(value: str) -> bool:
    return "%2e%2e" in value.lower() or "%2f" in value.lower() or "%5c" in value.lower()


if __name__ == "__main__":
    sys.exit(main())
