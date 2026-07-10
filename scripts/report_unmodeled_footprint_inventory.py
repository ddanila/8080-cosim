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
        (GEN, "'D105': ('DIP-14_W7.62mm', 'К155ЛА3'"),
        (PHYSICAL_EVIDENCE, "D105 two visible ЛА3 sections"),
        (PHYSICAL_EVIDENCE, "D2 wiring region is on sheet 1"),
        (PHYSICAL_EVIDENCE, "D2 = РТ4 .037"),
        (PHYSICAL_EVIDENCE, "D105 = К155ЛА3"),
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
    model = modeled_refs()
    source = pcb_refs(SOURCE_PCB)
    routed = pcb_refs(ROUTED_PCB)
    placements = dsn_placements()
    untraced = untraced_entries()
    evidence_ok, missing_markers = markers_ok()

    footprint_only = sorted((source | routed | set(placements)) - model, key=lambda ref: int(ref[1:]))
    common_footprint_only = sorted((source & routed & set(placements)) - model, key=lambda ref: int(ref[1:]))

    d105_pending = "D105" in common_footprint_only and "D105" in untraced
    release_pending = bool(footprint_only)
    if not evidence_ok:
        status = "EVIDENCE MARKERS MISSING"
    elif release_pending:
        status = "DESIGN HOLD / FUNCTIONAL FOOTPRINTS UNMODELED"
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

    lines = [
        "# Unmodeled footprint inventory",
        "",
        f"Status: **{status}**",
        "",
        "This generated report catches IC footprints that exist in the generated",
        "PCB/DSN artifacts but are not yet part of `kicad/juku.board.json`.",
        "These parts are placement-only in the current engineering package:",
        "promoting any of them to modeled nets changes the netlist and requires",
        "a routed-PCB refresh plus endpoint-coverage proof.",
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
        f"There are `{len(footprint_only)}` IC footprints in PCB/DSN artifacts with no",
        "pin-level representation in board JSON. KiCad's zero-unconnected result",
        "cannot detect missing connections on placement-only footprints. Every row",
        "below therefore blocks design release until it is either modeled and routed",
        "or explicitly dispositioned as a redesign/DNP and removed from the released",
        "PCB artifacts. Closing D105 alone is not sufficient.",
        "",
        "## D105 Wait-Gate Boundary",
        "",
        f"- D105 inventory state: `{d105_state}`",
        "- `D105` is an official `.009` `К155ЛА3` footprint present in",
        "  `kicad/gen_kicad_pcb.py`, `kicad/juku.dsn`, `kicad/juku.kicad_pcb`,",
        "  and `kicad/juku_routed.kicad_pcb`, but absent from",
        "  `kicad/juku.board.json`.",
        "- Existing sheet-1 evidence narrows the first useful closure to the",
        "  wait-state chain: D2 `DO`/pin 12 feeds D105 pin 9; D105 has the two",
        "  visible NAND sections `(9,10)->8` and `(4,5)->6`; D2 `V1/V2` are tied",
        "  to ground. The same sheet also shows D105 `(1,2)->3` with D13.4 and",
        "  MWR inputs, plus `(12,13)->11` used as an MRD inverter.",
        "- Do not promote D105 into board JSON from this partial read alone. The",
        "  remaining automatic/owner work is to trace the D105.10 `H` source and",
        "  the D105.6 destination, then rerun PCB generation/routing so both",
        "  source and routed PCB pad nets match the model.",
        "",
        "## D30 READY Flip-Flop Boundary",
        "",
        "- The full-resolution sheet-1 source proves D30 section A: pin 4 `/PRE`",
        "  and pin 2 `D` are pulled high, pin 3 `CLK` is `PHI2TTL`, pin 1",
        "  `/CLR` is driven by `-SSTB`, and pin 5 `Q` reaches D1 READY/pin 23",
        "  through R29 1 kΩ.",
        "- D30 section A, R5, R6, and R29 are now promoted into board JSON. D30",
        "  section B (pins 8-13) is visibly wired on the same sheet but its crossed",
        "  rail destinations still require a clean end-to-end read. The footprint",
        "  is no longer placement-only, but design release remains blocked until",
        "  section B is traced and the regenerated route is verified.",
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
            "1. Keep placement-only official footprints here until their pins are",
            "   traceable enough to add to `kicad/juku.board.json`.",
            "2. After board JSON promotion, regenerate PCB/DSN/BOM reports and route",
            "   the affected pads before claiming endpoint coverage.",
            "3. D105 has first priority because it is tied to D2's wait-state PROM",
            "   output and CPU wait behavior; D30 READY support and the FDC support",
            "   cluster still require their own complete dispositions.",
            "4. `READY FOR DESIGN RELEASE` is emitted only when no IC footprint",
            "   remains outside the board-JSON pin model.",
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
