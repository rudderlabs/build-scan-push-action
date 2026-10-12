# Changelog

## 2.4.0 (2026-10-12)

### Behavior changes

- The action ignores a repository `.truffleignore` file and logs a warning. The action owns
  the false-positive list in `scan-allowlist.txt`. Each entry is one detector and one path,
  and links the scan that showed it.
- The allowlist suppresses unverified findings only. The scanner never suppresses a finding
  marked verified or one with a verification error.
- The scan never enables verification, as before, because verification sends candidate
  strings to third-party APIs. A unit test fails if `--no-verification` is missing.
- The action installs TruffleHog in `$RUNNER_TEMP` and checks its sha256. Callers can drop a
  `path: src` checkout and any step that copies `.truffleignore`.

### Removed

- The unused `truffleignore` file. No version since v1.5 read it.
