#!/usr/bin/env python3
"""Guard shared-gain JPS normalization, structure, silence and refusal boundaries."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'normalization', ROOT / 'spinoffs/jukupoly/tools/build_normalization_ab.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture(tone=9, pcm=8):
    # One held tone plus a drum, then end. 64-sample silent and drum buffers.
    rows = bytes([1, 17, 0x23, 1, 255, 0x20 | tone, 0x5a, 0x18, 0, 128])
    body = rows + bytes(64) + bytes([0x5d, 0x18, 1]) + bytes([pcm, 0, 4, 1]) + bytes(60)
    return b'JPS\x01' + (16 + len(body)).to_bytes(2, 'little') + bytes(
        [64, 0, 0, 28, 16, 24, 26, 24, 0, 0]) + body


class NormalizationTest(unittest.TestCase):
    def test_shared_gain_and_structural_identity(self):
        original = fixture()
        normalized, info = module.normalize(original)
        self.assertEqual(info['gain'], 15 / 9)
        self.assertEqual(normalized[21], 0x2f)
        self.assertEqual(normalized[93:97], bytes([13, 0, 7, 2]))
        allowed = {21, 93, 95, 96}
        self.assertTrue(all(a == b for i, (a, b) in
                            enumerate(zip(original, normalized)) if i not in allowed))
        self.assertEqual(module.normalize(normalized)[0], normalized)

    def test_full_scale_drums_protect_balance(self):
        original = fixture(pcm=15)
        self.assertEqual(module.normalize(original)[0], original)

    def test_full_scale_tones_are_unchanged(self):
        original = fixture(tone=15)
        self.assertEqual(module.normalize(original)[0], original)

    def test_rejects_unsupported_and_corrupt_payloads(self):
        for offset, value in [(3, 2), (7, 1), (14, 1), (17, 0x21),
                              (21, 0x19), (22, 0), (90, 0), (93, 16)]:
            with self.subTest(offset=offset):
                data = bytearray(fixture())
                data[offset] = value
                with self.assertRaises(ValueError):
                    module.normalize(bytes(data))
        with self.assertRaises(ValueError):
            module.normalize(fixture()[:-1])


if __name__ == '__main__':
    unittest.main()
