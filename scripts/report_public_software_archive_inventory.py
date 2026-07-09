#!/usr/bin/env python3
"""Generate a classified inventory of public Juku software archives."""
from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "public-software-archive-inventory.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


ARTI_ROWS = [
    ("EKDOS30.ASM", "14.0 KiB", "2020-09-15", "vendored", "ref/ekdos-source/EKDOS30.ASM", "EKDOS source inspected for FDC/media constants"),
    ("EKDOSSRC.7Z", "5.7 KiB", "2020-09-15", "covered", "ref/ekdos-source/", "source payload represented by extracted `EKDOS30.ASM` and `axb.asm`"),
    ("JUKU1.7Z", "174.3 KiB", "2020-09-15", "vendored", "media/disks/JUKU1.CPM", "factory EKDOS boot disk; cosim and HDL prompt guards"),
    ("JUKU2.7Z", "899.9 KiB", "2020-09-15", "vendored", "media/disks/JUKGAME1.CPM, JUKPROG1.CPM, JUKPROG2.CPM, JUKPROGX.CPM", "companion disks; `JUKPROG2.CPM` drives disk BASIC guard"),
    ("JUKU2.CPM", "800.0 KiB", "2020-09-15", "covered", "media/disks/JUKGAME1.CPM", "same public disk family as extracted `JUKU2.7Z` contents"),
    ("README.html", "1021 B", "2020-09-15", "documented", "docs/public-software-archive-inventory.md", "archive description, no binary payload needed"),
    ("axb.asm", "8.4 KiB", "2020-09-15", "vendored", "ref/ekdos-source/axb.asm", "companion BIOS skeleton/reference"),
    ("juku_e5101_kryoflux.rar", "5.1 MiB", "2020-09-15", "optional", "-", "flux preservation source; not needed for raw-image FDC or board truth"),
    ("juku_e5101_kyf_repair.rar", "607.4 KiB", "2020-09-15", "optional", "-", "repair/flux preservation source; not needed for current guards"),
    ("juku_e5101_part01.rar", "2.0 MiB", "2020-09-15", "optional", "-", "software collection, not hardware/PROM-critical"),
    ("juku_e5101_part02.rar", "10.4 MiB", "2020-09-15", "optional", "-", "software collection, not hardware/PROM-critical"),
    ("juku_e5101_part02_ekdos_repair.rar", "1.7 MiB", "2020-09-15", "optional", "-", "repair software collection, not hardware/PROM-critical"),
]


