#!/usr/bin/env python3
"""Exercise INI identity, fallback, and snapshot policy through the C app."""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "build" / "jukuhost"


def identity(path: Path) -> tuple[int, str]:
    data = path.read_bytes()
    return len(data), hashlib.sha256(data).hexdigest()


def run(config: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(HOST), str(config)], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )


def main() -> int:
    if not HOST.is_file():
        raise SystemExit("missing build/jukuhost; run the Linux build first")
    with tempfile.TemporaryDirectory(prefix="jukuhost-config.") as name:
        temp = Path(name)
        primary_system = temp / "primary.bin"
        primary_fast = temp / "primary.jf16"
        fallback_system = temp / "fallback.bin"
        fallback_fast = temp / "fallback.jf16"
        base = temp / "base.img"
        working = temp / "working.img"
        primary_system.write_bytes(b"rejected primary system")
        primary_fast.write_bytes(b"unused primary fastboot")
        fallback_system.write_bytes(b"accepted fallback system")
        fallback_fast.write_bytes(b"accepted fallback fastboot")
        base.write_bytes(bytes(409600))
        system_size, system_hash = identity(fallback_system)
        fast_size, fast_hash = identity(fallback_fast)
        base_size, base_hash = identity(base)
        config = temp / "JUKUHOST.INI"
        config.write_text(
            "[host]\n"
            "port=/dev/jukuhost-intentionally-missing\n"
            "log=JUKUHOST.LOG\n"
            "network_rom=yes\n"
            "[system]\n"
            "file=primary.bin\n"
            f"size={primary_system.stat().st_size}\n"
            f"sha256={'0' * 64}\n"
            "[fastboot]\n"
            "file=primary.jf16\n"
            f"size={primary_fast.stat().st_size}\n"
            f"sha256={identity(primary_fast)[1]}\n"
            "[fallback_system]\n"
            "file=fallback.bin\n"
            f"size={system_size}\n"
            f"sha256={system_hash}\n"
            "[fallback_fastboot]\n"
            "file=fallback.jf16\n"
            f"size={fast_size}\n"
            f"sha256={fast_hash}\n"
            "[disk_a]\n"
            "base=base.img\n"
            "file=working.img\n"
            f"size={base_size}\n"
            f"sha256={base_hash}\n"
            "geometry=juku-cpm3\n"
            "mode=snapshot\n",
            encoding="ascii",
        )
        completed = run(config)
        assert completed.returncode == 4, completed.stdout
        assert working.read_bytes() == base.read_bytes()
        assert "primary boot slot rejected; trying fallback" in completed.stdout
        assert "fallback boot slot selected" in completed.stdout
        assert "A: created snapshot working copy" in completed.stdout
        log = (temp / "JUKUHOST.LOG").read_text(encoding="ascii")
        assert "identity mismatch" in log and "fallback system identity" in log

        # A subsequent start accepts the mutable working copy by size while
        # continuing to authenticate and preserve the immutable base.
        working_bytes = bytearray(working.read_bytes())
        working_bytes[0] = 0xA5
        working.write_bytes(working_bytes)
        completed = run(config)
        assert completed.returncode == 4, completed.stdout
        assert "A: resumed snapshot working copy" in completed.stdout
        assert base.read_bytes()[0] == 0

        malformed = temp / "BAD.INI"
        malformed.write_text("[host]\nport=x\nport=y\n", encoding="ascii")
        completed = run(malformed)
        assert completed.returncode == 2
        assert "invalid or duplicate value" in completed.stdout

    selftest = subprocess.run(
        [str(HOST), "--selftest"], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    assert selftest.returncode == 0 and "selftest: PASS" in selftest.stdout
    print("JUKUHOST-CONFIG-TEST: PASS (SHA-256 + fallback + safe snapshot)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
