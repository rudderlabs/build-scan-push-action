import json
import os
import subprocess
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "push-target.sh")


def run(push, by_digest, tags):
    with tempfile.NamedTemporaryFile("r", delete=False) as out:
        path = out.name
    try:
        env = {
            "PATH": os.environ["PATH"],
            "GITHUB_OUTPUT": path,
            "PUSH": push,
            "PUSH_BY_DIGEST": by_digest,
            "TAGS": tags,
        }
        proc = subprocess.run(["bash", SCRIPT], env=env, capture_output=True, text=True)
        with open(path) as f:
            raw = f.read()
    finally:
        os.unlink(path)
    return proc.returncode, parse(raw), proc.stderr


def parse(raw):
    values, lines, i = {}, raw.split("\n"), 0
    while i < len(lines):
        line = lines[i]
        if "<<" in line and "=" not in line.split("<<")[0]:
            key, delim = line.split("<<", 1)
            body = []
            i += 1
            while lines[i] != delim:
                body.append(lines[i])
                i += 1
            values[key] = "\n".join(body)
        elif "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
        i += 1
    return values


class PushTargetTest(unittest.TestCase):
    def test_tagged_push_is_unchanged(self):
        tags = "reg.example/team/app:1.2.3\nreg.example/team/app:latest"
        code, out, _ = run("true", "false", tags)
        self.assertEqual(code, 0)
        self.assertEqual(out["push"], "true")
        self.assertEqual(out["tags"], tags)
        self.assertEqual(out["outputs"], "")
        self.assertEqual(json.loads(out["repositories"]), ["reg.example/team/app"])

    def test_no_push_reports_no_repositories(self):
        code, out, _ = run("false", "false", "app:ci")
        self.assertEqual(code, 0)
        self.assertEqual(out["push"], "false")
        self.assertEqual(json.loads(out["repositories"]), [])

    def test_boolean_case_is_accepted(self):
        code, out, _ = run("True", "FALSE", "reg.example/app:1")
        self.assertEqual(code, 0)
        self.assertEqual(out["push"], "true")

    def test_by_digest_pushes_untagged(self):
        tags = "reg.example:5000/team/app:1.2.3, reg.example:5000/team/app:main\nreg.example/other"
        code, out, _ = run("true", "true", tags)
        self.assertEqual(code, 0)
        self.assertEqual(out["push"], "false")
        self.assertEqual(out["tags"], "")
        self.assertEqual(
            out["outputs"],
            'type=image,"name=reg.example/other,reg.example:5000/team/app",push-by-digest=true,name-canonical=true,push=true',
        )
        self.assertEqual(
            json.loads(out["repositories"]), ["reg.example/other", "reg.example:5000/team/app"]
        )

    def test_by_digest_needs_push(self):
        code, out, err = run("false", "true", "reg.example/app")
        self.assertNotEqual(code, 0)
        self.assertIn("needs push", err)
        self.assertEqual(out, {})

    def test_by_digest_needs_a_repository(self):
        code, _, err = run("true", "true", " \n")
        self.assertNotEqual(code, 0)
        self.assertIn("at least one repository", err)

    def test_by_digest_rejects_digest_references(self):
        code, _, err = run("true", "true", "reg.example/app@sha256:" + "a" * 64)
        self.assertNotEqual(code, 0)
        self.assertIn("not digest references", err)

    def test_invalid_boolean_fails(self):
        code, _, err = run("yes", "false", "reg.example/app:1")
        self.assertNotEqual(code, 0)
        self.assertIn("push must be true or false", err)


if __name__ == "__main__":
    unittest.main()
