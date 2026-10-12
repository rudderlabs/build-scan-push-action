#!/usr/bin/env bash
# Runs the install step from action.yml twice. As committed it must pass. With a wrong sha256 it must fail before extraction.
set -euo pipefail

export TRUFFLEHOG_ARCH="${TRUFFLEHOG_ARCH:-amd64}"
step="$(yq '.runs.steps[] | select(.name == "Install TruffleHog") | .run' action.yml)"
wrong_step="$(sed -E 's/[0-9a-f]{64}/0000000000000000000000000000000000000000000000000000000000000000/g' <<<"$step")"

good="$(mktemp -d)"
RUNNER_TEMP="$good" GITHUB_PATH="$good/path" bash --noprofile --norc -eo pipefail -c "$step"
test -x "$good/trufflehog/trufflehog"

bad="$(mktemp -d)"
if RUNNER_TEMP="$bad" GITHUB_PATH="$bad/path" bash --noprofile --norc -eo pipefail -c "$wrong_step"; then
  echo "The install step passed with a wrong sha256" >&2
  exit 1
fi
if [[ -e "$bad/trufflehog/trufflehog" ]]; then
  echo "The install step extracted TruffleHog before the sha256 check" >&2
  exit 1
fi
echo "The install step rejects a wrong sha256"
