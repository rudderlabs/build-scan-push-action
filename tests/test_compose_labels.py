import os
import subprocess
import tempfile
import unittest

from test_push_target import parse

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "compose-labels.sh")

RUN_SHA = "a" * 40
RUN_SOURCE = "https://github.com/org/repo"
CALLER_SHA = "b" * 40
INPUT_SHA = "c" * 40
REV = "org.opencontainers.image.revision="
SRC = "org.opencontainers.image.source="


def run(labels="", revision="", source=""):
    with tempfile.NamedTemporaryFile("r", delete=False) as out:
        path = out.name
    try:
        env = {
            "PATH": os.environ["PATH"],
            "GITHUB_OUTPUT": path,
            "INPUT_LABELS": labels,
            "REVISION": revision,
            "SOURCE": source,
            "DEFAULT_REVISION": RUN_SHA,
            "DEFAULT_SOURCE": RUN_SOURCE,
        }
        proc = subprocess.run(["bash", SCRIPT], env=env, capture_output=True, text=True)
        with open(path) as f:
            raw = f.read()
    finally:
        os.unlink(path)
    return proc.returncode, parse(raw).get("labels"), proc.stderr


class ComposeLabelsTest(unittest.TestCase):
    def test_defaults_when_nothing_is_set(self):
        code, labels, _ = run()
        self.assertEqual(code, 0)
        self.assertEqual(labels.splitlines(), [REV + RUN_SHA, SRC + RUN_SOURCE])

    def test_caller_label_is_kept_when_input_is_empty(self):
        code, labels, _ = run(f"team=x\n{REV}{CALLER_SHA}\n{SRC}https://example.com/fork")
        self.assertEqual(code, 0)
        self.assertEqual(
            labels.splitlines(), ["team=x", REV + CALLER_SHA, SRC + "https://example.com/fork"]
        )

    def test_input_overrides_caller_label(self):
        code, labels, _ = run(f"{REV}{CALLER_SHA}\nteam=x", revision=INPUT_SHA)
        self.assertEqual(code, 0)
        self.assertEqual(labels.splitlines(), ["team=x", REV + INPUT_SHA, SRC + RUN_SOURCE])

    def test_caller_revision_only_keeps_default_source(self):
        code, labels, _ = run(f"{REV}{CALLER_SHA}")
        self.assertEqual(code, 0)
        self.assertEqual(labels.splitlines(), [REV + CALLER_SHA, SRC + RUN_SOURCE])

    def test_invalid_input_fails(self):
        code, labels, err = run(revision="main")
        self.assertNotEqual(code, 0)
        self.assertIn("revision is not", err)
        self.assertIsNone(labels)
        code, _, err = run(source="http://example.com/repo")
        self.assertNotEqual(code, 0)
        self.assertIn("source is not", err)

    def test_input_is_trimmed_at_the_ends_only(self):
        code, labels, _ = run(revision=f" {INPUT_SHA}\n", source=" https://github.com/org/app ")
        self.assertEqual(code, 0)
        self.assertEqual(labels.splitlines(), [REV + INPUT_SHA, SRC + "https://github.com/org/app"])
        code, _, err = run(source="https://github.com/rudder labs/app")
        self.assertNotEqual(code, 0)
        self.assertIn("source is not", err)

    def test_other_labels_pass_through(self):
        code, labels, _ = run("a=1\nb=2")
        self.assertEqual(code, 0)
        self.assertEqual(labels.splitlines()[:2], ["a=1", "b=2"])


if __name__ == "__main__":
    unittest.main()
