#!/usr/bin/env python3
"""Generate the short physical-owner measurement/dump list."""
from __future__ import annotations

import json
from collections import Counter
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "owner-measurement-shortlist.md"
BOARD_JSON = ROOT / "kicad" / "juku.board.json"

REQUIRED = [
    BOARD_JSON,
    ROOT / "docs" / "community-prom-media-request.md",
    ROOT / "docs" / "prom-dump-procedure.md",
    ROOT / "docs" / "d2-reconstruction-constraints.md",
    ROOT / "docs" / "d94-reconstruction-constraints.md",
    ROOT / "docs" / "fdc-hardware-handoff.md",
    ROOT / "docs" / "beeper-readiness.md",
    ROOT / "docs" / "serial-handoff.md",
    ROOT / "docs" / "decap-value-fidelity.md",
    ROOT / "docs" / "d41-timing-boundary.md",
    ROOT / "docs" / "memory-timing-boundary.md",
    ROOT / "docs" / "io-decode-boundary.md",
    ROOT / "docs" / "video-analog-boundary.md",
    ROOT / "docs" / "s4-interrupt-boundary.md",
    ROOT / "docs" / "unmodeled-footprint-inventory.md",
    ROOT / "docs" / "replica-bringup-verification-points.md",
    ROOT / "docs" / "reconstructed-prom-fallbacks.md",
    ROOT / "docs" / "source-coverage-audit.md",
    ROOT / "docs" / "cartridge-basic-boundary.md",
    ROOT / "docs" / "assembly-drawing-extraction.md",
    ROOT / "docs" / "factory-modification-disposition.md",
    ROOT / "docs" / "source-pcb-drc.md",
]

FDC_SUPPORT_REFS = {"D28", "D95", "D96", "D97", "D98", "D99", "D101", "D102", "D106"}
PIN_CLOSURE_REFS = {"D2", "D3", "D10", "D11", "D35", "D41", "D53", "D59", "D93", "D94", "D100", "S4"} | FDC_SUPPORT_REFS


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def marker(path: Path, text: str) -> bool:
    return path.exists() and text in read(path)


def table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells:
            rows.append(cells)
    return rows


def bringup_categories() -> Counter[str]:
    text = read(ROOT / "docs" / "replica-bringup-verification-points.md")
    counts: Counter[str] = Counter()
    in_checklist = False
    for row in table_rows(text):
        if row[:2] == ["Net", "Category"]:
            in_checklist = True
            continue
        if not in_checklist or len(row) < 5:
            continue
        counts[row[1]] += 1
    return counts


def failed_d94_checks() -> list[str]:
    text = read(ROOT / "docs" / "d94-reconstruction-constraints.md")
    failures: list[str] = []
    for row in table_rows(text):
        if len(row) >= 3 and row[1] == "FAIL":
            failures.append(row[0])
    return failures


def inline(text: str) -> str:
    return text.replace("`", "")


def has_phrase(path: str, phrase: str) -> str:
    return "PASS" if marker(ROOT / path, phrase) else "MISSING"


def pin_sort_key(item: tuple[str, object]) -> object:
    pin = str(item[0])
    return int(pin) if pin.isdigit() else pin


def unnetted_pin_closure_rows() -> list[tuple[str, str, str]]:
    board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    netted: dict[str, set[str]] = defaultdict(set)
    for net in board["nets"].values():
        for ref, pin in net.get("nodes", []):
            netted[str(ref)].add(str(pin))
    intentional_nc = {(str(ref), str(pin)) for ref, pin in board.get("no_connects", [])}

    rows = []
    for chip in board["chips"]:
        ref = str(chip.get("ref", ""))
        if ref not in PIN_CLOSURE_REFS:
            continue
        missing = [
            f"{pin}:{signal}"
            for pin, signal in sorted(chip.get("pins", {}).items(), key=pin_sort_key)
            if str(pin) not in netted.get(ref, set()) and (ref, str(pin)) not in intentional_nc
        ]
        if not missing:
            continue
        if ref == "D2":
            evidence = "dump/programming disk plus sheet-1 continuity"
        elif ref == "D94":
            evidence = "A0-A4 input, enable, and output continuity; physical .092 table is already validated"
        elif ref in {"D10", "D93", "D100"} | FDC_SUPPORT_REFS:
            evidence = "continuity from an actual `.009` FDC-populated board"
        elif ref == "D11":
            evidence = "sheet-1 continuity plus `docs/serial-handoff.md`"
        elif ref in {"D35", "D41", "D59"}:
            evidence = "sheet-2 timing-chain continuity"
        elif ref == "D3":
            evidence = "sheet-1 serial/interrupt continuity or source-proved NC"
        elif ref == "D53":
            evidence = "sheet-2 memory-timing continuity or source-proved NC"
        elif ref == "S4":
            evidence = "`docs/s4-interrupt-boundary.md` plus sheet-1/SB switch continuity"
        else:
            evidence = "sheet-1/SB switch continuity"
        rows.append((ref, ", ".join(missing), evidence))
    return sorted(rows)


