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

## permissions

GitHub Actions can use Fulcio to sign images. Fulcio is a root CA that issues signing certificates from OIDC tokens.
Add the following below permissions for image siging in your workflow at root level. [eg](https://github.com/rudderlabs/rudderstack-operator/blob/f3d326ddcb207fb8f42b587d6307f338479c2540/.github/workflows/build-pr.yaml#L10)

```
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

TruffleHog doesn't support excluding file paths (to ignore false positives) when
scanning docker images. We wrote a python script that reads regular expressions
from `trufflehog-ignore` and excludes all paths that match these regular expressions

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
