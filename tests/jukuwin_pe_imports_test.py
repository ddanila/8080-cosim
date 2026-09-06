#!/usr/bin/env python3
"""Keep the exact import allowlist check portable across GNU binutils versions."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pe', ROOT / 'tools/check-jukuwin-pe.py')
pe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pe)


class ImportsTest(unittest.TestCase):
    def test_original_win95_excludes_later_interlocked_exports(self):
        allowlist = (ROOT / 'host/windows/win95-imports.txt').read_text().splitlines()
        self.assertIn('KERNEL32.DLL!InterlockedExchange', allowlist)
        for name in ('InterlockedExchangeAdd', 'InterlockedCompareExchange'):
            self.assertNotIn('KERNEL32.DLL!' + name, allowlist)

    def test_classic_and_bound_to_tables(self):
        for middle in ('', '<none> '):
            output = f'''
        DLL Name: kernel32.dll
        vma:  Hint/Ord Member-Name Bound-To
        0003e123 {middle}42 CloseHandle
        0003e234 {middle}1359 WriteFile
        DLL Name: USER32.DLL
        0003e456 {middle}123 MessageBoxA
'''
            self.assertEqual(pe.parse_imports(output), {
                'KERNEL32.DLL!CloseHandle', 'KERNEL32.DLL!WriteFile',
                'USER32.DLL!MessageBoxA'})

    def test_preserves_unexpected_imports_for_allowlist_rejection(self):
        self.assertEqual(pe.parse_imports('DLL Name: KERNEL32.DLL\n 1234 7 GetTickCount64'),
                         {'KERNEL32.DLL!GetTickCount64'})

    def test_ignores_headers_and_unscoped_rows(self):
        self.assertEqual(pe.parse_imports('1234 7 Ignored\nDLL Name: USER32.DLL\nvma: Hint/Ord Member-Name'), set())


if __name__ == '__main__':
    unittest.main()
