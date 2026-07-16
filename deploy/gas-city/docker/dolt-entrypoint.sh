#!/usr/bin/env bash
set -euo pipefail
umask 077

: "${DOLT_DATABASE:?DOLT_DATABASE is required}"
: "${DOLT_APP_USER:?DOLT_APP_USER is required}"
: "${DOLT_ROOT_PASSWORD_FILE:?DOLT_ROOT_PASSWORD_FILE is required}"
: "${DOLT_APP_PASSWORD_FILE:?DOLT_APP_PASSWORD_FILE is required}"

[[ "$DOLT_DATABASE" =~ ^[a-z][a-z0-9_]{0,62}$ ]]
[[ "$DOLT_APP_USER" =~ ^[a-z][a-z0-9_]{0,31}$ ]]
[[ -r "$DOLT_ROOT_PASSWORD_FILE" && -r "$DOLT_APP_PASSWORD_FILE" ]]

root_password=$(<"$DOLT_ROOT_PASSWORD_FILE")
app_password=$(<"$DOLT_APP_PASSWORD_FILE")
password_pattern='^[A-Za-z0-9._~!@%+=:-]{32,128}$'
[[ "$root_password" =~ $password_pattern ]]
[[ "$app_password" =~ $password_pattern ]]
[[ "$root_password" != "$app_password" ]]

install -d -m 0700 "$DOLT_DATA_DIR" "$DOLT_DATA_DIR/.doltcfg"
dolt config --global --add user.name gas-city-runtime >/dev/null 2>&1 || true
dolt config --global --add user.email gas-city-runtime@localhost >/dev/null 2>&1 || true

database_dir="$DOLT_DATA_DIR/$DOLT_DATABASE"
if [[ ! -d "$database_dir/.dolt" ]]; then
  install -d -m 0700 "$database_dir"
  (
    cd "$database_dir"
    dolt init --name gas-city-runtime --email gas-city-runtime@localhost >/dev/null
  )
fi

bootstrap_marker="$DOLT_DATA_DIR/.credentials-initialized"
credential_digest=$(
  printf '%s\0%s' "$root_password" "$app_password" | sha256sum | cut -d ' ' -f 1
)
expected_marker="gas-city-dolt-credentials/v1:$credential_digest"
if [[ -e "$bootstrap_marker" ]]; then
  [[ -f "$bootstrap_marker" && ! -L "$bootstrap_marker" ]]
  [[ $(stat -c '%a' "$bootstrap_marker") == 600 ]]
  [[ $(<"$bootstrap_marker") == "$expected_marker" ]] || {
    printf 'Dolt credential files changed without an attended rotation\n' >&2
    exit 70
  }
fi
bootstrap_pid=""
bootstrap_sql_dir=""
bootstrap_sql_file=""
marker_temporary=""

cleanup_bootstrap_sql() {
  local cleanup_failed=0

  if [[ -n "$bootstrap_sql_file" ]] \
    && [[ -e "$bootstrap_sql_file" || -L "$bootstrap_sql_file" ]]; then
    rm -f -- "$bootstrap_sql_file" || cleanup_failed=1
  fi
  if [[ -n "$bootstrap_sql_dir" ]]; then
    if [[ -d "$bootstrap_sql_dir" && ! -L "$bootstrap_sql_dir" ]]; then
      rmdir -- "$bootstrap_sql_dir" || cleanup_failed=1
    elif [[ -e "$bootstrap_sql_dir" || -L "$bootstrap_sql_dir" ]]; then
      cleanup_failed=1
    fi
  fi

  if [[ "$cleanup_failed" -eq 0 ]]; then
    bootstrap_sql_file=""
    bootstrap_sql_dir=""
  fi
  return "$cleanup_failed"
}

cleanup_marker_temporary() {
  local cleanup_failed=0

  if [[ -n "$marker_temporary" ]] \
    && [[ -e "$marker_temporary" || -L "$marker_temporary" ]]; then
    rm -f -- "$marker_temporary" || cleanup_failed=1
  fi
  if [[ "$cleanup_failed" -eq 0 ]]; then
    marker_temporary=""
  fi
  return "$cleanup_failed"
}

stop_bootstrap() {
  if [[ -n "$bootstrap_pid" ]] && kill -0 "$bootstrap_pid" 2>/dev/null; then
    kill -TERM "$bootstrap_pid" 2>/dev/null || true
    wait "$bootstrap_pid" 2>/dev/null || true
  fi
  bootstrap_pid=""
}

cleanup_on_exit() {
  local exit_status=$?
  local cleanup_failed=0

  trap - EXIT HUP INT TERM
  cleanup_bootstrap_sql || cleanup_failed=1
  cleanup_marker_temporary || cleanup_failed=1
  stop_bootstrap
  if [[ "$exit_status" -eq 0 && "$cleanup_failed" -ne 0 ]]; then
    exit_status=74
  fi
  exit "$exit_status"
}

trap cleanup_on_exit EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

dolt sql-server --config /opt/gas-city/dolt-bootstrap.yaml &
bootstrap_pid=$!

