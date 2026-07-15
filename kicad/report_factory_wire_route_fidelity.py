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
PHYSICAL_FIT_SCRIPTS = (
    "kicad/check_d3_factory_wire_landing.py",       # A20
    "kicad/check_d38_factory_wire_landings.py",     # A8B, A9
    "kicad/check_d5_factory_wire_landing.py",       # A19
    "kicad/check_a7_a14_factory_wire_landings.py",  # A7, A14
    "kicad/check_a8_factory_wire_landings.py",      # A8A and chord
    "kicad/check_a10_factory_wire_landings.py",     # A10
    "kicad/check_a11_factory_wire_landing.py",      # A11
    "kicad/check_a12_factory_wire_landing.py",      # A12 and held A12A
    "kicad/check_a13_factory_wire_boundaries.py",   # held A13 pair
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
    physical_fit_checks = {
        script: subprocess.run(
            [kicad_python, str(ROOT / script)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        for script in PHYSICAL_FIT_SCRIPTS
    }
    physical_fits_pass = all(
        check.returncode == 0 for check in physical_fit_checks.values()
    )
    physical_fits_passing = sum(
        check.returncode == 0 for check in physical_fit_checks.values()
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
        and physical_fits_pass
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
        "- Board-fit photo/copper evidence checks: "
        f"`{'PASS' if physical_fits_pass else 'FAIL'} "
        f"({physical_fits_passing}/{len(PHYSICAL_FIT_SCRIPTS)})`",
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
        "## Remaining release closure",
        "",
        "Four PCB landing coordinates/island assignments remain evidence-gated:",
        "`A9A`, `A12A`, `A13A`, and `A13B`. Existing registered component and",
        "solder views occlude their joints; the visible approaches do not uniquely",
        "identify copper. No automatic geometric promotion remains defensible.",
        "After owner continuity or a newly exposing photograph closes those four:",
        "",
        "1. Add the twenty one-pad landings to the source PCB and split each logical",
        "   net into its two original copper islands joined by an explicit wire-link",
        "   assembly object.",
        "2. Reroute only the affected islands, require exactly ten intentional",
        "   unconnected DRC pairs, and emit a wire cut/installation table with the",
        "   factory lengths.",
        "3. Only then may the refreshed candidate replace production copper.",
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
        "`(35.308,122.281)` mm. The same uninterrupted insulated lead ends at",
        "the distinct `(3255,1585)` surface joint below the marked black D7.",
        "The terminal is `(130.027,121.736)` mm: its 94.721 mm span from A19A",
        "matches the factory approximately 9.5 cm conductor and proves the",
        "D7.2-side MEMW landing rather than a neighboring white-wire endpoint.",
        "The same overlap method guards `А:11` at `(1563,3155)` in `114556899`",
        "and `(1898,2837)` in `114600417`. Two-sided D92 fits place owner pin",
        "D92.13 at `(2654.333,2345.833)` component and `(1214.333,2004.833)`",
        "solder pixels; neither pad face carries the wire. The distinct white",
        "surface joint printed `11` at `(2620,1764)` in `200418174` is the",
        "factory-table D92.13 end. Independent D40/D41 transforms agree within",
        "0.013 mm and promote A11B at `(261.325,128.548)` mm on `MEMR`; the",
        "overlapping D7 tile separates the known A19 joint from the second",
        "white joint at `(1825,1706)`, promoting A11A at",
        "`(142.256,123.468)` mm. Their 119.177 mm chord exceeds the approximate",
        "11.5 cm table entry; endpoint geometry is adopted while cut length is",
        "held for direct measurement.",
        "`А:10` is complete in one drawing view at `(821,3778)` and",
        "`(3016,3702)` in `114556899`. At the D41 end, component joint",
        "`(2148,2174)` and reflected solder joint `(1506,1834)` agree within",
        "0.024 mm and a 2.267 mm copper spur reaches D41.13. At the D50 end,",
        "component joint `(2804,2266)` and reflected solder joint `(915,2000)`",
        "agree within 0.012 mm and a 4.370 mm spur reaches D50.1. This proves",
        "A10A `(240.091,146.982)` mm and A10B `(108.865,152.813)` mm on",
        "`W10_QA_SEL`. Their 131.355 mm chord agrees with the duplicate's",
        "final corrected 13.5 cm conductor length; the earlier tentative",
        "`~11.5` reading is retired.",
        "`А:13` is guarded across `114556899`/`114600417` at `(467,3851)`",
        "immediately before C95 and `(1625,3443)` immediately after D38/before",
        "R35. Two-face fits place D13.1 at `(1426,906)` component /",
        "`(3051,1193.5)` solder pixels and D92.1 at `(2484,2290)` /",
        "`(1382,1949)`; none of those owner-pad faces carries the wire. Registered",
        "component panoramas put the remote corridors beneath the horizontal wire",
        "bundle and tied mastic junctions. Matching solder panoramas expose no",
        "printed `13` or isolated third joint; the nearby exposed joints already",
        "belong to A8/A9, so neither A13 endpoint is promoted by proximity.",
        "`А:9` is guarded across `114604420`/`114600417` at `(2967,1768)`",
        "and `(1159,3623)` on its shallow diagonal run. Projecting the fitted",
        "D51 field across six overlapping component tiles places the A9A",
        "drawing region beneath the same factory-wire bundle and mastic patch",
        "in every view. A visible wire approach does not identify the hidden",
        "joint, so A9A remains unpromoted while A9B stays proved at D38.12.",
        "`А:14` is the upper of two close parallel lines at `(1277,1832)` in",
        "`114604420` and `(1700,4044)` in `114600417`; the lower line is `А:7`.",
        "That lower `А:7` line is separately guarded at `(1161,1845)` and",
        "`(1761,4062)` in the same respective views.",
        "The owner backside resolves the right-hand printed joints directly:",
        "A14B `(1837,510)` in `200530933` maps to `(243.264,136.648)` mm on",
        "the D35.12-side `PHI2` island, while A7B `(1774,552)` maps to",
        "`(245.083,133.927)` mm on the D35.10-side `PHI1` island. Their",
        "3.273 mm separation and distinct printed numbers are guarded by the",
        "adjacent two-face D40 fit; the visible КР531ИЕ17 marking also",
        "withdraws the former false D35 package seeds. At the D1 end, the",
        "independently fitted CPU field separates the numbered remote joints",
        "below it: A14A `(2961,2672)` maps through the held-out-validated",
        "solder-grid transform to `(10.449,179.305)` mm, and A7A",
        "`(3151,2671)` maps to `(1.697,179.350)` mm. Their full chords are",
        "236.690 mm and 247.588 mm respectively; both exceed the approximate",
        "23/24 cm table entries, so endpoint geometry is adopted while both",
        "fabrication cut lengths remain held for direct measurement.",
        "`А:12` is guarded at `(1714,2216)` in `114604420` and `(1349,2148)`",
        "in `114611058`, spanning the D13/R20-to-C96/D35 drawing regions.",
        "A new reflected D37 solder fit holds pins 4/8/14 to 0.5 px and places",
        "D37.4 at `(850.5,2121.0)` in `200522685`; that pad has no visible",
        "solder-side etched departure. The photographed `12` is instead beside",
        "the two isolated C96 lead joints below that rail. Because the solder",
        "view is mirrored, raw-left `(2075,600)` is C96's drawing-right lead,",
        "the endpoint immediately after C96 in the assembly drawing. The global",
        "solder registration promotes it as A12B at `(235.083,187.641)` mm on",
        "the D37.4-side `RAM_OUT_EN` island; the other C96 lead is 4.100 mm away",
        "and both component faces are hidden by the wire bundle/mastic. Direct",
        "component/reflected-solder D13 fits place D13.2 at `(1369,906)` in",
        "`200450127` and `(2989.5,1193.5)`",
        "in `200537608`; neither face has an insulated-wire termination at the",
        "pad. A tempting tinned white-wire end at `(1405,1479)` in `200439607`",
        "is also rejected: cross-view projections land on bare component and",
        "solder substrate, not copper. The remote D13-side departure remains",
        "unidentified, so only A12A stays pending.",
        "`А:8` completes the drawing-image inventory at `(1624,276)` in",
        "`114604420` and `(1105,443)` in `114611058`; both are plain endpoint",
        "marks, not the separate circled drawing callout after R13. The D5-side",
        "white-wire joint `(1335,1103)` in `200411500` has a visible 42 px",
        "copper spur to fitted D5.1, proving A8A/STSTB at `(40.811,99.989)` mm.",
        "Together with the D38-side landing below, its 195.9 mm chord exceeds",
        "the duplicate's 19 cm entry; endpoint geometry is adopted, but the final",
        "A8 fabrication cut length remains held for re-read or direct measurement.",
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
    if logical.returncode or landing_check.returncode or not physical_fits_pass:
        checks = {
            "logical endpoint check": logical,
            "landing registration check": landing_check,
            **physical_fit_checks,
        }
        failures = [
            f"[{name}]\n{check.stdout}{check.stderr}"
            for name, check in checks.items()
            if check.returncode
        ]
        raise SystemExit("factory-wire evidence guard failed\n" + "".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
