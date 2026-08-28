# Managed by codex-starter-pack. This file contains no secret material.
_codex_gpg_readiness_expected="${HOME}/.local/bin/codex-gpg-readiness"
if (( ${+CODEX_GPG_READINESS_BIN} )); then
    if [[ "$CODEX_GPG_READINESS_BIN" != "$_codex_gpg_readiness_expected" ]]; then
        echo "GPG readiness helper path drift: $CODEX_GPG_READINESS_BIN" >&2
        unset _codex_gpg_readiness_expected
        return 1
    fi
else
    typeset -gr CODEX_GPG_READINESS_BIN="$_codex_gpg_readiness_expected"
fi
unset _codex_gpg_readiness_expected

function gpg_cache_ready {
    [[ -x "$CODEX_GPG_READINESS_BIN" ]] || return 1
    "$CODEX_GPG_READINESS_BIN" check >/dev/null 2>&1
}

function gpg-unlock {
    if [[ ! -x "$CODEX_GPG_READINESS_BIN" ]]; then
        echo "GPG readiness helper is missing: $CODEX_GPG_READINESS_BIN" >&2
        return 1
    fi
    "$CODEX_GPG_READINESS_BIN" unlock
}
