#!/usr/bin/env python3
"""Inventory PCB/DSN IC footprints that are not modeled in board JSON nets."""

from __future__ import annotations

import ast
import hashlib
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
SOURCE_DRC_REPORT = ROOT / "docs" / "source-pcb-drc.md"
FDC_BOUNDARY_REFS = {"D28", "D95", "D96", "D97", "D98", "D99", "D101", "D102", "D106"}

RISK_RE = re.compile(
    r"assumed|boundar(?:y|ies)|deferred|untraced|not traced|not established|not readable|"
    r"cannot be uniquely followed|pending|unread|await|owner-verify|mame|approx|refine|dump|"
    r"source confirmation|requires? (?:source|continuity)",
    re.I,
)


UNTRACED_RE = re.compile(r"^\s*'([^']+)':\s*\(([^#]+)\),\s*(?:#\s*(.*))?$")
PCB_REF_RE = re.compile(r'\(property\s+"Reference"\s+"([^"]+)"')
DSN_PLACE_RE = re.compile(r"\(place\s+([A-Z]+\d+)\s+.*?\(PN\s+([^)]+)\)\)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
        (GEN, "'D105':(31.9,215.5,270)"),
        (PHYSICAL_EVIDENCE, "D105 two visible ЛА3 sections"),
        (PHYSICAL_EVIDENCE, "The D2 pin table from sheet 1 is"),
        (PHYSICAL_EVIDENCE, "D2 = РТ4 .037"),
        (PHYSICAL_EVIDENCE, "D105 = К155ЛА3"),
        (SOURCE_DRC_REPORT, "Status: **PASS**"),
        (SOURCE_DRC_REPORT, "Unique colliding pad/item pairs: `0`"),
        (GEN, "'D95':(256.000,93.000,270)"),
        (GEN, "'D97':(268.604,110.273,90)"),
        (GEN, "'D99':(279.895,93.451,270)"),
        (GEN, "'D101':(244.810,110.380,270)"),
        (GEN, "'D102':(292.567,110.024,90)"),
        (SHEET1, None),
    ]
    missing: list[str] = []
    for path, needle in checks:
        if not path.exists():
            missing.append(path.relative_to(ROOT).as_posix())
        elif needle is not None and needle not in read(path):
            missing.append(f"{path.relative_to(ROOT).as_posix()} missing marker {needle!r}")
    return not missing, missing


def net_has_source_risk(name: str, net: dict) -> bool:
    override = net.get("source_risk")
    if override is None:
        return bool(RISK_RE.search(f"{name} {net.get('src', '')} {net.get('note', '')}"))
    if not isinstance(override, bool):
        raise SystemExit(f"{name}: source_risk override must be boolean")
    if override is False and not str(net.get("risk_disposition", "")).strip():
        raise SystemExit(f"{name}: source_risk=false requires risk_disposition")
    return override


