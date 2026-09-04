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
C8_OUTPUT = HERE / "juku-network-rom-abi1.3-c8.bin"
C8_D15_OUTPUT = HERE / "juku-network-rom-abi1.3-c8-d15.bin"
C8_D16_OUTPUT = HERE / "juku-network-rom-abi1.3-c8-d16.bin"
C8_METADATA_OUTPUT = HERE / "juku-network-rom-abi1.3-c8.json"
C9_OUTPUT = HERE / "juku-network-rom-abi1.4-c9.bin"
C9_D15_OUTPUT = HERE / "juku-network-rom-abi1.4-c9-d15.bin"
C9_D16_OUTPUT = HERE / "juku-network-rom-abi1.4-c9-d16.bin"
C9_METADATA_OUTPUT = HERE / "juku-network-rom-abi1.4-c9.json"
C10_OUTPUT = HERE / "juku-network-rom-abi1.4-c10.bin"
C10_D15_OUTPUT = HERE / "juku-network-rom-abi1.4-c10-d15.bin"
C10_D16_OUTPUT = HERE / "juku-network-rom-abi1.4-c10-d16.bin"
C10_METADATA_OUTPUT = HERE / "juku-network-rom-abi1.4-c10.json"
C11_OUTPUT = HERE / "juku-network-rom-abi1.4-c11.bin"
C11_D15_OUTPUT = HERE / "juku-network-rom-abi1.4-c11-d15.bin"
C11_D16_OUTPUT = HERE / "juku-network-rom-abi1.4-c11-d16.bin"
C11_METADATA_OUTPUT = HERE / "juku-network-rom-abi1.4-c11.json"
C12_OUTPUT = HERE / "juku-network-rom-abi1.5-c12.bin"
C12_D15_OUTPUT = HERE / "juku-network-rom-abi1.5-c12-d15.bin"
C12_D16_OUTPUT = HERE / "juku-network-rom-abi1.5-c12-d16.bin"
C12_METADATA_OUTPUT = HERE / "juku-network-rom-abi1.5-c12.json"

