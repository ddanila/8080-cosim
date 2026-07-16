#!/usr/bin/env python3
"""Inspect the vendored EKDOS source for FDC/media-relevant constants."""
from __future__ import annotations

import ast
import hashlib
import operator
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ref" / "ekdos-source" / "EKDOS30.ASM"
REPORT = ROOT / "docs" / "ekdos-source-inspection.md"
DISK = ROOT / "media" / "disks" / "JUKU1.CPM"

EQU_RE = re.compile(r"^([A-Za-z][A-Za-z0-9]*)\s+EQU\s+(.+)$", re.IGNORECASE)
DB_RE = re.compile(r"^\s*DB\s+(.+)$", re.IGNORECASE)
DATA_RE = re.compile(r"^\s*(?:DB|DW)\s+(.+)$", re.IGNORECASE)
COMMENT_RE = re.compile(r";.*$")

EXPECTED = {
    "MSIZE": 52,
    "CCP": 0xB400,
    "BDOS": 0xBC06,
    "BIOS": 0xCA00,
    "ROM": 0xFF50,
    "FLOPPY": 0xFF53,
    "START": 0xFF56,
    "RWFLOPPY": 0xFF59,
    "RAMDISKSEL": 0xFF5C,
    "RDCHR": 0xFFD3,
    "WRCHR": 0xFFD9,
    "CONSTA": 0xFF98,
    "CONCW": 0xFFB4,
    "NDISKS": 3,
    "RDNO": 2,
    "VIARV": 10,
    "TRACKS": 160,
    "BLKSIZ": 4096,
    "DIRTRK": 2,
    "BLOCKS": 197,
    "DIRENT": 128,
    "DIRCHK": 0x20,
    "TYP": 0xD600,
    "DISKNO": 0xD601,
    "TRACK": 0xD602,
    "SECTOR": 0xD604,
    "RQST": 0xD606,
    "DMAAD": 0xD607,
    "ERRC": 0xD609,
    "TYPEA": 0xD60A,
    "FBI": 0xD61A,
    "VERX": 0xD615,
    "SEKDSK": 0xD61A,
    "SEKSEC": 0xD61D,
    "HSTACT": 0xD623,
    "HSTWRT": 0xD624,
    "UNACNT": 0xD625,
    "RCOUNT": 0xD62A,
    "MEMADR": 0xD62E,
    "BDOSADDR": 0xFF64,
    "SAVEHL": 0xD2FE,
    "STAK": 0xD2FC,
    "DKRD": 0x11,
    "DKWR": 0x12,
}

CHECK_LABELS = [
    "ROM",
    "BIOS",
    "FLOPPY",
    "START",
    "RWFLOPPY",
    "RAMDISKSEL",
    "RDNO",
    "VIARV",
    "TRACKS",
    "BLKSIZ",
    "NDISKS",
    "TYP",
    "SEKDSK",
    "SEKSEC",
    "HSTACT",
    "HSTWRT",
    "UNACNT",
    "RCOUNT",
    "MEMADR",
    "STAK",
    "DKRD",
    "DKWR",
]

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strip_comment(line: str) -> str:
    return COMMENT_RE.sub("", line).strip()


def normalize_number(token: str) -> str:
    return re.sub(r"\b([0-9A-Fa-f]+)H\b", lambda m: str(int(m.group(1), 16)), token)


