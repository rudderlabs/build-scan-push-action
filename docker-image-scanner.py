import argparse
import json
import os
import sys
import subprocess
import pathspec

from typing import List, Dict

DEFAULT_IGNOREPATHS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "default.truffleignore"
)


def format_image_path(image_path: str) -> str:
    """Format the image path to use file:/// prefix with absolute path."""
    abs_path = os.path.abspath(image_path)
    return f"file://{abs_path}"


def build_command(image_path: str) -> List[str]:
    """Build the TruffleHog command. No option removes --no-verification."""
    return [
        "trufflehog",
        "docker",
        "--image",
        format_image_path(image_path),
        "--json",
        "--no-update",
        # Verification sends each candidate string to the provider's API.
        # A customer secret in an image must never be used against a provider by our CI.
        "--no-verification",
    ]


def scan_docker_image(image_path: str) -> List[Dict]:
    """Scan Docker image using trufflehog and return JSON results."""
    try:
        cmd = build_command(image_path)
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


def load_patterns(path: str) -> List[str]:
    with open(path, "r") as fh:
        return fh.read().splitlines()


def filter_results(
    findings: List[Dict],
    ignorepaths: str,
    default_ignorepaths: str = DEFAULT_IGNOREPATHS,
) -> List[Dict]:
    """Filter findings based on the bundled default patterns and the caller's gitignore patterns."""
    patterns = load_patterns(default_ignorepaths)
    if ignorepaths:
        try:
            patterns += load_patterns(ignorepaths)
        except FileNotFoundError:
            print(
                f"file {ignorepaths} not found in repository. Only filtering findings with the default ignore patterns."
            )

    spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)

    filtered_findings = []

    for finding in findings:
        file_path = str(finding["SourceMetadata"]["Data"]["Docker"]["file"])
        if spec.match_file(file_path):
            continue

        filtered_findings.append(finding)

    return filtered_findings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--image",
        required=True,
        help="local tarball of your docker image",
    )
    parser.add_argument(
        "--ignorepaths",
        required=False,
        help="file with paths to ignore (in gitignore pattern format)",
        default=".truffleignore",
    )
    args = parser.parse_args()

    findings = scan_docker_image(args.image)

    findings = filter_results(findings, args.ignorepaths)

    # Output results
    if findings:
        for finding in findings:
            file = (
                finding.get("SourceMetadata", {})
                .get("Data", {})
                .get("Docker", {})
                .get("file", "")
            )
            layer = (
                finding.get("SourceMetadata", {})
                .get("Data", {})
                .get("Docker", {})
                .get("layer", "")
            )
            raw = finding.get("Raw", "")
            redacted = finding.get("Redacted", "")
            if redacted:
                redacted_secret = redacted
            elif raw:
                redacted_secret = raw[:4] + "****" if len(raw) > 4 else "****"
            else:
                redacted_secret = "****"
            detector = finding["DetectorName"]
            print(
                f"Found unverified secret of type='{detector}' with value='{redacted_secret}' in file={file} layer={layer}"
            )
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