ready=false
root_uses_secret=false
for _ in $(seq 1 60); do
  if [[ -f "$bootstrap_marker" ]]; then
    if DOLT_CLI_PASSWORD="$root_password" \
      dolt --host 127.0.0.1 --port 3306 --user root --no-tls sql \
      --query 'SELECT 1' >/dev/null 2>&1; then
      ready=true
      root_uses_secret=true
      break
    fi
  else
    if DOLT_CLI_PASSWORD= \
      dolt --host 127.0.0.1 --port 3306 --user root --no-tls sql \
      --query 'SELECT 1' >/dev/null 2>&1; then
      ready=true
      break
    fi
    if DOLT_CLI_PASSWORD="$root_password" \
      dolt --host 127.0.0.1 --port 3306 --user root --no-tls sql \
      --query 'SELECT 1' >/dev/null 2>&1; then
      ready=true
      root_uses_secret=true
      break
    fi
  fi
  sleep 0.25
done
[[ "$ready" == true ]]

if [[ ! -f "$bootstrap_marker" ]]; then
  # Compose mounts /tmp as a private tmpfs for this read-only container. Keep
  # credential-bearing SQL in a mode-0700 directory and pass it to Dolt only
  # over stdin: process argv must never contain either password.
  bootstrap_sql_dir=$(mktemp -d /tmp/gas-city-dolt-bootstrap.XXXXXX)
  chmod 0700 "$bootstrap_sql_dir"
  [[ -d "$bootstrap_sql_dir" && ! -L "$bootstrap_sql_dir" ]]
  [[ $(stat -c '%a' "$bootstrap_sql_dir") == 700 ]]
  bootstrap_sql_file="$bootstrap_sql_dir/bootstrap.sql"
  : >"$bootstrap_sql_file"
  chmod 0600 "$bootstrap_sql_file"
  [[ -f "$bootstrap_sql_file" && ! -L "$bootstrap_sql_file" ]]
  [[ $(stat -c '%a' "$bootstrap_sql_file") == 600 ]]
  {
    printf 'CREATE DATABASE IF NOT EXISTS `%s`;\n' "$DOLT_DATABASE"
    printf "CREATE USER IF NOT EXISTS '%s'@'%%' IDENTIFIED BY '%s';\n" \
      "$DOLT_APP_USER" "$app_password"
    printf "ALTER USER '%s'@'%%' IDENTIFIED BY '%s';\n" \
      "$DOLT_APP_USER" "$app_password"
    printf "GRANT ALL PRIVILEGES ON \`%s\`.* TO '%s'@'%%';\n" \
      "$DOLT_DATABASE" "$DOLT_APP_USER"
    printf "CREATE USER IF NOT EXISTS 'root'@'%%' IDENTIFIED BY '%s';\n" \
      "$root_password"
    printf "CREATE USER IF NOT EXISTS 'root'@'localhost' IDENTIFIED BY '%s';\n" \
      "$root_password"
    printf "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%%' WITH GRANT OPTION;\n"
    printf "ALTER USER 'root'@'%%' IDENTIFIED BY '%s';\n" "$root_password"
    printf "ALTER USER 'root'@'localhost' IDENTIFIED BY '%s';\n" \
      "$root_password"
    printf 'FLUSH PRIVILEGES;\n'
  } >"$bootstrap_sql_file"
  if [[ "$root_uses_secret" == true ]]; then
    DOLT_CLI_PASSWORD="$root_password" \
      dolt --host 127.0.0.1 --port 3306 --user root --no-tls sql \
      <"$bootstrap_sql_file" >/dev/null
  else
    DOLT_CLI_PASSWORD= \
      dolt --host 127.0.0.1 --port 3306 --user root --no-tls sql \
      <"$bootstrap_sql_file" >/dev/null
  fi
  # Refuse to commit the marker unless the secret-bearing tmpfs artifact has
  # been removed. The EXIT trap retries cleanup on every failure path.
  cleanup_bootstrap_sql
  marker_temporary=$(mktemp "$DOLT_DATA_DIR/.credentials-initialized.XXXXXX")
  chmod 0600 "$marker_temporary"
  printf '%s\n' "$expected_marker" >"$marker_temporary"
  mv "$marker_temporary" "$bootstrap_marker"
  marker_temporary=""
fi

DOLT_CLI_PASSWORD="$root_password" \
  dolt --host 127.0.0.1 --port 3306 --user root --no-tls --use-db "$DOLT_DATABASE" \
  sql --query 'SELECT 1' >/dev/null
DOLT_CLI_PASSWORD="$app_password" \
  dolt --host 127.0.0.1 --port 3306 --user "$DOLT_APP_USER" --no-tls \
  --use-db "$DOLT_DATABASE" sql --query 'SELECT 1' >/dev/null
stop_bootstrap
cleanup_bootstrap_sql
cleanup_marker_temporary

trap - EXIT HUP INT TERM
exec dolt sql-server --config /opt/gas-city/dolt-server.yaml