def eval_ast(node: ast.AST) -> int:
    if isinstance(node, ast.Expression):
        return eval_ast(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return int(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        return OPS[type(node.op)](eval_ast(node.left), eval_ast(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        return OPS[type(node.op)](eval_ast(node.operand))
    raise ValueError(f"unsupported expression: {ast.dump(node)}")


def evaluate(expr: str, symbols: dict[str, int]) -> int:
    clean = strip_comment(expr).upper()
    if "NOT " in clean or "$" in clean:
        raise ValueError("expression intentionally skipped")
    clean = normalize_number(clean)
    for name, value in sorted(symbols.items(), key=lambda item: len(item[0]), reverse=True):
        clean = re.sub(rf"\b{re.escape(name)}\b", str(value), clean, flags=re.IGNORECASE)
    if re.search(r"[A-Z]", clean):
        raise ValueError(f"unresolved symbol in {expr!r}")
    return eval_ast(ast.parse(clean, mode="eval"))


def parse_symbols(lines: list[str]) -> tuple[dict[str, int], list[str]]:
    symbols: dict[str, int] = {}
    skipped: list[str] = []
    pending: list[tuple[str, str, str]] = []
    for raw in lines:
        clean = strip_comment(raw)
        match = EQU_RE.match(clean)
        if not match:
            continue
        name, expr = match.groups()
        pending.append((name.upper(), expr, raw.strip()))

    for _ in range(8):
        rest: list[tuple[str, str, str]] = []
        progressed = False
        for name, expr, raw in pending:
            try:
                symbols[name] = evaluate(expr, symbols)
                progressed = True
            except ValueError:
                rest.append((name, expr, raw))
        pending = rest
        if not pending or not progressed:
            break

    for name, _expr, raw in pending:
        if name in EXPECTED:
            skipped.append(raw)
    return symbols, skipped


def parse_db_values(payload: str) -> list[int]:
    values = []
    for item in payload.split(","):
        token = item.strip()
        if not token:
            continue
        if token.startswith("'") or token.startswith('"'):
            continue
        token = normalize_number(token)
        values.append(int(token, 0))
    return values


def parse_translation(lines: list[str], label: str) -> list[int]:
    values: list[int] = []
    in_table = False
    for raw in lines:
        clean = strip_comment(raw)
        upper = clean.upper()
        if upper.startswith(f"{label}:"):
            in_table = True
            payload = clean.split(":", 1)[1].strip()
            if payload.upper().startswith("DB"):
                values.extend(parse_db_values(payload[2:].strip()))
            continue
        if in_table:
            if not clean:
                break
            if re.match(r"^[A-Za-z][A-Za-z0-9]*:", clean):
                break
            match = DB_RE.match(clean)
            if not match:
                break
            values.extend(parse_db_values(match.group(1)))
    return values


def parse_numeric_table(lines: list[str], label: str) -> list[int]:
    values: list[int] = []
    in_table = False
    for raw in lines:
        clean = strip_comment(raw)
        if clean.upper().startswith(f"{label}:"):
            in_table = True
            clean = clean.split(":", 1)[1].strip()
            if not clean:
                continue
        elif not in_table:
            continue
        if not clean or re.match(r"^[A-Za-z][A-Za-z0-9]*:", clean):
            break
        match = DATA_RE.match(clean)
        if not match:
            break
        values.extend(parse_db_values(match.group(1)))
    return values


def fmt_hex(value: int) -> str:
    return f"0x{value:04X}" if value > 0xFF else f"0x{value:02X}"


def main() -> int:
    text = SOURCE.read_text(encoding="latin-1")
    lines = text.splitlines()
    symbols, skipped = parse_symbols(lines)
    trans = parse_translation(lines, "TRANS")
    trans1 = parse_translation(lines, "TRANS1")
    mdiskpar = parse_numeric_table(lines, "MDISKPAR")
    normalized_lines = {" ".join(strip_comment(line).upper().split()) for line in lines}

    failures: list[str] = []
    for label, expected in EXPECTED.items():
        if label in symbols and symbols[label] != expected:
            failures.append(f"{label} expected {fmt_hex(expected)}, got {fmt_hex(symbols[label])}")
    for label in CHECK_LABELS:
        if label not in symbols:
            failures.append(f"missing required symbol {label}")
    if len(trans) != 40 or sorted(trans) != list(range(1, 41)):
        failures.append("TRANS is not a 40-entry 1..40 sector map")
    if trans1 != trans:
        failures.append("TRANS1 does not match TRANS")
    expected_mdiskpar = [128, 3, 7, 0, 191, 63, 0xC0, 0, 0, 0]
    if mdiskpar != expected_mdiskpar:
        failures.append(
            f"MDISKPAR expected {expected_mdiskpar}, got {mdiskpar}"
        )
    bios_vectors = [
        ("CONST / CONSTAT", 2, "JMP CONSTAT"),
        ("PUNCH", 6, "DP RTNEMPTY"),
        ("READER", 7, "JMP RTNEMPTY"),
        ("HOME", 8, "JMP HOME"),
        ("SELDSK", 9, "JMP SELDSK"),
        ("SETTRK", 10, "JMP SETTRK"),
        ("SETSEC", 11, "JMP SETSEC"),
        ("SETDMA", 12, "JMP SETDMA"),
        ("READ", 13, "JMP READ"),
        ("WRITE", 14, "JMP WRITE"),
        ("LISTST / POLLPT", 15, "JMP POLLPT"),
        ("SECTRAN", 16, "JMP SECTRAN"),
    ]
    for name, _index, source_line in bios_vectors:
        if source_line not in normalized_lines:
            failures.append(
                f"BIOS jump table is missing archival evidence {source_line} for {name}"
            )
    if DISK.exists() and DISK.stat().st_size != 160 * 10 * 512:
        failures.append("JUKU1.CPM size does not match 160 tracks * 10 sectors * 512 bytes")

    status = "PASS" if not failures else "FAIL"
    physical_tracks = symbols.get("TRACKS", 0) // 2
    disk_size = DISK.stat().st_size if DISK.exists() else 0
    ram_records_per_track = mdiskpar[0] if len(mdiskpar) > 0 else 0
    ram_block_size = 128 << mdiskpar[1] if len(mdiskpar) > 1 else 0
    ram_blocks = mdiskpar[4] + 1 if len(mdiskpar) > 4 else 0
    ram_capacity = ram_block_size * ram_blocks
    ram_tracks = (ram_capacity // (ram_records_per_track * 128)
                  if ram_records_per_track else 0)
    ram_banks = ram_capacity // 0x8000
    lines_out = [
        "# EKDOS source inspection",
        "",
        f"Status: **{status}**",
        "",
        "This generated report inspects the vendored Arti `EKDOS30.ASM` source",
        "for constants that matter to the ROMBIOS/EKDOS/FDC path. It intentionally",
        "does not try to assemble the historical source; some source lines have",
        "archive/OCR-era wrapping damage, so this check only uses stable `EQU`",
        "labels and `TRANS` tables.",
        "",
        "## Source",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| File | `{SOURCE.relative_to(ROOT)}` |",
        f"| SHA256 | `{sha256(SOURCE)}` |",
        f"| Lines | `{len(lines)}` |",
        "",
        "## Monitor Interface Constants",
        "",
        "| Label | Value | Meaning |",
        "| --- | ---: | --- |",
        f"| `ROM` | `{fmt_hex(symbols['ROM'])}` | ROMBIOS cold-start loader base |",
        f"| `FLOPPY` | `{fmt_hex(symbols['FLOPPY'])}` | ROMBIOS floppy handler entry |",
        f"| `START` | `{fmt_hex(symbols['START'])}` | loader for `<A>` sectors to CCP |",
        f"| `RWFLOPPY` | `{fmt_hex(symbols['RWFLOPPY'])}` | ROMBIOS read/write floppy entry |",
        f"| `RAMDISKSEL` | `{fmt_hex(symbols['RAMDISKSEL'])}` | RAM-drive probe/format entry |",
        f"| `RDNO` | `{symbols['RDNO']}` | EKDOS RAM-drive number |",
        f"| `DKRD` | `{fmt_hex(symbols['DKRD'])}` | EKDOS read-sector request code |",
        f"| `DKWR` | `{fmt_hex(symbols['DKWR'])}` | EKDOS write-sector request code |",
        f"| `VIARV` | `{symbols['VIARV']}` | retries loaded into `RCOUNT` for disk I/O |",
        "",
        "## EKDOS BIOS Interface",
        "",
        "| Field | Value |",
        "| --- | ---: |",
        f"| `CCP` | `{fmt_hex(symbols['CCP'])}` |",
        f"| `BDOS` | `{fmt_hex(symbols['BDOS'])}` |",
        f"| `BIOS` | `{fmt_hex(symbols['BIOS'])}` |",
        *(f"| BIOS `{name}` (index {index}) | `{fmt_hex(symbols['BIOS'] + index * 3)}` |"
          for name, index, _source_line in bios_vectors),
        f"| DPH size used by `SELDSK` | `16` bytes |",
        f"| RAM-drive DPH displacement | `RDNO * 16 = {symbols['RDNO'] * 16}` bytes |",
        "",
        "## Floppy Parameter Block",
        "",
        "| Field | Value |",
        "| --- | ---: |",
        f"| `NDISKS` | `{symbols['NDISKS']}` |",
        f"| `TRACKS` | `{symbols['TRACKS']}` logical side-tracks = `{physical_tracks}` cylinders x 2 sides |",
        f"| physical sectors/track inferred from `TRANS` | `{len(trans) // 4}` x 512-byte sectors |",
        f"| CP/M logical sectors/track from `TRANS` | `{len(trans)}` x 128-byte sectors |",
        f"| logical bytes/side-track | `{len(trans) * 128}` |",
        f"| raw `JUKU1.CPM` size | `{disk_size}` bytes |",
        "",
        "## RAM Drive Parameter Block",
        "",
        "| Field | Value |",
        "| --- | ---: |",
        f"| logical 128-byte records/track | `{ram_records_per_track}` |",
        f"| block shift / block mask / extent mask | `{mdiskpar[1]}` / `{mdiskpar[2]}` / `{mdiskpar[3]}` |",
        f"| allocation blocks (`DSM+1`) | `{ram_blocks}` x `{ram_block_size}` bytes |",
        f"| directory entries (`DRM+1`) | `{mdiskpar[5] + 1}` |",
        f"| allocation bitmap | `0x{mdiskpar[6]:02X} 0x{mdiskpar[7]:02X}` |",
        f"| check-vector size / reserved tracks | `{mdiskpar[8]}` / `{mdiskpar[9]}` |",
        f"| total capacity | `{ram_capacity}` bytes = `{ram_banks}` x 32 KiB banks = `{ram_tracks}` track halves |",
        "",
        "## Floppy Handler Work Area",
        "",
        "| Label | Value | Meaning |",
        "| --- | ---: | --- |",
        f"| `TYP` | `{fmt_hex(symbols['TYP'])}` | monitor floppy work-area base |",
        f"| `SEKDSK` | `{fmt_hex(symbols['SEKDSK'])}` | selected drive |",
        f"| `SEKSEC` | `{fmt_hex(symbols['SEKSEC'])}` | selected sector |",
        f"| `HSTACT` | `{fmt_hex(symbols['HSTACT'])}` | host-sector cache active flag |",
        f"| `HSTWRT` | `{fmt_hex(symbols['HSTWRT'])}` | host-sector cache dirty flag |",
        f"| `UNACNT` | `{fmt_hex(symbols['UNACNT'])}` | unallocated-write counter |",
        f"| `RCOUNT` | `{fmt_hex(symbols['RCOUNT'])}` | retry counter |",
        f"| `MEMADR` | `{fmt_hex(symbols['MEMADR'])}` | DMA address field |",
        f"| `STAK` | `{fmt_hex(symbols['STAK'])}` | EKDOS temporary stack outside RAM-drive aperture |",
        "",
        "## Sector Translation",
        "",
        "| Table | Entries | Min | Max | Matches 1..40 |",
        "| --- | ---: | ---: | ---: | --- |",
        f"| `TRANS` | `{len(trans)}` | `{min(trans) if trans else 'n/a'}` | `{max(trans) if trans else 'n/a'}` | `{sorted(trans) == list(range(1, 41))}` |",
        f"| `TRANS1` | `{len(trans1)}` | `{min(trans1) if trans1 else 'n/a'}` | `{max(trans1) if trans1 else 'n/a'}` | `{trans1 == trans}` |",
        "",
        "## Parser Boundary",
        "",
        "The source contains a few visibly wrapped/collided historical lines; those",
        "are left as source text rather than repaired in place. Skipped required-like",
        "lines:",
        "",
    ]
    if skipped:
        lines_out.extend(f"- `{line}`" for line in skipped)
    else:
        lines_out.append("- none")
    lines_out.extend(
        [
            "",
            "## Failures",
            "",
        ]
    )
    if failures:
        lines_out.extend(f"- {failure}" for failure in failures)
    else:
        lines_out.append("- none")
    lines_out.append("")

    REPORT.write_text("\n".join(lines_out))
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    if failures:
        raise SystemExit("; ".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
