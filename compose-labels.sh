#!/usr/bin/env bash
# Sets the OCI revision and source labels. Precedence: input, then the caller's label, then the run default.
# Env: INPUT_LABELS REVISION SOURCE DEFAULT_REVISION DEFAULT_SOURCE. Writes labels to $GITHUB_OUTPUT.
set -euo pipefail

fail() { echo "::error::$*" >&2; exit 1; }

: "${GITHUB_OUTPUT:?}"
labels="${INPUT_LABELS:-}"
trim() { printf '%s' "$1" | sed -E '1s/^[[:space:]]+//; $s/[[:space:]]+$//'; }
REVISION="$(trim "${REVISION:-}")"
SOURCE="$(trim "${SOURCE:-}")"

revision_re='^[0-9a-f]{40,64}$'
source_re='^https://[A-Za-z0-9.-]+(:[0-9]+)?(/[A-Za-z0-9._-]+)*/?$'

resolve() {
  local key="$1" input="$2" default="$3" re="$4" what="$5" value
  local pattern="^org\.opencontainers\.image\.${key}="
  if [ -n "$input" ]; then
    value="$input"
  elif grep -qE "$pattern" <<< "$labels"; then
    return 0
  else
    value="$default"
  fi
  [[ "$value" =~ $re ]] || fail "$what"
  labels="$(grep -vE "$pattern" <<< "$labels" || true)"
  labels="${labels:+$labels$'\n'}org.opencontainers.image.${key}=${value}"
}

resolve revision "$REVISION" "${DEFAULT_REVISION:-}" "$revision_re" "revision is not a lowercase hex commit id"
resolve source "$SOURCE" "${DEFAULT_SOURCE:-}" "$source_re" "source is not an https URL"

delim="EOF_$(od -An -N8 -tx1 /dev/urandom | tr -d ' \n')"
printf 'labels<<%s\n%s\n%s\n' "$delim" "$labels" "$delim" >> "$GITHUB_OUTPUT"
