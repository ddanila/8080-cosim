"""Check shell profile dispatch without running the long HDL simulations."""

import os
import re
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NetworkProfileTest(unittest.TestCase):
    def test_revb_ci_controls_the_inner_boot_phase(self):
        system = (ROOT / "spinoffs/minimal-vga/sim/revb_rom_system_check.sh").read_text()
        tier = (ROOT / "spinoffs/minimal-vga/sim/revb_tier_suite.sh").read_text()
        phase = re.search(r'EKTA_PHASE="\$\{(\w+):-all\}"', system)
        self.assertIsNotNone(phase)
        ci_branch = tier.split("  --ci)", 1)[1].split("  full)", 1)[0]
        self.assertIn(phase.group(1) + "=modes WRITES=1000", ci_branch)

    def run_profile(self, *args):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            for name in ("python3", "iverilog"):
                command = temp / name
                command.write_text("#!/bin/sh\nexit 0\n")
                command.chmod(0o755)
            command = temp / "vvp"
            command.write_text('''#!/bin/sh
printf '%s\\n' "$*" >> "$PROFILE_CALLS"
case "$1" in
  *video-pof-tb) echo "VIDEO-POF-HDL: PASS" ;;
  *network-first-rom-abi-tb) echo "NETWORK-FIRST-ROM-ABI-HDL: PASS netdisk_dma=128" ;;
  *) echo "NETWORK-FIRST-ROM-HDL: PASS" ;;
esac
''')
            command.chmod(0o755)
            calls = temp / "calls"
            result = subprocess.run(
                ["bash", "sync/network_first_rom_hdl_check.sh", *args],
                cwd=ROOT, env={**os.environ, "PATH": directory + os.pathsep + os.environ["PATH"],
                               "PROFILE_CALLS": str(calls)},
                capture_output=True, text=True, timeout=10,
            )
            return result, calls.read_text().splitlines() if calls.exists() else []

    def test_ci_runs_only_focused_hardware_guard(self):
        result, calls = self.run_profile("--ci")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(calls), 1)
        self.assertIn("video-pof-tb", calls[0])
        self.assertIn("firmware simulation is local-only", result.stdout)

    def test_default_keeps_full_local_matrix(self):
        result, calls = self.run_profile()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(calls), 8)
        self.assertTrue(any("network-rom-c12-abi.hex" in call for call in calls))
        self.assertTrue(any("+netdisk" in call for call in calls))

    def test_typo_cannot_silently_reduce_coverage(self):
        result, calls = self.run_profile("--typo")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
