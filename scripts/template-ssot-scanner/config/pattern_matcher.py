#!/usr/bin/env python3
"""Allowlist/blocklist pattern matching for scanner configuration."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from fnmatch import fnmatchcase
from typing import Any, Mapping, Sequence

from .config_loader import ConfigLoader

ALL_RULES = "all"


class PatternMatcherError(ValueError):
    """Base exception for pattern matcher failures."""


class PatternConfigError(PatternMatcherError):
    """Raised when a configured pattern entry is invalid."""


class PatternTarget(str, Enum):
    """Pattern target groups supported by the scanner config."""

    PATHS = "paths"
    REFERENCES = "references"


class PatternGroup(str, Enum):
    """Pattern source group."""

    ALLOWLIST = "allowlists"
    BLOCKLIST = "blocklists"


class PatternKind(str, Enum):
    """Pattern syntax supported by the matcher."""

    GLOB = "glob"
    REGEX = "regex"


@dataclass(frozen=True)
class PatternEntry:
    """Compiled allowlist/blocklist pattern entry."""

    group: PatternGroup
    target: PatternTarget
    pattern: str
    kind: PatternKind
    rules: tuple[str, ...] = field(default_factory=tuple)
    reason: str = ""
    expires: date | None = None
    _compiled_regex: re.Pattern[str] | None = field(default=None, repr=False, compare=False)

    @classmethod
    def from_mapping(
        cls,
        group: PatternGroup | str,
        target: PatternTarget | str,
        mapping: Mapping[str, Any],
    ) -> "PatternEntry":
        """Create a compiled pattern entry from config data."""
        pattern_group = PatternGroup(group)
        pattern_target = PatternTarget(target)

        pattern = mapping.get("pattern")
        if not isinstance(pattern, str) or not pattern:
            raise PatternConfigError("Pattern entry requires a non-empty string 'pattern'")

        try:
            kind = PatternKind(mapping.get("kind"))
        except ValueError as exc:
            valid = ", ".join(kind.value for kind in PatternKind)
            raise PatternConfigError(f"Invalid pattern kind {mapping.get('kind')!r}. Expected one of: {valid}") from exc

        rules = mapping.get("rules", ())
        if rules is None:
            rules = ()
        if not isinstance(rules, Sequence) or isinstance(rules, (str, bytes)):
            raise PatternConfigError("Pattern entry 'rules' must be a sequence of strings")
        rule_tuple = tuple(str(rule) for rule in rules)

        reason = mapping.get("reason", "")
        if not isinstance(reason, str):
            raise PatternConfigError("Pattern entry 'reason' must be a string")

        expires = _parse_expiration(mapping.get("expires"))
        compiled_regex = None
        if kind == PatternKind.REGEX:
            try:
                compiled_regex = re.compile(pattern)
            except re.error as exc:
                raise PatternConfigError(f"Invalid regex pattern {pattern!r}: {exc}") from exc

        return cls(
            group=pattern_group,
            target=pattern_target,
            pattern=pattern,
            kind=kind,
            rules=rule_tuple,
            reason=reason,
            expires=expires,
            _compiled_regex=compiled_regex,
        )

    def applies_to_rule(self, rule_name: str | None) -> bool:
        """Return whether this pattern applies to a rule."""
        if not self.rules:
            return True
        if ALL_RULES in self.rules:
            return True
        if rule_name is None:
            return True
        return rule_name in self.rules

    def is_expired(self, today: date | None = None) -> bool:
        """Return whether this entry is expired."""
        if self.expires is None:
            return False
        effective_today = today or date.today()
        return self.expires < effective_today

    def matches(self, value: str, rule_name: str | None = None, today: date | None = None) -> bool:
        """Return whether this active entry matches a value for an optional rule."""
        if self.is_expired(today):
            return False
        if not self.applies_to_rule(rule_name):
            return False

        candidate = normalize_match_value(value)
        if self.kind == PatternKind.GLOB:
            return fnmatchcase(candidate, self.pattern)
        if self._compiled_regex is None:
            raise PatternConfigError(f"Regex pattern {self.pattern!r} was not compiled")
        return self._compiled_regex.search(candidate) is not None

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable pattern entry."""
        return {
            "group": self.group.value,
            "target": self.target.value,
            "pattern": self.pattern,
            "kind": self.kind.value,
            "rules": list(self.rules),
            "reason": self.reason,
            "expires": self.expires.isoformat() if self.expires else None,
        }


@dataclass(frozen=True)
class PatternMatch:
    """Single pattern match result."""

    entry: PatternEntry
    value: str
    rule_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = self.entry.to_dict()
        payload["value"] = self.value
        if self.rule_name is not None:
            payload["rule_name"] = self.rule_name
        return payload


@dataclass(frozen=True)
class PatternDecision:
    """Allow/block decision for a value."""

    value: str
    target: PatternTarget
    rule_name: str | None = None
    allowed: bool = False
    blocked: bool = False
    allow_matches: tuple[PatternMatch, ...] = field(default_factory=tuple)
    block_matches: tuple[PatternMatch, ...] = field(default_factory=tuple)

    @property
    def status(self) -> str:
        """Return block-wins decision status."""
        if self.blocked:
            return "blocked"
        if self.allowed:
            return "allowed"
        return "neutral"

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "value": self.value,
            "target": self.target.value,
            "status": self.status,
            "allowed": self.allowed,
            "blocked": self.blocked,
            "allow_matches": [match.to_dict() for match in self.allow_matches],
            "block_matches": [match.to_dict() for match in self.block_matches],
        }
        if self.rule_name is not None:
            payload["rule_name"] = self.rule_name
        return payload


