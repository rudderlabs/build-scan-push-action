import argparse
import json
import os
import sys
import subprocess
import pathspec

from typing import List, Dict, Optional

# The allowlist ships with the action. Callers cannot extend it.
DEFAULT_ALLOWLIST = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "scan-allowlist.txt"
)
REPO_IGNORE_FILE = ".truffleignore"


def format_image_path(image_path: str) -> str:
    """Format the image path to use file:/// prefix with absolute path."""
    abs_path = os.path.abspath(image_path)
    return f"file://{abs_path}"


def scan_docker_image(image_path: str, trufflehog: str = "trufflehog") -> List[Dict]:
    """Scan Docker image using trufflehog and return JSON results."""
    try:
        formatted_path = format_image_path(image_path)
        cmd = [
            trufflehog,
            "docker",
            "--image",
            formatted_path,
            "--json",
            "--no-update",
            # Verification is off, so the allowlist suppresses unverified findings
            # by detector and path. Each allowlist entry must cite its evidence.
            "--no-verification",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error running trufflehog: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        # Process output line by line as each line is a JSON object
        findings = []
        for line in result.stdout.splitlines():
            if line.strip():
                try:
                    findings.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        return findings
    except subprocess.CalledProcessError as e:
        print(f"Error executing trufflehog: {e}", file=sys.stderr)
        sys.exit(1)


class Allowlist:
    """Path patterns per TruffleHog detector. Lines are "<Detector> /<pattern>"."""

    def __init__(self, specs: Dict[str, pathspec.PathSpec]):
        self.specs = specs

    def matches(self, detector: str, path: str) -> bool:
        spec = self.specs.get(detector.lower())
        return bool(path) and spec is not None and spec.match_file(path)


def parse_allowlist(lines) -> Allowlist:
    """Parse the allowlist. A malformed line fails the scan instead of widening it."""
    patterns: Dict[str, List[str]] = {}
    for n, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 2:
            raise ValueError(f"allowlist line {n}: want '<Detector> /<path>', got {line!r}")
        detector, pattern = parts
        if not detector.isalnum():
            raise ValueError(f"allowlist line {n}: detector must be one name, got {detector!r}")
        if not pattern.startswith("/"):
            raise ValueError(f"allowlist line {n}: path must start with '/', got {pattern!r}")
        patterns.setdefault(detector.lower(), []).append(pattern)
    return Allowlist(
        {d: pathspec.PathSpec.from_lines("gitwildmatch", p) for d, p in patterns.items()}
    )


def load_allowlist(path: str) -> Allowlist:
    """Load the central allowlist. A missing file is a broken action, so fail."""
    with open(path, "r") as fh:
        return parse_allowlist(fh)


def warn_repo_ignore(path: str = REPO_IGNORE_FILE) -> bool:
    """Warn when the caller repo still has a .truffleignore. Returns True if found."""
    if not os.path.exists(path):
        return False
    print(
        f"::warning title=.truffleignore ignored::{path} is ignored. "
        "build-scan-push-action owns the scan allowlist (scan-allowlist.txt). "
        "Open a PR on rudderlabs/build-scan-push-action to add a false positive, "
        "and delete this file."
    )
    return True


def finding_file(finding: Dict) -> str:
    return str(
        finding.get("SourceMetadata", {})
        .get("Data", {})
        .get("Docker", {})
        .get("file", "")
    )


def verification_status(finding: Dict) -> str:
    """Return 'verified', 'unknown' (verification error) or 'unverified'."""
    if finding.get("Verified") is True:
        return "verified"
    if finding.get("VerificationError"):
        return "unknown"
    return "unverified"


def is_suppressed(finding: Dict, spec: Allowlist) -> bool:
    """Only an unverified finding of an allowlisted detector on its path is suppressed."""
    if verification_status(finding) != "unverified":
        return False
    return spec.matches(str(finding.get("DetectorName", "")), finding_file(finding))


def filter_results(findings: List[Dict], spec: Allowlist) -> List[Dict]:
    return [f for f in findings if not is_suppressed(f, spec)]


def redact(finding: Dict) -> str:
    redacted = finding.get("Redacted", "")
    raw = finding.get("Raw", "")
    if redacted:
        return redacted
    if raw:
        return raw[:4] + "****" if len(raw) > 4 else "****"
    return "****"


def report(findings: List[Dict]) -> None:
    for finding in findings:
        layer = (
            finding.get("SourceMetadata", {})
            .get("Data", {})
            .get("Docker", {})
            .get("layer", "")
        )
        print(
            f"Found {verification_status(finding)} secret of "
            f"type='{finding.get('DetectorName', '')}' with value='{redact(finding)}' "
            f"in file={finding_file(finding)} layer={layer}"
        )


def run(
    image: str,
    allowlist: str = DEFAULT_ALLOWLIST,
    repo_ignore: str = REPO_IGNORE_FILE,
    findings: Optional[List[Dict]] = None,
    trufflehog: str = "trufflehog",
) -> int:
    warn_repo_ignore(repo_ignore)
    spec = load_allowlist(allowlist)
    if findings is None:
        findings = scan_docker_image(image, trufflehog)
    remaining = filter_results(findings, spec)
    suppressed = len(findings) - len(remaining)
    if suppressed:
        print(f"Suppressed {suppressed} unverified finding(s) matching the allowlist.")
    if remaining:
        report(remaining)
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--image",
        required=True,
        help="local tarball of your docker image",
    )
    parser.add_argument(
        "--trufflehog",
        default="trufflehog",
        help="path to the trufflehog binary",
    )
    args = parser.parse_args()
    sys.exit(run(args.image, trufflehog=args.trufflehog))


if __name__ == "__main__":
    main()
