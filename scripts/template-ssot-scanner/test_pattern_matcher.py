#!/usr/bin/env python3
"""Tests for scanner allowlist/blocklist pattern matching."""

import sys
import time
from datetime import date
from pathlib import Path

import pytest

SCANNER_DIR = Path(__file__).resolve().parent

if str(SCANNER_DIR) not in sys.path:
    sys.path.insert(0, str(SCANNER_DIR))

from config.config_loader import ConfigLoader  # noqa: E402
from config.pattern_matcher import (  # noqa: E402
    PatternConfigError,
    PatternEntry,
    PatternGroup,
    PatternKind,
    PatternMatcher,
    PatternTarget,
    normalize_match_value,
)


@pytest.fixture(autouse=True)
def reset_config_loader_singletons():
    ConfigLoader.reset_instances_for_tests()
    yield
    ConfigLoader.reset_instances_for_tests()


def test_pattern_entry_matches_glob_paths_and_normalizes_backslashes():
    entry = PatternEntry.from_mapping(
        PatternGroup.ALLOWLIST,
        PatternTarget.PATHS,
        {
            "pattern": "templates/legacy/**",
            "kind": "glob",
            "rules": ["migrated_monolith_references"],
            "reason": "temporary",
            "expires": None,
        },
    )

    assert entry.kind == PatternKind.GLOB
    assert entry.matches(r".\templates\legacy\old.md", "migrated_monolith_references")
    assert not entry.matches("templates/current/new.md", "migrated_monolith_references")


def test_pattern_entry_matches_regex_references():
    entry = PatternEntry.from_mapping(
        "allowlists",
        "references",
        {
            "pattern": r"^https://example\.invalid/",
            "kind": "regex",
            "rules": ["broken_references"],
            "reason": "example",
            "expires": None,
        },
    )

    assert entry.matches("https://example.invalid/path", "broken_references")
    assert not entry.matches("https://openai.com/", "broken_references")


def test_pattern_entry_rule_scoping_supports_exact_all_and_unspecified_rules():
    exact = PatternEntry.from_mapping(
        "allowlists",
        "paths",
        {"pattern": "**/*.md", "kind": "glob", "rules": ["broken_references"], "reason": "exact"},
    )
    all_rules = PatternEntry.from_mapping(
        "blocklists",
        "paths",
        {"pattern": ".codex/cache/**", "kind": "glob", "rules": ["all"], "reason": "all"},
    )
    unspecified = PatternEntry.from_mapping(
        "allowlists",
        "paths",
        {"pattern": "docs/**", "kind": "glob", "reason": "all by omission"},
    )

    assert exact.matches("templates/a.md", "broken_references")
    assert not exact.matches("templates/a.md", "duplicate_references")
    assert exact.matches("templates/a.md", None)
    assert all_rules.matches(".codex/cache/generated.json", "any_rule")
    assert unspecified.matches("docs/readme.md", "any_rule")


def test_pattern_entry_ignores_expired_entries():
    entry = PatternEntry.from_mapping(
        "allowlists",
        "paths",
        {
            "pattern": "legacy/**",
            "kind": "glob",
            "rules": ["all"],
            "reason": "expired",
            "expires": "2026-01-01",
        },
    )

    assert not entry.matches("legacy/file.md", today=date(2026, 4, 30))
    assert entry.matches("legacy/file.md", today=date(2025, 12, 31))


def test_pattern_matcher_loads_allowlist_and_blocklist_from_config():
    loader = ConfigLoader.get_instance(SCANNER_DIR / "config" / "examples" / "scanner_config.example.yaml")
    matcher = PatternMatcher.from_config_loader(loader)

    path_entries = matcher.entries(target="paths")

    assert any(entry.pattern == "templates/legacy/**" for entry in path_entries)
    assert any(entry.pattern == ".codex/cache/**" for entry in path_entries)


def test_pattern_matcher_decision_allows_allowed_paths():
    matcher = PatternMatcher.from_config(
        {
            "allowlists": {
                "paths": [
                    {
                        "pattern": "templates/legacy/**",
                        "kind": "glob",
                        "rules": ["migrated_monolith_references"],
                        "reason": "temporary",
                    }
                ]
            },
            "blocklists": {"paths": [], "references": []},
        }
    )

    decision = matcher.decide("templates/legacy/old.md", "paths", "migrated_monolith_references")

    assert decision.status == "allowed"
    assert decision.allowed
    assert not decision.blocked
    assert decision.allow_matches[0].entry.reason == "temporary"


