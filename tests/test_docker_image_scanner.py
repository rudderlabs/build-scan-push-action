import importlib.util
import os
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "scanner", os.path.join(ROOT, "docker-image-scanner.py")
)
scanner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scanner)


class CommandTest(unittest.TestCase):
    def test_verification_is_always_off(self):
        cmd = scanner.build_command("image.tar")
        self.assertIn("--no-verification", cmd)
        self.assertEqual(cmd[:2], ["trufflehog", "docker"])

    def test_command_scans_the_image_and_prints_json(self):
        # The scanner parses JSON lines only. Without --json it gets no findings and passes.
        cmd = scanner.build_command("/images/app.tar")
        self.assertEqual(
            cmd[:4],
            ["trufflehog", "docker", "--image", "file:///images/app.tar"],
        )
        self.assertCountEqual(cmd[4:], ["--json", "--no-update", "--no-verification"])

    def test_scan_runs_the_built_command(self):
        seen = []

        def fake_run(cmd, **kwargs):
            seen.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        with mock.patch.object(scanner.subprocess, "run", fake_run):
            scanner.scan_docker_image("build/other.tar")
        self.assertEqual(seen, [scanner.build_command("build/other.tar")])
        self.assertIn("--no-verification", seen[0])


def finding(path):
    return {
        "DetectorName": "Test",
        "SourceMetadata": {"Data": {"Docker": {"file": path, "layer": "sha256:0"}}},
    }


class FilterTest(unittest.TestCase):
    def filtered_paths(self, paths, caller_patterns=None):
        findings = [finding(p) for p in paths]
        if caller_patterns is None:
            return [
                f["SourceMetadata"]["Data"]["Docker"]["file"]
                for f in scanner.filter_results(findings, "/nonexistent/.truffleignore")
            ]
        with tempfile.TemporaryDirectory() as tmp:
            ignorefile = os.path.join(tmp, ".truffleignore")
            with open(ignorefile, "w") as fh:
                fh.write(caller_patterns)
            return [
                f["SourceMetadata"]["Data"]["Docker"]["file"]
                for f in scanner.filter_results(findings, ignorefile)
            ]

    def test_default_ignores_filter_base_package_metadata(self):
        ignored = [
            "/var/lib/dpkg/available",
            "/var/lib/dpkg/status.d/libc6",
            "/var/lib/rpm/rpmdb.sqlite",
            "/var/lib/rpm/Packages",
            "/var/lib/apk/db/installed",
            "/lib/apk/db/installed",
            "/usr/libexec/docker/cli-plugins/docker-compose",
            "/opt/harness/.venv/bin/ruff",
            "/home/user/.venv/bin/ruff",
            "/.venv/bin/ruff",
        ]
        self.assertEqual(self.filtered_paths(ignored), [])

    def test_default_ignores_apply_without_caller_file(self):
        self.assertEqual(self.filtered_paths(["/var/lib/dpkg/available"]), [])

    def test_app_paths_are_still_scanned(self):
        kept = [
            "/app/config.js",
            "/opt/svc/main.go",
            "/usr/local/bin/tool",
            "/app/node_modules/pkg/index.js",
            "/opt/harness/.venv/lib/python3.12/site-packages/pkg/__init__.py",
            "/opt/harness/.venv/pyvenv.cfg",
            "/var/lib/app/data",
            "/srv/var/lib/dpkg/available",
        ]
        self.assertEqual(self.filtered_paths(kept), kept)

    def test_default_list_has_no_broad_entries(self):
        with open(scanner.DEFAULT_IGNOREPATHS) as fh:
            entries = [line.strip() for line in fh if line.strip()]
        for broad in ["/usr/**", "/opt/**", "/app/**", "/var/**", "/**", "*"]:
            self.assertNotIn(broad, entries)
        self.assertEqual(self.filtered_paths(["/app/config.js", "/usr/bin/x"]), ["/app/config.js", "/usr/bin/x"])

    def test_caller_ignores_still_apply(self):
        paths = ["/app/vendor/lib.js", "/app/config.js", "/var/lib/dpkg/available"]
        self.assertEqual(
            self.filtered_paths(paths, "/app/vendor/**\n"), ["/app/config.js"]
        )

    def test_caller_file_does_not_disable_defaults(self):
        self.assertEqual(
            self.filtered_paths(["/var/lib/dpkg/available", "/app/a"], "# nothing\n"),
            ["/app/a"],
        )


if __name__ == "__main__":
    unittest.main()
