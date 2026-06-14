#!/usr/bin/env bash
# Pre-commit secret guard (TM 222). Blocks a commit whose STAGED added lines contain a
# high-confidence API-key pattern. Added after the 2026-06-14 incident where a tracked
# .claude.json exposed real Firecrawl + ElevenLabs keys when the repo went public.
#
# Scope: only high-prefix, low-false-positive patterns. This is a backstop, not a full
# scanner — real keys belong in gitignored local config, never in tracked files.
set -u

# Known real-key shapes (provider prefix + sufficient length to avoid matching regexes/docs).
PATTERNS=(
  'fc-[A-Za-z0-9]{24,}'                 # Firecrawl
  'sk-ant-[A-Za-z0-9_-]{24,}'           # Anthropic
  'sk-[A-Za-z0-9]{32,}'                 # OpenAI
  'sk_[A-Za-z0-9]{32,}'                 # ElevenLabs / Stripe-style
  'AIza[A-Za-z0-9_-]{35}'               # Google
  'xai-[A-Za-z0-9]{24,}'               # xAI
  'pplx-[A-Za-z0-9]{24,}'              # Perplexity
)

# Staged added lines only (exclude this guard and the pre-commit config, which carry the
# patterns themselves as literals).
added="$(git diff --cached --no-color -U0 \
  -- . ':(exclude).claude/scripts/secret-scan.sh' ':(exclude).pre-commit-config.yaml' \
  | grep -E '^\+' | grep -Ev '^\+\+\+')"

hit=0
for pat in "${PATTERNS[@]}"; do
  if printf '%s\n' "$added" | grep -Eq "$pat"; then
    # Report the pattern that matched, never the secret value.
    echo "BLOCKED: staged content matches a secret pattern: ${pat%%[*}…" >&2
    hit=1
  fi
done

if [ "$hit" -ne 0 ]; then
  echo "" >&2
  echo "A high-confidence API key appears in staged changes. Remove it; real keys belong" >&2
  echo "in a gitignored local config (e.g. .claude.json), never in tracked files." >&2
  echo "If this is a false positive, scrub the value or adjust .claude/scripts/secret-scan.sh." >&2
  exit 1
fi
exit 0
