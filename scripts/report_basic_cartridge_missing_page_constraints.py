#!/usr/bin/env python3
"""Generate static constraints for the missing Monitor 3.3 BASIC cartridge page."""
from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CART = ROOT / "roms" / "jbasic11.bin"
REPORT = ROOT / "docs" / "basic-cartridge-missing-page-constraints.md"

LOAD_BASE = 0x0100
RELOC_SRC_START = 0x0200
RELOC_DST_START = 0x0100
RELOC_LEN = 0x2000
MISSING_SRC_START = 0x2100
MISSING_DST_START = 0x2000
MISSING_LEN = 0x0100
LOOP_TAIL_START = 0x2009
LOOP_TAIL_END = 0x2015

TWO_BYTE_OPS = {
    0x06,
    0x0E,
    0x16,
    0x1E,
    0x26,
    0x2E,
    0x36,
    0x3E,
    0xC6,
    0xCE,
    0xD3,
    0xD6,
    0xDB,
    0xDE,
    0xE6,
    0xEE,
    0xF6,
    0xFE,
}

THREE_BYTE_OPS = {
    0x01,
    0x11,
    0x21,
    0x22,
    0x2A,
    0x31,
    0x32,
    0x3A,
    0xC2,
    0xC3,
    0xC4,
    0xCA,
    0xCC,
    0xCD,
    0xD2,
    0xD4,
    0xDA,
    0xDC,
    0xE2,
    0xE4,
    0xEA,
    0xEC,
    0xF2,
    0xF4,
    0xFA,
    0xFC,
}

MNEMONICS = {
    0x01: "LXI B",
    0x11: "LXI D",
    0x21: "LXI H",
    0x22: "SHLD",
    0x2A: "LHLD",
    0x31: "LXI SP",
    0x32: "STA",
    0x3A: "LDA",
    0xC2: "JNZ",
    0xC3: "JMP",
    0xC4: "CNZ",
    0xCA: "JZ",
    0xCC: "CZ",
    0xCD: "CALL",
    0xD2: "JNC",
    0xD4: "CNC",
    0xDA: "JC",
    0xDC: "CC",
    0xE2: "JPO",
    0xE4: "CPO",
    0xEA: "JPE",
    0xEC: "CPE",
    0xF2: "JP",
    0xF4: "CP",
    0xFA: "JM",
    0xFC: "CM",
}

