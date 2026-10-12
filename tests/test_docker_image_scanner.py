import contextlib
import importlib.util
import io
import os
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "scanner", os.path.join(ROOT, "docker-image-scanner.py")
)
scanner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scanner)


def finding(path, verified=False, verification_error=""):
    f = {
        "DetectorName": "Box",
        "Verified": verified,
        "Redacted": "",
        "Raw": "abcdefgh",
        "SourceMetadata": {"Data": {"Docker": {"file": path, "layer": "sha256:x"}}},
    }
    if verification_error:
        f["VerificationError"] = verification_error
    return f


class ScanTest(unittest.TestCase):
    def run_scan(self, findings, repo_ignore_content=None):
        with tempfile.TemporaryDirectory() as tmp:
            repo_ignore = os.path.join(tmp, ".truffleignore")
            if repo_ignore_content is not None:
                with open(repo_ignore, "w") as fh:
                    fh.write(repo_ignore_content)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = scanner.run(
                    "unused.tar", repo_ignore=repo_ignore, findings=findings
                )
            return code, out.getvalue()

    def test_table(self):
        cases = [
            ("os path, unverified: suppressed", [finding("/usr/bin/gpgsm")], 0),
            ("os path, verified: fails", [finding("/usr/bin/gpgsm", verified=True)], 1),
            (
                "os path, verification error: fails",
                [finding("/usr/bin/gpgsm", verification_error="timeout")],
                1,
            ),
            ("app path, unverified: fails", [finding("/app/config.json")], 1),
            (
                "allowlisted name under app dir: fails",
                [finding("/app/usr/bin/gpgsm")],
                1,
            ),
            (
                "snowpipe noble paths, unverified: suppressed",
                [
                    finding("/usr/bin/perl"),
                    finding("/usr/lib/x86_64-linux-gnu/libgnutls.so.30.37.1"),
                    finding("/usr/lib/aarch64-linux-gnu/libgnutls.so.30.37.1"),
                    finding("/var/lib/dpkg/info/keyboxd.md5sums"),
                    finding("/var/lib/dpkg/info/libc6:arm64.md5sums"),
                ],
                0,
            ),
            ("node image yarn, unverified: suppressed", [finding("/opt/yarn-v1.22.22/lib/cli.js")], 0),
            ("empty path: fails", [finding("")], 1),
            ("no findings: passes", [], 0),
            (
                "one real finding among suppressed: fails",
                [finding("/usr/bin/gpgsm"), finding("/app/.env")],
                1,
            ),
        ]
        for name, findings, want in cases:
            with self.subTest(name):
                code, _ = self.run_scan(findings)
                self.assertEqual(code, want)

    def test_verified_finding_is_reported_as_verified(self):
        code, out = self.run_scan([finding("/usr/bin/gpgsm", verified=True)])
        self.assertEqual(code, 1)
        self.assertIn("Found verified secret", out)
        self.assertIn("file=/usr/bin/gpgsm", out)
        self.assertNotIn("abcdefgh", out)

    def test_repo_truffleignore_is_ignored_with_warning(self):
        code, out = self.run_scan(
            [finding("/app/config.json")], repo_ignore_content="/app/**\n"
        )
        self.assertEqual(code, 1)
        self.assertIn("::warning title=.truffleignore ignored::", out)
        self.assertIn("file=/app/config.json", out)

    def test_no_warning_without_repo_truffleignore(self):
        _, out = self.run_scan([])
        self.assertNotIn("::warning", out)

    def test_missing_allowlist_fails(self):
        with self.assertRaises(FileNotFoundError):
            scanner.run("unused.tar", allowlist="/nonexistent", findings=[])


if __name__ == "__main__":
    unittest.main()
