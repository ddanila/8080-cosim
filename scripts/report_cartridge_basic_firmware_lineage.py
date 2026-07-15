#!/usr/bin/env python3
"""Pin the byte lineage between the cartridge and onboard Monitor BASIC."""
from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "cartridge-basic-firmware-lineage.md"
CART = ROOT / "roms" / "jbasic11.bin"
MONITORS = (
    ("Monitor 2.2", ROOT / "roms" / "jmon22.bin"),
    ("Monitor 3.3", ROOT / "roms" / "jmon33.bin"),
)

CART_BODY_START = 0x0100
CART_BODY_END = 0x1D38
MONITOR_BODY_START = 0x03C8
MONITOR_BODY_END = 0x2000
DELTA = MONITOR_BODY_START - CART_BODY_START


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checksum_rows(data: bytes) -> list[tuple[int, int, int, int, bool]]:
    rows = []
    for block in range(8):
        start = 4 if block == 0 else block * 0x800
        end = (block + 1) * 0x800
        computed = sum(data[start:end]) & 0xFF
        stored = data[3 + block]
        rows.append((block, start, end - 1, stored, computed == stored))
    return rows


def main() -> int:
    cart = CART.read_bytes()
    if len(cart) != 0x2000:
        raise SystemExit(f"expected 8192-byte cartridge, got {len(cart)}")

    cart_body = cart[CART_BODY_START:CART_BODY_END]
    monitor_results = []
    for label, path in MONITORS:
        data = path.read_bytes()
        if len(data) != 0x4000:
            raise SystemExit(f"expected 16384-byte {path.name}, got {len(data)}")
        body = data[MONITOR_BODY_START:MONITOR_BODY_END]
        mismatches = [
            (offset, left, right)
            for offset, (left, right) in enumerate(zip(cart_body, body, strict=True))
            if left != right
        ]
        monitor_results.append((label, path, data, body, mismatches, checksum_rows(data)))

    zero_gap = cart[CART_BODY_END:0x1F00]
    bootstrap = cart[0x1F00:0x2000]
    loop_tail = bytes.fromhex("7e 12 23 13 0b 78 b1 c2 09 20 c3 00 01")
    loop_offset = bootstrap.find(loop_tail)

    lines = [
        "# Cartridge BASIC firmware-lineage audit",
        "",
        "Status: **ONBOARD BASIC LINEAGE PINNED / MISSING PAGE NOT DERIVED**",
        "",
        "This generated audit tests whether the Monitor ROMs contain source evidence",
        "for the unresolved `jbasic11.bin` cartridge tail. It establishes a strong",
        "lineage match, but deliberately does not export a reconstructed cartridge:",
        "the exact match ends before the missing page.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_cartridge_basic_firmware_lineage.py",
        "```",
        "",
        "## Exact body mapping",
        "",
        f"Cartridge offsets `0x{CART_BODY_START:04X}..0x{CART_BODY_END - 1:04X}` map to",
        f"Monitor-ROM offsets `0x{MONITOR_BODY_START:04X}..0x{MONITOR_BODY_END - 1:04X}`",
        f"with a constant source delta of `+0x{DELTA:03X}`. The compared span is",
        f"`{len(cart_body)}` bytes (`0x{len(cart_body):04X}`).",
        "",
        "| Firmware | SHA256 | Compared slice SHA256 | Mismatches | Disposition |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for label, path, data, body, mismatches, _ in monitor_results:
        disposition = "byte-exact" if not mismatches else "single-byte divergence"
        lines.append(
            f"| {label} (`{path.relative_to(ROOT)}`) | `{sha256(data)}` | "
            f"`{sha256(body)}` | `{len(mismatches)}` | {disposition} |"
        )

    lines.extend(["", "Mismatch detail:", ""])
    mismatch_lines = []
    for label, _, _, _, mismatches, _ in monitor_results:
        for offset, cart_byte, monitor_byte in mismatches:
            mismatch_lines.append(
                f"- {label}: cartridge `0x{CART_BODY_START + offset:04X}=0x{cart_byte:02X}`; "
                f"Monitor ROM `0x{MONITOR_BODY_START + offset:04X}=0x{monitor_byte:02X}`."
            )
    lines.extend(mismatch_lines or ["- none"])

    lines.extend(
        [
            "",
            "The Monitor 3.3 slice is byte-identical to the cartridge slice. Monitor",
            "2.2 differs at only one byte. This proves that the public cartridge and",
            "the onboard BASIC are the same firmware lineage, and it supplies the",
            "entire meaningful BASIC body already present in the 8 KiB cartridge.",
            "",
            "## Cartridge suffix",
            "",
            "| Span | Bytes | Non-zero bytes | SHA256 | Interpretation |",
            "| --- | ---: | ---: | --- | --- |",
            f"| `0x{CART_BODY_END:04X}..0x1EFF` | `{len(zero_gap)}` | "
            f"`{sum(byte != 0 for byte in zero_gap)}` | `{sha256(zero_gap)}` | zero padding |",
            f"| `0x1F00..0x1FFF` | `{len(bootstrap)}` | "
            f"`{sum(byte != 0 for byte in bootstrap)}` | `{sha256(bootstrap)}` | relocation bootstrap page |",
            "",
            "The required loop-survival sequence occurs at bootstrap offset",
            f"`0x{loop_offset:02X}`. The earlier final-page-mirror experiment therefore",
            "already tested the strongest source-adjacent reconstruction: a second copy",
            "of this bootstrap page after the known 8 KiB image. It completed the",
            "self-overwriting relocation but still did not render `READY`.",
            "",
            "## Monitor 2.2 integrity",
            "",
            "The Monitor 2.2 reset code verifies eight 2 KiB ROM blocks using checksum",
            "bytes at offsets `0x0003..0x000A`. The public museum image fails three",
            "blocks before it can exercise an early-firmware BASIC path: blocks 3, 6, and 7.",
            "",
            "| Block | Covered bytes | Stored | Computed | Result |",
            "| ---: | --- | ---: | ---: | --- |",
        ]
    )
    jmon22 = monitor_results[0]
    for block, start, end, stored, passed in jmon22[5]:
        computed = sum(jmon22[2][start : end + 1]) & 0xFF
        lines.append(
            f"| `{block}` | `0x{start:04X}..0x{end:04X}` | `0x{stored:02X}` | "
            f"`0x{computed:02X}` | {'PASS' if passed else 'FAIL'} |"
        )

    lines.extend(
        [
            "",
            "The dedicated `docs/jmon22-reconstruction.md` audit proves that the",
            "block-3 failure is the sole BASIC-body mismatch: replacing `0x9A` at",
            "`0x1EFC` with the `0xDA` found in both Monitor 3.3 and this cartridge",
            "exactly closes the stored checksum. It leaves the original dump unchanged",
            "because blocks 6 and 7 remain unresolved.",
            "",
            "A bounded diagnostic with checksum bytes repaired in temporary memory",
            "passed the self-test, but then executed at `0xC482`, outside the validated",
            "E5104 upper-ROM window (`0xD800..0xFFFF`). Widening that temporary window",
            "advanced execution into further low-ROM dependencies without reaching a",
            "visible prompt. This is evidence for an earlier hardware/firmware mapping,",
            "not authority to alter the reproduced E5104 decode or publish a patched ROM.",
            "",
            "## Boundary",
            "",
            "- The cartridge's BASIC body is no longer an unknown implementation: it is",
            "  byte-exactly present in Monitor 3.3 and nearly exact in Monitor 2.2.",
            "- The exact shared span ends at cartridge offset `0x1D37`; extrapolating the",
            "  `+0x2C8` source delta into later monitor/bootstrap code is not a defensible",
            "  missing-page donor.",
            "- A mirrored bootstrap/survival page fixes relocation mechanics but does not",
            "  fix the later monitor ABI/configuration mismatch or reach `READY`.",
            "- The remaining preservation input is therefore a complete removable-memory",
            "  image or a documented early-board decode/loading procedure, not another",
            "  copy of the BASIC body already recovered here.",
            "",
        ]
    )

    REPORT.write_text("\n".join(lines))
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
