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
LOCALE_OUTPUT = HERE / "juku-network-rom-abi1.1-c5.bin"
LOCALE_D15_OUTPUT = HERE / "juku-network-rom-abi1.1-c5-d15.bin"
LOCALE_D16_OUTPUT = HERE / "juku-network-rom-abi1.1-c5-d16.bin"
LOCALE_METADATA_OUTPUT = HERE / "juku-network-rom-abi1.1-c5.json"
EXTENDED_OUTPUT = HERE / "juku-network-rom-abi1.2-c6.bin"
EXTENDED_D15_OUTPUT = HERE / "juku-network-rom-abi1.2-c6-d15.bin"
EXTENDED_D16_OUTPUT = HERE / "juku-network-rom-abi1.2-c6-d16.bin"
EXTENDED_METADATA_OUTPUT = HERE / "juku-network-rom-abi1.2-c6.json"
SUCCESSOR_OUTPUT = HERE / "juku-network-rom-abi1.2-c7.bin"
SUCCESSOR_D15_OUTPUT = HERE / "juku-network-rom-abi1.2-c7-d15.bin"
SUCCESSOR_D16_OUTPUT = HERE / "juku-network-rom-abi1.2-c7-d16.bin"
SUCCESSOR_METADATA_OUTPUT = HERE / "juku-network-rom-abi1.2-c7.json"

LOWER_SIZE = 0x1800
RESIDENT_SIZE = 0x2800
GATE_STORED = 0x1000
HELP_STORED = 0x1400
CORE_STORED = 0x0F00
EMBEDDED_EXTENSION_STORED = 0x0600
EMBEDDED_EXTENSION_BYTES = 361
EXTENSION_BYTES = 267
LOCALE_EXTENSION_BYTES = 307
CANDIDATE = "network-first-abi1-cs00015-c4"
LOCALE_CANDIDATE = "network-first-abi1.1-cs00015-c5-desk"
EXTENDED_CANDIDATE = "network-first-abi1.2-c6-simulator"
SUCCESSOR_CANDIDATE = "network-first-abi1.2-c7-modified-raw-simulator"


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


