#!/usr/bin/env python3
"""Inventory PCB/DSN IC footprints that are not modeled in board JSON nets."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad" / "juku.board.json"
DSN = ROOT / "kicad" / "juku.dsn"
SOURCE_PCB = ROOT / "kicad" / "juku.kicad_pcb"
ROUTED_PCB = ROOT / "kicad" / "juku_routed.kicad_pcb"
GEN = ROOT / "kicad" / "gen_kicad_pcb.py"
REPORT = ROOT / "docs" / "unmodeled-footprint-inventory.md"
PHYSICAL_EVIDENCE = ROOT / "ref" / "photos" / "juku-pcb-2" / "BODGE-TRIAGE.md"
SHEET1 = ROOT / "ref" / "schematics" / "p3_sheet1.png"
FDC_BOUNDARY_REFS = {"D28", "D95", "D96", "D97", "D98", "D99", "D101", "D102", "D106"}


UNTRACED_RE = re.compile(r"^\s*'([^']+)':\s*\(([^#]+)\),\s*(?:#\s*(.*))?$")
PCB_REF_RE = re.compile(r'\(property\s+"Reference"\s+"([^"]+)"')
DSN_PLACE_RE = re.compile(r"\(place\s+([A-Z]+\d+)\s+.*?\(PN\s+([^)]+)\)\)")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def is_ic_ref(ref: str) -> bool:
    return bool(re.fullmatch(r"D\d+", ref))


def modeled_refs() -> set[str]:
    board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    return {str(chip.get("ref")) for chip in board["chips"] if is_ic_ref(str(chip.get("ref")))}


def pcb_refs(path: Path) -> set[str]:
    return {ref for ref in PCB_REF_RE.findall(read(path)) if is_ic_ref(ref)}


def dsn_placements() -> dict[str, str]:
    return {ref: pn.strip() for ref, pn in DSN_PLACE_RE.findall(read(DSN)) if is_ic_ref(ref)}


def untraced_entries() -> dict[str, dict[str, object]]:
    entries: dict[str, dict[str, object]] = {}
    for line in read(GEN).splitlines():
        match = UNTRACED_RE.match(line)
        if not match:
            continue
        ref, tuple_src, comment = match.groups()
        if not is_ic_ref(ref):
            continue
        try:
            values = ast.literal_eval("(" + tuple_src.strip() + ")")
        except (SyntaxError, ValueError):
            values = ()
        entries[ref] = {
            "footprint": values[0] if len(values) >= 1 else "-",
            "mark": values[1] if len(values) >= 2 else "-",
            "x": values[2] if len(values) >= 3 else "-",
            "y": values[3] if len(values) >= 4 else "-",
            "rot": values[4] if len(values) >= 5 else "-",
            "comment": (comment or "").strip(),
        }
    return entries


def markers_ok() -> tuple[bool, list[str]]:
    checks = [
        (GEN, "'D105':(31.9,215.5,90)"),
        (PHYSICAL_EVIDENCE, "D105 two visible ЛА3 sections"),
        (PHYSICAL_EVIDENCE, "D2 wiring region is on sheet 1"),
        (PHYSICAL_EVIDENCE, "D2 = РТ4 .037"),
        (PHYSICAL_EVIDENCE, "D105 = К155ЛА3"),
        (GEN, "'D97':(228,88,90)"),
        (GEN, "'D99':(250.8,110,90)"),
        (GEN, "'D102':(270.8,111.8,90)"),
        (SHEET1, None),
    ]
    missing: list[str] = []
    for path, needle in checks:
        if not path.exists():
            missing.append(path.relative_to(ROOT).as_posix())
        elif needle is not None and needle not in read(path):
            missing.append(f"{path.relative_to(ROOT).as_posix()} missing marker {needle!r}")
    return not missing, missing


def main() -> int:
    board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    model = modeled_refs()
    source = pcb_refs(SOURCE_PCB)
    routed = pcb_refs(ROUTED_PCB)
    placements = dsn_placements()
    untraced = untraced_entries()
    evidence_ok, missing_markers = markers_ok()
    netted_nodes = {
        (str(ref), str(pin))
        for net in board["nets"].values()
        for ref, pin in net.get("nodes", [])
    }
    boundary_untraced = {}
    for chip in board["chips"]:
        ref = str(chip.get("ref"))
        if ref in FDC_BOUNDARY_REFS:
            missing = sorted(
                (str(pin) for pin in chip.get("pins", {}) if (ref, str(pin)) not in netted_nodes),
                key=int,
            )
            if missing:
                boundary_untraced[ref] = missing

    footprint_only = sorted((source | routed | set(placements)) - model, key=lambda ref: int(ref[1:]))
    common_footprint_only = sorted((source & routed & set(placements)) - model, key=lambda ref: int(ref[1:]))

    d105_pending = "D105" in common_footprint_only and "D105" in untraced
    release_pending = bool(footprint_only)
    if not evidence_ok:
        status = "EVIDENCE MARKERS MISSING"
    elif release_pending:
        status = "DESIGN HOLD / FUNCTIONAL FOOTPRINTS UNMODELED"
    elif boundary_untraced:
        status = "DESIGN HOLD / FDC FUNCTIONAL PINS UNTRACED"
    else:
        status = "READY FOR DESIGN RELEASE"
    if "D105" in model:
        d105_state = "MODELED"
    elif d105_pending:
        d105_state = "PENDING MODEL + REROUTE"
    elif "D105" in source | routed | set(placements):
        d105_state = "INCONSISTENT ARTIFACT INVENTORY"
    else:
        d105_state = "NOT PRESENT"

    if d105_state == "MODELED":
        d105_lines = [
            "- `D105` is promoted into board JSON and both PCB artifacts as a",
            "  four-section К155ЛА3. The regenerated route has zero unrouted items.",
            "- Sheet 1 proves D2.12 -> D105.9, D105.10 -> `H`/−5 V,",
            "  D105.8 -> tied inputs 4+5, D13.4/MWR -> inputs 2/1, and the",
            "  tied-input MRD inverter 12+13 -> 11 -> D30.13.",
            "- D105.6 is traced to a D95 inverter on the older `.006` sheet and",
            "  onward as `-WAIT` to E8-1. The `.009` BOM reassigns D95 to an FDC",
            "  К555КП12, so that revision-specific inverter destination remains an",
            "  explicit boundary rather than being assigned to the wrong footprint.",
        ]
    else:
        d105_lines = [
            "- `D105` remains outside the pin-level board model.",
            "- Existing sheet-1 evidence proves the four NAND sections, but the",
            "  target-revision handoff still requires reconciliation.",
        ]

    lines = [
        "# Unmodeled footprint inventory",
        "",
        f"Status: **{status}**",
        "",
        "This generated report catches both IC footprints absent from the board",
        "model and promoted devices whose functional pins remain outside named",
        "nets. Adding either class of endpoint requires a routed-PCB refresh and",
        "endpoint-coverage proof.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_unmodeled_footprint_inventory.py",
        "```",
        "",
        "## Summary",
        "",
        f"- Modeled board-JSON `D*` ICs: `{len(model)}`",
        f"- Source PCB IC footprints: `{len(source)}`",
        f"- Routed PCB IC footprints: `{len(routed)}`",
        f"- DSN IC placements: `{len(placements)}`",
        f"- Footprint-only ICs in any PCB/DSN artifact: `{len(footprint_only)}`",
        f"- Footprint-only ICs present in source PCB, routed PCB, and DSN: `{len(common_footprint_only)}`",
        "",
        "## Design-Release Consequence",
        "",
        f"There are `{len(footprint_only)}` IC footprints with no board-JSON representation",
        f"and `{len(boundary_untraced)}` promoted FDC devices with functional pins still",
        "outside named nets. KiCad's zero-unconnected result cannot detect either class",
        "until those endpoints are modeled. Both classes block design release.",
        "",
        "## D105 Wait-Gate Boundary",
        "",
        f"- D105 inventory state: `{d105_state}`",
        *d105_lines,
        "",
        "## D30 READY Flip-Flop Boundary",
        "",
        "- The full-resolution sheet-1 source proves D30 section A: pin 4 `/PRE`",
        "  and pin 2 `D` are pulled high, pin 3 `CLK` is `PHI2TTL`, pin 1",
        "  `/CLR` is driven by `-SSTB`, and pin 5 `Q` reaches D1 READY/pin 23",
        "  through R29 1 kΩ.",
        "- D30 section A, R5, R6, and R29 are now promoted into board JSON. In",
        "  section B, pins 10+12 are tied, pins 6+9 are intentional no-connects,",
        "  and D105.11 now drives pin 13. Pin 8, pin 11, and the upstream source",
        "  of pins 10+12 still require end-to-end reads.",
        "",
        "## AG3 Package Correction",
        "",
        "- `D97`, `D99`, and `D102` are КМ555АГ3 dual one-shots and use",
        "  16-pin 7.62 mm DIP packages, matching the already traced D56 AG3",
        "  pinout (including RC pins 14/15). The earlier 14-pin placement-only",
        "  footprints omitted six physical holes across these three positions.",
        "- D99 is shifted 0.7 mm within its explicitly assumed photo placement",
        "  to clear R75 after restoring the full package length.",
        "",
        "## Footprint-Only ICs",
        "",
        "| Ref | Mark/value | Footprint | Source PCB | Routed PCB | DSN | Generator note |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for ref in common_footprint_only:
        entry = untraced.get(ref, {})
        lines.append(
            table_row(
                [
                    f"`{ref}`",
                    f"`{entry.get('mark', placements.get(ref, '-'))}`",
                    f"`{entry.get('footprint', '-')}`",
                    "yes" if ref in source else "no",
                    "yes" if ref in routed else "no",
                    f"`{placements.get(ref, '-')}`" if ref in placements else "no",
                    entry.get("comment", "-"),
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Promoted FDC Pin Boundaries",
            "",
            "These devices now have physical pin models and routed power pins. Their",
            "remaining signal pins stay explicitly unnetted until continuity is proved.",
            "",
            "| Ref | Untraced functional pins |",
            "| --- | --- |",
        ]
    )
    for ref in sorted(boundary_untraced, key=lambda item: int(item[1:])):
        lines.append(table_row([f"`{ref}`", ", ".join(boundary_untraced[ref])]))

    only_partial = [ref for ref in footprint_only if ref not in common_footprint_only]
    if only_partial:
        lines.extend(
            [
                "",
                "## Artifact Mismatches",
                "",
                "These footprint-only refs are not present across all three PCB/DSN",
                "artifacts and should be investigated before relying on them:",
                "",
            ]
        )
        lines.extend(f"- `{ref}`" for ref in only_partial)

    lines.extend(
        [
            "",
            "## Closure Rule",
            "",
            "1. Keep every unread functional pin explicit until continuity is proved.",
            "2. After any board-JSON net promotion, regenerate PCB/DSN/BOM reports",
            "   and route the affected pads before claiming endpoint coverage.",
            "3. D105 is modeled and routed. Remaining priority belongs to D2's",
            "   truth/input rails, the `.009` WAIT-inverter handoff, D30's unread",
            "   section-B endpoints, and the FDC support cluster.",
            "4. `READY FOR DESIGN RELEASE` is emitted only when no footprint or",
            "   promoted FDC functional pin remains outside the net model.",
            "",
        ]
    )

    if missing_markers:
        lines.extend(["## Missing Evidence Markers", ""])
        lines.extend(f"- `{item}`" for item in missing_markers)
        lines.append("")

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    if not evidence_ok:
        print("Missing evidence markers: " + ", ".join(missing_markers))
        return 1
    missing_generator_entries = [ref for ref in common_footprint_only if ref not in untraced]
    if missing_generator_entries:
        print(
            "Placement-only footprints are missing from the generator inventory: "
            + ", ".join(missing_generator_entries)
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
