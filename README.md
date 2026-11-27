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

## Pushing by digest

Set `push-by-digest: "true"` (with `push: "true"` and exactly one entry in `platforms`,
the platform the scan covers) to push the image without a tag.
`tags` then only names the repositories; any tag part is ignored. Read the pushed
manifest digest from the `digest` output.

Use this for per-platform builds on native runners: each job pushes its image
untagged, and a later job joins the digests into one multi-arch index under the
final tags. No per-platform tags are left in the repository.

```yaml
- id: build
  uses: rudderlabs/build-scan-push-action@<sha>
  with:
    platforms: linux/arm64
    push: "true"
    push-by-digest: "true"
    tags: registry.example.com/team/app
# steps.build.outputs.digest is the per-platform image digest
```

Keep `provenance` and `sbom` off for these builds: with attestations the push is
an index, not a single-platform image.

## Outputs

- `imageid`, `digest`, `metadata`: as returned by `docker/build-push-action`
- `repositories`: JSON array of the repositories pushed to (tag stripped); empty when `push` is false

The action sets the `org.opencontainers.image.revision` and `org.opencontainers.image.source`
labels from the `revision` and `source` inputs (defaults: the commit and repository of the run).

## Ignoring false positives

By default TruffleHog doesn't support excluding file paths when
scanning docker images. In our GitHub Action, we have added support
to exclude paths using a `.truffleignore` file.

Create a `.truffleignore` file at the root of your repository. Add paths
that you want to exclude in [gitignore-style pattern](https://git-scm.com/docs/gitignore)
format. All paths that match these patterns are excluded in TruffleHog scans.

The action also ignores a built-in list of paths for OS package databases and
vendored binaries (see `default.truffleignore`). These defaults always apply and
are merged with your `.truffleignore`.

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
- `push-by-digest`
- `revision`
- `sbom`
- `secret-envs`
- `secrets`
- `source`
- `tags`
- `target`

If you want to use an input which is not in the above mentioned list,
feel free to contribute or reach out to infra team for support.

## Upgrade Guide

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
