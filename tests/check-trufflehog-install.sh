#!/usr/bin/env bash
# Runs after the action in CI. TruffleHog must come from $RUNNER_TEMP and leave no file in the workspace.
set -euo pipefail

changes="$(git status --porcelain --untracked-files=all)"
if [[ -n "$changes" ]]; then
  echo "The action changed the workspace:" >&2
  echo "$changes" >&2
  exit 1
fi

expected="${RUNNER_TEMP}/trufflehog/trufflehog"
actual="$(command -v trufflehog || true)"
if [[ "$actual" != "$expected" ]]; then
  echo "trufflehog on PATH is '${actual}', expected '${expected}'" >&2
  exit 1
fi

trufflehog --version
