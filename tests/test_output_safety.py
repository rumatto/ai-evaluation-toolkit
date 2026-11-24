import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ai_qa_toolkit"))

from io_core import write_json_atomic, write_text_atomic
from runner import main as runner_main
from quality_runner import main as quality_main


class OutputSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

        self.suite = self.root / "suite.json"
        self.suite.write_text(json.dumps({
            "schemaVersion": "evaluation-cases.v1",
            "cases": [{
                "id": "SEC-001",
                "category": "agent-safety",
                "expected": {"decision": "allow"},
                "fixture": {"decision": "allow"}
            }]
        }))

        self.policy = self.root / "policy.json"
        self.policy.write_text(json.dumps({
            "schemaVersion": "quality-gates.v1",
            "gates": {"decisionAccuracy": 0.0}
        }))

    def run_cli(self, func, args):
        with contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            return func(args)

    def test_json_rejects_protected_input(self):
        before = self.suite.read_bytes()
        with self.assertRaises(ValueError):
            write_json_atomic(self.suite, {}, protected=[self.suite])
        self.assertEqual(self.suite.read_bytes(), before)

    def test_text_rejects_protected_input(self):
        before = self.suite.read_bytes()
        with self.assertRaises(ValueError):
            write_text_atomic(self.suite, "changed", protected=[self.suite])
        self.assertEqual(self.suite.read_bytes(), before)

    def test_json_rejects_symlink(self):
        link = self.root / "linked.json"
        link.symlink_to(self.suite)
        before = self.suite.read_bytes()
        with self.assertRaises(ValueError):
            write_json_atomic(link, {})
        self.assertEqual(self.suite.read_bytes(), before)

    def test_text_rejects_hardlink(self):
        link = self.root / "hardlink.json"
        link.hardlink_to(self.suite)
        before = self.suite.read_bytes()
        with self.assertRaises(ValueError):
            write_text_atomic(link, "changed", protected=[self.suite])
        self.assertEqual(self.suite.read_bytes(), before)

    def runner(self, output):
        config = self.root / "config.json"
        config.write_text(json.dumps({
            "schemaVersion": "evaluation-runner.v1",
            "suite": "suite.json",
            "report": str(output),
            "failOnFailedCases": False
        }))
        return self.run_cli(runner_main, ["--config", str(config)])

    def test_runner_rejects_symlink(self):
        link = self.root / "linked.json"
        link.symlink_to(self.suite)
        before = self.suite.read_bytes()
        self.assertEqual(self.runner(link), 2)
        self.assertEqual(self.suite.read_bytes(), before)

    def test_runner_rejects_hardlink(self):
        link = self.root / "hardlink.json"
        link.hardlink_to(self.suite)
        before = self.suite.read_bytes()
        self.assertEqual(self.runner(link), 2)
        self.assertEqual(self.suite.read_bytes(), before)

    def test_runner_creates_report(self):
        output = self.root / "report.json"
        self.assertEqual(self.runner(output), 0)
        self.assertTrue(output.is_file())
        self.assertEqual(json.loads(output.read_text())["schemaVersion"],
                         "evaluation-report.v1")

    def test_quality_runner_rejects_symlink(self):
        link = self.root / "linked.md"
        link.symlink_to(self.suite)
        before = self.suite.read_bytes()
        result = self.run_cli(quality_main, [
            "--suite", str(self.suite),
            "--policy", str(self.policy),
            "--report", str(self.root / "quality.json"),
            "--markdown", str(link)
        ])
        self.assertEqual(result, 2)
        self.assertEqual(self.suite.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
