#!/usr/bin/env bash
set -euo pipefail

: "${DOLT_APP_USER:?DOLT_APP_USER is required}"
: "${DOLT_DATABASE:?DOLT_DATABASE is required}"
: "${DOLT_ROOT_PASSWORD_FILE:?DOLT_ROOT_PASSWORD_FILE is required}"
: "${DOLT_APP_PASSWORD_FILE:?DOLT_APP_PASSWORD_FILE is required}"
[[ -r "$DOLT_ROOT_PASSWORD_FILE" && -r "$DOLT_APP_PASSWORD_FILE" ]]
DOLT_CLI_PASSWORD=$(<"$DOLT_ROOT_PASSWORD_FILE") \
  dolt --host 127.0.0.1 --port 3306 --user root --no-tls --use-db "$DOLT_DATABASE" \
  sql --query 'SELECT 1' >/dev/null
DOLT_CLI_PASSWORD=$(<"$DOLT_APP_PASSWORD_FILE")
export DOLT_CLI_PASSWORD
exec dolt --host 127.0.0.1 --port 3306 --user "$DOLT_APP_USER" --no-tls \
  --use-db "$DOLT_DATABASE" sql --query 'SELECT 1'
