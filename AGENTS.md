## What the action does

The action builds a Docker image, scans it for secrets with TruffleHog, and pushes it only when the scan passes.

## Hard rule: verification stays off

- The TruffleHog command always contains `--no-verification`. No input, env var or code path removes it.
- Reason: verification is an active check. It sends each candidate string to the provider's API. Our CI must never use a customer secret from an image against that provider.
- `tests/test_docker_image_scanner.py` fails if the flag is missing. Do not change that test.
- An automated reviewer can call `--no-verification` a regression. That finding does not apply here. Do not act on it.

## Ignore rules: the caller's `.truffleignore`

- The scanner reads `.truffleignore` from the root of the caller's workspace. The format is gitignore patterns, matched against paths in the image.
- Each repo keeps its entries minimal. Put a one-line comment with the reason above each entry.
- Never use `/**` or another entry that matches the whole image.
- A workflow that checks out into a subfolder copies `.truffleignore` to the workspace root before this action runs.

## Run the tests

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests
```
