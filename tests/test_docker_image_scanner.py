import importlib.util
import os
import subprocess
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

    def test_scan_runs_the_built_command(self):
        seen = []

        def fake_run(cmd, **kwargs):
            seen.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        with mock.patch.object(scanner.subprocess, "run", fake_run):
            scanner.scan_docker_image("image.tar")
        self.assertEqual(seen, [scanner.build_command("image.tar")])
        self.assertIn("--no-verification", seen[0])


if __name__ == "__main__":
    unittest.main()
