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
