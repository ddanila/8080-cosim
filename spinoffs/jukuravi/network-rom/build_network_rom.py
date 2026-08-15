#!/usr/bin/env python3
"""Build the from-scratch 16 KiB network-first Juku ROM skeleton."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
COMMON = ROOT / "third_party" / "juku-common" / "platform"
sys.path.insert(0, str(ROOT / "tools"))
from build_zmac import executable  # noqa: E402


OUTPUT = HERE / "juku-network-rom-abi1.bin"
D15_OUTPUT = HERE / "juku-network-rom-abi1-d15.bin"
D16_OUTPUT = HERE / "juku-network-rom-abi1-d16.bin"
METADATA_OUTPUT = HERE / "juku-network-rom-abi1.json"

LOWER_SIZE = 0x1800
RESIDENT_SIZE = 0x2800
GATE_STORED = 0x1000
HELP_STORED = 0x1400


def assemble(source: Path, output: Path, includes: tuple[Path, ...]) -> bytes:
    command = [str(executable()), "--nmnv", "--zmac", "-8"]
    for include in includes:
        command.extend(("-I", str(include)))
    command.extend(("-o", str(output), str(source)))
    subprocess.run(command, check=True)
    return output.read_bytes()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build() -> tuple[bytes, dict[str, object]]:
    with tempfile.TemporaryDirectory(prefix="juku-network-rom.") as name:
        temporary = Path(name)
        gate = assemble(HERE / "gate-wrapper.asm", temporary / "gate.cim",
                        (COMMON,))
        helper = assemble(HERE / "ram-helper.asm", temporary / "helper.cim",
                          (COMMON,))
        if len(gate) > 0xE0:
            raise ValueError(f"RAM gate is {len(gate)} bytes; envelope is 224")
        if len(helper) > 0x80:
            raise ValueError(f"RAM helper is {len(helper)} bytes; envelope is 128")

        generated = HERE / "network-rom-generated.inc"
        expected_generated = (
            "; Generated/verified by build_network_rom.py.\n"
            f"JROMGATEBYTES equ {len(gate)}\n"
            f"JROMHELPERBYTES equ {len(helper)}\n"
            f"GATESTORED equ 0{GATE_STORED:04x}h\n"
            f"HELPSTORED equ 0{HELP_STORED:04x}h\n"
        )
        if generated.read_text() != expected_generated:
            raise ValueError("network-rom-generated.inc is stale")
        includes = (HERE, COMMON)
        boot = assemble(HERE / "boot.asm", temporary / "boot.cim", includes)
        resident = assemble(
            HERE / "resident.asm", temporary / "resident.cim", includes,
        )
        if len(boot) > GATE_STORED:
            raise ValueError(f"boot code overlaps stored gate: {len(boot)} bytes")
        if len(resident) != RESIDENT_SIZE:
            raise ValueError(
                f"resident image is {len(resident)} bytes, expected {RESIDENT_SIZE}"
            )

        lower = bytearray(b"\xFF" * LOWER_SIZE)
        lower[:len(boot)] = boot
        lower[GATE_STORED:GATE_STORED + len(gate)] = gate
        lower[HELP_STORED:HELP_STORED + len(helper)] = helper
        image = bytes(lower) + resident

    metadata: dict[str, object] = {
        "schema": "juku-network-rom-abi1-v1",
        "image_bytes": len(image),
        "image_sha256": digest(image),
        "d15_sha256": digest(image[:0x2000]),
        "d16_sha256": digest(image[0x2000:]),
        "boot_code_bytes": len(boot),
        "gate_bytes": len(gate),
        "helper_bytes": len(helper),
        "resident_bytes": len(resident),
        "abi": {"base": "FF00", "major": 1, "minor": 0},
        "status": "ABI skeleton; not for physical programming",
    }
    return image, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    image, metadata = build()
    expected = (
        (OUTPUT, image),
        (D15_OUTPUT, image[:0x2000]),
        (D16_OUTPUT, image[0x2000:]),
        (METADATA_OUTPUT,
         (json.dumps(metadata, indent=2) + "\n").encode()),
    )
    if args.check:
        for path, data in expected:
            if not path.is_file() or path.read_bytes() != data:
                raise SystemExit(f"NETWORK-ROM: {path.name} is stale")
        print(f"NETWORK-ROM-CHECK: PASS {metadata['image_sha256']}")
        return 0
    for path, data in expected:
        path.write_bytes(data)
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