CONTROL_OPS = {
    0xC2,
    0xC3,
    0xC4,
    0xCA,
    0xCC,
    0xCD,
    0xD2,
    0xD4,
    0xDA,
    0xDC,
    0xE2,
    0xE4,
    0xEA,
    0xEC,
    0xF2,
    0xF4,
    0xFA,
    0xFC,
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def fmt_addr(value: int) -> str:
    return f"`0x{value:04X}`"


def fmt_span(start: int, end: int) -> str:
    return f"`0x{start:04X}..0x{end:04X}`"


def opcode_len(op: int) -> int:
    if op in THREE_BYTE_OPS:
        return 3
    if op in TWO_BYTE_OPS:
        return 2
    return 1


def known_runtime(cart: bytes) -> dict[int, int]:
    # After Monitor 3.3 enters the cartridge bootstrap, the bootstrap copies
    # source 0x0200..0x21FF to destination 0x0100..0x20FF. The public 8 KiB
    # image only supplies source bytes through 0x20FF, so runtime 0x0100..0x1FFF
    # is known and runtime 0x2000..0x20FF is the missing page.
    return {
        RELOC_DST_START + offset: byte
        for offset, byte in enumerate(cart[RELOC_SRC_START:MISSING_SRC_START])
    }


def scan_missing_page_operands(runtime: dict[int, int]) -> list[tuple[int, int, int, str]]:
    refs: list[tuple[int, int, int, str]] = []
    pc = RELOC_DST_START
    while pc < MISSING_DST_START:
        op = runtime.get(pc, 0x00)
        length = opcode_len(op)
        if length == 3 and pc + 2 < MISSING_DST_START:
            target = runtime[pc + 1] | (runtime[pc + 2] << 8)
            if MISSING_DST_START <= target < MISSING_DST_START + MISSING_LEN:
                kind = "control" if op in CONTROL_OPS else "data/immediate"
                refs.append((pc, op, target, kind))
        pc += length
    return refs


def find_page_hits(pattern: bytes) -> list[tuple[str, int, int]]:
    hits: list[tuple[str, int, int]] = []
    for dirname in ("roms", "ref", "media"):
        base = ROOT / dirname
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            data = path.read_bytes()
            start = 0
            while True:
                pos = data.find(pattern, start)
                if pos < 0:
                    break
                page_start = pos - (LOOP_TAIL_START - MISSING_DST_START)
                if page_start >= 0 and page_start + MISSING_LEN <= len(data):
                    hits.append((str(path.relative_to(ROOT)), page_start, pos - page_start))
                start = pos + 1
    return hits


def main() -> int:
    cart = CART.read_bytes()
    runtime = known_runtime(cart)
    refs = scan_missing_page_operands(runtime)
    target_counts = Counter(target for _pc, _op, target, _kind in refs)
    refs_by_target: dict[int, list[tuple[int, int, str]]] = defaultdict(list)
    for pc, op, target, kind in refs:
        refs_by_target[target].append((pc, op, kind))

    loop_tail_file_start = LOOP_TAIL_START - LOAD_BASE
    loop_tail_file_end = LOOP_TAIL_END - LOAD_BASE
    loop_tail = cart[loop_tail_file_start : loop_tail_file_end + 1]
    page_hits = find_page_hits(loop_tail)
    control_refs = [ref for ref in refs if ref[3] == "control"]
    unique_targets = sorted(target_counts)
    referenced_span = (
        fmt_span(min(unique_targets), max(unique_targets)) if unique_targets else "-"
    )
    unreferenced = MISSING_LEN - len(unique_targets)

    lines = [
        "# BASIC cartridge missing-page constraints",
        "",
        "Status: **MISSING PAGE CONSTRAINED / ARTIFACT REQUIRED**",
        "",
        "This generated report turns the Monitor 3.3 cartridge BASIC missing-page",
        "boundary into static reconstruction constraints. It does not export a",
        "patched cartridge image; the real page still needs a larger artifact,",
        "programming source, or hardware-confirmed dump.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_basic_cartridge_missing_page_constraints.py",
        "```",
        "",
        "## Inputs",
        "",
        "| Item | Value |",
        "| --- | --- |",
        table_row(["Cartridge", f"`{CART.relative_to(ROOT)}`"]),
        table_row(["Cartridge bytes", len(cart)]),
        table_row(["Cartridge SHA256", f"`{sha256(cart)}`"]),
        table_row(["Known relocated runtime span", fmt_span(RELOC_DST_START, MISSING_DST_START - 1)]),
        table_row(["Missing source span", fmt_span(MISSING_SRC_START, MISSING_SRC_START + MISSING_LEN - 1)]),
        table_row(["Missing runtime span", fmt_span(MISSING_DST_START, MISSING_DST_START + MISSING_LEN - 1)]),
        "",
        "## Relocation Loop Survival Bytes",
        "",
        "The relocation loop overwrites itself while running. For the loop tail to",
        "survive until the final iteration, the missing page must reproduce these",
        "runtime bytes at the corresponding source offsets:",
        "",
        "| Missing source | Runtime destination | Required bytes | Meaning |",
        "| --- | --- | --- | --- |",
        table_row([
            fmt_span(MISSING_SRC_START + (LOOP_TAIL_START - MISSING_DST_START), MISSING_SRC_START + (LOOP_TAIL_END - MISSING_DST_START)),
            fmt_span(LOOP_TAIL_START, LOOP_TAIL_END),
            f"`{loop_tail.hex(' ')}`",
            "`MOV A,M; STAX D; INX H; INX D; DCX B; MOV A,B; ORA C; JNZ 0x2009; JMP 0x0100` loop tail and exit",
        ]),
        "",
        "## Known-Body References Into Missing Page",
        "",
        "A linear 8080 sweep over the known relocated body (`0x0100..0x1FFF`)",
        "finds direct 16-bit operands that point into the missing runtime page.",
        "This is a conservative static constraint, not proof that every operand",
        "is executed as code.",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        table_row(["Total direct references", len(refs)]),
        table_row(["Unique referenced missing-page bytes", len(unique_targets)]),
        table_row(["Unreferenced missing-page bytes by direct operand scan", unreferenced]),
        table_row(["Referenced missing-page address span", referenced_span]),
        table_row(["Control-transfer references", len(control_refs)]),
        "",
        "| Target | References | Kinds | Sample source PCs |",
        "| ---: | ---: | --- | --- |",
    ]
    for target in unique_targets:
        target_refs = refs_by_target[target]
        kinds = sorted({kind for _pc, _op, kind in target_refs})
        sample = ", ".join(
            f"`0x{pc:04X}:{MNEMONICS.get(op, f'op{op:02X}')}`"
            for pc, op, _kind in target_refs[:6]
        )
        if len(target_refs) > 6:
            sample += f" (+{len(target_refs) - 6})"
        lines.append(table_row([fmt_addr(target), len(target_refs), ", ".join(kinds), sample]))

    lines.extend(
        [
            "",
            "## Control References",
            "",
        ]
    )
    if control_refs:
        lines.extend(
            [
                "| Source PC | Opcode | Target | Interpretation |",
                "| ---: | --- | ---: | --- |",
            ]
        )
        for pc, op, target, _kind in control_refs:
            lines.append(
                table_row(
                    [
                        fmt_addr(pc),
                        f"`{MNEMONICS.get(op, f'op{op:02X}')}`",
                        fmt_addr(target),
                        "relocation loop branch target; not an independent BASIC entry",
                    ]
                )
            )
    else:
        lines.append("No direct control-transfer references into the missing page were found.")

    lines.extend(
        [
            "",
            "## Repository Donor Scan",
            "",
            "The loop-tail byte pattern is searched at the same page offset across",
            "`roms/`, `ref/`, and `media/`. A useful donor would be a page-shaped",
            "hit outside the public cartridge's own final page.",
            "",
            "| File | Page start | Pattern offset in page |",
            "| --- | ---: | ---: |",
        ]
    )
    if page_hits:
        for path, page_start, offset in page_hits:
            lines.append(table_row([f"`{path}`", fmt_addr(page_start), fmt_addr(offset)]))
    else:
        lines.append(table_row(["-", "-", "-"]))

    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- The missing page maps exactly from cartridge/runtime source",
            f"  `0x{MISSING_SRC_START:04X}..0x{MISSING_SRC_START + MISSING_LEN - 1:04X}`",
            f"  to runtime `0x{MISSING_DST_START:04X}..0x{MISSING_DST_START + MISSING_LEN - 1:04X}`.",
            "- Current direct-operand evidence concentrates all known-body references",
            f"  in `0x{min(unique_targets):04X}..0x{max(unique_targets):04X}`; the remaining",
            "  missing-page bytes have no direct 16-bit operands from the known body.",
            "- The only direct control transfer into the missing page is the relocation",
            "  loop's own `JNZ 0x2009`. The other references are data/immediate operands,",
            "  mostly to low variables/workspace in `0x2007..0x2018`.",
            "- No current repository artifact provides a page-shaped donor beyond the",
            "  public cartridge's own final page. A burnable cartridge fix still needs",
            "  the real larger BASIC artifact, programming source, or a deeper manual",
            "  reconstruction validated against the BASIC `READY` oracle.",
            "",
        ]
    )

    REPORT.write_text("\n".join(lines))
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
