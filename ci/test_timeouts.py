"""Prevent unbounded or over-budget CI from returning unnoticed."""

import unittest

from ci.check_timeouts import check_workflow


WORKFLOW = """name: fixture
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v7
      - name: Test
        timeout-minutes: 5
        run: |
          echo test
"""


class TimeoutTest(unittest.TestCase):
    def test_bounded_workflow(self):
        self.assertEqual(check_workflow(WORKFLOW), [])

    def test_only_ttl_lane_has_measured_eight_minute_exception(self):
        text = WORKFLOW.replace("  test:", "  revb-ttl-boot:")
        self.assertEqual(check_workflow(text.replace("timeout-minutes: 5", "timeout-minutes: 8")), [])
        self.assertTrue(check_workflow(text.replace("timeout-minutes: 5", "timeout-minutes: 9")))

    def test_missing_or_long_job_budget(self):
        for value in ("", "    timeout-minutes: 11\n", "    timeout-minutes: 0\n"):
            with self.subTest(value=value):
                self.assertTrue(check_workflow(WORKFLOW.replace("    timeout-minutes: 10\n", value)))

    def test_missing_or_long_step_budget(self):
        for value in ("", "        timeout-minutes: 6\n", "        timeout-minutes: 0\n"):
            with self.subTest(value=value):
                self.assertTrue(check_workflow(WORKFLOW.replace("        timeout-minutes: 5\n", value)))

    def test_run_first_step_is_checked(self):
        self.assertTrue(check_workflow(WORKFLOW.replace(
            "      - name: Test\n        timeout-minutes: 5\n        run: |",
            "      - run: echo unbounded",
        )))

    def test_each_job_needs_its_own_budget(self):
        self.assertTrue(check_workflow(WORKFLOW + "  another:\n    runs-on: ubuntu-latest\n"))


if __name__ == "__main__":
    unittest.main()
