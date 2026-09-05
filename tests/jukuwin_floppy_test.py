#!/usr/bin/env python3
"""Verify full CP/M transfer media, FAT12 readback and capacity/identity failures."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FloppyTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='jukuwin-floppy-test.')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.build = self.root / 'build'
        self.build.mkdir()
        self.package = self.root / 'package'
        self.media = ROOT / 'host/windows/media'

    def package_exe(self, size=180000):
        (self.build / 'JUKUWIN.EXE').write_bytes(b'MZ' + bytes(size - 2))
        subprocess.run([sys.executable, str(ROOT / 'tools/package-jukuhost-windows.py'),
                        '--build-dir', str(self.build), '--output', str(self.package)],
                       check=True, capture_output=True)

    def run_floppy(self):
        return subprocess.run([sys.executable, str(ROOT / 'tools/package-jukuwin-floppy.py'),
                               '--package', str(self.package), '--media', str(self.media),
                               '--output', str(self.root / 'floppy')],
                              capture_output=True, text=True)

    @unittest.skipUnless(shutil.which('mformat') and shutil.which('mcopy'), 'requires mtools')
    def test_full_bundle_fat12_roundtrip(self):
        self.package_exe()
        result = self.run_floppy()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        out = self.root / 'floppy'
        image = (out / 'JUKUWIN.IMG').read_bytes()
        self.assertEqual(len(image), 1474560)
        self.assertEqual(image[510:512], b'\x55\xaa')
        self.assertEqual(image[54:62], b'FAT12   ')
        files = out / 'files'
        self.assertEqual({p.name for p in files.iterdir()}, {
            'JUKUWIN.EXE', 'JUKUWIN.INI', 'CPM3.IMG', 'README.TXT',
            'LICENSE.TXT', 'MANIFEST.JSN', 'SHA256.TXT'})
        self.assertEqual((files / 'CPM3.IMG').read_bytes(), (self.media / 'CPM3.IMG').read_bytes())
        config = (files / 'JUKUWIN.INI').read_text()
        self.assertIn('mode=stock', config)
        self.assertIn('[drive_a]\nimage=CPM3.IMG', config)
        self.assertIn('[drive_b]\nimage=\n', config)
        manifest = json.loads((files / 'MANIFEST.JSN').read_text())
        self.assertTrue({'ED.COM', 'SID.COM', 'PIP.COM', 'HELP.HLP', 'HEXCOM.COM',
                         'PATCH.COM', 'STATUS.COM', 'DIAG.COM'} <= set(manifest['cpm_files']))
        for line in (files / 'SHA256.TXT').read_text().splitlines():
            expected, name = line.split('  ')
            self.assertEqual(hashlib.sha256((files / name).read_bytes()).hexdigest(), expected)

    @unittest.skipUnless(shutil.which('mformat') and shutil.which('mcopy'), 'requires mtools')
    def test_rejects_floppy_overflow(self):
        self.package_exe(1200000)
        result = self.run_floppy()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('exceeds 1.44 MB floppy capacity', result.stderr)
        self.assertFalse((self.root / 'floppy/JUKUWIN.IMG').exists())

    def test_rejects_changed_cpm_media(self):
        self.package_exe()
        copied = self.root / 'media'
        shutil.copytree(self.media, copied)
        self.media = copied
        image = copied / 'CPM3.IMG'
        data = bytearray(image.read_bytes())
        data[1000] ^= 1
        image.write_bytes(data)
        result = self.run_floppy()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('CP/M media identity mismatch', result.stderr)


if __name__ == '__main__':
    unittest.main()