def build(*, abi_selftest: bool = False,
          cursor_phase: str | None = None,
          netdisk_selftest: bool = False,
          sound_selftest: bool = False,
          raw_selftest: str | None = None,
          locale: bool = False,
          extended: bool = False,
          successor: bool = False) -> tuple[bytes, dict[str, object]]:
    if successor:
        extended = True
    if extended:
        locale = True
    if cursor_phase not in (None, "hidden", "visible"):
        raise ValueError(f"unknown cursor phase {cursor_phase!r}")
    if cursor_phase is not None and not abi_selftest:
        raise ValueError("cursor phase fixtures require abi_selftest")
    if netdisk_selftest and not abi_selftest:
        raise ValueError("NetDisk fixture requires abi_selftest")
    if sound_selftest and (not abi_selftest or not extended):
        raise ValueError("sound fixture requires extended ABI selftest")
    if raw_selftest not in (None, "shift-f8", "ctrl-up"):
        raise ValueError(f"unknown raw-key fixture {raw_selftest!r}")
    if raw_selftest is not None and (not abi_selftest or not successor):
        raise ValueError("raw-key fixtures require successor ABI selftest")
    selftest_defines = ("ROM_ABI_LOCALE",) if locale else ()
    if locale and not successor:
        selftest_defines += ("CREEP_LEGACY_PSEUDO",)
    if extended:
        selftest_defines += ("ROM_ABI_EXTENDED",)
        selftest_defines += (
            ("ROM_ABI_RAW_FIXED",) if successor else
            ("ROM_ABI_RAW_MODIFIER_FIRST",)
        )
    extension_bytes = LOCALE_EXTENSION_BYTES if locale else EXTENSION_BYTES
    if abi_selftest:
        selftest_defines += ("ABI_SELFTEST",)
    if cursor_phase is not None:
        selftest_defines += (
            "ABI_CURSOR_" + cursor_phase.upper(),
        )
    if netdisk_selftest:
        selftest_defines += ("ABI_NETDISK_SELFTEST",)
    if sound_selftest:
        selftest_defines += ("ABI_SOUND_SELFTEST",)
    if raw_selftest is not None:
        selftest_defines += (
            "ABI_RAW_" + raw_selftest.replace("-", "_").upper(),
        )
    with tempfile.TemporaryDirectory(prefix="juku-network-rom.") as name:
        temporary = Path(name)
        gate = assemble(HERE / "gate-wrapper.asm", temporary / "gate.cim",
                        (COMMON,), selftest_defines)
        helper_c4 = assemble(
            HERE / "ram-helper.asm", temporary / "helper-c4.cim", (COMMON,),
        )
        helper_c5 = assemble(
            HERE / "ram-helper.asm", temporary / "helper-c5.cim", (COMMON,),
            ("ROM_ABI_LOCALE",),
        )
        helper = helper_c5 if locale else helper_c4
        embedded_extension = assemble(
            ROOT / "third_party" / "juku-common" / "transport" /
            "fastboot-extension.asm",
            temporary / "embedded-extension.cim",
            (ROOT / "third_party" / "juku-common" / "transport",),
            (
                "FASTBOOT_8N1", "FASTBOOT_ZX0", "FASTBOOT_STREAM",
                "FASTBOOT_STREAM_ACK", "FASTBOOT_CPM3",
                "FASTBOOT_CPM3_ROM", "FASTBOOT_BOOT_RECORD",
                "FASTBOOT_V16",
            ),
        ) if extended else b""
        if extended and len(embedded_extension) != EMBEDDED_EXTENSION_BYTES:
            raise ValueError(
                "V16 embedded extension is "
                f"{len(embedded_extension)} bytes; expected "
                f"{EMBEDDED_EXTENSION_BYTES}"
            )
        core_defines = (
            "FASTBOOT_8N1", "FASTBOOT_ZX0", "FASTBOOT_STREAM",
            "FASTBOOT_EXACT", "FASTBOOT_EXT_ACK", "FASTBOOT_PROBE_SYNC",
        ) + (("FASTBOOT_V16", "FASTBOOT_ROM_EXTENSION") if extended else
             ("FASTBOOT_V15",))
        core = assemble(
            ROOT / "third_party" / "juku-common" / "transport" /
            "fastboot-core.asm",
            temporary / "core.cim",
            (ROOT / "third_party" / "juku-common" / "transport",),
            core_defines,
        )
        if len(core) > 128:
            raise ValueError(
                f"fastboot core is {len(core)} bytes; envelope is 128"
            )
        core = bytearray(core.ljust(128, b"\0"))
        expected_core_magic = b"JF16" if extended else b"JF15"
        if core[3:7] != expected_core_magic or core[8] != 0:
            raise ValueError("fastboot core metadata layout changed")
        core[9:11] = (
            0 if extended else extension_bytes
        ).to_bytes(2, "little")
        length_sentinel = bytes.fromhex("01 5A A5")
        if not extended:
            if core.count(length_sentinel) != 1:
                raise ValueError("V15 core extension-length sentinel changed")
            length_offset = core.index(length_sentinel) + 1
            core[length_offset:length_offset + 2] = \
                extension_bytes.to_bytes(2, "little")

        # The automatic ROM has no operator event for host synchronization.
        # Redirect only the first find_first RX call to a one-shot prelude at
        # 0180h. It sends C4h, self-patches that call back to the canonical
        # RX routine at 0173h, then tail-jumps there. The extension retains its
        # fixed rx=0173h contract and later parser retries emit no extra C4h.
        if not extended:
            first_rx = bytes.fromhex("CD 73 01 FE A5")
            if core.count(first_rx) != 1:
                raise ValueError("V15 core first-RX signature changed")
            first_rx_offset = core.index(first_rx)
            core[first_rx_offset + 1:first_rx_offset + 3] = \
                bytes.fromhex("80 01")
            call_operand = 0x0100 + first_rx_offset + 1
            prelude = bytes((
                0x3E, 0xC4,               # MVI A,C4h
                0xD3, 0x08,               # OUT USARTDATA
                0x21, 0x73, 0x01,         # LXI H,0173h
                0x22, call_operand & 0xFF, call_operand >> 8,
                0xC3, 0x73, 0x01,         # JMP 0173h
            ))
            core.extend(prelude)
        if len(core) > GATE_STORED - CORE_STORED:
            raise ValueError(f"automatic fastboot core is {len(core)} bytes")
        core = bytes(core)
        if len(gate) > 0xE0:
            raise ValueError(f"RAM gate is {len(gate)} bytes; envelope is 224")
        expected_gate_bytes = 214 if locale else 196
        if len(gate) != expected_gate_bytes:
            raise ValueError(
                f"RAM gate is {len(gate)} bytes, expected {expected_gate_bytes}"
            )
        if len(helper_c4) > 0x80 or len(helper_c5) > 0x80:
            raise ValueError(f"RAM helper is {len(helper)} bytes; envelope is 128")

        generated = HERE / "network-rom-generated.inc"
        expected_generated = (
            "; Generated/verified by build_network_rom.py.\n"
            ".ifdef ROM_ABI_LOCALE\n"
            "JROMGATEBYTES equ 214\n"
            ".else\n"
            "JROMGATEBYTES equ 196\n"
            ".endif\n"
            ".ifdef ROM_ABI_LOCALE\n"
            f"JROMHELPERBYTES equ {len(helper_c5)}\n"
            ".else\n"
            f"JROMHELPERBYTES equ {len(helper_c4)}\n"
            ".endif\n"
            ".ifdef ROM_ABI_EXTENDED\n"
            f"JROMCOREBYTES equ {len(core) if extended else 128}\n"
            f"JROMEMBEDEXTBYTES equ {EMBEDDED_EXTENSION_BYTES}\n"
            ".else\n"
            "JROMCOREBYTES equ 141\n"
            ".endif\n"
            ".ifdef ROM_ABI_LOCALE\n"
            f"JROMEXTENSIONBYTES equ {LOCALE_EXTENSION_BYTES}\n"
            ".else\n"
            f"JROMEXTENSIONBYTES equ {EXTENSION_BYTES}\n"
            ".endif\n"
            f"CORESTORED equ 0{CORE_STORED:04x}h\n"
            f"EMBEDSTORED equ 0{EMBEDDED_EXTENSION_STORED:04x}h\n"
            f"GATESTORED equ 0{GATE_STORED:04x}h\n"
            f"HELPSTORED equ 0{HELP_STORED:04x}h\n"
        )
        if generated.read_text() != expected_generated:
            raise ValueError("network-rom-generated.inc is stale")
        includes = (
            HERE, COMMON,
            ROOT / "third_party" / "juku-common" / "diag",
            ROOT / "third_party" / "juku-common" / "music",
        )
        boot = assemble(
            HERE / "boot.asm", temporary / "boot.cim", includes,
            selftest_defines,
        )
        resident = assemble(
            HERE / "resident.asm", temporary / "resident.cim", includes,
            selftest_defines,
        )
        if len(boot) > GATE_STORED:
            raise ValueError(f"boot code overlaps stored gate: {len(boot)} bytes")
        if len(resident) != RESIDENT_SIZE:
            raise ValueError(
                f"resident image is {len(resident)} bytes, expected {RESIDENT_SIZE}"
            )

        lower = bytearray(b"\xFF" * LOWER_SIZE)
        lower[:len(boot)] = boot
        if extended:
            extension_end = EMBEDDED_EXTENSION_STORED + len(embedded_extension)
            if len(boot) > EMBEDDED_EXTENSION_STORED or \
                    extension_end > CORE_STORED:
                raise ValueError("embedded V16 extension overlaps lower ROM")
            lower[EMBEDDED_EXTENSION_STORED:extension_end] = embedded_extension
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
        "fastboot_extension_bytes": 0 if extended else extension_bytes,
        "embedded_fastboot_extension_bytes": len(embedded_extension),
        "embedded_fastboot_extension_sha256": (
            digest(embedded_extension) if embedded_extension else None
        ),
        "embedded_fastboot_extension_file_offset": (
            f"{EMBEDDED_EXTENSION_STORED:04X}" if embedded_extension else None
        ),
        "fastboot_protocol": 16 if extended else 15,
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
        "target_ready_byte": "C7" if extended else "C4",
        "resident_bytes": len(resident),
        "resident_services": [
            "console", "serial", "keyboard", "netdisk-v3", "diagnostics",
        ] + ([
            "bounded-console-span", "netdisk-multi", "raw-keyboard",
            "sound",
        ] if extended else []),
        "console": {
            "geometry": "80x24",
            "font": "Creep-0.31-adapted-5x7",
            "cursor_period_polls": 512,
        },
        "abi": {
            "base": "FF00", "major": 1,
            "minor": 2 if extended else (1 if locale else 0),
        },
        "abi_vectors": {
            "init": "FF20",
            "console_init": "FF23",
            "console_status": "FF26",
            "console_input": "FF29",
            "console_output": "FF2C",
            "serial_init": "FF2F",
            "serial_receive": "FF32",
            "serial_transmit": "FF35",
            "netdisk_single": "FF38",
            "keyboard_init": "FF3B",
            "keyboard_scan": "FF3E",
            "sound": "FF41",
            "diagnostics": "FF44",
            "get_info": "FF47",
        },
        "candidate": (
            (SUCCESSOR_CANDIDATE if successor else EXTENDED_CANDIDATE)
            if extended else
            (LOCALE_CANDIDATE if locale else CANDIDATE)
        ),
        "status": (
            ("modified-raw simulator successor; C6 remains immutable"
             if successor else
             "simulator candidate; C5 remains the physical baseline")
            if extended else (
                "desk-qualified locale candidate; physical qualification pending"
                if locale else
                "CS00015 bench candidate; physical qualification pending"
            )
        ),
    }
    if locale:
        metadata["abi_vectors"].update({
            "configuration": "FF4A",
            "keyboard_remap": "FF4D",
            "boot_policy": "FF50",
        })
        metadata["console"]["geometry"] = "S21-bits-2:1"
        metadata["console"]["modes"] = {
            "00": "40x24", "01": "53x24",
            "10": "64x20", "11": "80x24",
        }
        metadata["console"]["locale"] = {
            "s21_bits": "4:3", "banks": ["english", "estonian", "cp866"],
            "cp437_ui": "B0-DF",
        }
        metadata["key_remap_pairs"] = 4
        metadata["netdisk_cache"] = {
            "records_per_drive": 8,
            "drives": 2,
            "shared_pointer_fallback": "alias-safe",
        }
        metadata["boot_policy"] = {
            "s21_bit": 0,
            "set": "automatic network boot",
            "clear": "wait for local N",
        }
        metadata["boot_status_record"] = {
            "base": "D610",
            "post": "D610",
            "stage": "D611",
            "crc_retries": "D612",
            "protocol": "D613",
            "stages": {
                "10": "POST active",
                "20": (
                    "V16 core entered; ROM-resident loader active"
                    if extended else
                    "V15 core entered; extension pending"
                ),
                "30": "extension active; system header pending",
                "31": "system header accepted; payload pending",
                "E2": "compressed payload CRC failed; retrying",
                "32": "compressed payload authenticated; decompressing",
                "40": "CP/M system entered",
                "50": "first NetDisk transaction succeeded",
            },
        }
    if extended:
        metadata["fastboot_wire_contract"] = (
            "JF16 core descriptor plus JZ/length/compressed/CRC stream; "
            "no executable extension"
        )
        metadata["abi_vectors"].update({
            "console_block": "FF53",
            "netdisk_multi": "FF56",
            "keyboard_raw": "FF59",
        })
        metadata["feature_bits"] = {
            "value": "0FBF",
            "console_block": "0200",
            "netdisk_multi": "0400",
            "keyboard_raw": "0800",
        }
        metadata["netdisk_multi"] = {
            "maximum_descriptors": 8,
            "descriptor_bytes": 10,
            "write_policy": "synchronous-write-through",
        }
    return image, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    image, metadata = build()
    locale_image, locale_metadata = build(locale=True)
    extended_image, extended_metadata = build(extended=True)
    successor_image, successor_metadata = build(successor=True)
    expected = (
        (OUTPUT, image),
        (D15_OUTPUT, image[:0x2000]),
        (D16_OUTPUT, image[0x2000:]),
        (METADATA_OUTPUT,
         (json.dumps(metadata, indent=2) + "\n").encode()),
        (LOCALE_OUTPUT, locale_image),
        (LOCALE_D15_OUTPUT, locale_image[:0x2000]),
        (LOCALE_D16_OUTPUT, locale_image[0x2000:]),
        (LOCALE_METADATA_OUTPUT,
         (json.dumps(locale_metadata, indent=2) + "\n").encode()),
        (EXTENDED_OUTPUT, extended_image),
        (EXTENDED_D15_OUTPUT, extended_image[:0x2000]),
        (EXTENDED_D16_OUTPUT, extended_image[0x2000:]),
        (EXTENDED_METADATA_OUTPUT,
         (json.dumps(extended_metadata, indent=2) + "\n").encode()),
        (SUCCESSOR_OUTPUT, successor_image),
        (SUCCESSOR_D15_OUTPUT, successor_image[:0x2000]),
        (SUCCESSOR_D16_OUTPUT, successor_image[0x2000:]),
        (SUCCESSOR_METADATA_OUTPUT,
         (json.dumps(successor_metadata, indent=2) + "\n").encode()),
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
