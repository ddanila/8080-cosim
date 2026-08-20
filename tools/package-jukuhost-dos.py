#!/usr/bin/env python3
"""Create the self-contained, 8.3-safe Pocket8086 Juku host directory."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def identity(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return path.stat().st_size, digest.hexdigest()


def require_artifact(root: Path, entry: dict[str, object]) -> Path:
    path = root / "out" / str(entry["file"])
    size, digest = identity(path)
    if size != entry["bytes"] or digest != entry["sha256"]:
        raise SystemExit(f"artifact identity mismatch: {path}")
    return path


def copy(source: Path, destination: Path) -> None:
    shutil.copyfile(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cpm-root",
        type=Path,
        default=ROOT.parent / "cpm-plus-juku",
        help="cpm-plus-juku checkout (default: adjacent checkout)",
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "build" / "dos-package"
    )
    args = parser.parse_args()

    executable = ROOT / "build" / "dos" / "JUKUHOST.EXE"
    if not executable.is_file():
        raise SystemExit("build/dos/JUKUHOST.EXE is missing; run DOS build first")
    manifest_path = args.cpm_root / "out" / "cpm-plus-juku-c8-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("schema") != "cpm-plus-juku-boot-manifest-v1":
        raise SystemExit(f"unsupported manifest: {manifest_path}")

    system = manifest["system"]
    fastboot = manifest["fast_stage"]
    volumes = {entry["profile"]: entry for entry in manifest["volumes"]}
    disk_a = volumes["full-a"]
    disk_b = volumes["approved-apps-b"]
    sources = {
        "JUKUHOST.EXE": executable,
        "SYSTEM.BIN": require_artifact(args.cpm_root, system),
        "FAST16.BIN": require_artifact(args.cpm_root, fastboot),
        "BASE.IMG": require_artifact(args.cpm_root, disk_a),
        "APPS.JUK": require_artifact(args.cpm_root, disk_b),
    }

    args.output.mkdir(parents=True, exist_ok=True)
    for name, source in sources.items():
        copy(source, args.output / name)

    config = f"""[host]\r
port=COM1\r
log=JUKUHOST.LOG\r
capture=JUKUHOST.CAP\r
console=CON\r
network_rom=yes\r
timeout=120\r
disk_timeout=0\r
boot_restarts=3\r
reconnect_timeout=30\r
\r
[network]\r
protocol=3\r
baud=19200\r
read_ahead=3\r
reply_guard_ms=2\r
\r
[system]\r
file=SYSTEM.BIN\r
size={system['bytes']}\r
sha256={system['sha256']}\r
\r
[fastboot]\r
file=FAST16.BIN\r
size={fastboot['bytes']}\r
sha256={fastboot['sha256']}\r
\r
[disk_a]\r
base=BASE.IMG\r
file=WORK.IMG\r
size={disk_a['bytes']}\r
sha256={disk_a['sha256']}\r
geometry=juku-cpm3\r
mode=snapshot\r
\r
[disk_b]\r
file=APPS.JUK\r
size={disk_b['bytes']}\r
sha256={disk_b['sha256']}\r
geometry=juku-native\r
mode=read-only\r
"""
    (args.output / "JUKUHOST.INI").write_bytes(config.encode("ascii"))
    (args.output / "JUKU.BAT").write_bytes(b"@ECHO OFF\r\nJUKUHOST\r\n")
    (args.output / "README.TXT").write_bytes(
        b"Juku host for Pocket8086 / DOS\r\n"
        b"Run JUKU.BAT or JUKUHOST with no options.\r\n"
        b"COM1, 19200 baud NetDisk, local N4 console.\r\n"
        b"Press F10 while idle to stop cleanly.\r\n"
    )

    listed = []
    for path in sorted(args.output.iterdir()):
        if path.name != "MANIFEST.SHA" and path.is_file():
            size, digest = identity(path)
            listed.append(f"{digest}  {path.name}  {size}\r\n")
    (args.output / "MANIFEST.SHA").write_bytes("".join(listed).encode("ascii"))
    print(f"JUKUHOST-DOS-PACKAGE: PASS ({args.output})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
