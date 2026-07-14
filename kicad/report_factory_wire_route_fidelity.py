#!/usr/bin/env python3
"""Report whether routed copper preserves the factory insulated-link boundary."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

import pcbnew

from check_factory_wire_links import LINKS


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "kicad/juku.kicad_pcb"
CANDIDATE = ROOT / "kicad/juku_routed_candidate.kicad_pcb"
REPORT = ROOT / "docs/factory-wire-route-fidelity.md"
LANDINGS = (
    ROOT
    / "ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json"
)


def run_drc(board: Path) -> dict:
    cli = subprocess.check_output(
        [str(ROOT / "scripts/find-kicad-cli.sh")], text=True
    ).strip()
    with tempfile.TemporaryDirectory(prefix="juku-factory-wire-drc-") as tmp_name:
        out = Path(tmp_name) / "drc.json"
        proc = subprocess.run(
            [cli, "pcb", "drc", "--format", "json", "--output", str(out), str(board)],
            text=True,
            capture_output=True,
        )
        if not out.exists():
            raise SystemExit(f"KiCad DRC produced no report: {proc.stdout}{proc.stderr}")
        return json.loads(out.read_text(encoding="utf-8"))


def row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def main() -> int:
    source = pcbnew.LoadBoard(str(SOURCE))
    candidate = pcbnew.LoadBoard(str(CANDIDATE))
    drc = run_drc(CANDIDATE)
    source_refs = {footprint.GetReference() for footprint in source.GetFootprints()}
    candidate_tracks = list(candidate.GetTracks())

    def pad_map(board: pcbnew.BOARD) -> dict[tuple[str, str], tuple[str, float, float]]:
        return {
            (footprint.GetReference(), pad.GetNumber()): (
                pad.GetNetname(),
                pcbnew.ToMM(pad.GetPosition().x),
                pcbnew.ToMM(pad.GetPosition().y),
            )
            for footprint in board.GetFootprints()
            for pad in footprint.Pads()
        }

    source_pads = pad_map(source)
    candidate_pads = pad_map(candidate)
    pad_identity_match = source_pads.keys() == candidate_pads.keys()
    common_pads = source_pads.keys() & candidate_pads.keys()
    pad_net_mismatches = sum(
        source_pads[key][0] != candidate_pads[key][0] for key in common_pads
    )
    moved_pads = sum(
        max(
            abs(source_pads[key][1] - candidate_pads[key][1]),
            abs(source_pads[key][2] - candidate_pads[key][2]),
        )
        > 0.00005
        for key in common_pads
    )

    kicad_python = subprocess.check_output(
        [str(ROOT / "scripts/find-kicad-python.sh")], text=True
    ).strip() or "/usr/bin/python3"
    logical = subprocess.run(
        [kicad_python, str(ROOT / "kicad/check_factory_wire_links.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    landing_check = subprocess.run(
        [
            kicad_python,
            str(ROOT / "kicad/check_factory_wire_landing_registration.py"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    landing_document = json.loads(LANDINGS.read_text(encoding="utf-8"))
    registered_by_point = {
        record["point"]: len(record.get("endpoints", []))
        for record in landing_document.get("points", [])
    }
    image_registered = sum(
        len(record.get("endpoints", []))
        for record in landing_document.get("points", [])
    )
    board_fitted = sum(
        endpoint.get("board_mm") is not None
        for record in landing_document.get("points", [])
        for endpoint in record.get("endpoints", [])
    )

    link_rows = []
    modeled_terminals = 0
    copper_substitutions = 0
    for position, point, length, net_name, endpoints in LINKS:
        expected_refs = {f"A{point}A", f"A{point}B"}
        present_refs = sorted(expected_refs & source_refs)
        modeled_terminals += len(present_refs)
        net_code = candidate.GetNetcodeFromNetname(net_name)
        copper_count = sum(
            1 for item in candidate_tracks if item.GetNetCode() == net_code
        )
        if copper_count:
            copper_substitutions += 1
        endpoint_text = ", ".join(
            f"{ref}.{pin}" for ref, pin in sorted(endpoints)
        )
        link_rows.append(
            row([
                position,
                f"А:{point}",
                length,
                f"`{net_name}`",
                endpoint_text,
                registered_by_point.get(point, 0),
                len(present_refs),
                copper_count,
            ])
        )

    unconnected = len(drc.get("unconnected_items", []))
    expected_terminals = 2 * len(LINKS)
    release_ready = (
        logical.returncode == 0
        and landing_check.returncode == 0
        and image_registered == expected_terminals
        and board_fitted == expected_terminals
        and modeled_terminals == expected_terminals
        and pad_identity_match
        and pad_net_mismatches == 0
        and moved_pads == 0
        and copper_substitutions == 0
        and unconnected == len(LINKS)
    )
    status = (
        "FACTORY WIRE CONSTRUCTION PRESERVED"
        if release_ready
        else (
            "LOGICAL LINKS ADOPTED / LANDING REGISTRATION PARTIAL / ROUTED CANDIDATE HOLD"
            if image_registered
            else "LOGICAL LINKS ADOPTED / PHYSICAL LANDINGS ABSENT / ROUTED CANDIDATE HOLD"
        )
    )

    lines = [
        "# Factory insulated-wire route fidelity",
        "",
        f"Status: **{status}**",
        "",
        "The `.009` assembly table proves ten on-board insulated links. Their",
        "logical endpoints are source-closed, but logical net equality is not",
        "permission to replace the original flying wire with PCB etch. This report",
        "separates those two claims and blocks production adoption of the current",
        "zero-open routing checkpoint.",
        "",
        "## Guarded state",
        "",
        f"- Logical endpoint check: `{'PASS' if logical.returncode == 0 else 'FAIL'}`",
        f"- Landing-registration check: `{'PASS' if landing_check.returncode == 0 else 'FAIL'}`",
        f"- Drawing-image landing endpoints registered: `{image_registered}/{expected_terminals}`",
        f"- Landing endpoints fitted to PCB coordinates/islands: `{board_fitted}/{expected_terminals}`",
        f"- Paired A-point landing terminals modeled: `{modeled_terminals}/{expected_terminals}`",
        f"- Candidate/source pad identities equal: `{'PASS' if pad_identity_match else 'FAIL'}`",
        f"- Candidate/source pad-net mismatches: `{pad_net_mismatches}`",
        f"- Candidate/source moved pads (>50 nm): `{moved_pads}`",
        f"- Link nets carrying candidate copper: `{copper_substitutions}/{len(LINKS)}`",
        f"- Candidate DRC unconnected items: `{unconnected}`",
        "- Required release state: twenty registered landing terminals, no copper",
        "  bridge between each island pair, and exactly ten assembly-wire closures.",
        "",
        "The current candidate's zero unconnected items are useful routing-convergence",
        "evidence, but for these ten links they prove copper substitution rather than",
        "historical construction fidelity. It is also a preserved checkpoint rather",
        "than a current-source route: later net and photo-placement corrections must",
        "be incorporated only after the landing islands and functional netlist freeze.",
        "",
        "## Link audit",
        "",
        "| Conductor | Board point | Length cm | Logical net | Guarded logical endpoints | Image-registered endpoints | Modeled A-point terminals | Candidate copper items on net |",
        "| ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |",
        *link_rows,
        "",
        "## Next automatic closure",
        "",
        "1. Register both physical landing positions for each repeated `А:N` label",
        "   from the full-resolution placement drawing and two-sided owner photos.",
        "2. Add the twenty one-pad landings to the source PCB and split each logical",
        "   net into its two original copper islands joined by an explicit wire-link",
        "   assembly object.",
        "3. Reroute only the affected islands, require exactly ten intentional",
        "   unconnected DRC pairs, and emit a wire cut/installation table with the",
        "   factory lengths.",
        "4. Only then may the refreshed candidate replace production copper.",
        "",
        "`А:20` remains on `S_TTL`: enlarged sheet-1 review reads the adjacent",
        "vertical package as `Д104`, not `Д14`, consistent with owner continuity",
        "D3.10-A23-X3.3 and inconsistent with moving the link onto `SER_TXD`.",
        "Its two drawing endpoints are now guarded at `(2022,1408)` and",
        "`(2503,2325)` original-image pixels (each ±6 px). The D3-side white wire",
        "terminates at `(1232,872)` in owner image `200418174`; its short tinned",
        "departure reaches locally fitted D3.10, proving A20B/S_TTL at",
        "`(213.571,78.499)` mm. At the other end, three component overlaps put",
        "the entering white wire and mastic over A23.1; independent solder views",
        "`200506061`/`200509593` show the third-from-right A23 joint with no",
        "solder-side copper departure. This proves the shared A20A/A23.1/X3.3",
        "through-hole joint at `(178.780,15.200)` mm rather than merely net equality.",
        "`А:19` is likewise guarded across two overlapping views: R7 lies between",
        "the left `(1310,3122)` and right `(1283,3110)` image-local endpoints.",
        "At its D5 end, the marked КР580ВК38's complete contact field and",
        "right-facing notch identify D5.26 at `(1214,1480)` in owner image",
        "`200411500`; a straight 113 px copper segment reaches the distinct",
        "white-wire surface joint `(1218,1593)`. This proves A19A/MEMW at",
        "`(47.058,119.861)` mm; the D7-side terminal remains pending.",
        "The same overlap method guards `А:11` at `(1563,3155)` in `114556899`",
        "and `(1898,2837)` in `114600417`; PCB promotion remains pending.",
        "`А:10` is complete in one view at `(821,3778)` and `(3016,3702)`",
        "in `114556899`, again with PCB coordinates deliberately unset.",
        "`А:13` is guarded across `114556899`/`114600417` at `(467,3851)`",
        "and `(1625,3443)`, with C95/D38 between the marks.",
        "`А:9` is guarded across `114604420`/`114600417` at `(2967,1768)`",
        "and `(1159,3623)` on its shallow diagonal run.",
        "`А:14` is the upper of two close parallel lines at `(1277,1832)` in",
        "`114604420` and `(1700,4044)` in `114600417`; the lower line is `А:7`.",
        "That lower `А:7` line is separately guarded at `(1161,1845)` and",
        "`(1761,4062)` in the same respective views.",
        "`А:12` is guarded at `(1714,2216)` in `114604420` and `(1349,2148)`",
        "in `114611058`, spanning the D13/R20-to-C96/D35 drawing regions.",
        "`А:8` completes the image inventory at `(1624,276)` in `114604420`",
        "and `(1105,443)` in `114611058`; both are plain endpoint marks, not",
        "the separate circled drawing callout after R13.",
        "Two D38-side physical landings are now promoted through the validated",
        "D38/D41 local fits. The right white-wire joint at `(2286,2450)` in",
        "`200418174` reaches via `(2288,2298)` and then fitted D38.12 on continuous",
        "solder copper, proving A9B/SYNC at `(245.695,160.293)` mm. With exactly",
        "two factory-wire joints in that D38 field, the remaining `(1810,2696)`",
        "joint is A8B/D38.8 at `(223.601,170.724)` mm. Both are component-side",
        "surface-soldered copper landings, not invented through-hole pads.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
