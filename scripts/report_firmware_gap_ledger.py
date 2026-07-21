#!/usr/bin/env python3
"""Generate the firmware/PROM gap ledger."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "firmware-gap-ledger.md"
EXPECTED_SHA256 = {
    "ref/physical-proms/validated/d2_037.raw.bin": "953be4bf899e02f0885ecef53e4f9d26469b8d78ceea87394aa35cd28df0255b",
    "ref/physical-proms/validated/d6_038.raw.bin": "c07ba671c4a75c35e1265e370a4fed4b82d1cd423859b5c56bc6cbc6572a9489",
    "ref/physical-proms/validated/d8_039.raw.bin": "345b67e66562741dd48e70f30e7862d4e3fc19d3a113f21c999d6ec497af59cc",
    "ref/physical-proms/validated/d94_092.raw.bin": "bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0",
    "ref/eprom-images/d15_ekta37_low.bin": "d6c4ec7418f05e5761ef450e6ee36fb2579d65d9cbf87dce265eaf1c0d077596",
    "ref/eprom-images/d16_ekta37_high.bin": "35b348ae7c88dc8cb24d1bc9d62a06212fdc2c2f601eddf8e00b233893d92817",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def reconstructed_cell(path: str, expected_size: int) -> tuple[str, bool]:
    artifact = ROOT / path
    if not artifact.exists():
        return "missing", False
    digest = sha256(artifact)
    image_ok = (
        artifact.stat().st_size == expected_size
        and digest == EXPECTED_SHA256[path]
    )
    return f"`{path}` ({artifact.stat().st_size} bytes, SHA256 `{digest}`)", image_ok


def marker(path: str, *needles: str) -> bool:
    text = read(path)
    return all(needle in text for needle in needles)


def main() -> int:
    d2_cell, d2_image_ok = reconstructed_cell(
        "ref/physical-proms/validated/d2_037.raw.bin", 256
    )
    d6_cell, d6_ok = reconstructed_cell(
        "ref/physical-proms/validated/d6_038.raw.bin",
        256,
    )
    d8_cell, d8_ok = reconstructed_cell(
        "ref/physical-proms/validated/d8_039.raw.bin",
        32,
    )
    d94_cell, d94_image_ok = reconstructed_cell(
        "ref/physical-proms/validated/d94_092.raw.bin", 32
    )
    d15_cell, d15_ok = reconstructed_cell(
        "ref/eprom-images/d15_ekta37_low.bin", 8192
    )
    d16_cell, d16_ok = reconstructed_cell(
        "ref/eprom-images/d16_ekta37_high.bin", 8192
    )
    bios = ROOT / "roms/ekta37.bin"
    d15 = ROOT / "ref/eprom-images/d15_ekta37_low.bin"
    d16 = ROOT / "ref/eprom-images/d16_ekta37_high.bin"
    eprom_roundtrip_ok = (
        d15_ok
        and d16_ok
        and bios.exists()
        and d15.read_bytes() + d16.read_bytes() == bios.read_bytes()
    )
    eprom_report_ok = marker(
        "docs/eprom-programming-images.md",
        "TIER-1/2 FUNCTIONAL IMAGES READY / PHYSICAL DUMPS PENDING",
        "`U_D15`, `HALF=0`",
        "`U_D16`, `HALF=1`",
        "not dumps of the original D15/D16 devices",
    ) and exists("scripts/export_eprom_pair.py")
    factory_basic = ROOT / "ref/reconstructed-firmware/dgsh5-106-106-d1.bin"
    factory_basic_ok = (
        factory_basic.exists()
        and factory_basic.stat().st_size == 2048
        and sha256(factory_basic) == "2cd7398b167ceebc256614b9de4cd8953b858e4f35722e57723559d990fc80a6"
        and factory_basic.read_bytes() == (ROOT / "roms/jbasic11.bin").read_bytes()[:2048]
        and marker(
            "docs/dgsh5-106-106-rom-table.md",
            "FACTORY 2 KiB IMAGE RECONSTRUCTED / ONE ARCHIVE TYPO CORRECTED",
            "| `021A` | `A1` | `21` | `21` | `21` |",
        )
    )
    d2_text = read("docs/d2-reconstruction-constraints.md")
    d2_ok = (
        "Status: **D2 PHYSICAL TABLE ADOPTED / CONNECTIVITY GUARDED**" in d2_text
        and "D2 raw electrical polarity executes through D30 READY | PASS" in d2_text
        and d2_image_ok
    )
    d94_ok = marker(
        "docs/d94-reconstruction-constraints.md",
        "Status: **D94 PHYSICAL TABLE ADOPTED / CONNECTIVITY GUARDED**",
        "all five address inputs are owner-continuity-closed nets",
        "Minimized active-low equations reproduce all 256 captured bits | PASS",
        "validated/d94_092.raw.bin",
    ) and d94_image_ok
    d8_open_collector_ok = marker(
        "hdl/devices.v",
        "К155РЕ3 outputs are open collector",
        "assign d[bit_index] = (!e_n && !raw[bit_index]) ? 1'b0 : 1'bz;",
    ) and marker(
        "hdl/sim/prom_fallback_tb.v",
        "D8 disabled outputs did not release",
        "D8 row 00 is not one open-collector D4 sink",
    )
    d8_decode_ok = marker(
        "docs/d8-physical-decode.md",
        "Status: **PHYSICAL D8 TABLE MINIMIZED AND EXECUTED**",
        "All 256 captured bits match the equations | PASS",
        "No replacement D8 firmware remains to reconstruct",
    )
    re3_lineage_ok = marker(
        "docs/re3-firmware-inspection.md",
        "D94 `.092`",
        "neither scanned table represents those parts",
    )
    fallback_report_ok = marker(
        "docs/reconstructed-prom-fallbacks.md",
        "HISTORICAL D8 FALLBACK RETAINED / PHYSICAL PROM TABLES ADOPTED",
        "c07ba671c4a75c35e1265e370a4fed4b82d1cd423859b5c56bc6cbc6572a9489",
        "bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0",
    )
    rt4_validator_ok = marker(
        "docs/rt4-dump-acquisition.md",
        "READER-3 CONTROL VALIDATED / D6 CHANNEL ORDER CORRECTED",
        "revision-3 reread",
        "*.raw.bin",
        "D94 `.092` requires a",
        "separate К155РЕ3 reader",
    ) and exists("scripts/validate_rt4_dump.py")
    re3_validator_ok = marker(
        "docs/prom-dump-procedure.md",
        "scripts/validate_re3_dump.py",
        "Raw levels are the authoritative dump",
        "repeat-mismatched RE3 rows",
    ) and exists("scripts/validate_re3_dump.py") and exists("tools/re3_dumper/re3_dumper.ino")
    d6_top = read("hdl/juku_top.v")
    d6_runnable_physical_ok = all(
        needle in d6_top
        for needle in (
            "decode_prom U_DECODE",
            "wire        rom_sel_n = d6_rom_select_n;",
            "wire        roe_n     = d6_roe_physical;",
            "Functional decode oracle retired from the boot path",
        )
    ) and "decode_prom_functional U_" not in d6_top
    d6_open_collector_ok = marker(
        "hdl/devices.v",
        "К556РТ4 outputs are open collector",
        "assign d[bit_index] = (!v_en_n && !raw[bit_index]) ? 1'b0 : 1'bz;",
    ) and marker(
        "hdl/sim/prom_fallback_tb.v",
        "D6 disabled outputs did not release",
        "D6 row 00 is not raw open-collector word 1",
    )
    d94_runnable_physical_ok = all(
        needle in d6_top
        for needle in (
            "Runnable behavioral core consumes the physical .092 PROM strobes",
            "wire fdc_model_re_n = fdc_prom_re_n;",
            "wire fdc_model_we_n = fdc_prom_we_n;",
        )
    )
    all_physical_proms_runnable_ok = all(
        needle in d6_top
        for needle in (
            "wait_prom_037 U_D2",
            "re3_prom  U_D8",
            "decode_prom U_DECODE",
            "re3_prom_092 U_D94",
            "wire fdc_model_cs_n = fdc_prom_cs_n;",
            "wire fdc_model_re_n = fdc_prom_re_n;",
            "wire fdc_model_we_n = fdc_prom_we_n;",
        )
    ) and "decode_prom_functional U_" not in d6_top

    rows = [
        [
            "D2",
            "К556РТ4",
            "`ДГШ5.106.037`",
            "READY/bus-control PROM",
            d2_cell,
            "`docs/d2-reconstruction-constraints.md`; `docs/d2-physical-dump-and-continuity.md`",
            "programming-disk comparison or independent future read",
        ],
        [
            "D6",
            "К556РТ4",
            "`ДГШ5.106.038`",
            "memory decode PROM",
            d6_cell,
            "`ref/physical-proms/README.md`",
            "revision-3 reader capture is adopted; programming-disk comparison or independent read is Tier-3 corroboration",
        ],
        [
            "D8",
            "К155РЕ3",
            "`ДГШ5.106.039`",
            "ROM-socket pager PROM",
            d8_cell,
            "`ref/physical-proms/README.md`",
            "programming-disk comparison or independent future read",
        ],
        [
            "D94",
            "К155РЕ3",
            "`ДГШ5.106.092`",
            "FDC control/decode PROM",
            d94_cell,
            "`docs/d94-reconstruction-constraints.md`",
            "programming-disk comparison plus the shared-enable and equation-targeted D0 hidden-branch probes; the guarded D29.4/IORD recheck is optional corroboration, while R87-R89 and D4-D7/D104.10 are owner/drawing-closed",
        ],
        [
            "D15",
            "M2764/2764",
            "repository EktaSoft BIOS split",
            "BIOS low 8 KiB",
            d15_cell,
            "`docs/eprom-programming-images.md`",
            "repeat physical D15 dump for Tier-3 truth",
        ],
        [
            "D16",
            "M2764/2764",
            "repository EktaSoft BIOS split",
            "BIOS high 8 KiB",
            d16_cell,
            "`docs/eprom-programming-images.md`",
            "repeat physical D16 dump for Tier-3 truth",
        ],
    ]

    checks = [
        ("D2 validated physical raw image has exact size and SHA256", d2_image_ok),
        ("D6 validated physical raw image has exact size and SHA256", d6_ok),
        ("D8 validated physical raw image has exact size and SHA256", d8_ok),
        ("D8 physical table executes as open-collector socket selects", d8_open_collector_ok),
        ("D8 physical table has exhaustive minimized socket-select equations", d8_decode_ok),
        ("D94 validated physical raw image has exact size and SHA256", d94_image_ok),
        ("D15 functional image has exact size and SHA256", d15_ok),
        ("D16 functional image has exact size and SHA256", d16_ok),
        ("D15+D16 round-trip exactly to roms/ekta37.bin", eprom_roundtrip_ok),
        ("D15/D16 split and non-dump provenance are documented", eprom_report_ok),
        ("Factory .106.106 BASIC page is reconstructed and photo-adjudicated", factory_basic_ok),
        ("D2 physical table and continuity are guarded", d2_ok),
        ("D2 open-collector raw polarity executes through the D30 READY latch", d2_ok),
        ("D6 corrected physical table drives runnable selection directly", d6_runnable_physical_ok),
        ("D6 physical table preserves open-collector release", d6_open_collector_ok),
        ("D94 physical table is adopted while continuity stays guarded", d94_ok),
        ("D94 physical table drives runnable FDC read/write strobes under guarded upstream fits", d94_runnable_physical_ok),
        ("Runnable top executes all four physical small-PROM tables without a functional PROM stand-in", all_physical_proms_runnable_ok),
        (".113/.117 RE3 scans are guarded as not D8/D94", re3_lineage_ok),
        ("Historical fallback report adopts all physical PROM tables", fallback_report_ok),
        ("Repeated RT4 dump validation procedure is available", rt4_validator_ok),
        ("Repeated RE3 dump validation procedure is available", re3_validator_ok),
    ]
    status = (
        "BURNABLE SET VERIFIED / TIER-3 CORROBORATION PENDING"
        if all(ok for _, ok in checks)
        else "FIRMWARE GAP LEDGER FAILED"
    )

    lines = [
        "# Firmware gap ledger",
        "",
        f"Status: **{status}**",
        "",
        "This generated ledger is the single-page burnability view for the",
        "small PROMs that still matter to replica and Tier-3 preservation work.",
        "It separates boot-validated functional EPROM images from dumped factory",
        "PROM truth. Every populated device has an exact-hash-guarded burnable",
        "repository image for Tier 1/2. Programming-disk files, independent PROM",
        "reads, and original D15/D16 reads remain Tier-3 corroboration and win",
        "if a stable difference appears.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_firmware_gap_ledger.py",
        "```",
        "",
        "## PROM Matrix",
        "",
        "| Ref | Part | Programmed drawing | Role | Burnable repository image | Guard | Next truth source |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(table_row(row) for row in rows)
    lines.extend(
        [
            "",
            "## Evidence Checks",
            "",
            "| Check | Result |",
            "| --- | --- |",
        ]
    )
    lines.extend(table_row([name, "PASS" if ok else "FAIL"]) for name, ok in checks)
    lines.extend(
        [
            "",
            "## Practical Burn Rule",
            "",
            "- D2, D6, D8, and D94 have validated physical raw tables; D15/D16",
            "  still use the deterministic `ekta37` EPROM split.",
            "- Reader-3 reproduced D2 byte-for-byte across three captures including a",
            "  power cycle. Three equally stable D6 reads then proved the old artifact",
            "  had all four output channels reversed; socket continuity and the full",
            "  boot guard adopt the corrected direct table.",
            "- D15/D16 are deterministic Tier-1/2 functional images, not physical",
            "  device dumps. Program them as low/high 8 KiB respectively and",
            "  retain programmer verification records.",
            "- The printed `.106.106` 2 KiB BASIC table is reconstructed separately;",
            "  its sole BAS0/JBASIC disagreement at `021A` is photo-adjudicated as `21`,",
            "  yielding an exact match to the first page of `roms/jbasic11.bin`.",
            "- Never substitute the older D2-as-I/O-decode behavioral table; D9 is",
            "  the chip-select decoder and D2 is the separate `.037` READY/wait PROM.",
            "- Do not substitute the guarded `.113/.117` RE3 scans for D8 `.039`",
            "  or D94 `.092`; they are lineage evidence, not matching processor",
            "  module programming tables.",
            "- D94 content and all A0-A4 input destinations are owner-closed. Its",
            "  physical table now drives the runnable FDC `/RE` and `/WE` inputs;",
            "  A3 already consumes the owner-closed D105.3 qualified `/WR` conductor.",
            "  The decoded enable and pulled-high A4 runtime behavior remain explicit",
            "  simulation fits rather than claimed functional closure. The shared",
            "  enable source and D0 hidden load remain unresolved",
            "  connectivity boundaries and still block an FDC hardware release.",
            "",
            "## Required External Closure",
            "",
            "- Locate the Baltijets programming-disk files referenced by doc 007.",
            "- Compare the validated D2/D6 tables against Baltijets programming files",
            "  if recovered; use it as independent corroboration of D8/D94 as well.",
            "- Validate D2/D6 serial captures with `scripts/validate_rt4_dump.py`;",
            "  preserve raw pin-level and active-low asserted tables separately.",
            "- Preserve future D2/D6 corroboration with the reader-3 metadata and",
            "  independent enable-release checks documented in `docs/rt4-dump-acquisition.md`.",
            "- Preserve future D8/D94 serial captures with `scripts/validate_re3_dump.py`;",
            "  the adopted D94 table still requires shared-enable and D0-load closure.",
            "- Repeatedly read physical D15/D16 and compare their concatenation",
            "  with `roms/ekta37.bin`; preserve any stable mismatch as a variant.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {rel(REPORT)}")
    return 0 if status.startswith("BURNABLE SET VERIFIED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
