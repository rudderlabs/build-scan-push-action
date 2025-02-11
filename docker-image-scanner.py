import json
import os
import sys
import re
import subprocess

from typing import List, Dict


def load_regex_patterns(regex_file: str) -> List[str]:
    """Load regex patterns from a file."""
    try:
        with open(regex_file, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: Regex file '{regex_file}' not found", file=sys.stderr)
        sys.exit(1)


def format_image_path(image_path: str) -> str:
    """Format the image path to use file:/// prefix with absolute path."""
    abs_path = os.path.abspath(image_path)
    return f"file://{abs_path}"


def scan_docker_image(image_path: str) -> List[Dict]:
    """Scan Docker image using trufflehog and return JSON results."""
    try:
        formatted_path = format_image_path(image_path)
        cmd = [
            "trufflehog",
            "docker",
            "--image",
            formatted_path,
            "--json",
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


def filter_results(findings: List[Dict], patterns: List[str]) -> List[Dict]:
    """Filter findings based on regex patterns."""
    if not patterns:
        return findings

    compiled_patterns = [re.compile(pattern) for pattern in patterns]
    filtered_findings = []

    for finding in findings:
        raw_result = str(finding["SourceMetadata"]["Data"]["Docker"]["file"])
        if any(pattern.search(raw_result) for pattern in compiled_patterns):
            continue

        filtered_findings.append(finding)

    return filtered_findings


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python scanner.py <docker_image.tar> [regex_file]", file=sys.stderr
        )
        sys.exit(1)

    image_path = sys.argv[1]
    regex_file = sys.argv[2] if len(sys.argv) > 2 else None

    patterns = load_regex_patterns(regex_file) if regex_file else []

    findings = scan_docker_image(image_path)

    # Filter results if patterns provided
    if patterns:
        findings = filter_results(findings, patterns)

    # Output results
    if findings:
        for finding in findings:
            file = finding["SourceMetadata"]["Data"]["Docker"]["file"]
            layer = finding["SourceMetadata"]["Data"]["Docker"]["layer"]
            redacted_secret = finding["Redacted"]
            print(
                f"Found unverified secret {redacted_secret} in file={file} layer={layer}"
            )
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
