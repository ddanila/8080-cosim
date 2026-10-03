"""An incomplete Gerber review must close the package gate without crashing."""

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "order_readiness", ROOT / "kicad/report_order_readiness.py"
)
ORDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORDER)


class ExternalReviewTest(unittest.TestCase):
    def review(self, code, report):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "external-gerber-review.md").write_text(report)
            result = subprocess.CompletedProcess(["review"], code)
            with patch.object(ORDER.subprocess, "run", return_value=result):
                return ORDER.run_external_gerber_review(output)

    def test_completed_review_is_ready(self):
        self.assertTrue(self.review(0, "Status: **READY**\n")["ready"])

    def test_incomplete_review_is_not_ready(self):
        self.assertFalse(self.review(3, "Status: **NOT READY**\n## Failures\nmissing Gerbers\n")["ready"])

    def test_incomplete_exit_cannot_reuse_ready_report(self):
        self.assertFalse(self.review(3, "Status: **READY**\n")["ready"])

    def test_failures_in_report_close_gate(self):
        self.assertFalse(self.review(0, "Status: **READY**\n## Failures\n")["ready"])

    def test_unexpected_tool_failure_propagates(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.review(1, "Status: **READY**\n")


if __name__ == "__main__":
    unittest.main()
