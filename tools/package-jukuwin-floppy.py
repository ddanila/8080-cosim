#!/usr/bin/env python3
"""Package the checked Windows host and full development CP/M disk for transfer."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FLOPPY_BYTES = 1474560
# Standard FAT12 1.44 MB: boot + two 9-sector FATs + 14-sector root directory.
DATA_BYTES = (2880 - 1 - 18 - 14) * 512


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path: Path) -> dict:
    return {'file': path.name, 'bytes': path.stat().st_size, 'sha256': sha256(path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=ROOT / 'build/jukuwin-package')
    parser.add_argument('--media', type=Path, default=ROOT / 'host/windows/media')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/jukuwin-floppy')
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / 'tools/check-jukuwin-package.py'),
                    str(args.package)], check=True)
    media = json.loads((args.media / 'manifest.json').read_text())
    report_path = args.media / 'cpm3-report.json'
    volume = args.media / 'CPM3.IMG'
    if (media.get('schema') != 'jukuwin-media-v1' or
            media.get('file') != volume.name or media.get('bytes') != 409600 or
            volume.stat().st_size != 409600 or sha256(volume) != media.get('sha256') or
            sha256(report_path) != media.get('report_sha256')):
        raise SystemExit('CP/M media identity mismatch')
    report = json.loads(report_path.read_text())
    if (report.get('profile') != 'development-a' or
            report.get('image_sha256') != sha256(volume)):
        raise SystemExit('CP/M development profile report differs')
    for tool in ('mformat', 'mcopy'):
        if not shutil.which(tool):
            raise SystemExit(f'{tool} is required (install mtools)')
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f'output must be empty: {output}')
    files = output / 'files'
    files.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.package / 'JUKUWIN.EXE', files / 'JUKUWIN.EXE')
    shutil.copyfile(volume, files / 'CPM3.IMG')
    shutil.copyfile(args.media / 'LICENSE.TXT', files / 'LICENSE.TXT')
    config = (ROOT / 'host/windows/JUKUWIN.INI.example').read_text()
    config = config.replace('mode=c12', 'mode=stock').replace(
        '[drive_a]\nimage=', '[drive_a]\nimage=CPM3.IMG').replace(
        'working=', 'working=CPM3-WORK.IMG')
    (files / 'JUKUWIN.INI').write_bytes(config.replace('\n', '\r\n').encode('ascii'))
    tool_names = [item['destination'].split(':', 1)[1] for item in report['files']]
    readme = f'''JUKU WINDOWS HOST - FLOPPY TRANSFER BUNDLE

Copy all files from this floppy into a writable hard-disk folder, then run
JUKUWIN.EXE. Do not run directly from the transfer floppy: snapshots and
serial captures need writable hard-disk space.

Select the serial adapter and the ROM actually fitted in the Juku.
Stock ROM is preselected for CS00014, at 9600 baud with reset recovery.
C11 and C12 are also supported; choose the matching mode if fitted.
Press Listen, then select T -> N on a stock-ROM Juku to boot from Janet.
The host also recognizes a running CP/M session and recovers after reset.

CPM3.IMG is the 400 KiB full development A: volume ({len(tool_names)} files).
Snapshot mode keeps that base intact and creates CPM3-WORK.IMG on the host.
B: is empty; an optional native 800 KiB music/apps image can be selected later.
Type DIR at the CP/M prompt, or HELP and TYPE TOOLS.TXT for the tools.

Included CP/M files:
{', '.join(tool_names)}

This is a Windows transfer floppy, not a PC boot disk or a native Juku disk.
JUKUWIN.IMG is a complete 1.44 MB FAT12 transfer image if writing whole disks.
Alternatively, copy the contents of the files folder to a formatted floppy.

MANIFEST.JSN records the build, embedded boot payloads and CP/M image source.
SHA256.TXT checks every delivered file except itself. LICENSE.TXT contains
redistribution notices. Windows 95 and physical Windows serial qualification
remain pending; the CI checks are recorded on the workflow run.

https://github.com/ddanila/8080-cosim
'''
    (files / 'README.TXT').write_bytes(readme.replace('\n', '\r\n').encode('ascii'))
    host_manifest = json.loads((args.package / 'MANIFEST.json').read_text())
    manifest = {'schema': 'jukuwin-floppy-v1', 'host': host_manifest,
                'cpm_media': media, 'cpm_files': tool_names,
                'files': [identity(path) for path in sorted(files.iterdir())]}
    (files / 'MANIFEST.JSN').write_text(json.dumps(manifest, indent=2) + '\n', encoding='ascii')
    sums = ''.join(f'{sha256(path)}  {path.name}\n' for path in sorted(files.iterdir()))
    (files / 'SHA256.TXT').write_bytes(sums.replace('\n', '\r\n').encode('ascii'))
    allocated = sum((path.stat().st_size + 511) // 512 * 512 for path in files.iterdir())
    if allocated > DATA_BYTES:
        raise SystemExit(f'bundle exceeds 1.44 MB floppy capacity: {allocated} > {DATA_BYTES}')
    image = output / 'JUKUWIN.IMG'
    image.write_bytes(bytes(FLOPPY_BYTES))
    subprocess.run(['mformat', '-i', str(image), '-f', '1440', '-v', 'JUKUWIN', '::'], check=True)
    subprocess.run(['mcopy', '-i', str(image), *map(str, sorted(files.iterdir())), '::'], check=True)
    # Read every file back through FAT12, rather than trusting just mcopy's exit.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='jukuwin-fat12-check.') as name:
        subprocess.run(['mcopy', '-i', str(image), '::*', name], check=True)
        extracted = Path(name)
        if {p.name.upper() for p in extracted.iterdir()} != {p.name for p in files.iterdir()}:
            raise SystemExit('FAT12 directory readback differs')
        for path in extracted.iterdir():
            if path.read_bytes() != (files / path.name.upper()).read_bytes():
                raise SystemExit(f'FAT12 readback mismatch: {path.name}')
    (output / 'SHA256SUMS').write_text(f'{sha256(image)}  {image.name}\n', encoding='ascii')
    print(f'JUKUWIN-FLOPPY: PASS ({len(tool_names)} CP/M files, '
          f'{allocated} bytes allocated, {DATA_BYTES - allocated} bytes free)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
