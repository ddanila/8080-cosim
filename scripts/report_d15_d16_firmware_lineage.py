#!/usr/bin/env python3
"""Guard the distinct factory, archival, functional, and physical D15/D16 claims."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "d15-d16-firmware-lineage.md"
PHOTO = ROOT / "ref/photos/juku-pcb-2/PXL_20260519_201900001.jpg"
CENSUS = ROOT / "ref/juku-official-009-ic-census.json"
ARCHIVE_LOW = ROOT / "ref/firmware/JUKUROM0.HEX"
ARCHIVE_HIGH = ROOT / "ref/firmware/JUKUROM1.HEX"

EXPECTED = {
    "ref/photos/juku-pcb-2/PXL_20260519_201900001.jpg": "f293afb2a59467ab56f7e9da5256972c3f4eba50a691de04de7396b9b938d889",
    "ref/juku-official-009-ic-census.json": "473e882082d369136211f37b0d7eb04438f7405408f81d8ad0a8ca1623f38125",
    "ref/firmware/JUKUROM0.HEX": "d6c4ec7418f05e5761ef450e6ee36fb2579d65d9cbf87dce265eaf1c0d077596",
    "ref/firmware/JUKUROM1.HEX": "35b348ae7c88dc8cb24d1bc9d62a06212fdc2c2f601eddf8e00b233893d92817",
    "roms/ekta24.bin": "e1bd9894134ee4085c14bde854780539d3b1e03cfc032c81ec352729e9d69287",
    "roms/ekta31.bin": "26f1f4161a547ea60312a250bde9df41c0b07a939c0b880628050eaec18ec4e4",
    "roms/ekta32.bin": "1826563e23b5d8bc23c61694ceccb923d6a31778077934ad0338772070671122",
    "roms/ekta35.bin": "e8fe5e657037b8f3203f57512cd01cc35f7eaa2a3f0dae8d0ae19378908bd518",
    "roms/ekta37.bin": "fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27",
    "roms/ekta43.bin": "39e3ca8978b369632d03c658300654445b898139009f188cb154e2f901238ba7",
    "roms/jmon22.bin": "1b68f89ae4355391f434b3fae34e95cb4b150bf4bbcb967b5b177d48cd390589",
    "roms/jmon33.bin": "ce9e9c63abbb1780566423a871081bd0bf048a2f3c79e370b465ea9869ff51b8",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"D15/D16 lineage check: {message}")


def mismatch_count(left: bytes, right: bytes) -> int:
    require(len(left) == len(right), "mismatch comparison has unequal sizes")
    return sum(a != b for a, b in zip(left, right))


def main() -> int:
    for relative, expected in EXPECTED.items():
        path = ROOT / relative
        require(path.is_file(), f"missing {relative}")
        require(digest(path.read_bytes()) == expected, f"hash changed for {relative}")

    census = json.loads(CENSUS.read_text())
    programs = {entry["refs"][0]: entry.get("program") for entry in census["rows"]}
    require(programs.get("D15") == "ДГШ5.106.087", "factory D15 program changed")
    require(programs.get("D16") == "ДГШ5.106.041", "factory D16 program changed")

    low = ARCHIVE_LOW.read_bytes()
    high = ARCHIVE_HIGH.read_bytes()
    require(len(low) == 8192 and len(high) == 8192, "archival pair is not 8 KiB + 8 KiB")
    archival = low + high
    require(archival == (ROOT / "roms/ekta37.bin").read_bytes(), "JUKUROM0/1 no longer concatenate to ekta37")

    candidates = []
    for relative in sorted(key for key in EXPECTED if key.startswith("roms/")):
        data = (ROOT / relative).read_bytes()
        require(len(data) == 16384, f"{relative} is not 16 KiB")
        candidates.append((Path(relative).name, digest(data), mismatch_count(low, data[:8192]), mismatch_count(high, data[8192:]), data == archival))
    require(sum(exact for *_, exact in candidates) == 1, "archival pair lacks one unique candidate match")

    lines = [
        "# D15/D16 firmware lineage", "",
        "Status: **ARCHIVAL EKTA 3.7 IDENTITY PROVED / FITTED CONTENTS STILL PENDING**", "",
        "This generated audit keeps four different evidence claims separate. The",
        "factory parts list names programmed drawings, the preservation archive",
        "contains two raw 8 KiB programmer files, the replica uses a boot-validated",
        "functional image, and the owner photographs show the fitted package bodies.",
        "Only the archival and functional byte streams can presently be joined.", "",
        "## Command", "", "```sh", "python3 scripts/report_d15_d16_firmware_lineage.py", "```", "",
        "## Exact archival identity", "",
        "`ref/firmware/JUKUROM0.HEX` and `JUKUROM1.HEX` are raw binary despite",
        "their suffixes. They are exactly 8,192 bytes each and concatenate",
        "byte-for-byte to `roms/ekta37.bin` (SHA256",
        f"`{digest(archival)}`). No byte conversion, interleave, inversion, or",
        "address permutation is involved.", "",
        "| Candidate | SHA256 | D15/low mismatches | D16/high mismatches | Exact pair |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for name, sha, low_diff, high_diff, exact in candidates:
        lines.append(f"| `{name}` | `{sha}` | {low_diff} | {high_diff} | {'YES' if exact else 'no'} |")
    lines.extend([
        "", "## Evidence layers", "",
        "| Layer | D15 | D16 | What it proves |", "| --- | --- | --- | --- |",
        "| Factory `.009` parts list | `К573РФ5`, `ДГШ5.106.087` | `К573РФ5`, `ДГШ5.106.041` | Intended fitted device and programmed-drawing designations for this assembly revision |",
        "| Preservation archive | `JUKUROM0.HEX`, 8 KiB | `JUKUROM1.HEX`, 8 KiB | An exact preserved EktaSoft 3.7 low/high pair; filenames contain no refdes or factory drawing number |",
        "| Replica functional images | `d15_ekta37_low.bin` | `d16_ekta37_high.bin` | Deterministic burnable images already guarded by boot/cosim checks |",
        "| Owner overview photo | ST `M2764AF1`, windowed and socketed | ST `M2764AF1`, windowed and socketed | Physical package class and population only; neither window has a content-identifying sticker |",
        "", "The owner overview is checksum-pinned as",
        f"`ref/photos/juku-pcb-2/{PHOTO.name}` (`{digest(PHOTO.read_bytes())}`).",
        "The two populated EPROMs are visible at the upper-left of the component",
        "field; their printed ST/M2764AF1 markings are legible, while their quartz",
        "windows are uncovered. This is compatible with the replica's 2764 choice",
        "but cannot identify bytes, version, or factory program number.", "",
        "## Bounded conclusion", "",
        "- The previously loose `JUKUROM0/1` provenance is now closed to one",
        "  unique repository image: EktaSoft 3.7.",
        "- The evidence does **not** establish that `ДГШ5.106.087/.041` are the",
        "  two halves of EktaSoft 3.7. No surviving cross-reference binds those",
        "  drawing numbers to the archival filenames or bytes.",
        "- The evidence also does **not** establish that the photographed D15/D16",
        "  contain EktaSoft 3.7. Package markings do not encode programmed content.",
        "- EktaSoft 3.7 belongs to the direct-bus/NOP family proved in",
        "  `docs/fdc-bus-polarity.md`. That makes it electrically consistent with",
        "  the recovered `.009` D93 bus, but does not explain the historical CMA",
        "  family or elevate the owner board to a content-verified Ekta 3.7 unit.",
        "- Repeat reads of both physical EPROMs remain the decisive fitted-profile",
        "  test. Original `.087/.041` programming media are separately required to",
        "  identify the factory designations' byte contents.", "",
    ])
    REPORT.write_text("\n".join(lines))
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("D15-D16-FIRMWARE-LINEAGE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