def test_pattern_matcher_blocklist_wins_over_allowlist():
    matcher = PatternMatcher.from_config(
        {
            "allowlists": {
                "paths": [
                    {"pattern": ".codex/**", "kind": "glob", "rules": ["all"], "reason": "broad allow"}
                ]
            },
            "blocklists": {
                "paths": [
                    {"pattern": ".codex/cache/**", "kind": "glob", "rules": ["all"], "reason": "runtime cache"}
                ]
            },
        }
    )

    decision = matcher.decide(".codex/cache/generated.json", "paths", "broken_references")

    assert decision.status == "blocked"
    assert decision.allowed
    assert decision.blocked
    assert matcher.is_blocked(".codex/cache/generated.json", "paths", "broken_references")
    assert not matcher.is_allowed(".codex/cache/generated.json", "paths", "broken_references")


def test_pattern_matcher_handles_reference_patterns_separately_from_paths():
    matcher = PatternMatcher.from_config(
        {
            "allowlists": {
                "references": [
                    {
                        "pattern": r"^https://example\.invalid/",
                        "kind": "regex",
                        "rules": ["broken_references"],
                        "reason": "example domain",
                    }
                ]
            },
            "blocklists": {"paths": [], "references": []},
        }
    )

    assert matcher.decide("https://example.invalid/ref", "references", "broken_references").status == "allowed"
    assert matcher.decide("https://example.invalid/ref", "paths", "broken_references").status == "neutral"


def test_pattern_matcher_decision_serializes_matches():
    matcher = PatternMatcher.from_config(
        {
            "allowlists": {
                "paths": [
                    {"pattern": "docs/**", "kind": "glob", "rules": ["all"], "reason": "docs"}
                ]
            }
        }
    )

    payload = matcher.decide("./docs/readme.md", "paths", "broken_references").to_dict()

    assert payload["status"] == "allowed"
    assert payload["value"] == "docs/readme.md"
    assert payload["allow_matches"][0]["pattern"] == "docs/**"
    assert payload["allow_matches"][0]["rule_name"] == "broken_references"


@pytest.mark.parametrize(
    "mapping, expected",
    [
        ({"pattern": "", "kind": "glob", "reason": "bad"}, "non-empty"),
        ({"pattern": "**", "kind": "prefix", "reason": "bad"}, "Invalid pattern kind"),
        ({"pattern": "**", "kind": "glob", "rules": "all", "reason": "bad"}, "rules"),
        ({"pattern": "**", "kind": "glob", "reason": []}, "reason"),
        ({"pattern": "[", "kind": "regex", "reason": "bad"}, "Invalid regex"),
        ({"pattern": "**", "kind": "glob", "reason": "bad", "expires": "not-a-date"}, "expiration"),
    ],
)
def test_pattern_entry_rejects_invalid_config(mapping, expected):
    with pytest.raises(PatternConfigError, match=expected):
        PatternEntry.from_mapping("allowlists", "paths", mapping)


@pytest.mark.parametrize(
    "config, expected",
    [
        ({"allowlists": []}, "allowlists"),
        ({"allowlists": {"paths": "templates/**"}}, "allowlists.paths"),
        ({"allowlists": {"paths": ["templates/**"]}}, "allowlists.paths entries"),
    ],
)
def test_pattern_matcher_rejects_invalid_group_shapes(config, expected):
    with pytest.raises(PatternConfigError, match=expected):
        PatternMatcher.from_config(config)


def test_pattern_matcher_filters_entries_and_expiration():
    matcher = PatternMatcher.from_config(
        {
            "allowlists": {
                "paths": [
                    {
                        "pattern": "legacy/**",
                        "kind": "glob",
                        "reason": "expired",
                        "expires": "2026-01-01",
                    }
                ],
                "references": [
                    {"pattern": r"^https://", "kind": "regex", "reason": "active"}
                ],
            }
        }
    )

    assert matcher.entries(target="paths", today=date(2026, 4, 30)) == ()
    assert len(matcher.entries(target="paths", include_expired=True, today=date(2026, 4, 30))) == 1
    assert len(matcher.entries(target="references", today=date(2026, 4, 30))) == 1


def test_normalize_match_value_converts_windows_and_relative_paths():
    assert normalize_match_value(r".\templates\legacy\file.md") == "templates/legacy/file.md"


def test_pattern_matcher_performance_is_predictable():
    matcher = PatternMatcher.from_config_loader(ConfigLoader.get_instance())

    start = time.perf_counter()
    for _ in range(1000):
        matcher.decide("templates/legacy/old.md", "paths", "migrated_monolith_references")
        matcher.decide(".codex/cache/generated.json", "paths", "broken_references")
        matcher.decide("https://example.invalid/ref", "references", "broken_references")
    elapsed = time.perf_counter() - start

    assert elapsed < 2.0
