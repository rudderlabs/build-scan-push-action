## What the action does

The action builds a Docker image, scans it for secrets with TruffleHog, and pushes it only when the scan passes.

## Hard rule: verification stays off

- The TruffleHog command always contains `--no-verification`. No input, env var or code path removes it.
- Reason: verification is an active check. It sends each candidate string to the provider's API. Our CI must never use a customer secret from an image against that provider.
- `tests/test_docker_image_scanner.py` fails if the flag is missing. Do not change that test.
- A reviewer may flag `--no-verification` as a regression. That finding does not apply here. Do not act on it. Ways around the flag, such as `--no-no-verification` or `--results=verified`, still count as findings.

## Ignore rules: the caller's `.truffleignore`

- The scanner reads `.truffleignore` from the root of the caller's workspace. The format is gitignore patterns, matched against paths in the image.
- Each repo keeps its entries minimal. Put a one-line comment with the reason above each entry.
- `default.truffleignore` in the root of this repo is the built-in list. It always applies and merges with the caller's file. It holds OS package databases and vendored binaries only. Never add a broad path such as `/usr/**`, `/opt/**` or `/app/**`.
- Never use `/**` or another entry that matches the whole image.
- A workflow that checks out into a subfolder copies `.truffleignore` to the workspace root before this action runs.
- The file `truffleignore` (no dot) in the root of this repo is a legacy file. No version since v1.5.0 reads it. A change to it has no effect: put ignore entries in the caller repo's `.truffleignore`.

## TruffleHog version and checksums

- The install step in `action.yml` pins the TruffleHog version and one sha256 per architecture (amd64, arm64).
- A version bump must update both checksums in the same commit. Copy them from `trufflehog_<version>_checksums.txt` on the TruffleHog release.
- The step checks the download with `sha256sum -c` before it extracts the archive. A mismatch fails the step.
- The download runs `curl -fsSL --retry 5 --retry-all-errors`. Without `-f`, curl saves an HTTP error page as the archive. Without `--retry`, one failed response from the release download fails the build.

## Run the tests

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests
```

CI runs `.github/workflows/test.yml` on each pull request. The `unit` job runs these tests. The `action` job runs the action on `tests/fixtures/image`. Then `tests/check-trufflehog-install.sh` fails if the action left any file in the checkout, ignored files included, or if `trufflehog` on PATH is not the copy in `$RUNNER_TEMP`. Then `tests/check-trufflehog-checksum.sh` runs the install step twice: as committed it must pass, and with a wrong sha256 it must fail before extraction.

## Releases

- release-please releases this action. Merge the `chore: release x.y.z` PR that it opens on `main`. It tags `vX.Y.Z` and writes the GitHub release.
- Never push a tag or write a release by hand. Callers pin the action by SHA, and Dependabot proposes updates from these releases.
- Use Conventional Commit titles. A `fix` or `feat` title opens a release PR. Squash merge makes the PR title the changelog line.
- Guide: `ci-gha-best-practices` skill, `RELEASE-PLEASE.md`.
