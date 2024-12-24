
## About

GitHub Action to build, scan and push Docker images. This is a thin wrapper
around [docker-build-push](https://github.com/docker/build-push-action) GitHub action.

This action contains three steps:

1. Builds the docker image (with push set to `false`).
2. Scans the built docker image for secrets with [Trufflehog](https://github.com/trufflesecurity/trufflehog).
   - GitHub action fails if secrets are found in the docker image
3. Pushes the docker image to a docker repository if not secrets are found.

## Usage

Refer the documentation of
[docker-build-push](https://github.com/docker/build-push-action) GitHub Action

## Current Limitations

Although this GitHub Action accepts all the inputs of [docker-build-push]
GitHub Action, we only use the following inputs in our GitHub Action.

- `build-args`
- `cache-to`
- `context`
- `labels`
- `platforms`
- `push`
- `tags`

If you want to use an input which is not in the above mentioned list,
feel free to contribute or reach out to @infra team for support.