def main() -> int:
    missing = [path for path in REQUIRED if not path.exists()]
    d94_failures = failed_d94_checks() if not missing else []
    categories = bringup_categories() if not missing else Counter()
    pin_closure_rows = unnetted_pin_closure_rows() if not missing else []

    checks = [
        ("Community request packet ready", has_phrase("docs/community-prom-media-request.md", "Status: **READY TO SEND**")),
        ("PROM dump procedure exists", has_phrase("docs/prom-dump-procedure.md", "Bipolar PROMs")),
        ("Physical D2/D6/D8/D94 tables are guarded", has_phrase("docs/reconstructed-prom-fallbacks.md", "PHYSICAL PROM TABLES ADOPTED")),
        ("D2 constraint report generated", "PASS" if marker(ROOT / "docs/d2-reconstruction-constraints.md", "Status: **D2 PHYSICAL TABLE ADOPTED / CONNECTIVITY GUARDED**") else "MISSING"),
        ("D30 section-B continuity closure guarded", has_phrase("docs/d30-section-b-scan-chase.md", "Status: **OWNER CONTINUITY CLOSED / OLDER SCAN AMBIGUITY RETAINED**")),
        ("D94 constraint report generated", has_phrase("docs/d94-reconstruction-constraints.md", "Status: **D94 PHYSICAL TABLE ADOPTED / CONNECTIVITY GUARDED**")),
        ("FDC hardware handoff generated", has_phrase("docs/fdc-hardware-handoff.md", "Status: **BUS-SIDE GUARDED / OWNER CONTINUITY REQUIRED**")),
        ("Beeper source/handoff guarded", has_phrase("docs/beeper-readiness.md", "Status: **DIGITAL BEEPER SOURCE + BOARD HANDOFF READY**")),
        ("Serial USART behavior guarded", has_phrase("docs/serial-handoff.md", "Status: **SERIAL CORE GUARDED / PHYSICAL LEVELS PENDING**")),
        ("Decap value boundary guarded", has_phrase("docs/decap-value-fidelity.md", "Status: **DECAP CONNECTIVITY GUARDED / PER-POSITION VALUE PENDING**")),
        ("D41 timing connectivity source-closed", has_phrase("docs/d41-timing-boundary.md", "Status: **D41 PACKAGE CONNECTIVITY SOURCE-CLOSED**")),
        ("Memory timing boundary guarded", has_phrase("docs/memory-timing-boundary.md", "Status: **MEMORY TIMING GUARDED / CAS-D56 SOURCE BOUNDARY PENDING**")),
        ("I/O decode boundary guarded", has_phrase("docs/io-decode-boundary.md", "Status: **IO DECODE GUARDED / SMALL SOURCE BOUNDARIES PENDING**")),
        (".009 video / .006 RF disposition guarded", has_phrase("docs/video-analog-boundary.md", "Status: **.009 COMPOSITE HANDOFF GUARDED / .006 RF OPTION DNP**")),
        ("S4 interrupt boundary guarded", has_phrase("docs/s4-interrupt-boundary.md", "Status: **S4 INTERRUPT SELECTOR GUARDED**")),
        ("FDC functional-pin design hold is visible", has_phrase("docs/unmodeled-footprint-inventory.md", "Status: **DESIGN HOLD / FDC FUNCTIONAL PINS UNTRACED**")),
        (
            "Bring-up verification points generated",
            "PASS" if any(
                marker(ROOT / "docs/replica-bringup-verification-points.md", status)
                for status in (
                    "Status: **EVIDENCE INDEX READY / RISKS UNRESOLVED**",
                    "Status: **ENDPOINT COVERAGE FAILED**",
                    "Status: **DESIGN RELEASE RISKS CLOSED**",
                )
            ) else "MISSING",
        ),
        ("Source coverage audit current", has_phrase("docs/source-coverage-audit.md", "Status: **PASS**")),
        ("Cartridge BASIC boundary documented", has_phrase("docs/cartridge-basic-boundary.md", "Status: **ARTIFACT OR DOCUMENTED PROCEDURE REQUIRED**")),
        (".009 assembly drawing extraction guarded", has_phrase("docs/assembly-drawing-extraction.md", "Status: **SHEETS 1-6 AND WIRE-TABLE PIN MAPPING ADOPTED**")),
        ("Factory Вид В modifications guarded", has_phrase("docs/factory-modification-disposition.md", "Status: **FACTORY MODIFICATIONS GUARDED / PAD MAPPING REQUIRED**")),
        ("Source-PCB placement collision gate passes", has_phrase("docs/source-pcb-drc.md", "Status: **PASS**") and has_phrase("docs/source-pcb-drc.md", "Unique colliding pad/item pairs: `0`")),
    ]
    failed_checks = [name for name, state in checks if state != "PASS"]

    priority_rows = [
        (
            "P0",
            "programming disk / PROM truth",
            "Baltijets doc 007 programming files; physical dumps of D15/D16 EPROMs; independent future D2/D6/D8/D94 reads only as corroboration of the validated captures",
            "`docs/community-prom-media-request.md`; `docs/prom-dump-procedure.md`; `docs/d2-reconstruction-constraints.md`",
            "cross-checks all four validated physical PROM tables and supplies missing Tier-3 EPROM truth",
        ),
        (
            "P2",
            "JUKU-1 media provenance",
            "independent `JUKU-1` / `ДГШ5.106.105` disk image or checksum/provenance for `media/disks/JUKU1.CPM`",
            "`docs/community-prom-media-request.md`; `docs/ekdos-media-acquisition.md`",
            "turns the public EKDOS boot image into stronger physical-media evidence",
        ),
        (
            "P2",
            "cartridge BASIC truth",
            "larger/different removable-memory BASIC cartridge image, programming artifact, or hardware-confirmed Monitor 3.3 launch procedure to BASIC `READY`",
            "`docs/community-prom-media-request.md`; `docs/cartridge-basic-boundary.md`",
            "closes the remaining Monitor 3.3 cartridge BASIC compatibility boundary",
        ),
        (
            "P0",
            "D94 .092 continuity",
            "first test D94.13/D104.7 continuity to D5.27 IOWR; if open, simultaneously scope D94.13 and active-low IOWR during known FDC reads/writes. The physical table requires equal levels on those cycles (firmware-derived functional prediction, not copper proof). Also identify the pull-up resistors on D94.13-D104.7, D94.14-D101.7, and D94.1; trace D104.10 and D5-D7 far destinations (D4/pin5 is photo-closed to the internally NC/back-bias D93.1 socket contact). The minimized table proves D101.Q0/A4 is exactly a register-3 transfer-steering qualifier: at BA1:BA0=11, A4 low asserts D94.1 independently of A3/A2 and releases D93 /RE and /WE, while A4 high restores the normal D93 strobe. Scope D101.7, D94.1, /RE, and /WE together on port 1F data transfers; do not infer D0's load. Later recheck D29.4-D7.8, D29.4-D29.8, and D29.8-D27.5 because direct continuity places D94.12/D27.5/D29.4 on IORD contrary to the older IOM_STATUS scan interpretation",
            "`docs/d94-reconstruction-constraints.md`; `docs/photo-registration.md`; exact two-sided local-fit rows in `ref/photos/juku-pcb-2/endpoints.csv`",
            "uses the recovered PROM equations to target D0's hidden branch, replaces the retired same-as-D8 BA mapping with measured row semantics, and resolves the read/write control path before an FDC hardware release",
        ),
        (
            "P1",
            "FDC interrupt/buffer continuity",
            "WD1793 DRQ/INTRQ to 8259 inputs, D93 MR/CLK, plus D100 OE/T if accessible",
            "`docs/fdc-hardware-handoff.md`; `docs/replica-bringup-verification-points.md`; `PLAN.md` P0/P1 gates",
            "reduces first EKDOS-on-hardware debug risk",
        ),
        (
            "P0",
            "memory-decode stragglers",
            "find the source or obscured branch on the measured D6.15-D105.1 input-only boundary; D6-removed resistance to both +5V and GND fluctuates around 100-200 kohm, excluding a simple low-value pull. D6.1<-D3.4<-/PC1 and D6.2<-D3.6<-/PC0 are closed. Chip-removed continuity closes D6.12-D8.15 and proves D6.11/D6.12 separate; follow-up continuity closes the combined D2.15/-WREQ-D6.11-D92.5-R12.2 conductor. D13.12-D6.14 continuity plus visually confirmed bottom-layer D6.13-D6.14 copper closes the enable branch; recheck only the surprising D13.12-D16.13 report with D16 removed. The D6.9-D13.1, D13.2-D37.4, D37.6-D58.9 endpoint chain is owner-confirmed, and native sheet 2 separately closes MEMR-D33.3/D33.4-D37.5 as the other D37 NAND input. During the known B37A RAM read scope D6.9, D13.2, D37.6, D58.9, and D58.11. All eight raw A7..A5 rows leave pin9 high at B37A. Still close C99 far plate, the upstream D7.5/D29.3 -INHIB source, and remaining D36 timing feeds. Separately chase D105.3 bundle code 7 and D7.8 code 8; the full-resolution sheet proves those adjacent driven-output risers are distinct and does not junction D29.2 onto either",
            "`docs/d6-runtime-path-diagnostic.md`; `docs/d6-physical-decode.md`; `docs/io-decode-boundary.md`; `docs/memory-timing-boundary.md`; `docs/d41-timing-boundary.md`; `PLAN.md` P0 connectivity gate",
            "physically confirms or removes the provisional D0/D3 correction now used with the physical D6 table, closes its missing address qualifier, and tightens the remaining RAM/video timing nets before netlist freeze",
        ),
        (
            "P1",
            "R94 220-ohm far endpoint",
            "R94.1 is now photo-proved and modeled at D98.3; identify only the lower/far R94.2 endpoint without reopening the separate D98.7/S1.2 harness net",
            "`ref/schematics/dgsh5-109-009-sb-wire-table.md` rows 11/12; `docs/assembly-drawing-extraction.md`; `ref/photos/juku-pcb-2/BODGE-TRIAGE.md`",
            "closes the remaining endpoint of the now-modeled .009 R94 part without reopening the closed S1 harness",
        ),
        (
            "P0",
            "factory Вид В pad mapping",
            "at D56 the three physical callout locations are fixed as the separate left annulus plus D56.5/D56.12 and bare-board gaps to the adjacent rail are visible; continuity-map the installed item-159 conductor/material among those three locations and the rail. Note 11 proves position 150 is tubing, not a cut, and position 159 remains an unexpanded solder-location callout. D15 is photo-closed as the cut A2/A1 bridge and needs no continuity probe; D14 row numbering, the local D32.4/GND-to-D14.1 link, and fifth-landing geometry are photo-registered, so continuity-test the fifth landing's conductor, three long drawn traces, and right-row dogleg/D14.7—both component and solder faces are photo-exhausted there, and position 159 does not prove replacements; at D11 the L trace and four solder locations are registered in two component views, the older pins-4-6 solder scar is excluded, and validated two-sided package fits exhaust four solder views without a unique through-hole match—continuity-test the bridge, D11 pin/net, and upper/lower remote endpoints; the acquired sheets 2-5 wire table covers wires/cables only, so use registered solder-side imagery plus continuity",
            "`docs/factory-modification-disposition.md`; `ref/photos/dgsh5-109-009-sb/PXL_20260711_114626340.jpg`",
            "proves that the clean source-PCB topology is electrically equivalent to the factory-modified artwork before reroute/release",
        ),
        (
            "P0",
            "FDC support signal dispositions",
            "pin-level continuity or an explicit redesign/DNP decision for D28, D95-D99, D101, D102, and D106. D106.7-D93.26 RCLK is photo-closed, selecting the IE7-only output; resistance-test D106.11-D93.27 and D106.14-D93.33 specifically for hidden layer handoffs because calibrated solder-crop review rejects both direct same-layer paths. Meter the now-photo-bounded D106 setup probes: pins 15/1/5 to a known P5V anchor, pins 10/9 to a known GND anchor, and pin 4 to its clock source; pins 9/10 are rail-obscured and the others show only local copper or handoffs, so visual overlap is not continuity. Do not assume the now-excluded WD RCLK chain D106.3-D96.3/D96.5-D93.26, but still identify D96 section 1's actual role. For write precompensation, the photo now closes the R92/R99 ladder at D95.14, D101.4, and D101.8/GND; test the remaining D95/D101 select candidates against D93.18/.17, pins 1 to ground, and pin 7 toward an inverter/write-data path. Recheck legacy-NC D28.5/.6 only if that path approaches them. D96 section 2 and D99 section 1 are already excluded from the WD roles",
            "`docs/fdc-hardware-handoff.md`; `docs/unmodeled-footprint-inventory.md`; `PLAN.md` P0 connectivity gate; Western Digital June-1980 application note Figure 11; Kovalenko et al. МПСС 1986 No. 3 pp. 3-8; `.009` assembly/photo evidence",
            "the recovered-clock output is now closed from target copper; the remaining probes complete its loading/reset context and test the mux family that the WD-only comparison left unexplained",
        ),
        (
            "P1",
            ".009 FDC/analog passive continuity",
            "trace both leads of factory-positioned C9/C10/C11/C12/C15, the far end of R67.2, and X6.1 on the .009 owner board; do not restore the revision-superseded .006 VT3/VT4 RF nets",
            "`docs/video-analog-boundary.md`; `docs/source-pcb-drc.md`; `ref/photos/dgsh5-109-009-sb/rf-option-disposition.json`",
            "turns twelve explicit target-revision boundary pins into real .009 connectivity while preserving the now-zero-short source placement",
        ),
        (
            "P1",
            "C94 endpoint continuity",
            "identify the two lead destinations of the now-restored 680п C94 below D102; its factory identity, populated body, and `(287.07,132.26)` mm centre are already proved",
            "`docs/analog-cluster-photo-placement.md`; `docs/video-analog-boundary.md`; `kicad/juku.board.json` C94 boundary nets",
            "completes the electrical disposition of a target-revision component that was previously absent from the physical model",
        ),
        (
            "P1",
            "C63 population disposition",
            "determine whether the factory-drawn C63 between D41 and D40 was intentionally DNP on the .009 build or physically removed later; inspect the two package-bracketed landing area for lead remnants and test whether any candidate pads join the expected array bypass rails",
            "`docs/fdc-lower-assembly-placement.md`; `docs/photo-registration.md`; raw component photo `PXL_20260710_200418174.jpg`",
            "resolves the conflict between the factory assembly outline and the bare owner-board gap without inventing a through-hole footprint",
        ),
        (
            "P1",
            "lower-FDC C16 continuity",
            "read C16's value and identify both lead destinations; R92=1.3 kΩ and R99=4.7 kΩ are photo-closed and calibrated component copper already closes every resistor endpoint to D95.14, D101.4, or D101.8/GND",
            "`docs/fdc-lower-assembly-placement.md`; `docs/analog-cluster-photo-placement.md`; `kicad/juku.board.json` C16 boundary nets",
            "turns the remaining restored lower-FDC passive boundary into functional circuitry without guessing from nearby solder rails",
        ),
        (
            "P1",
            "right-edge resistor column",
            "read C19's value and both lead destinations, read R108/R86 values, and identify all four resistor lead destinations in the restored .009 right-edge column; R100=R102=12 kΩ are photo-closed and all factory identities, population, orientation, and placements are registered",
            "`docs/fdc-lower-assembly-placement.md`; `docs/analog-cluster-photo-placement.md`; `kicad/juku.board.json` C19/R100/R102/R108/R86 boundary nets",
            "turns five restored physical parts into functional FDC-area circuitry without guessing connectivity from C19's bent body overlap or the obsolete .006 sheet",
        ),
        (
            "P1",
            "C20/C22 endpoint and value continuity",
            "confirm C20's enhanced-photo `1Н5` body reading, read C22's obscured value, and identify both remote lead destinations of the restored grey axial pair immediately right of D102; their identities, adjacent 2.54 mm columns, and 10.00 mm vertical drill spans are already component/solder-photo proved",
            "`docs/analog-cluster-photo-placement.md`; `docs/fdc-lower-assembly-placement.md`; `kicad/juku.board.json` C20/C22 boundary nets",
            "turns two newly restored target-board capacitors into functional circuitry without mistaking their leaning bodies for D102 pin connections",
        ),
        (
            "P2",
            "analog/video/sound/serial bring-up captures",
            "composite/RF/sync/audio nodes plus X3 serial loopback while running the staged bring-up ladder",
            "`docs/video-analog-boundary.md`; `docs/replica-bringup-verification-points.md`; `docs/beeper-readiness.md`; `docs/video-readout-readiness.md`; `docs/serial-handoff.md`",
            "bench evidence only; does not block PCB fabrication",
        ),
        (
            "P2",
            "photos and passive values",
            "macro photos for the FDC/top-center quadrant, C35-C72 bypass-cap values by refdes/position, sound/video analog corner passives",
            "`docs/decap-value-fidelity.md`; `PLAN.md`; generated BOM/sourcing docs",
            "improves authenticity and reduces assembly substitutions",
        ),
    ]

    lines = [
        "# Owner measurement shortlist",
        "",
        "Status: **READY**" if not missing and not failed_checks else "Status: **SOURCE REPORTS MISSING**",
        "",
        "This generated report compresses the remaining physical-owner asks into",
        "the shortest useful list. It is not a bench log and does not claim any",
        "measurement has been performed; it records what still cannot be derived",
        "automatically from the current repo evidence.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_owner_measurement_shortlist.py",
        "```",
        "",
        "## Evidence freshness",
        "",
        "| Check | Status |",
        "| --- | --- |",
    ]
    lines.extend(f"| {name} | {state} |" for name, state in checks)
    if missing:
        lines.extend(["", "Missing required inputs:", ""])
        lines.extend(f"- `{path.relative_to(ROOT)}`" for path in missing)

    lines.extend(
        [
            "",
            "## Highest-value physical asks",
            "",
            "| Priority | Ask | Exact deliverable | Evidence source | Why it matters |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    lines.extend(f"| {priority} | {ask} | {deliverable} | {source} | {why} |" for priority, ask, deliverable, source, why in priority_rows)

    lines.extend(
        [
            "",
            "## Current D94 blockers",
            "",
            f"- D94 failed evidence checks: `{', '.join(inline(item) for item in d94_failures) if d94_failures else 'none'}`",
            "- D94 A0-A4/pins 10-14 are owner-closed onto BA0, BA1, IORD, D104.7+pull-up, and D101.7+pull-up.",
            "  D94.15->D93.3, D94.2->D99.8/GND, D94.3->D93.4, and D94.4->D93.2 are owner-closed.",
            "  Exposed-socket front copper closes D94 D4/pin5 to D93.1. Pull-up references and D104.10 remain unknown. D94.1 has a separate unidentified +5 V pull-up with no other observed branch; D5-D7 remain PCB-fidelity asks.",
            "  Because A2 is measured to active-low IORD, the minimized `/RE`/`/WE` equations require A3 to equal active-low IOWR during selected FDC cycles. Probe D94.13/D104.7 against D5.27; this functional prediction does not authorize a source-net merge.",
            "  A4/D101.Q0 only affects BA1:BA0=11: low selects D0 and releases D93 `/RE`/`/WE`; high selects the normal D93 data-register strobe. Scope that four-node transition without assigning D0's unknown load.",
            "  The content table itself is already closed.",
            "",
            "## Pin-Level Closure",
            "",
            "These rows mirror the unnetted functional pins exposed by",
            "`docs/board-fidelity-gap-ledger.md`. They are the exact pin-level",
            "closures that endpoint coverage cannot prove because the pins are not",
            "yet modeled as nets.",
            "",
            "| Ref | Unnetted functional pins | Needed evidence |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(f"| `{ref}` | `{pins}` | {evidence} |" for ref, pins, evidence in pin_closure_rows)

    lines.extend(
        [
            "",
            "## Bring-up verification scope",
            "",
            f"- Generated bring-up verification nets: `{sum(categories.values())}`",
        ]
    )
    lines.extend(f"- `{category}`: `{count}` net(s)" for category, count in sorted(categories.items()))
    lines.extend(
        [
            "",
            "## Practical sequencing",
            "",
            "1. Ask for programming disk files and BASIC cartridge artifacts first;",
            "   they can close PROM/software truth without touching fragile sockets.",
            "2. If a board owner can help, dump socketed PROM/EPROM parts before",
            "   continuity probing; repeated reads plus socket photos are enough to",
            "   compare against the validated physical tables and retained historical evidence.",
            "3. Use continuity only for the P1 nets above; broad bring-up checklist",
            "   probes are deferred until a replica or owner board is already on the",
            "   bench.",
        ]
    )

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    if missing:
        return 1
    if failed_checks:
        print("Missing evidence markers: " + ", ".join(failed_checks))
        return 1
    expected_d94_failures: set[str] = set()
    if set(d94_failures) != expected_d94_failures or "Enable pin D94.15 is traced" in d94_failures:
        print("Unexpected D94 status: owner-closed enable or input blockers changed; review shortlist")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
