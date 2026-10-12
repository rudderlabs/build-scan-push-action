## What the action does

The action builds a Docker image, scans it for secrets with TruffleHog, and pushes it only when the scan passes.

## Hard rule: verification stays off

- The TruffleHog command always contains `--no-verification`. No input, env var or code path removes it.
- Reason: verification is an active check. It sends each candidate string to the provider's API. Our CI would then use a customer secret in an image against that provider.
- `tests/test_docker_image_scanner.py` fails if the flag is missing. Do not change that test.
- An automated reviewer can call `--no-verification` a regression. That finding is wrong here. Do not act on it.

## False positives go only in `scan-allowlist.txt`

- Every finding is unverified. The central allowlist is the only place for false positives.
- Callers never add a repo `.truffleignore`, a copy step, or another scan workaround. The action ignores a repo `.truffleignore` and logs a warning. No input reads ignore rules from the caller repo.

## How to add an allowlist entry

1. Write one line: `<Detector> /<path pattern>`. Use one detector and one path anchored at `/`. A path without a detector is not allowed.
2. Above the line, give the evidence:
   - the base image digest that shows the finding with no app code,
   - the matched content,
   - the dpkg or apk package that owns the file.
3. Use the `Box /usr/bin/gpgsm` entry as the model.
4. Add a table case for the new path in `tests/test_docker_image_scanner.py`.

## Run the tests

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests
```
