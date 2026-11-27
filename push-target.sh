#!/usr/bin/env bash
# Resolves where the final build step pushes.
# Env: PUSH PUSH_BY_DIGEST TAGS. Writes repositories, tags, push, outputs to $GITHUB_OUTPUT.
set -euo pipefail

fail() { echo "::error::$*" >&2; exit 1; }

PUSH="$(tr -d '[:space:]' <<< "${PUSH:-false}" | tr '[:upper:]' '[:lower:]')"
PUSH_BY_DIGEST="$(tr -d '[:space:]' <<< "${PUSH_BY_DIGEST:-false}" | tr '[:upper:]' '[:lower:]')"
[ -n "$PUSH" ] || PUSH=false
[ -n "$PUSH_BY_DIGEST" ] || PUSH_BY_DIGEST=false
TAGS="${TAGS:-}"
PLATFORMS="$(printf '%s' "${PLATFORMS:-}" | sed -E '1s/^[[:space:]]+//; $s/[[:space:]]+$//')"
: "${GITHUB_OUTPUT:?}"

[[ "$PUSH" == "true" || "$PUSH" == "false" ]] || fail "push must be true or false"
[[ "$PUSH_BY_DIGEST" == "true" || "$PUSH_BY_DIGEST" == "false" ]] || fail "push-by-digest must be true or false"

refs="$(tr ',' '\n' <<< "$TAGS" | sed -E 's/[[:space:]]//g; /^$/d')"
repos="$(sed -E 's/@sha256:.*$//; s/:[^:/]*$//' <<< "$refs" | sed '/^$/d' | sort -u)"

if [[ "$PUSH_BY_DIGEST" == "true" ]]; then
  [[ "$PUSH" == "true" ]] || fail "push-by-digest needs push: true"
  [[ "$PLATFORMS" =~ ^[a-z0-9]+/[a-z0-9]+(/[a-z0-9]+)?$ ]] || fail "push-by-digest needs exactly one platform, the one the scan covers"
  [ -n "$repos" ] || fail "push-by-digest needs at least one repository in tags"
  ! grep -q '@' <<< "$refs" || fail "push-by-digest takes repository names, not digest references"
  names="$(paste -sd, - <<< "$repos")"
  outputs="type=image,\"name=$names\",push-by-digest=true,name-canonical=true,push=true"
  push=false
  tags=""
else
  outputs=""
  push="$PUSH"
  tags="$TAGS"
fi

json="[]"
[[ "$PUSH" == "true" && -n "$repos" ]] && json="$(jq -R . <<< "$repos" | jq -sc .)"

delim="EOF_$(od -An -N8 -tx1 /dev/urandom | tr -d ' \n')"
{
  printf 'repositories=%s\n' "$json"
  printf 'push=%s\n' "$push"
  printf 'outputs=%s\n' "$outputs"
  printf 'tags<<%s\n%s\n%s\n' "$delim" "$tags" "$delim"
} >> "$GITHUB_OUTPUT"
