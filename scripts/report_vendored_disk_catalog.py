#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DISK_DIR = ROOT / "media" / "disks"
REPORT = ROOT / "docs" / "vendored-disk-catalog.md"
DISK_GLOBS = ("*.CPM", "*.JUK")

DIRECTORY_OFFSET = 0x5000
DIRECTORY_ENTRIES = 128
ENTRY_SIZE = 32

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
            }
        )
    return entries


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
        "This rules out a plainly named/text-tagged payload in the current images; it",
        "cannot rule out an unidentified binary table with no embedded identifier.",
        "",
        table_row(["Disk", "Active candidate names", "Deleted names", "Raw marker hits"]),
        table_row(["---", "---", "---", "---"]),
    ]

    catalog_by_name = {disk.name: (disk, entries) for disk, entries in catalogs}
    for name in PROGRAMMING_DISKS:
        disk, entries = catalog_by_name[name]
        active = prom_name_candidates(entries)
        deleted = parse_deleted_directory(disk)
        deleted_names = sorted(entry["filename"] for entry in deleted)
        hits = marker_hits(disk)
        lines.append(
            table_row(
                [
                    rel(disk),
                    ", ".join(f"`{value}`" for value in active) or "none",
                    ", ".join(f"`{value}`" for value in deleted_names) or "none",
                    ", ".join(f"`{value}`" for value in hits) or "none",
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