MUSEUM_ROWS = [
    ("CASTOOLS.JUK", "800 KiB", "2026-03-31", "optional", "-", "classroom/user disk; no board/PROM dependency identified"),
    ("EMUSYS1.JUK", "800 KiB", "2024-11-14", "optional", "-", "emulator/system disk, not used by current guards"),
    ("EMUSYS2.JUK", "800 KiB", "2024-11-14", "optional", "-", "emulator/system disk, not used by current guards"),
    ("EMUSYS3.JUK", "800 KiB", "2024-11-14", "optional", "-", "emulator/system disk, not used by current guards"),
    ("HEIKITAPE.ZIP", "432102 KiB", "2025-08-14", "defer-large", "-", "large tape capture archive; outside current disk/board proof"),
    ("INDY.ZIP", "36 KiB", "2024-11-14", "optional", "-", "game package; inspected, not board/PROM-critical"),
    ("J3KGAME1.JUK", "800 KiB", "2024-12-31", "optional", "-", "game disk"),
    ("J3KGAME2.JUK", "800 KiB", "2026-01-14", "optional", "-", "game disk"),
    ("J3KUTIL4.JUK", "800 KiB", "2025-01-11", "vendored", "media/disks/J3KUTIL4.JUK", "EKDOS 2.30 prompt provenance disk used by earlier FDC probe"),
    ("JUKGAME1.JUK", "800 KiB", "2024-11-14", "covered", "media/disks/JUKGAME1.CPM", "same named companion disk from Arti `JUKU2.7Z`"),
    ("JUKPROG1.JUK", "800 KiB", "2024-11-14", "covered", "media/disks/JUKPROG1.CPM", "same named companion disk from Arti `JUKU2.7Z`"),
    ("JUKPROG2.JUK", "800 KiB", "2024-11-14", "covered", "media/disks/JUKPROG2.CPM", "same named companion disk from Arti `JUKU2.7Z`; disk BASIC guard"),
    ("JUKPROGX.JUK", "800 KiB", "2024-11-14", "covered", "media/disks/JUKPROGX.CPM", "same named companion disk from Arti `JUKU2.7Z`"),
    ("JUKUROMS.ZIP", "94 KiB", "2026-01-15", "covered-identical", "roms/", "inspected; contains only the nine canonical ROM files already vendored byte-identically"),
    ("JUKUSYS.ZIP", "25 KiB", "2024-11-14", "vendored", "media/system/", "public CP/M/EKDOS system binaries"),
    ("MAALT01.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MAALT02.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MAALT03.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MAALT04.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MAALT05.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MAALT06.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MAALT07.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MAALT08.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MAALT09.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MAALT10.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MAALT11.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MAALT13.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MAALT15.JUK", "800 KiB", "2024-11-29", "optional", "-", "classroom/user disk"),
    ("MAALT18.JUK", "800 KiB", "2024-11-29", "optional", "-", "classroom/user disk"),
    ("MAALT20.JUK", "800 KiB", "2024-11-29", "optional", "-", "classroom/user disk"),
    ("MAALT21.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MAALT22.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MAALT23.JUK", "800 KiB", "2024-11-29", "optional", "-", "classroom/user disk"),
    ("MAALT24.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MAALT25D.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MAALT26.JUK", "818688 B", "2024-11-14", "optional", "-", "non-standard-size classroom/user disk; not needed by current raw 819200-byte guards"),
    ("MAALT27.JUK", "800 KiB", "2024-11-14", "optional", "-", "classroom/user disk"),
    ("MANUALID.ZIP", "26 KiB", "2024-11-14", "optional", "-", "inspected; DBASE/GTR/JCM user docs, not board/PROM-critical"),
    ("MUSEUM01.JUK", "800 KiB", "2024-11-14", "optional", "-", "museum/user disk"),
    ("MUSEUM02.JUK", "800 KiB", "2024-11-14", "optional", "-", "museum/user disk"),
    ("MUSEUM03.JUK", "800 KiB", "2024-11-14", "optional", "-", "museum/user disk"),
    ("MUSEUM04.JUK", "800 KiB", "2024-11-14", "optional", "-", "museum/user disk"),
    ("OKSJON01.JUK", "800 KiB", "2024-11-14", "optional", "-", "auction/user disk"),
    ("OKSJON02.JUK", "800 KiB", "2024-11-14", "optional", "-", "auction/user disk"),
    ("OKSJON03.JUK", "800 KiB", "2024-11-14", "optional", "-", "auction/user disk"),
    ("OKSJON04.JUK", "400 KiB", "2024-11-14", "optional", "-", "single-side auction/user disk"),
    ("OKSJON05.JUK", "400 KiB", "2024-11-14", "optional", "-", "single-side auction/user disk"),
    ("OKSJON06.JUK", "800 KiB", "2024-11-14", "optional", "-", "auction/user disk"),
    ("STEF2.JUK", "800 KiB", "2024-11-29", "optional", "-", "user disk"),
    ("VAKSTU01.JUK", "800 KiB", "2024-12-30", "optional", "-", "user disk"),
    ("VAKSTU05.JUK", "800 KiB", "2024-12-30", "optional", "-", "user disk"),
    ("VAKSTU06.JUK", "800 KiB", "2024-12-30", "optional", "-", "user disk"),
]


REQUIRED_LOCAL = [
    "media/disks/JUKU1.CPM",
    "media/disks/JUKGAME1.CPM",
    "media/disks/JUKPROG1.CPM",
    "media/disks/JUKPROG2.CPM",
    "media/disks/JUKPROGX.CPM",
    "media/disks/J3KUTIL4.JUK",
    "media/system/CPM22.BIN",
    "media/system/CPM231E.BIN",
    "media/system/EKDOS229.BIN",
    "media/system/EKDOS230.BIN",
    "media/system/EKDOSVSW.BIN",
    "roms/ekta24.bin",
    "roms/ekta31.bin",
    "roms/ekta32.bin",
    "roms/ekta35.bin",
    "roms/ekta37.bin",
    "roms/ekta43.bin",
    "roms/jbasic11.bin",
    "roms/jmon22.bin",
    "roms/jmon33.bin",
    "ref/ekdos-source/EKDOS30.ASM",
    "ref/ekdos-source/axb.asm",
]


