#!/usr/bin/env python3
"""Inspect the Monitor 3.3 BASIC low-stub copy boundary."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "basic-low-stub-inspection.md"
JBASIC = ROOT / "roms" / "jbasic11.bin"
JMON33 = ROOT / "roms" / "jmon33.bin"
BAS_PARTS = [ROOT / "ref" / "firmware" / f"BAS{idx}.HEX" for idx in range(4)]
DISASM = ROOT / "cosim" / "dis8080.py"

# Pinned by sync/basic_launch_probe.py / docs/basic-launch-probe.md.
LOW_RAM_PATCH = {
    0x0101: 0xFE,
    0x0102: 0xFF,
    0x0111: 0xFE,
    0x0112: 0xFF,
    0x0121: 0xFE,
    0x0122: 0xFF,
    0x0129: 0x00,
    0x012A: 0x22,
    0x0133: 0xCC,
    0x0134: 0xFF,
    0x013F: 0x00,
    0x0140: 0x00,
    0x0141: 0x56,
    0x0142: 0x6F,
}


def load_disassembler():
    spec = importlib.util.spec_from_file_location("dis8080", DISASM)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {DISASM}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def decode_hex_bytes(path: Path) -> bytes:
    text = path.read_text(errors="replace")
    hex_digits = "".join(ch for ch in text if ch in "0123456789abcdefABCDEF")
    return bytes.fromhex(hex_digits)


def sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def disassemble(module, data: bytes, start: int, end: int, base: int = 0) -> list[str]:
    lines: list[str] = []
    pc = start
    while pc < end:
        text, size = module.decode(data, pc, base)
        off = pc - base
        raw = " ".join(f"{data[off + idx]:02X}" for idx in range(size) if off + idx < len(data))
        lines.append(f"{pc:04X}: {raw:<9} {text}")
        pc += size
    return lines


def word(data: bytes, addr: int) -> int:
    return data[addr] | (data[addr + 1] << 8)


def main() -> int:
    dis8080 = load_disassembler()
    cart = JBASIC.read_bytes()
    jmon33 = JMON33.read_bytes()
    legacy = b"".join(decode_hex_bytes(path) for path in BAS_PARTS)
    loaded = bytearray(cart)
    for addr, value in LOW_RAM_PATCH.items():
        loaded[addr] = value
    loaded_bytes = bytes(loaded)

    changed = [(addr, cart[addr], loaded[addr]) for addr in sorted(LOW_RAM_PATCH)]
    grouped = [
        ("0101..0102", f"`LXI SP` operand changes `0x{word(cart, 0x0101):04X}` -> `0x{word(loaded_bytes, 0x0101):04X}`"),
        ("0111..0112", f"low control bytes change `0x{word(cart, 0x0111):04X}` -> `0x{word(loaded_bytes, 0x0111):04X}`"),
        ("0121..0122", f"low control bytes change `0x{word(cart, 0x0121):04X}` -> `0x{word(loaded_bytes, 0x0121):04X}`"),
        ("0129..012A", f"workspace/vector word changes `0x{word(cart, 0x0129):04X}` -> `0x{word(loaded_bytes, 0x0129):04X}`"),
        ("0133..0134", f"workspace/control word changes `0x{word(cart, 0x0133):04X}` -> `0x{word(loaded_bytes, 0x0133):04X}`"),
        ("013F..0142", "four-byte low workspace/control block changes before the shared body at `0x0151`"),
    ]

    lines = [
        "# BASIC low-stub inspection",
        "",
        "Status: **LOW STUB PATCHED / BODY MATCHES**",
        "",
        "This generated report interprets the 14-byte `0x0100..0x01FF`",
        "cartridge-vs-RAM mismatch pinned by `docs/basic-launch-probe.md`.",
        "The `0x0200..0x1FFF` BASIC body is byte-identical after Monitor 3.3",
        "loads the cartridge; the unresolved boundary is the post-`0x0100`",
        "handoff through this low entry/workspace area, not the cartridge",
        "window or bulk copy.",
        "",
        "## Inputs",
        "",
        "| Item | Value |",
        "| --- | --- |",
        f"| `roms/jbasic11.bin` SHA1 | `{sha1(cart)}` |",
        f"| `roms/jmon33.bin` SHA1 | `{sha1(jmon33)}` |",
        f"| legacy `BAS0-3.HEX` SHA1 | `{sha1(legacy)}` |",
        f"| images identical | `{'YES' if legacy == cart else 'NO'}` |",
        f"| first `0x0200` bytes identical | `{'YES' if legacy[:0x0200] == cart[:0x0200] else 'NO'}` |",
        f"| low mismatches | `{len(changed)}` |",
        "| body mismatches from `0x0200` | `0` |",
        "",
        "## Mismatch Bytes",
        "",
        "| Address | Cartridge | Loaded RAM |",
        "| --- | ---: | ---: |",
    ]
    lines.extend(f"| `0x{addr:04X}` | `0x{cart_byte:02X}` | `0x{ram_byte:02X}` |" for addr, cart_byte, ram_byte in changed)
    lines.extend(
        [
            "",
            "## Grouped Interpretation",
            "",
            "| Range | Interpretation |",
            "| --- | --- |",
        ]
    )
    lines.extend(f"| `{addr_range}` | {text} |" for addr_range, text in grouped)
    lines.extend(
        [
            "",
            "The only unambiguous executable entry change is the stack pointer at",
            "`0x0100`: the loaded image starts with `LXI SP,0xFFFE` instead of the",
            "cartridge's `LXI SP,0xD700`. The remaining changes sit in the BASIC",
            "low control/workspace region. A linear disassembly is useful for",
            "orientation, but should not be treated as proof that every byte below",
            "`0x0151` is executable code.",
            "",
            "## Monitor 3.3 Handoff",
            "",
            "In memory modes 1 and 2, Monitor 3.3's high-ROM window maps CPU",
            "addresses `0xD800..0xFFFF` to `roms/jmon33.bin` offsets",
            "`0x1800..0x3FFF`; equivalently, disassemble the ROM with file byte",
            "0 mapped at CPU address `0xC000` for high-window snippets.",
            "",
            "The source-aware launch probe now shows the first cartridge reads from",
            "high ROM at `0xEF4D` / `0xFF09`, followed by reads from RAM-resident",
            "copy code at `0xD763`. The eventual execution in `0x4000..0xBFFF`",
            "happens in mode 1 from RAM, not in mode 2 from the cartridge overlay,",
            "and the sampled opcodes there are `0x00`.",
            "",
            "Header check around the first sampled high-ROM cartridge read:",
            "",
            "```text",
            *disassemble(dis8080, jmon33, 0xEF4A, 0xEF5C, 0xC000),
            "```",
            "",
            "Launch/copy setup around the second sampled high-ROM cartridge read:",
            "",
            "```text",
            *disassemble(dis8080, jmon33, 0xFF01, 0xFF1C, 0xC000),
            "```",
            "",
            "Shared high-ROM copy trampoline reached with `A=0x12`, `BC=0x4000`,",
            "and `DE=0x0100` from the launch setup:",
            "",
            "```text",
            *disassemble(dis8080, jmon33, 0xEE43, 0xEE85, 0xC000),
            "```",
            "",
            "This proves that the monitor deliberately validates the cartridge header,",
            "copies from the `0x4000` cartridge window into low RAM starting at",
            "`0x0100`, then jumps to `0x0100`. The still-wrong later execution from",
            "zero-filled RAM at `0x4000` is therefore after this intentional handoff.",
            "",
            "## Linear Disassembly: Cartridge",
            "",
            "```text",
            *disassemble(dis8080, cart, 0x0100, 0x0151),
            "```",
            "",
            "## Linear Disassembly: Loaded RAM Shape",
            "",
            "```text",
            *disassemble(dis8080, loaded_bytes, 0x0100, 0x0151),
            "```",
            "",
            "## Boundary",
            "",
            "- The loaded low stub is not random corruption: changes are sparse,",
            "  repeat for both public BASIC media shapes, and leave the body exact.",
            "- The next cartridge-BASIC step is to identify what monitor routine patches",
            "  or synthesizes these low bytes, then confirm the intended launch PC/mode.",
            "- Disk-side EKDOS `JBASIC.COM` is already proven separately to visible",
            "  `READY`; this report only narrows the unresolved Monitor 3.3 cartridge",
            "  path.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines))
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