LOWER_SIZE = 0x1800
RESIDENT_SIZE = 0x2800
GATE_STORED = 0x1000
HELP_STORED = 0x1400
CHECKER_STORED = 0x1500
CORE_STORED = 0x0F00
EMBEDDED_EXTENSION_STORED = 0x0600
EMBEDDED_EXTENSION_BYTES = 361
C11_EMBEDDED_EXTENSION_BYTES = 456
EXTENSION_BYTES = 267
LOCALE_EXTENSION_BYTES = 307
CANDIDATE = "network-first-abi1-cs00015-c4"
LOCALE_CANDIDATE = "network-first-abi1.1-cs00015-c5-desk"
EXTENDED_CANDIDATE = "network-first-abi1.2-c6-simulator"
SUCCESSOR_CANDIDATE = "network-first-abi1.2-c7-modified-raw-simulator"
C8_CANDIDATE = "network-first-abi1.3-c8-resident-host-simulator"
C9_CANDIDATE = "network-first-abi1.4-c9-bounded-host-simulator"
C10_CANDIDATE = "network-first-abi1.4-c10-pof-release-candidate"
C11_CANDIDATE = "network-first-abi1.4-c11-post-raster-candidate"
C12_CANDIDATE = "network-first-abi1.5-c12-runtime-console-candidate"


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
          successor: bool = False,
          c8: bool = False,
          c9: bool = False,
          c10: bool = False,
          c11: bool = False,
          c12: bool = False,
          host_selftest: bool = False,
          selftest_locale: int = 1,
          runtime_console_target: tuple[int, int] | None = None,
          ) -> tuple[bytes, dict[str, object]]:
    if c12:
        c11 = True
    if c11:
        c10 = True
    if c10:
        c9 = True
    if c9:
        c8 = True
    if c8:
        successor = True
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
    if host_selftest and (not abi_selftest or not c9):
        raise ValueError("host transport fixture requires C9 ABI selftest")
    if selftest_locale not in range(4):
        raise ValueError("selftest locale must be 0..3")
    if selftest_locale != 1 and (not abi_selftest or not locale):
        raise ValueError("non-default locale requires localized ABI selftest")
    if runtime_console_target is not None:
        if not abi_selftest or not c12:
            raise ValueError("runtime console fixture requires C12 ABI selftest")
        if len(runtime_console_target) != 2 or any(
                value not in range(4) for value in runtime_console_target):
            raise ValueError("runtime console target must be (mode, bank) 0..3")
    selftest_defines = ("ROM_ABI_LOCALE",) if locale else ()
    if locale and not successor:
        selftest_defines += ("CREEP_LEGACY_PSEUDO",)
    if extended:
        selftest_defines += ("ROM_ABI_EXTENDED",)
        selftest_defines += (
            ("ROM_ABI_RAW_FIXED",) if successor else
            ("ROM_ABI_RAW_MODIFIER_FIRST",)
        )
    if c8:
        selftest_defines += ("ROM_ABI_HOSTSERVICES",)
    if c9:
        selftest_defines += ("ROM_ABI_C9",)
    if c10:
        selftest_defines += ("ROM_ABI_C10",)
    if c11:
        selftest_defines += ("ROM_ABI_C11",)
    if c12:
        selftest_defines += ("ROM_ABI_C12",)
    if runtime_console_target is not None:
        target_mode, target_bank = runtime_console_target
        selftest_defines += (
            "ABI_C12_KEEP_OVERRIDE",
            f"ABI_C12_MODE_{target_mode}",
            f"ABI_C12_BANK_{target_bank}",
        )
    if host_selftest:
        selftest_defines += ("ABI_HOST_SELFTEST",)
    selftest_defines += ((
        "ABI_LOCALE_ENGLISH", "ABI_LOCALE_ESTONIAN",
        "ABI_LOCALE_RUSSIAN", "ABI_LOCALE_USER",
    )[selftest_locale],) if abi_selftest and locale else ()
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
        helper_c11 = assemble(
            HERE / "ram-helper.asm", temporary / "helper-c11.cim", (COMMON,),
            ("ROM_ABI_LOCALE", "ROM_ABI_C10", "ROM_ABI_C11"),
        )
        helper = helper_c11 if c11 else (helper_c5 if locale else helper_c4)
        checker = assemble(
            HERE / "checker-helper.asm", temporary / "checker.cim", (),
        )
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
            ) + (("FASTBOOT_CPM3_C8",) if c8 else ()) +
            (("FASTBOOT_C12_DISCOVERY",) if c12 else
             (("FASTBOOT_C11_DISCOVERY",) if c11 else ())),
        ) if extended else b""
        expected_embedded_extension_bytes = (
            C11_EMBEDDED_EXTENSION_BYTES if c11 else
            EMBEDDED_EXTENSION_BYTES
        )
        if extended and len(embedded_extension) != \
                expected_embedded_extension_bytes:
            raise ValueError(
                "V16 embedded extension is "
                f"{len(embedded_extension)} bytes; expected "
                f"{expected_embedded_extension_bytes}"
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
        expected_gate_bytes = (
            224 if c12 else (219 if c8 else (214 if locale else 196))
        )
        if len(gate) != expected_gate_bytes:
            raise ValueError(
                f"RAM gate is {len(gate)} bytes, expected {expected_gate_bytes}"
            )
        if len(helper_c4) > 0x80 or len(helper_c5) > 0x80 or \
                len(helper_c11) > 0x80:
            raise ValueError(f"RAM helper is {len(helper)} bytes; envelope is 128")
        if len(checker) > 0x80:
            raise ValueError(
                f"POST checker helper is {len(checker)} bytes; envelope is 128"
            )

        generated = HERE / "network-rom-generated.inc"
        expected_generated = (
            "; Generated/verified by build_network_rom.py.\n"
            ".ifdef ROM_ABI_C12\n"
            "JROMGATEBYTES equ 224\n"
            ".else\n"
            ".ifdef ROM_ABI_HOSTSERVICES\n"
            "JROMGATEBYTES equ 219\n"
            ".else\n"
            ".ifdef ROM_ABI_LOCALE\n"
            "JROMGATEBYTES equ 214\n"
            ".else\n"
            "JROMGATEBYTES equ 196\n"
            ".endif\n"
            ".endif\n"
            ".endif\n"
            ".ifdef ROM_ABI_LOCALE\n"
            f"JROMHELPERBYTES equ {len(helper_c5)}\n"
            ".else\n"
            f"JROMHELPERBYTES equ {len(helper_c4)}\n"
            ".endif\n"
            f"JROMCHECKERBYTES equ {len(checker)}\n"
            ".ifdef ROM_ABI_EXTENDED\n"
            f"JROMCOREBYTES equ {len(core) if extended else 128}\n"
            ".ifdef ROM_ABI_C11\n"
            f"JROMEMBEDEXTBYTES equ {C11_EMBEDDED_EXTENSION_BYTES}\n"
            ".else\n"
            f"JROMEMBEDEXTBYTES equ {EMBEDDED_EXTENSION_BYTES}\n"
            ".endif\n"
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
            f"CHECKERSTORED equ 0{CHECKER_STORED:04x}h\n"
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

        if c8:
            resident = bytearray(resident)
            checksum_offset = 0xFF1F - 0xD800
            resident[checksum_offset] = (-sum(resident)) & 0xFF
            if sum(resident) & 0xFF:
                raise ValueError("C8 resident-ROM checksum balance failed")
            resident = bytes(resident)

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
        if c11:
            checker_end = CHECKER_STORED + len(checker)
            if checker_end > LOWER_SIZE:
                raise ValueError("C11 POST checker helper overlaps resident ROM")
            lower[CHECKER_STORED:checker_end] = checker
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
            ("ppi0-82-checker-pc7-high-then-low" if c11 else
             ("ppi0-82-pc7-high-then-low" if c10 else
              "ppi0-82-pc7-high")),
            "ppi1-9b", "stock-raster-refresh",
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
            *(["resident-host", "full-diagnostics"] if c8 else []),
            *(["runtime-console"] if c12 else []),
        ] if extended else []),
        "console": {
            "geometry": "80x24",
            "font": "Creep-0.31-adapted-5x7",
            "cursor_period_polls": 512,
        },
        "abi": {
            "base": "FF00", "major": 1,
            "minor": (5 if c12 else
                      (4 if c9 else
                      (3 if c8 else
                       (2 if extended else (1 if locale else 0))))),
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
            (C12_CANDIDATE if c12 else
             (C11_CANDIDATE if c11 else
             (C10_CANDIDATE if c10 else
             (C9_CANDIDATE if c9 else
             (C8_CANDIDATE if c8 else
             (SUCCESSOR_CANDIDATE if successor else EXTENDED_CANDIDATE)))
            )))
            if extended else
            (LOCALE_CANDIDATE if locale else CANDIDATE)
        ),
        "status": (
            (("runtime-console ABI simulator candidate; C11 remains immutable"
              if c12 else
              ("deterministic POST/raster/recovery simulator candidate; "
              "C10 remains immutable"
              if c11 else
              ("desk-qualified POF-release successor; physical acceptance "
              "pending"
              if c10 else
              ("bounded-host simulator/HDL candidate; physical programming "
              "not authorized; C8 remains immutable"
              if c9 else
              "resident-host simulator successor; C7 remains immutable"))))
             if c8 else
             ("modified-raw simulator successor; C6 remains immutable"
              if successor else
              "simulator candidate; C5 remains the physical baseline"))
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
    if c8:
        metadata["abi_vectors"]["host_services"] = "FF5C"
        metadata["feature_bits"]["value"] = "0FFF"
        metadata["feature_bits"]["resident_host"] = "0040"
        metadata["post_audio"] = {
            "C1": "short-short-long",
            "C2": "short-long-short",
            "C3": "short-long-long",
            "C4": "long-short-short",
            "C5": "long-short-long",
            "success_and_host_wait": "silent",
        }
        metadata["resident_checksum"] = "additive-8 over D800h..FFFFh = 00"
    if c9:
        metadata["boot_policy"] = {
            "s21_bit": 0,
            "behavior": "reserved; unconditional network boot",
        }
        metadata["resident_host"] = {
            "state_bytes": 4,
            "state_prefix_abi_1_3_bytes": 2,
            "failure_reasons": {
                "00": "none", "01": "transmitter-timeout",
                "02": "receive-timeout", "03": "sync-budget",
                "04": "sequence", "05": "reply-integrity",
                "06": "host-status",
            },
            "flags": {
                "01": "host-detected", "02": "n4-selected",
                "04": "console-capability", "08": "mirroring-enabled",
                "10": "reconnected",
            },
            "transaction_deadline": {
                "transmitter_ready_polls_per_byte": 8192,
                "receiver_ready_polls_per_byte": 65535,
                "reply_prefix_scan_bytes": 256,
                "failure_backoff_console_polls": 1,
            },
        }
    if c10:
        metadata["video_enable"] = {
            "ppi0_port_c_bit": 7,
            "signal": "POF",
            "post_state": "high-picture-suppressed",
            "runtime_state": "low-picture-enabled",
            "successful_runtime_port_c": "01",
            "ordered_control_writes": ["82", "0F", "0E"],
            "physical_evidence": (
                "CS00000 C9 live 0E write restored local video 2026-08-27"
            ),
        }
    if c11:
        metadata["checker_helper_bytes"] = len(checker)
        metadata["video_enable"].update({
            "release_after": "deterministic-320x241-checkerboard",
            "checkerboard": "8x8-full-raster",
        })
        metadata["console"]["physical_raster_clear_bytes"] = {
            "00": 9640, "01": 9640, "10": 9648, "11": 9600,
            "implementation_envelope": 9648,
        }
        metadata["boot_discovery"] = {
            "framing": "19200-8O1",
            "frame": (
                "4A 42 0C 01 05" if c12 else "4A 42 0B 01 02"
            ),
            "copies_per_interval": 2,
            "idle_interval": "approximately 1 second at 1.7 MHz",
            "fastboot_framing": "19200-8N1",
            "scope": "idle JZ scanner only; payload receive remains blocking",
        }
    if c12:
        metadata["abi"]["minor"] = 5
        metadata["abi_vectors"]["console_config"] = "FF5F"
        metadata["feature_bits"]["value"] = "1FFF"
        metadata["feature_bits"]["console_config"] = "1000"
        metadata["runtime_console"] = {
            "selectors": {"query": 0, "set": 1, "default": 2},
            "video_modes": ["40x24", "53x24", "64x20", "80x24"],
            "character_banks": [
                "english", "estonian", "cp866", "english/user-remap",
            ],
            "override_flags": {"video": "01", "character_bank": "02"},
            "transition": "cursor-hide, timing/font switch, full clear, state publish",
            "warm_boot": "preserve override",
            "reset": "restore latched S21 default",
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
    c8_image, c8_metadata = build(c8=True)
    c9_image, c9_metadata = build(c9=True)
    c10_image, c10_metadata = build(c10=True)
    c11_image, c11_metadata = build(c11=True)
    c12_image, c12_metadata = build(c12=True)
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
        (C8_OUTPUT, c8_image),
        (C8_D15_OUTPUT, c8_image[:0x2000]),
        (C8_D16_OUTPUT, c8_image[0x2000:]),
        (C8_METADATA_OUTPUT,
         (json.dumps(c8_metadata, indent=2) + "\n").encode()),
        (C9_OUTPUT, c9_image),
        (C9_D15_OUTPUT, c9_image[:0x2000]),
        (C9_D16_OUTPUT, c9_image[0x2000:]),
        (C9_METADATA_OUTPUT,
         (json.dumps(c9_metadata, indent=2) + "\n").encode()),
        (C10_OUTPUT, c10_image),
        (C10_D15_OUTPUT, c10_image[:0x2000]),
        (C10_D16_OUTPUT, c10_image[0x2000:]),
        (C10_METADATA_OUTPUT,
         (json.dumps(c10_metadata, indent=2) + "\n").encode()),
        (C11_OUTPUT, c11_image),
        (C11_D15_OUTPUT, c11_image[:0x2000]),
        (C11_D16_OUTPUT, c11_image[0x2000:]),
        (C11_METADATA_OUTPUT,
         (json.dumps(c11_metadata, indent=2) + "\n").encode()),
        (C12_OUTPUT, c12_image),
        (C12_D15_OUTPUT, c12_image[:0x2000]),
        (C12_D16_OUTPUT, c12_image[0x2000:]),
        (C12_METADATA_OUTPUT,
         (json.dumps(c12_metadata, indent=2) + "\n").encode()),
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