def main() -> int:
    board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    model = modeled_refs()
    source = pcb_refs(SOURCE_PCB)
    routed = pcb_refs(ROUTED_PCB)
    placements = dsn_placements()
    untraced = untraced_entries()
    evidence_ok, missing_markers = markers_ok()
    node_nets = {
        (str(ref), str(pin)): (name, net)
        for name, net in board["nets"].items()
        for ref, pin in net.get("nodes", [])
    }
    intentional_no_connects = {
        (str(ref), str(pin)) for ref, pin in board.get("no_connects", [])
    }
    boundary_untraced = {}
    for chip in board["chips"]:
        ref = str(chip.get("ref"))
        if ref in FDC_BOUNDARY_REFS:
            missing = sorted(
                (
                    (str(pin), str(role))
                    for pin, role in chip.get("pins", {}).items()
                    if (ref, str(pin)) not in intentional_no_connects
                    and (
                        (ref, str(pin)) not in node_nets
                        or net_has_source_risk(*node_nets[(ref, str(pin))])
                    )
                ),
                key=lambda item: int(item[0]),
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
        status = "ENDPOINT INVENTORY CLOSED"
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
            "  four-section К155ЛА3. Direct `.009` continuity proves D1.17 DBIN ->",
            "  D105.9, pulled-up edge `H`/D13.13 -> D105.10, tied D105.4/.5, and",
            "  D105.6 -> D5.4. The two NAND stages implement `DBIN AND H`.",
            "- The same continuity pass proves MEMW on tied D105.12/.13 and",
            "  D105.11 -> D30.13. This supersedes both the false D2.12-to-D105.9",
            "  merge and the older `.006` D95 WAIT handoff.",
            "- The promoted routed board has exact source-pad identity and carries",
            "  these corrections with zero electrical blockers. Any future P0 source",
            "  closure still requires complete route/package regeneration.",
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
        "model and promoted devices whose functional pins remain untraced or on",
        "explicit continuity-boundary nets. Closing either class requires source-model",
        "and endpoint-coverage proof, followed by complete route/package regeneration.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_unmodeled_footprint_inventory.py",
        "```",
        "",
        "## Summary",
        "",
        f"- Board JSON SHA-256: `{sha256(BOARD_JSON)}`",
        f"- Source PCB SHA-256: `{sha256(SOURCE_PCB)}`",
        f"- Routed PCB SHA-256: `{sha256(ROUTED_PCB)}`",
        f"- DSN SHA-256: `{sha256(DSN)}`",
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
        "untraced or carried only by explicit boundary nets. KiCad's zero-unconnected",
        "result cannot establish remote continuity for those endpoints. They block",
        "design release until measured or explicitly dispositioned.",
        "",
        "## D105 Wait-Gate Boundary",
        "",
        f"- D105 inventory state: `{d105_state}`",
        *d105_lines,
        "",
        "## D30 READY Flip-Flop Boundary",
        "",
        "- The full-resolution sheet-1 source draws D30 section A pin 4 `/PRE`",
        "  pulled high through R5 and proves pin 2 `D` is pulled high, pin 3 `CLK` is `PHI2TTL`, pin 1",
        "  `/CLR` is driven by `-SSTB`, and pin 5 `Q` reaches D1 READY/pin 23",
        "  through R29 1 kΩ. Direct target-board continuity instead places physical",
        "  R5 on D30.10/.12, so D30.4 remains a separate continuity boundary.",
        "- Owner continuity plus the native cross-sheet chase establish that D2.12",
        "  and R6 feed D30.2;",
        "  D30.1 is source-closed to the D38.8/W8.2 status-strobe island; D30.5",
        "  reaches CPU READY through R29; D30.10/.12 share the R5 pull-up;",
        "  and D105.11 drives D30.13. Section B is also closed: D30.11 joins the",
        "  D105.2/D13.4/D11.20 clock conductor, and D30.8 drives D29.7. Native",
        "  sheet 1 plus `.009` placement/photo evidence close `H` at X1.107B",
        "  with R1 2 kΩ to +5 V. The measured READY/WAIT edge conductors are closed;",
        "  D30.4's asynchronous preset is the remaining section-A control boundary.",
        "",
        "## AG3 Package Correction",
        "",
        "- `D97`, `D99`, and `D102` are photographed К155АГ3 dual one-shots and use",
        "  16-pin 7.62 mm DIP packages, matching the already traced D56 AG3",
        "  pinout (including RC pins 14/15). The earlier 14-pin placement-only",
        "  footprints omitted six physical holes across these three positions.",
        "- Their two photographed rows are now package-fitted and placed from",
        "  shared-image pitch plus the visible right board edge; the previous",
        "  placeholder grid and its D99 clearance nudge are retired.",
        "",
        "## FDC Device Pinout Recovery",
        "",
        "- `D95` and `D101` are typed as К555КП12 / 74LS253 dual 4:1",
        "  three-state multiplexers. Recovered `.009` sheet 3 now closes every",
        "  D95 functional pin as the 1/2 MHz controller and 4/8 MHz separator",
        "  clock mux; D101 retains only its explicitly listed precomp boundaries.",
        "  Pin roles follow <https://gatchina.pw/datasheets/микросхемы/555/555КП12.pdf>.",
        "- `D98` is now typed as a К155ЛП11 / SN74367 six-channel three-state",
        "  buffer; its two enable groups and six A/Y pairs follow the device sheet.",
        "  Exact-revision sheet 3 uses five pairs and explicitly omits pair 4/pins 9-10:",
        "  <https://static.chipdip.ru/lib/493/DOC048493374.pdf>.",
        "  The five used buffers and both grounded enable groups are now structural-only",
        "  HDL and LVS-visible; pair 4 remains an explicit structural no-connect.",
        "- `D28` is now typed as the К155ЛН3 six-inverter open-collector family.",
        "  Factory `.009` sheet 3 closes all six sections through drive-select, READY,",
        "  separator-clock, and DRQ/INTRQ conditioner paths. The drawing instead omits",
        "  D96.13, D98.9/.10, and complementary outputs D97.13/D102.4.",
        "  All six D28 sections are now structural-only HDL and LVS-visible.",
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
            "listed signal pins are either unnetted or carried by a source-risk boundary",
            "until continuity or an explicit disposition is proved. Source-closed nets and",
            "documented intentional no-connects are excluded.",
            "",
            "| Ref | Untraced functional pins |",
            "| --- | --- |",
        ]
    )
    for ref in sorted(boundary_untraced, key=lambda item: int(item[1:])):
        lines.append(table_row([f"`{ref}`", ", ".join(f"{pin}:{role}" for pin, role in boundary_untraced[ref])]))

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
            "3. D105 is modeled in board JSON, the source PCB, HDL, and the promoted",
            "   exact-source route. X1.107B/R1 close `H`;",
            "   remaining priority belongs to D94 and the FDC (D30.8/.11 are owner-closed)",
            "   support cluster. Physical D2 truth and its measured D0 path are adopted.",
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
