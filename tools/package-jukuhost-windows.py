#!/usr/bin/env python3
"""Create the portable JUKUWIN folder without loose boot payloads."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "file": path.name,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", type=Path,
                        default=ROOT / "build/win32")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/jukuwin-package")
    args = parser.parse_args()
    executable = args.build_dir / "JUKUWIN.EXE"
    if not executable.is_file():
        raise SystemExit(f"missing {executable}")
    args.output.mkdir(parents=True, exist_ok=True)
    outputs = {
        "JUKUWIN.EXE": executable,
        "JUKUWIN.INI": ROOT / "host/windows/JUKUWIN.INI.example",
        "README.md": ROOT / "docs/windows-jukuhost-client.md",
    }
    for name, source in outputs.items():
        shutil.copyfile(source, args.output / name)

    payload_manifest = json.loads(
        (ROOT / "host/windows/payload-manifest.json").read_text()
    )
    source_revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        text=True, stdout=subprocess.PIPE,
    ).stdout.strip()
    manifest = {
        "schema": "jukuwin-package-v1",
        "source_revision": source_revision,
        "compiler": "Open Watcom V2 2026-08-20",
        "target": "PE32/i386 Windows GUI subsystem 4.0",
        "qualification": {
            "desk": "see docs/windows-jukuhost-client-implementation.md",
            "physical_windows": "pending",
            "physical_windows_95": "pending",
        },
        "executable": identity(args.output / "JUKUWIN.EXE"),
        "embedded_payload_source": payload_manifest["source"],
        "embedded_payloads": payload_manifest["payloads"],
    }
    manifest_path = args.output / "MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    packaged = [args.output / name for name in outputs]
    packaged.append(manifest_path)
    sums = "".join(
        f"{identity(path)['sha256']}  {path.name}\n"
        for path in sorted(packaged, key=lambda item: item.name)
    )
    (args.output / "SHA256SUMS").write_text(sums, encoding="ascii")
    print(
        f"JUKUWIN-PACKAGE: PASS ({args.output}, "
        f"{manifest['executable']['bytes']} byte EXE)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
