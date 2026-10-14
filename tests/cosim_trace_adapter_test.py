#!/usr/bin/env python3
"""The HDL adapter never claims a partial capture is complete or timed."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("trace_adapter", ROOT / "scripts/import_cosim_trace.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class AdapterTests(unittest.TestCase):
    def test_explicit_window_and_strict_bus_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, rom = Path(tmp) / "bus", Path(tmp) / "rom"
            rom.write_bytes(b"test ROM")
            source.write_text("MR 0000 3e\nMW 8000 42\n")
            result = adapter.convert(source, rom, 2)
            self.assertIsNone(result[0]["profile"]["clock_hz"])
            self.assertEqual(result[2]["address"], 0x8000)
            with self.assertRaises(ValueError):
                adapter.convert(source, rom, 3)
            for malformed in ("MR 0000 xx", "MW 10000 42", "XX 0 0", "MR 0 100", "MW 0"):
                source.write_text(malformed)
                with self.assertRaises(ValueError):
                    adapter.convert(source, rom, 1)


if __name__ == "__main__":
    unittest.main()
