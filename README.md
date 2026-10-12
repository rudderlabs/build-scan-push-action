# build-scan-push-action

## About

GitHub Action to build, scan and push Docker images. This is a thin wrapper
around [docker-build-push](https://github.com/docker/build-push-action) GitHub action.

This action does the following:

1. Builds the docker image (with push set to `false`).
2. Scans the built docker image for secrets with [Trufflehog](https://github.com/trufflesecurity/trufflehog).
   - GitHub action fails if secrets are found in the docker image
3. Pushes the docker image to a docker repository if no secrets are found
   (when push is set to `true`).

## Usage

Replace `docker/build-push-action@vX` with `rudderlabs/build-scan-push-action@v2.x`
in your GitHub Workflows.

For more info, refer the documentation of
[docker-build-push](https://github.com/docker/build-push-action) GitHub Action.

## False positives

The action owns the list of known false positives. Repositories cannot extend it.

- The list is [`scan-allowlist.txt`](scan-allowlist.txt). Each entry is
  `<Detector> /<path>`: a TruffleHog detector name and a
  [gitignore-style pattern](https://git-scm.com/docs/gitignore#_pattern_format)
  matched against absolute paths in the image.
- The scan never enables TruffleHog verification, because verification sends
  candidate strings to third-party APIs. Every finding is unverified.
- An entry suppresses unverified findings of its detector on its path. The
  scanner never suppresses a finding marked verified or one with a verification
  error.
- The action ignores a `.truffleignore` file in your repository and logs a warning.
- To add a false positive, open a PR on this repository. Put a comment above the
  entry with the base image digest, the matched content, and the package that
  owns the file. See [AGENTS.md](AGENTS.md) for the rules.

## Current Limitations

This GitHub Action only accepts the following inputs.

- `build-args`
- `cache-from`
- `cache-to`
- `context`
- `file`
- `labels`
- `load`
- `platforms`
- `provenance`
- `push`
- `sbom`
- `secret-envs`
- `secrets`
- `tags`
- `target`

If you want to use an input which is not in the above mentioned list,
feel free to contribute or reach out to infra team for support.

## Upgrade Guide

### From v2.3.x to v2.4.x

- The action no longer reads `.truffleignore` from your repository. Delete the file.
  If the scan now fails on a false positive, add the path to `scan-allowlist.txt`
  in this repository.
- The action installs TruffleHog in `$RUNNER_TEMP` and no longer writes to your
  workspace. You can drop a `path: src` checkout and any step that copies
  `.truffleignore` into place.

### From v1.4.x to v1.5.x

We have added support to exclude paths in v1.4 where we relied on
a common `truffleignore` file in this repository to filter findings.
We no longer do that in versions >=v1.5.x and instead rely on repo
specific `.truffleignore` file at the root of your repository.

If you were using `truffleignore` to exclude paths, you need to move
your paths to `.truffleignore` file at the root of your repository.
All your paths should follow [gitignore pattern format](https://git-scm.com/docs/gitignore#_pattern_format)

If you are not using exclude paths feature, you don't have to do
anything.
