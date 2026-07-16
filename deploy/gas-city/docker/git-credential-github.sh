#!/usr/bin/env bash
set -euo pipefail

[[ ${1:-} == get ]] || exit 0
: "${GC_GITHUB_TOKEN_FILE:?GC_GITHUB_TOKEN_FILE is required}"
[[ -r "$GC_GITHUB_TOKEN_FILE" ]]

host=
while IFS='=' read -r key value; do
  [[ -n "$key" ]] || break
  if [[ "$key" == host ]]; then
    host=$value
  fi
done
[[ "$host" == github.com ]] || exit 0

printf 'username=x-access-token\n'
printf 'password=%s\n' "$(<"$GC_GITHUB_TOKEN_FILE")"
