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
CORE_STORED = 0x0F00
EXTENSION_BYTES = 267


def assemble(source: Path, output: Path, includes: tuple[Path, ...],
             defines: tuple[str, ...] = ()) -> bytes:
    command = [str(executable()), "--nmnv", "--zmac", "-8"]
    command.extend(f"-D{name}" for name in defines)
    for include in includes:
        command.extend(("-I", str(include)))
    command.extend(("-o", str(output), str(source)))
    subprocess.run(command, check=True)
    return output.read_bytes()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(*, abi_selftest: bool = False) -> tuple[bytes, dict[str, object]]:
    with tempfile.TemporaryDirectory(prefix="juku-network-rom.") as name:
        temporary = Path(name)
        gate = assemble(HERE / "gate-wrapper.asm", temporary / "gate.cim",
                        (COMMON,))
        helper = assemble(HERE / "ram-helper.asm", temporary / "helper.cim",
                          (COMMON,))
        core = assemble(
            ROOT / "third_party" / "juku-common" / "transport" /
            "fastboot-core.asm",
            temporary / "core.cim",
            (ROOT / "third_party" / "juku-common" / "transport",),
            ("FASTBOOT_8N1", "FASTBOOT_ZX0", "FASTBOOT_STREAM",
             "FASTBOOT_V15", "FASTBOOT_EXACT", "FASTBOOT_EXT_ACK",
             "FASTBOOT_PROBE_SYNC"),
        )
        if len(core) > 128:
            raise ValueError(f"V15 core is {len(core)} bytes; envelope is 128")
        core = bytearray(core.ljust(128, b"\0"))
        if core[3:7] != b"JF15" or core[8] != 0:
            raise ValueError("V15 core metadata layout changed")
        core[9:11] = EXTENSION_BYTES.to_bytes(2, "little")
        length_sentinel = bytes.fromhex("01 5A A5")
        if core.count(length_sentinel) != 1:
            raise ValueError("V15 core extension-length sentinel changed")
        length_offset = core.index(length_sentinel) + 1
        core[length_offset:length_offset + 2] = \
            EXTENSION_BYTES.to_bytes(2, "little")

        # The automatic ROM has no operator event for host synchronization.
        # Redirect only the first find_first RX call to a one-shot prelude at
        # 0180h. It sends C4h, self-patches that call back to the canonical
        # RX routine at 0173h, then tail-jumps there. The extension retains its
        # fixed rx=0173h contract and later parser retries emit no extra C4h.
        first_rx = bytes.fromhex("CD 73 01 FE A5")
        if core.count(first_rx) != 1:
            raise ValueError("V15 core first-RX signature changed")
        first_rx_offset = core.index(first_rx)
        core[first_rx_offset + 1:first_rx_offset + 3] = bytes.fromhex("80 01")
        call_operand = 0x0100 + first_rx_offset + 1
        prelude = bytes((
            0x3E, 0xC4,                   # MVI A,C4h
            0xD3, 0x08,                   # OUT USARTDATA
            0x21, 0x73, 0x01,             # LXI H,0173h
            0x22, call_operand & 0xFF, call_operand >> 8,  # SHLD call operand
            0xC3, 0x73, 0x01,             # JMP 0173h
        ))
        core.extend(prelude)
        if len(core) > GATE_STORED - CORE_STORED:
            raise ValueError(f"automatic V15 core is {len(core)} bytes")
        core = bytes(core)
        if len(gate) > 0xE0:
            raise ValueError(f"RAM gate is {len(gate)} bytes; envelope is 224")
        if len(helper) > 0x80:
            raise ValueError(f"RAM helper is {len(helper)} bytes; envelope is 128")

        generated = HERE / "network-rom-generated.inc"
        expected_generated = (
            "; Generated/verified by build_network_rom.py.\n"
            f"JROMGATEBYTES equ {len(gate)}\n"
            f"JROMHELPERBYTES equ {len(helper)}\n"
            f"JROMCOREBYTES equ {len(core)}\n"
            f"JROMEXTENSIONBYTES equ {EXTENSION_BYTES}\n"
            f"CORESTORED equ 0{CORE_STORED:04x}h\n"
            f"GATESTORED equ 0{GATE_STORED:04x}h\n"
            f"HELPSTORED equ 0{HELP_STORED:04x}h\n"
        )
        if generated.read_text() != expected_generated:
            raise ValueError("network-rom-generated.inc is stale")
        includes = (
            HERE, COMMON,
            ROOT / "third_party" / "juku-common" / "diag",
        )
        boot = assemble(
            HERE / "boot.asm", temporary / "boot.cim", includes,
            ("ABI_SELFTEST",) if abi_selftest else (),
        )
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
        lower[CORE_STORED:CORE_STORED + len(core)] = core
        lower[GATE_STORED:GATE_STORED + len(gate)] = gate
        lower[HELP_STORED:HELP_STORED + len(helper)] = helper
        lower[0x3F] = (-sum(lower) - sum(resident)) & 0xFF
        image = bytes(lower) + resident
        if sum(image) & 0xFF:
            raise ValueError("complete-ROM checksum balance failed")

    metadata: dict[str, object] = {
        "schema": "juku-network-rom-abi1-v1",
        "image_bytes": len(image),
        "image_sha256": digest(image),
        "d15_sha256": digest(image[:0x2000]),
        "d16_sha256": digest(image[0x2000:]),
        "boot_code_bytes": len(boot),
        "gate_bytes": len(gate),
        "helper_bytes": len(helper),
        "fastboot_core_bytes": len(core),
        "fastboot_extension_bytes": EXTENSION_BYTES,
        "quick_post": [
            "cpu", "ram-data", "ram-address", "complete-rom", "pit-usart",
        ],
        "hardware_init": [
            "ppi0-82-pc7-high", "ppi1-9b", "stock-raster-refresh",
            "pic-d6-fe-masked", "d57-ch0-mode2-count4", "d11-8n1",
        ],
        "post_status": {
            "ok": "00", "cpu": "C1", "ram-data": "C2",
            "ram-address": "C3", "complete-rom": "C4", "pit-usart": "C5",
        },
        "target_ready_byte": "C4",
        "resident_bytes": len(resident),
        "resident_services": [
            "console", "serial", "keyboard", "diagnostics",
        ],
        "abi": {"base": "FF00", "major": 1, "minor": 0},
        "status": "automatic-boot desk image; not for physical programming",
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