class PatternMatcher:
    """Matcher for configured allowlist and blocklist path/reference entries."""

    def __init__(self, entries: Sequence[PatternEntry] | None = None) -> None:
        self._entries = tuple(entries or ())

    @classmethod
    def from_config_loader(cls, loader: ConfigLoader | None = None) -> "PatternMatcher":
        """Create a matcher from a ConfigLoader config."""
        config_loader = loader or ConfigLoader.get_instance()
        return cls.from_config(config_loader.load())

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> "PatternMatcher":
        """Create a matcher from a loaded config mapping."""
        entries: list[PatternEntry] = []
        for group in (PatternGroup.ALLOWLIST, PatternGroup.BLOCKLIST):
            raw_group = config.get(group.value, {})
            if raw_group is None:
                continue
            if not isinstance(raw_group, Mapping):
                raise PatternConfigError(f"Config field {group.value!r} must be a mapping")

            for target in PatternTarget:
                raw_entries = raw_group.get(target.value, [])
                if raw_entries is None:
                    continue
                if not isinstance(raw_entries, Sequence) or isinstance(raw_entries, (str, bytes)):
                    raise PatternConfigError(f"Config field {group.value}.{target.value} must be a list")
                for raw_entry in raw_entries:
                    if not isinstance(raw_entry, Mapping):
                        raise PatternConfigError(f"Config field {group.value}.{target.value} entries must be mappings")
                    entries.append(PatternEntry.from_mapping(group, target, raw_entry))
        return cls(entries)

    def entries(
        self,
        group: PatternGroup | str | None = None,
        target: PatternTarget | str | None = None,
        include_expired: bool = False,
        today: date | None = None,
    ) -> tuple[PatternEntry, ...]:
        """Return configured entries, optionally filtered by group/target."""
        selected_group = PatternGroup(group) if group is not None else None
        selected_target = PatternTarget(target) if target is not None else None
        output = []
        for entry in self._entries:
            if selected_group and entry.group != selected_group:
                continue
            if selected_target and entry.target != selected_target:
                continue
            if not include_expired and entry.is_expired(today):
                continue
            output.append(copy.deepcopy(entry))
        return tuple(output)

    def match(
        self,
        value: str,
        target: PatternTarget | str,
        group: PatternGroup | str | None = None,
        rule_name: str | None = None,
        today: date | None = None,
    ) -> tuple[PatternMatch, ...]:
        """Return active pattern matches for a value."""
        selected_target = PatternTarget(target)
        selected_group = PatternGroup(group) if group is not None else None
        matches = []
        for entry in self._entries:
            if entry.target != selected_target:
                continue
            if selected_group and entry.group != selected_group:
                continue
            if entry.matches(value, rule_name=rule_name, today=today):
                matches.append(PatternMatch(entry=copy.deepcopy(entry), value=normalize_match_value(value), rule_name=rule_name))
        return tuple(matches)

    def decide(
        self,
        value: str,
        target: PatternTarget | str,
        rule_name: str | None = None,
        today: date | None = None,
    ) -> PatternDecision:
        """Return block-wins allow/block decision for a value."""
        selected_target = PatternTarget(target)
        allow_matches = self.match(value, selected_target, PatternGroup.ALLOWLIST, rule_name, today)
        block_matches = self.match(value, selected_target, PatternGroup.BLOCKLIST, rule_name, today)
        return PatternDecision(
            value=normalize_match_value(value),
            target=selected_target,
            rule_name=rule_name,
            allowed=bool(allow_matches),
            blocked=bool(block_matches),
            allow_matches=allow_matches,
            block_matches=block_matches,
        )

    def is_allowed(self, value: str, target: PatternTarget | str, rule_name: str | None = None) -> bool:
        """Return whether a value is explicitly allowed and not blocked."""
        decision = self.decide(value, target, rule_name)
        return decision.status == "allowed"

    def is_blocked(self, value: str, target: PatternTarget | str, rule_name: str | None = None) -> bool:
        """Return whether a value is blocked."""
        return self.decide(value, target, rule_name).blocked


def normalize_match_value(value: str) -> str:
    """Normalize configured match values to POSIX-style strings."""
    normalized = str(value).replace("\\", "/")
    if normalized.startswith("./"):
        return normalized[2:]
    return normalized


def _parse_expiration(raw_expires: Any) -> date | None:
    if raw_expires is None:
        return None
    if isinstance(raw_expires, date):
        return raw_expires
    if not isinstance(raw_expires, str):
        raise PatternConfigError("Pattern entry 'expires' must be a date string or null")
    try:
        return date.fromisoformat(raw_expires)
    except ValueError as exc:
        raise PatternConfigError(f"Invalid pattern expiration date {raw_expires!r}") from exc
