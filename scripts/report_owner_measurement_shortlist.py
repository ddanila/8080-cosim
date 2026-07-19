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
    ROOT / "docs" / "fdc-bus-polarity.md",
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
        ("FDC firmware profiles proved; physical D100 attribution retired", has_phrase("docs/fdc-bus-polarity.md", "Status: **FIRMWARE PROFILES PROVED / PHYSICAL D100 ATTRIBUTION RETIRED / TARGET EPROM DUMPS PENDING**")),
        ("Beeper source/handoff guarded", has_phrase("docs/beeper-readiness.md", "Status: **DIGITAL BEEPER SOURCE + BOARD HANDOFF READY**")),
        ("Serial USART behavior guarded", has_phrase("docs/serial-handoff.md", "Status: **SERIAL CORE GUARDED / PHYSICAL LEVELS PENDING**")),
        ("Decap value boundary guarded", has_phrase("docs/decap-value-fidelity.md", "Status: **DRAM-FIELD ARTWORK/POPULATION CLOSED / VALUES AND NON-FIELD PLACEMENTS PENDING**")),
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
            "D94 .092 remaining outputs",
            "the 2026-07-19 session closes A3 as D105.3 qualified /WR, separates D104.7 and raw D5.27, maps R87/R88/R89 to D94.4/.3/.2, maps R8 2 kΩ to the pull-up-only D94.1 branch, and retracts D94.5-D93.1. Trace only D94 D5-D7 far destinations and D104.10; optionally scope D101.7, D94.1, /RE, and /WE on port 1F to observe the table's register-3 steering behavior",
            "`docs/d94-reconstruction-constraints.md`; `docs/photo-registration.md`; exact two-sided local-fit rows in `ref/photos/juku-pcb-2/endpoints.csv`",
            "uses the recovered PROM equations to target D0's hidden branch, replaces the retired same-as-D8 BA mapping with measured row semantics, and resolves the read/write control path before an FDC hardware release",
        ),
        (
            "P0",
            "FDC interrupt/buffer continuity and fitted ROM profile",
            "WD1793 DRQ/INTRQ to 8259 inputs and D93 MR/CLK. Dump D15/D16 twice and identify the guarded CMA or NOP VG93 profile; factory sheet 1 proves D93 pins 7..14 connect directly to DB0..DB7. Trace only the shared D100 pins 9/11 continuation `1`; recovered sheet 3 already closes D100.6 to D101.9 write precompensation",
            "`docs/fdc-bus-polarity.md`; `docs/fdc-hardware-handoff.md`; `docs/replica-bringup-verification-points.md`; `PLAN.md` P0 gate",
            "identifies the exact board/EPROM configuration and closes the remaining drive-output-buffer inputs without reopening source-closed paths",
        ),
        (
            "P0",
            "memory-decode stragglers",
            "D6.15-D105.1 is now closed to D7.8 as the I/O-cycle-active-high qualifier, and D105.3 is independently closed as qualified peripheral /WR. Recheck only the surprising D13.12-D16.13 report with D16 removed. Still close C99 far plate, the upstream D7.5/D29.3 -INHIB source, and remaining D36 timing feeds; the D6.1<-D3.4<-/PC1, D6.2<-D3.6<-/PC0, D6.11/-WREQ, D6.12-D8.15, enable, and RAM-read endpoint chains are already closed",
            "`docs/d6-runtime-path-diagnostic.md`; `docs/d6-physical-decode.md`; `docs/io-decode-boundary.md`; `docs/memory-timing-boundary.md`; `docs/d41-timing-boundary.md`; `PLAN.md` P0 connectivity gate",
            "corroborates the now-direct corrected D6 decode path, closes its missing address qualifier, and tightens the remaining RAM/video timing nets before netlist freeze",
        ),
        (
            "P1",
            "R94 220-ohm far endpoint",
            "R94.1 is photo-proved and modeled at D98.3; continuity-identify only the lower/far R94.2 endpoint without reopening the separate D98.7/S1.2 harness net. Two overlapping component views are cable-obscured at the landing and two registered solder regions are non-unique, so imagery is exhausted",
            "`ref/photos/juku-pcb-2/r94-photo-exhaustion.json`; `ref/schematics/dgsh5-109-009-sb-wire-table.md` rows 11/12; `docs/assembly-drawing-extraction.md`; `ref/photos/juku-pcb-2/BODGE-TRIAGE.md`",
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
            "pin-level continuity or an explicit redesign/DNP decision for the still-open D28, D96-D99, D101, D102, and D106 pins. Preserve the source-closed D95 1/2 MHz controller and 4/8 MHz separator clock mux, D106.7-D28.9-D28.8-D96.3-D96.5-D93.26 chain, and D97/D102/D101 write-precomp chain. Resistance-test D106.11-D93.27 and D106.14-D93.33 for hidden handoffs, then meter D106's bounded setup pins. D101.1/.3/.5/.6, D97.13, and D102.4 remain the specific precomp-area boundaries",
            "`docs/fdc-hardware-handoff.md`; `ref/schematics/fdc-clock-mux-map.md`; `ref/schematics/fdc-write-precomp-map.md`; `PLAN.md` P0 connectivity gate",
            "completes only the genuinely open support-circuit context without re-probing source-closed timing paths",
        ),
        (
            "P1",
            ".009 FDC/analog passive continuity",
            "trace both leads of factory-positioned C9/C10/C11/C12/C15; X6 is already photo-closed through bracket cable A:3/X6.1 at VD3.2/SOUND_CLAMP and A:4/X6.2 at GND. Continuity-test the now-photo-exhausted R67.2 joint, whose two component views stop at its solder pool and whose D102-local cross-side projection proves the coincident backside trace has no via; do not restore the revision-superseded .006 VT3/VT4 RF nets",
            "`docs/video-analog-boundary.md`; `docs/source-pcb-drc.md`; `ref/photos/juku-pcb-2/r67-photo-exhaustion.json`; `ref/photos/juku-pcb-2/x6-cable-registration.json`",
            "turns the remaining eleven explicit target-revision boundary pins into real .009 connectivity while preserving the now-zero-short source placement",
        ),
        (
            "P1",
            "C94 inspection and continuity",
            "inspect whether the separate factory-drawn C94 immediately right of VT2 is populated, read its value, and identify both endpoint destinations; the formerly assigned yellow body and VIDEO_OUT join are retracted because two July views plus a May angle identify that three-lead Б/8901 body and its joints as VT2",
            "`ref/photos/juku-pcb-2/c94-endpoint-registration.json`; `docs/analog-cluster-photo-placement.md`; `docs/video-analog-boundary.md`; `kicad/juku.board.json` C94 boundary nets",
            "closes a target-revision capacitor without reusing the adjacent transistor's marking or emitter landing",
        ),
        (
            "P1",
            "lower-FDC capacitor markings",
            "determine the unit/type behind C16's bare `27` and C19's bare `22`, plus tolerance/voltage markings for C16/C19/C20/C22. Recovered sheet 3 closes every endpoint and the +5 V timing-resistor rail; do not re-open connectivity from unread body codes",
            "`docs/fdc-lower-assembly-placement.md`; `ref/schematics/fdc-write-precomp-map.md`",
            "closes procurement attributes without guessing electrical topology",
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
            "target-revision placement/population disposition for C51-C53 and C70-C72 (their retired fit-to-space coordinates are no longer fabricated), readable bypass-cap values by refdes/position (the complete 4x8 inherited DRAM-field artwork and population are closed), plus macro photos for FDC/top-center and sound/video analog passives",
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
            "- D94 A0-A4/pins 10-14 are owner-closed onto BA0, BA1, IORD, D105.3 qualified /WR, and D101.7.",
            "  D94.15->D93.3, D94.2->D99.9/R89, D94.3->D93.4/R88, and D94.4->D93.2/R87 are owner-closed.",
            "  D94.5 is visibly NC; D93.1 alone owns the visible open stub. R8 2 kΩ is the only measured D94.1 branch; D5-D7 remain PCB-fidelity asks.",
            "  D5.27->D7.10 is raw IOWR_N; D7.8->D105.1/D6.15 and D13.4->D105.2 produce D105.3 qualified peripheral /WR. D104.7 is separate at about 84 kΩ from D94.13.",
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
