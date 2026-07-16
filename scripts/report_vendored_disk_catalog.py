#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DISK_DIR = ROOT / "media" / "disks"
REPORT = ROOT / "docs" / "vendored-disk-catalog.md"
DISK_GLOBS = ("*.CPM", "*.JUK")

DIRECTORY_OFFSET = 0x5000
DIRECTORY_ENTRIES = 128
ENTRY_SIZE = 32
BLOCK_SIZE = 4096
CPM_RECORD_SIZE = 128
CPM_SECTORS_PER_TRACK = 40
LOGICAL_SYSTEM_TRACKS = 4
LOGICAL_SECTOR_TRANSLATION = (
    1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28,
    33, 34, 35, 36, 5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24,
    29, 30, 31, 32, 37, 38, 39, 40,
)

PHYSICAL_PROM_DIR = ROOT / "ref" / "physical-proms" / "validated"
PHYSICAL_PROM_TABLES = {
    "D2 .037": "d2_037",
    "D6 .038": "d6_038",
    "D8 .039": "d8_039",
    "D94 .092": "d94_092",
}

BASIC_RELATED = {
    "B80.COM",
    "BASCOM.COM",
    "BASCOM.DOK",
    "BASLIB.REL",
    "BIO80.BAS",
    "BRUN.COM",
    "JBASIC.COM",
    "MATIC80.BAS",
    "STIIL.BAS",
    "YL80.BAS",
}

PROGRAMMING_DISKS = (
    "JUKPROG1.CPM",
    "JUKPROG2.CPM",
    "JUKPROGX.CPM",
)

# Strong, human-readable identifiers expected around a factory programming
# table/file. Bare decimal strings are deliberately excluded because they are
# common in binaries and would not identify a PROM payload.
PROM_MARKERS = (
    ".037",
    ".038",
    ".039",
    ".092",
    "106.037",
    "106.038",
    "106.039",
    "106.092",
    "RT4",
    "RE3",
)

PROM_NAME_TOKENS = (
    "037",
    "038",
    "039",
    "092",
    "PROM",
    "RT4",
    "RE3",
)


def rel(path):
    return path.relative_to(ROOT).as_posix()


def decode_text(raw):
    return bytes(byte & 0x7F for byte in raw).decode("ascii", errors="replace").rstrip()


def valid_name(text):
    if not text:
        return False
    for char in text:
        if char == " ":
            continue
        if char.isalnum() or char in "$#@!%&'()-{}~^_":
            continue
        return False
    return True


def parse_directory(path):
    data = path.read_bytes()
    entries = []
    start = DIRECTORY_OFFSET
    end = start + DIRECTORY_ENTRIES * ENTRY_SIZE
    for index, offset in enumerate(range(start, min(end, len(data)), ENTRY_SIZE)):
        entry = data[offset : offset + ENTRY_SIZE]
        if len(entry) < ENTRY_SIZE:
            continue
        user = entry[0]
        if user == 0xE5 or user > 0x0F:
            continue
        stem = decode_text(entry[1:9])
        ext = decode_text(entry[9:12])
        if not valid_name(stem) or not valid_name(ext):
            continue
        stem = stem.strip()
        ext = ext.strip()
        filename = f"{stem}.{ext}" if ext else stem
        extent = entry[12]
        record_count = entry[15]
        entries.append(
            {
                "index": index,
                "offset": offset,
                "user": user,
                "filename": filename,
                "extent": extent,
                "records": record_count,
                "blocks": [block for block in entry[16:32] if block],
            }
        )
    return entries


def logical_sector_offset(logical_sector):
    logical_track = LOGICAL_SYSTEM_TRACKS + logical_sector // CPM_SECTORS_PER_TRACK
    sector_in_track = logical_sector % CPM_SECTORS_PER_TRACK
    translated = LOGICAL_SECTOR_TRANSLATION[sector_in_track] - 1
    return logical_track * CPM_SECTORS_PER_TRACK * CPM_RECORD_SIZE + translated * CPM_RECORD_SIZE


