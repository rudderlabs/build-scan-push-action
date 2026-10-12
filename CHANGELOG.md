# Changelog

## 2.3.1 (2026-10-12)

- A unit test fails if the TruffleHog command does not contain `--no-verification`. The scan
  behavior does not change.
- TruffleHog is installed in `$RUNNER_TEMP`, so its README.md and LICENSE no longer land in the build context.
- TruffleHog downloads are verified with sha256 before install.