def emit_inventory(title: str, rows: list[tuple[str, str, str, str, str, str]]) -> list[str]:
    lines = [
        f"## {title}",
        "",
        "| Archive item | Size | Listing date | Disposition | Local evidence | Role |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    lines.extend(table_row([f"`{name}`", size, date, disposition, f"`{local}`" if local != "-" else "-", role]) for name, size, date, disposition, local, role in rows)
    lines.append("")
    return lines


def main() -> int:
    missing = [path for path in REQUIRED_LOCAL if not (ROOT / path).exists()]
    bad_manifest: list[str] = []
    for manifest in ("media/disks/SHA256SUMS", "media/system/SHA256SUMS"):
        text = (ROOT / manifest).read_text(encoding="utf-8")
        for path in REQUIRED_LOCAL:
            if path.startswith(str(Path(manifest).parent)) and Path(path).name not in text:
                bad_manifest.append(f"{manifest} lacks {Path(path).name}")

    j3k = ROOT / "media/disks/J3KUTIL4.JUK"
    j3k_ok = j3k.exists() and j3k.stat().st_size == 819200 and sha256(j3k) == "d7a0b766a00c80ac487e24f48499386249534418ccb42739bae83a9e5a075de3"
    if not j3k_ok:
        bad_manifest.append("J3KUTIL4.JUK size/hash mismatch")

    roms_ok = all((ROOT / path).exists() for path in REQUIRED_LOCAL if path.startswith("roms/"))
    status = "PUBLIC SOFTWARE INVENTORY CLASSIFIED" if not missing and not bad_manifest and roms_ok else "PUBLIC SOFTWARE INVENTORY INCOMPLETE"

    lines = [
        "# Public software archive inventory",
        "",
        "Status date: 2026-07-09.",
        "",
        f"Status: **{status}**",
        "",
        "This generated report classifies the finite public software listings that",
        "matter to the Juku replica work. It distinguishes required/vendored",
        "binary evidence from optional classroom, game, tape, and user-software",
        "preservation inputs. The inventory is intentionally network-free in CI;",
        "the listed rows are the archive state observed on 2026-07-09.",
        "",
        "## Checks",
        "",
        "| Check | Result |",
        "| --- | --- |",
        table_row(["Required local media/ROM/source files exist", "PASS" if not missing else "FAIL"]),
        table_row(["`media/disks/J3KUTIL4.JUK` is vendored with expected 819200-byte hash", "PASS" if j3k_ok else "FAIL"]),
        table_row(["Disk/system manifests include required vendored binaries", "PASS" if not bad_manifest else "FAIL"]),
        table_row(["Museum `JUKUROMS.ZIP` inspected as byte-identical to `roms/` payloads", "PASS" if roms_ok else "FAIL"]),
        "",
        "## Inspected Small Archives",
        "",
        "| Archive | SHA256 | Contents / disposition |",
        "| --- | --- | --- |",
        table_row(["`JUKUROMS.ZIP`", "`e9b8da139a5766ca6a16c100989d8a6c52d2adb882efe6bb3cf79ba8034fc731`", "nine canonical ROM files; every payload hash matched `roms/`"]),
        table_row(["`MANUALID.ZIP`", "`430d9e865fbe3a3c619ca6e7154c443c2a93f738cf9c1b2652173bf4b9992309`", "`DBASE.DOK`, `GTR.DOK`, `GTRLISA.DOK`, `JCM.DOK`; optional user docs"]),
        table_row(["`INDY.ZIP`", "`e01145360b8e6a033f1da3311bd8cb42ec993adb6c365b8c0ebe53a73a3ea891`", "game package; optional user software"]),
        "",
    ]
    lines.extend(emit_inventory("Arti `tarkvara/` Listing", ARTI_ROWS))
    lines.extend(emit_inventory("Elektroonikamuuseum `tarkvara/` Listing", MUSEUM_ROWS))
    lines.extend(
        [
            "## Disposition",
            "",
            "- Required binary/media inputs for current board, ROM, EKDOS, FDC, and",
            "  BASIC guards are now vendored under `roms/`, `media/disks/`,",
            "  `media/system/`, and `ref/ekdos-source/`.",
            "- `J3KUTIL4.JUK` is now vendored because earlier docs cite it as the first",
            "  external EKDOS prompt proof; `JUKU1.CPM` remains the stronger factory",
            "  `TDD` boot guard.",
            "- Museum `JUKUROMS.ZIP` does not add new ROM bytes; it is a packaging copy",
            "  of the already-vendored canonical ROM set.",
            "- The remaining unvendored `.JUK` files are user/classroom/game disks.",
            "  They are useful for Tier 2/Tier 3 software preservation, but no current",
            "  PCB, PROM, FDC, EKDOS, Monitor 3.3, or BASIC launch proof depends on",
            "  them.",
            "- The large tape/flux archives stay deferred until tape/flux preservation",
            "  becomes an active workstream.",
            "",
        ]
    )
    if missing or bad_manifest:
        lines.extend(["## Failures", ""])
        lines.extend(f"- missing `{path}`" for path in missing)
        lines.extend(f"- {item}" for item in bad_manifest)
        lines.append("")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if status == "PUBLIC SOFTWARE INVENTORY CLASSIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
