# build-scan-push-action

## About

GitHub Action to build, scan, sign and push Docker images. This is a thin wrapper
around [docker-build-push](https://github.com/docker/build-push-action) GitHub action.

This action does the following:

1. Builds the docker image (with push set to `false`).
2. Scans the built docker image for secrets with [Trufflehog](https://github.com/trufflesecurity/trufflehog).
   - GitHub action fails if secrets are found in the docker image
3. Pushes the docker image to a docker repository if no secrets are found
   (when push is set to `true`).
4. Signs the docker image

## Permissions

GitHub Actions can use Fulcio to sign images. Fulcio is a root CA that issues signing certificates from OIDC tokens.
Add the following permissions in your workflow at root level. [eg](https://github.com/rudderlabs/rudderstack-operator/blob/f3d326ddcb207fb8f42b587d6307f338479c2540/.github/workflows/build-pr.yaml#L10)

```yaml
 permissions:
  id-token: write  
  contents: read
```

## Usage

Replace `docker/build-push-action@vX` with `rudderlabs/build-scan-push-action@v1.x`
in your GitHub Workflows.

For more info, refer the documentation of
[docker-build-push](https://github.com/docker/build-push-action) GitHub Action.

## Ignoring false positives

By default TruffleHog doesn't support excluding file paths when
scanning docker images. In our GitHub Action, we have added support
to exclude paths using a `.truffleignore` file.

Create a `.truffleignore` file at the root of your repository. Add paths
that you want to exclude in [gitignore-style pattern](https://git-scm.com/docs/gitignore)
format. All paths that match these patterns are excluded in TruffleHog scans.

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
