#!/usr/bin/env python3
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DISK_DIR = ROOT / "media" / "disks"
OUT_DIR = ROOT / "ref" / "extracted-software"
REPORT = ROOT / "docs" / "basic-disk-extraction.md"

DIRECTORY_OFFSET = 0x5000
DIRECTORY_ENTRIES = 128
ENTRY_SIZE = 32
BLOCK_SIZE = 4096
CPM_RECORD_SIZE = 128
CPM_SECTORS_PER_TRACK = 40
LOGICAL_SYSTEM_TRACKS = 4
LOGICAL_SECTOR_TRANSLATION = [
    1,
    2,
    3,
    4,
    9,
    10,
    11,
    12,
    17,
    18,
    19,
    20,
    25,
    26,
    27,
    28,
    33,
    34,
    35,
    36,
    5,
    6,
    7,
    8,
    13,
    14,
    15,
    16,
    21,
    22,
    23,
    24,
    29,
    30,
    31,
    32,
    37,
    38,
    39,
    40,
]


def rel(path):
    return path.relative_to(ROOT).as_posix()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


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


def parse_directory(data):
    entries = []
    for index in range(DIRECTORY_ENTRIES):
        offset = DIRECTORY_OFFSET + index * ENTRY_SIZE
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
        if not stem:
            continue
        filename = f"{stem}.{ext}" if ext else stem
        entries.append(
            {
                "index": index,
                "offset": offset,
                "user": user,
                "filename": filename,
                "extent": entry[12],
                "records": entry[15],
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


def find_entry(entries, filename):
    matches = [entry for entry in entries if entry["filename"] == filename]
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]
    matches.sort(key=lambda entry: entry["extent"])
    return {
        "index": matches[0]["index"],
        "offset": matches[0]["offset"],
        "user": matches[0]["user"],
        "filename": filename,
        "extent": ",".join(str(entry["extent"]) for entry in matches),
        "records": sum(entry["records"] for entry in matches),
        "blocks": [block for entry in matches for block in entry["blocks"]],
    }


def string_offsets(data, needles):
    found = {}
    for needle in needles:
        pos = data.find(needle.encode("ascii"))
        if pos >= 0:
            found[needle] = pos
    return found


def table_row(values):
    escaped = [str(value).replace("|", "/") for value in values]
    return "| " + " | ".join(escaped) + " |"


def write_artifact(name, data):
    path = OUT_DIR / name
    path.write_bytes(data)
    return path


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    juku1 = (DISK_DIR / "JUKU1.CPM").read_bytes()
    jukprog2 = (DISK_DIR / "JUKPROG2.CPM").read_bytes()
    juku1_entries = parse_directory(juku1)
    jukprog2_entries = parse_directory(jukprog2)

    jukprog2_jbasic_entry = find_entry(jukprog2_entries, "JBASIC.COM")
    if jukprog2_jbasic_entry is None:
        raise SystemExit("JUKPROG2.CPM does not contain JBASIC.COM")
    jukprog2_jbasic = extract_entry(jukprog2, jukprog2_jbasic_entry)
    jukprog2_jbasic_path = write_artifact("JUKPROG2_JBASIC.COM", jukprog2_jbasic)

    juku1_jbasic_entry = find_entry(juku1_entries, "JBASIC.COM")
    if juku1_jbasic_entry is None:
        raise SystemExit("JUKU1.CPM does not contain JBASIC.COM")
    juku1_directory_jbasic = extract_entry(juku1, juku1_jbasic_entry)

    # The JUKU1 directory entry is present, but the same logical extraction maps
    # to erased bytes. A nearby raw copy has the expected CP/M COM jump and
    # BASIC/READY/ERROR strings, so keep it as an explicit candidate rather than
    # silently treating the directory entry as good.
    juku1_raw_offset = 0x67000
    juku1_raw_len = juku1_jbasic_entry["records"] * CPM_RECORD_SIZE
    juku1_raw_candidate = juku1[juku1_raw_offset : juku1_raw_offset + juku1_raw_len]
    juku1_raw_candidate_path = write_artifact("JUKU1_JBASIC_raw_candidate.COM", juku1_raw_candidate)

    artifacts = [
        (jukprog2_jbasic_path, jukprog2_jbasic),
        (juku1_raw_candidate_path, juku1_raw_candidate),
    ]
    (OUT_DIR / "SHA256SUMS").write_text(
        "".join(f"{sha256(data)}  {path.name}\n" for path, data in artifacts)
    )
    (OUT_DIR / "README.md").write_text(
        "\n".join(
            [
                "# Extracted Juku software",
                "",
                "Generated by `scripts/extract_basic_disk_files.py` from the vendored",
                "raw CP/M images in `media/disks/`.",
                "",
                "- `JUKPROG2_JBASIC.COM` is directory-backed from `JUKPROG2.CPM`.",
                "- `JUKU1_JBASIC_raw_candidate.COM` is a raw-offset candidate from",
                "  `JUKU1.CPM`; its directory entry currently maps to erased bytes",
                "  under the same extractor.",
                "",
            ]
        )
    )

    rows = []
    for disk_name, entry, payload, source in [
        ("JUKPROG2.CPM", jukprog2_jbasic_entry, jukprog2_jbasic, "directory"),
        ("JUKU1.CPM", juku1_jbasic_entry, juku1_directory_jbasic, "directory"),
    ]:
        strings = string_offsets(payload, ["BASIC", "READY", "ERROR", "COPYRIGHT"])
        rows.append(
            [
                disk_name,
                source,
                entry["filename"],
                entry["records"] * CPM_RECORD_SIZE,
                " ".join(f"0x{block:02X}" for block in entry["blocks"]),
                payload[:8].hex(" "),
                ", ".join(f"`{key}`@0x{value:04X}" for key, value in strings.items()) or "-",
                sha256(payload),
            ]
        )

    raw_strings = string_offsets(juku1_raw_candidate, ["BASIC", "READY", "ERROR", "COPYRIGHT"])
    rows.append(
        [
            "JUKU1.CPM",
            f"raw 0x{juku1_raw_offset:05X}",
            "JBASIC.COM candidate",
            len(juku1_raw_candidate),
            "-",
            juku1_raw_candidate[:8].hex(" "),
            ", ".join(f"`{key}`@0x{value:04X}" for key, value in raw_strings.items()) or "-",
            sha256(juku1_raw_candidate),
        ]
    )

    lines = [
        "# BASIC disk extraction",
        "",
        "Status: **BASIC DISK FILES EXTRACTED**",
        "",
        "This generated report extracts BASIC-relevant CP/M files from the",
        "vendored Arti Juku disk images. The directory-backed extractor uses the",
        "visible directory window at `0x5000`, 4 KiB allocation blocks, a",
        "four-side-track system area, and the `TRANS` sector order from",
        "`ref/ekdos-source/EKDOS30.ASM`.",
        "",
        "## Generated artifacts",
        "",
        table_row(["Path", "Source", "SHA256"]),
        table_row(["---", "---", "---"]),
        table_row([rel(jukprog2_jbasic_path), "`JUKPROG2.CPM` directory `JBASIC.COM`", sha256(jukprog2_jbasic)]),
        table_row([rel(juku1_raw_candidate_path), "`JUKU1.CPM` raw candidate at `0x67000`", sha256(juku1_raw_candidate)]),
        "",
        "## Extraction checks",
        "",
        table_row(["Disk", "Source", "Name", "Bytes", "Blocks", "First bytes", "Strings", "SHA256"]),
        table_row(["---", "---", "---", "---:", "---", "---", "---", "---"]),
    ]
    for row in rows:
        row = row[:2] + [f"`{row[2]}`"] + row[3:5] + [f"`{row[5]}`", row[6], row[7]]
        lines.append(table_row(row))

    lines.extend(
        [
            "",
            "## Disposition",
            "",
            "- `JUKPROG2_JBASIC.COM` is the best current directory-backed disk BASIC",
            "  executable candidate. It has a CP/M-style jump header and is suitable",
            "  for the next EKDOS command-launch probe.",
            "- The `JUKU1.CPM` directory entry for `JBASIC.COM` remains important",
            "  catalog evidence, but this extractor maps it to erased bytes. The raw",
            "  candidate at `0x67000` has a CP/M jump header plus `BASIC`, `READY`,",
            "  and `ERROR` strings, so it is preserved separately and explicitly",
            "  marked as a candidate.",
            "- This report does not claim a BASIC prompt yet; it creates stable",
            "  inputs for the prompt oracle work.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