def read_block(data, block):
    out = bytearray()
    first_sector = block * (BLOCK_SIZE // CPM_RECORD_SIZE)
    for sector in range(first_sector, first_sector + BLOCK_SIZE // CPM_RECORD_SIZE):
        offset = logical_sector_offset(sector)
        out.extend(data[offset : offset + CPM_RECORD_SIZE])
    return bytes(out)


def extract_entry(data, entry):
    payload = b"".join(read_block(data, block) for block in entry["blocks"])
    return payload[: entry["records"] * CPM_RECORD_SIZE]


def extract_active_files(path, entries):
    data = path.read_bytes()
    grouped = {}
    for entry in entries:
        grouped.setdefault((entry["user"], entry["filename"]), []).append(entry)
    files = {}
    for (user, filename), extents in grouped.items():
        extents.sort(key=lambda entry: entry["extent"])
        files[f"u{user}:{filename}"] = b"".join(
            extract_entry(data, entry) for entry in extents
        )
    return files


def parse_deleted_directory(path):
    data = path.read_bytes()
    entries = []
    start = DIRECTORY_OFFSET
    end = start + DIRECTORY_ENTRIES * ENTRY_SIZE
    for index, offset in enumerate(range(start, min(end, len(data)), ENTRY_SIZE)):
        entry = data[offset : offset + ENTRY_SIZE]
        if len(entry) < ENTRY_SIZE or entry[0] != 0xE5:
            continue
        raw_name = entry[1:12]
        # CP/M initializes unused directory slots with E5 bytes. Do not turn
        # that erased fill into a plausible-looking "eeeeeeee.eee" filename.
        if all(byte in (0x00, 0x20, 0xE5) for byte in raw_name):
            continue
        stem = decode_text(entry[1:9])
        ext = decode_text(entry[9:12])
        if not valid_name(stem) or not valid_name(ext):
            continue
        stem = stem.strip()
        ext = ext.strip()
        if not stem:
            continue
        filename = f"{stem}.{ext}" if ext else stem
        entries.append({"index": index, "offset": offset, "filename": filename})
    return entries


def marker_hits(path):
    data = path.read_bytes().upper()
    return [marker for marker in PROM_MARKERS if marker.encode("ascii") in data]


def prom_name_candidates(entries):
    return sorted(
        {
            entry["filename"]
            for entry in entries
            if any(token in entry["filename"].upper() for token in PROM_NAME_TOKENS)
        }
    )


def packed_nibbles(data, high_nibble_first):
    if len(data) % 2 or any(byte > 0x0F for byte in data):
        return None
    out = bytearray()
    for index in range(0, len(data), 2):
        first, second = data[index : index + 2]
        if high_nibble_first:
            out.append((first << 4) | second)
        else:
            out.append(first | (second << 4))
    return bytes(out)


def intel_hex_data(data, record_size, uppercase, line_ending):
    records = []
    for address in range(0, len(data), record_size):
        payload = data[address : address + record_size]
        fields = bytes(
            [len(payload), address >> 8, address & 0xFF, 0x00]
        ) + payload
        checksum = (-sum(fields)) & 0xFF
        record = ":" + (fields + bytes([checksum])).hex()
        records.append(record.upper() if uppercase else record.lower())
    return (line_ending.join(records) + line_ending).encode()


def table_encodings(stem):
    encodings = {}
    for polarity in ("raw", "asserted"):
        table = (PHYSICAL_PROM_DIR / f"{stem}.{polarity}.bin").read_bytes()
        expected_size = 256 if stem.startswith(("d2_", "d6_")) else 32
        if len(table) != expected_size:
            raise SystemExit(
                f"{stem}.{polarity}.bin has {len(table)} bytes, expected {expected_size}"
            )
        for order, ordered in (("forward", table), ("address-reversed", table[::-1])):
            prefix = f"{polarity}/{order}"
            encodings[f"{prefix}/bytes"] = ordered
            for case, hex_bytes in (
                ("upper", [f"{byte:02X}" for byte in ordered]),
                ("lower", [f"{byte:02x}" for byte in ordered]),
            ):
                encodings[f"{prefix}/hex-{case}-compact"] = "".join(
                    hex_bytes
                ).encode()
                encodings[f"{prefix}/hex-{case}-spaces"] = " ".join(
                    hex_bytes
                ).encode()
                encodings[f"{prefix}/hex-{case}-lf"] = (
                    "\n".join(hex_bytes) + "\n"
                ).encode()
                encodings[f"{prefix}/hex-{case}-crlf"] = (
                    "\r\n".join(hex_bytes) + "\r\n"
                ).encode()
            for record_size in (16, 32):
                for case, uppercase in (("upper", True), ("lower", False)):
                    for ending, line_ending in (("lf", "\n"), ("crlf", "\r\n")):
                        encodings[
                            f"{prefix}/intel-hex-{record_size}-{case}-{ending}"
                        ] = intel_hex_data(
                            ordered, record_size, uppercase, line_ending
                        )
            if all(byte <= 0x0F for byte in ordered):
                encodings[f"{prefix}/nibble-ascii-upper"] = "".join(
                    f"{byte:X}" for byte in ordered
                ).encode()
                encodings[f"{prefix}/nibble-ascii-lower"] = "".join(
                    f"{byte:x}" for byte in ordered
                ).encode()
                encodings[f"{prefix}/packed-high-first"] = packed_nibbles(ordered, True)
                encodings[f"{prefix}/packed-low-first"] = packed_nibbles(ordered, False)
    if any(not payload for payload in encodings.values()):
        raise SystemExit(f"empty search encoding generated for {stem}")
    return encodings


def disk_search_corpora(path, entries):
    corpora = {"raw-image": path.read_bytes()}
    corpora.update(extract_active_files(path, entries))
    return corpora


def exact_table_hits(corpora, encodings):
    hits = []
    for encoding, needle in encodings.items():
        for corpus_name, corpus in corpora.items():
            start = 0
            while (offset := corpus.find(needle, start)) >= 0:
                hits.append(f"{encoding} in {corpus_name}@0x{offset:X}")
                start = offset + 1
    return hits


def table_row(values):
    escaped = [str(value).replace("|", "/") for value in values]
    return "| " + " | ".join(escaped) + " |"


def main():
    disks = []
    for pattern in DISK_GLOBS:
        disks.extend(DISK_DIR.glob(pattern))
    disks = sorted(disks)
    catalogs = [(disk, parse_directory(disk)) for disk in disks]

    lines = [
        "# Vendored disk catalog",
        "",
        "Status: **VENDORED DISK DIRECTORY INDEXED**",
        "",
        "This report indexes the visible CP/M directory entries in the vendored",
        "Juku raw disk images under `media/disks/`. It is intentionally a",
        "conservative catalog, not a full CP/M filesystem extractor.",
        "",
        f"The current images expose their directory at byte offset `0x{DIRECTORY_OFFSET:04X}`.",
        f"The scanner reads `{DIRECTORY_ENTRIES}` directory entries of `{ENTRY_SIZE}` bytes",
        "and strips CP/M attribute bits from filename bytes.",
        "",
        "## BASIC-relevant files",
        "",
        table_row(["Disk", "Files"]),
        table_row(["---", "---"]),
    ]

    any_basic = False
    for disk, entries in catalogs:
        found = sorted({entry["filename"] for entry in entries if entry["filename"] in BASIC_RELATED})
        if found:
            any_basic = True
            lines.append(table_row([rel(disk), ", ".join(f"`{name}`" for name in found)]))
    if not any_basic:
        lines.append(table_row(["-", "-"]))

    lines += [
        "",
        "## Programming-media PROM search",
        "",
        "The three `JUKPROG` images were checked separately because factory doc 007",
        "says the `.037`/`.038`/`.039`/`.092` programming tables were held on disk.",
        "The audit checks active directory filenames, recoverable deleted-entry",
        "filenames, and every raw image byte for strong ASCII drawing/part markers.",
        "It also searches the complete raw images and every reconstructed active CP/M",
        "file for exact encodings of all four validated physical PROM tables.",
        "The exact search covers raw and asserted polarity, forward and reversed address",
        "order, compact/space/line-oriented ASCII hex, checksum-valid Intel HEX,",
        "and, where the table is nibble-wide, nibble ASCII plus both packed-nibble",
        "orders.",
        "No match under these common exact encodings rules out a plainly stored validated",
        "table; a proprietary, permuted, compressed, or otherwise transformed encoding",
        "still cannot be ruled out.",
        "",
        table_row(["Disk", "Active candidate names", "Deleted names", "Raw marker hits", "Exact table hits"]),
        table_row(["---", "---", "---", "---", "---"]),
    ]

    catalog_by_name = {disk.name: (disk, entries) for disk, entries in catalogs}
    encoding_sets = {
        label: table_encodings(stem) for label, stem in PHYSICAL_PROM_TABLES.items()
    }
    binary_results = []
    for name in PROGRAMMING_DISKS:
        disk, entries = catalog_by_name[name]
        active = prom_name_candidates(entries)
        deleted = parse_deleted_directory(disk)
        deleted_names = sorted(entry["filename"] for entry in deleted)
        hits = marker_hits(disk)
        corpora = disk_search_corpora(disk, entries)
        disk_table_hits = []
        for label, encodings in encoding_sets.items():
            exact_hits = exact_table_hits(corpora, encodings)
            binary_results.append(
                (disk, label, len(corpora), len(encodings), exact_hits)
            )
            disk_table_hits.extend(f"{label}: {hit}" for hit in exact_hits)
        lines.append(
            table_row(
                [
                    rel(disk),
                    ", ".join(f"`{value}`" for value in active) or "none",
                    ", ".join(f"`{value}`" for value in deleted_names) or "none",
                    ", ".join(f"`{value}`" for value in hits) or "none",
                    "; ".join(f"`{value}`" for value in disk_table_hits) or "none",
                ]
            )
        )

    lines += [
        "",
        "### Exact binary-table forensics",
        "",
        "Each encoding is searched once in the physical byte stream and once in every",
        "active file reconstructed in CP/M logical extent order. Offsets would be shown",
        "for every match; `none` means the full encoding was absent from both views.",
        "",
        table_row(
            [
                "Disk",
                "Validated table",
                "Corpora searched",
                "Encoding forms tested",
                "Matches",
            ]
        ),
        table_row(["---", "---", "---:", "---:", "---"]),
    ]
    for disk, label, corpus_count, encoding_count, exact_hits in binary_results:
        lines.append(
            table_row(
                [
                    rel(disk),
                    label,
                    corpus_count,
                    encoding_count,
                    "; ".join(f"`{hit}`" for hit in exact_hits) or "none",
                ]
            )
        )

    lines += [
        "",
        "## Directory entries",
        "",
    ]

    for disk, entries in catalogs:
        lines += [
            f"### `{rel(disk)}`",
            "",
            f"- Size: `{disk.stat().st_size}` bytes",
            f"- Directory entries found: `{len(entries)}`",
            "",
            table_row(["Entry", "Offset", "User", "Filename", "Extent", "Records"]),
            table_row(["---:", "---:", "---:", "---", "---:", "---:"]),
        ]
        for entry in entries:
            lines.append(
                table_row(
                    [
                        entry["index"],
                        f"0x{entry['offset']:05X}",
                        entry["user"],
                        f"`{entry['filename']}`",
                        entry["extent"],
                        entry["records"],
                    ]
                )
            )
        lines.append("")

    REPORT.write_text("\n".join(lines).rstrip() + "\n")


if __name__ == "__main__":
    main()
