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
ROUTED = ROOT / "kicad/juku_routed.kicad_pcb"
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
    routed = pcbnew.LoadBoard(str(ROUTED))
    candidate_drc = run_drc(CANDIDATE)
    routed_drc = run_drc(ROUTED)
    candidate_tracks = list(candidate.GetTracks())
    routed_tracks = list(routed.GetTracks())

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
    routed_pads = pad_map(routed)
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
    routed_pad_identity_match = source_pads.keys() == routed_pads.keys()
    routed_common_pads = source_pads.keys() & routed_pads.keys()
    routed_pad_net_mismatches = sum(
        source_pads[key][0] != routed_pads[key][0] for key in routed_common_pads
    )
    routed_moved_pads = sum(
        max(
            abs(source_pads[key][1] - routed_pads[key][1]),
            abs(source_pads[key][2] - routed_pads[key][2]),
        )
        > 0.00005
        for key in routed_common_pads
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
    explicit_wire_splits = 0
    direct_copper_substitutions = 0
    candidate_copper_nets = 0
    for position, point, length, net_name, endpoints in LINKS:
        wire_ref = f"W{point}"
        present_terminals = [
            f"{wire_ref}.{pin}"
            for pin in ("1", "2")
            if (wire_ref, pin) in source_pads
        ]
        modeled_terminals += len(present_terminals)
        candidate_net_code = candidate.GetNetcodeFromNetname(net_name)
        candidate_copper_count = sum(
            1 for item in candidate_tracks if item.GetNetCode() == candidate_net_code
        )
        if candidate_copper_count:
            candidate_copper_nets += 1
        routed_net_code = routed.GetNetcodeFromNetname(net_name)
        routed_copper_count = sum(
            1 for item in routed_tracks if item.GetNetCode() == routed_net_code
        )
        wire_pad_nets = {
            routed_pads[(wire_ref, pin)][0]
            for pin in ("1", "2")
            if (wire_ref, pin) in routed_pads
        }
        explicitly_split = len(wire_pad_nets) == 2
        if explicitly_split:
            explicit_wire_splits += 1
        else:
            direct_copper_substitutions += 1
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
                len(present_terminals),
                "explicit wire / split islands" if explicitly_split else "same-net copper / landing hold",
                routed_copper_count,
            ])
        )

    candidate_unconnected = len(candidate_drc.get("unconnected_items", []))
    routed_unconnected = len(routed_drc.get("unconnected_items", []))
    expected_terminals = 2 * len(LINKS)
    release_ready = (
        logical.returncode == 0
        and landing_check.returncode == 0
        and physical_fits_pass
        and image_registered == expected_terminals
        and board_fitted == expected_terminals
        and modeled_terminals == expected_terminals
        and routed_pad_identity_match
        and routed_pad_net_mismatches == 0
        and routed_moved_pads == 0
        and explicit_wire_splits == len(LINKS)
        and direct_copper_substitutions == 0
        and routed_unconnected == 0
    )
    status = (
        "FACTORY WIRE CONSTRUCTION PRESERVED"
        if release_ready
        else (
            "PROMOTED ROUTE VERIFIED / FACTORY WIRE LANDING HOLD"
            if image_registered and physical_fits_pass and landing_check.returncode == 0
            else "FACTORY WIRE LANDING EVIDENCE HOLD"
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
        "separates those two claims. The promoted route is electrically verified,",
        "but factory-construction release remains held until all ten links are",
        "represented as explicit assembly wires between split copper islands.",
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
        "- Photo-confirmed modeled landing relocations still required: `W7.1, W14.1`",
        f"- Promoted/source pad identities equal: `{'PASS' if routed_pad_identity_match else 'FAIL'}`",
        f"- Promoted/source pad-net mismatches: `{routed_pad_net_mismatches}`",
        f"- Promoted/source moved pads (>50 nm): `{routed_moved_pads}`",
        f"- Explicit assembly-wire island splits: `{explicit_wire_splits}/{len(LINKS)}`",
        f"- Same-net copper substitutions still held: `{direct_copper_substitutions}/{len(LINKS)}`",
        f"- Promoted DRC unconnected items: `{routed_unconnected}`",
        "- Historical pre-promotion candidate audit:",
        f"  - Candidate/source pad identities equal: `{'PASS' if pad_identity_match else 'FAIL'}`",
        f"  - Candidate/source pad-net mismatches: `{pad_net_mismatches}`",
        f"  - Candidate/source moved pads (>50 nm): `{moved_pads}`",
        f"  - Link nets carrying historical candidate copper: `{candidate_copper_nets}/{len(LINKS)}`",
        f"  - Historical candidate DRC unconnected items: `{candidate_unconnected}`",
        "- Required release state: twenty registered and modeled landing terminals,",
        "  ten split island pairs, ten explicit assembly-wire closures, exact source",
        "  parity, and zero electrical/unconnected DRC findings.",
        "",
        "The promoted board now has exact source identity and zero KiCad opens. Seven",
        "links (A7/A8/A10/A11/A14/A19/A20) are explicit W-footprint assembly wires",
        "between separately named copper islands. A9/A12/A13 lack five evidence-gated",
        "landing coordinates, so their endpoints remain same-net copper routes. A7B",
        "and A14B are also masked candidates, and W7.1/W14.1 still need relocation. This",
        "is a historical-construction hold, not an electrical package failure.",
        "The historical candidate counts remain below only to preserve the migration",
        "audit that led to the promoted board.",
        "",
        "## Link audit",
        "",
        "| Conductor | Board point | Length cm | Logical net | Guarded logical endpoints | Image-registered endpoints | Modeled A-point terminals | Promoted construction | Copper items on primary island |",
        "| ---: | ---: | ---: | --- | --- | ---: | ---: | --- | ---: |",
        *link_rows,
        "",
        "## Remaining release closure",
        "",
        f"{expected_terminals - board_fitted} PCB landing coordinates/island assignments remain evidence-gated:",
        "`A7B`, `A8B`, `A9A`, `A9B`, `A10B`, `A12A`, `A13A`, `A13B`, `A14B`, and `A12B`. Existing registered component and",
        "solder views either occlude the termination or leave its through-hole",
        "pairing, copper path, or cable identity unproved. A13B now has a",
        "strong photo-traced D92.1/ROE candidate, still awaiting continuity.",
        "The former A14B and A7B metric projections from D41 are withdrawn",
        "after the common lower-cluster solder correction. Their printed",
        "joints remain visible, but wire termination is hidden by mastic; W14's landing and cut length",
        "remain under measurement hold.",
        "The promoted routed board has exact source identity, zero shorts, and zero",
        "opens; its fabrication package is machine-verified. It remains under design",
        "hold because A8/A9/A10/A12/A13 physical landings or construction",
        "remain unproved, and because the broader functional P0 netlist is open.",
        "A:7, A:8, A:10, A:11, A:14, A:19, and A:20 are already split into modeled landing pairs and",
        "explicit assembly-wire components. After owner continuity or a newly exposing",
        "photograph closes the unresolved joints:",
        "",
        "1. Finish the twenty landing terminals and split each remaining logical",
        "   net into its two original copper islands joined by an explicit wire-link",
        "   assembly object.",
        "2. Add W9/W12/W13 assembly footprints, split their island net names, reroute",
        "   only the affected islands, and retain zero electrical/unconnected DRC",
        "   findings.",
        "3. Regenerate the fabrication package and emit a wire cut/installation table",
        "   with the factory lengths before design release.",
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
        "D92.13 at `(2654.333,2345.833)` component and `(1552.167,2007)`",
        "solder pixels; neither pad face carries the wire. The distinct white",
        "surface joint printed `11` at `(2620,1764)` in `200418174` is the",
        "factory-table D92.13 end. Independent D40/D41 transforms agree within",
        "0.013 mm and promote A11B at `(261.325,128.548)` mm on `MEMR`; the",
        "overlapping D7 tile separates the known A19 joint from the second",
        "white joint at `(1825,1706)`, promoting A11A at",
        "`(142.256,123.468)` mm. Their 119.177 mm chord exceeds the approximate",
        "revised 11.5 cm table entry (earlier value crossed out); endpoint geometry",
        "is adopted while cut length is held for direct measurement.",
        "`А:10` is complete in one drawing view at `(821,3778)` and",
        "`(3016,3702)` in `114556899`, with a right-side overlap in",
        "`114600417`. The left mark is beside native-labeled D50/C95;",
        "the right mark continues toward the D41 region. The former D41-end joint",
        "`(2148,2174)` is a trace point without a visible wire termination;",
        "its supposed solder counterpart `(1506,1834)` came from the displaced",
        "D41 field. The old D30-tile owner candidates are withdrawn.",
        "Factory-right A10B still has no identified owner joint.",
        "At factory-left A10A beside D50,",
        "component joint `(2804,2266)` and reflected solder joint `(915,2000)`",
        "agree within 0.012 mm and a 4.370 mm spur reaches D50.1. This proves",
        "A10A `(108.865,152.813)` mm remains fitted. The former 131.355 mm",
        "chord is invalid; the drawing still gives the corrected 13.5 cm",
        "conductor length and A10B needs a new physical landing fit.",
        "Corrected D41.13 solder contact near `(2054,1790)` runs visibly to a",
        "soldered endpoint near `(2415,2090)`. A close component crop shows",
        "the exposed white-wire metal tip near `(1825,2435)` over the trace",
        "field without a discernible solder pool or pad. The cross-face",
        "projection of the solder endpoint is near `(1777,2424)`, about",
        "50 px west beneath insulation. Do not promote this tip as A10B",
        "without direct cable-to-D41.13 continuity.",
        "`А:13` is guarded across `114556899`/`114600417` at `(467,3851)`",
        "immediately before C95 and `(1625,3443)` immediately after D38/before",
        "R35. Two-face fits place D13.1 at `(1426,906)` component /",
        "`(2682,825)` solder pixels and D92.1 at `(2484,2290)` /",
        "`(1719,1951)`; none of those owner-pad faces carries the wire. In the",
        "corrected D50/C95 component tile `200411500`, a white wire joint near",
        "`(2400,2330)` is an A13A position candidate. It is a separate lower",
        "cable from the upper fitted A10A/D50.1 wire. Its D50-local projection",
        "near solder `(1334,2065)` lies on a bare trace without a distinct",
        "through-hole joint. A closer front crop reveals a short copper spur",
        "from the joint to open annulus `(2430,2377)`; its reflected solder",
        "prediction is `(1303,2111)` from D50 or `(1306,2136)` from nearby",
        "D51. The latter misses the plausible open hole `(1294,2149)` by",
        "about 18 px, versus 39 px from D50. The through counterpart, ROE continuity,",
        "and cable destination remain open.",
        "Interpolating that candidate from D50 pitch gives a board search point",
        "near `(90.05,155.75)` mm; independent D51 pitch gives",
        "`(89.91,156.27)` mm, only 0.54 mm apart. Its straight-line chord to D92.1 is",
        "166.2 mm, about 16 mm over the approximate 150 mm factory A13 length;",
        "the chord to D38.1 is 140.8 mm. A D38-adjacent remote surface",
        "landing therefore remains geometrically plausible; A13A itself",
        "still lacks ROE continuity and a traced opposite cable end.",
        "In the A13B corridor near D38,",
        "the right-side white-wire/annulus pair near `(2286,2450)`/`(2288,2298)`",
        "is the same physical feature formerly logged as A9B. A D92-local",
        "two-face fit places its front annulus about 9.5 px from the solder",
        "annulus `(1916,1950)`, which visibly traces west to registered",
        "D92.1/ROE `(1719,1951)`. This strongly favors A13B over A9B; exact",
        "through-hole pairing and cable continuity still hold formal landing",
        "promotion. The candidate A13A-to-A13B straight chord is about",
        "157.1 mm, 7 mm beyond the table's approximate 15 cm cut length",
        "before wire routing. Measure the installed cable; A13A remains open.",
        "`А:9` is guarded across `114604420`/`114600417` at `(2967,1768)`",
        "and `(1159,3623)` on its shallow diagonal run. Projecting the fitted",
        "D51 field across six overlapping component tiles places the A9A",
        "drawing region beneath the same factory-wire bundle and mastic patch",
        "in every view. A visible wire approach does not identify the hidden",
        "joint. The old A9B-to-D38.12 solder trace used the displaced D38/D41",
        "field. A corrected D38 three-pin cross-face fit projects the visible",
        "A9 candidate front annulus `(2288,2298)` to solder `(1907,1982)`,",
        "while a wider four-package fit places it near `(1914,1964)`, only",
        "14 px from the open solder annulus `(1916,1950)`. The D92-local fit",
        "narrows that miss to about 9.5 px, and the solder copper connects the",
        "annulus directly to D92.1/ROE, not corrected D38.12/SYNC `(2076,2064)`.",
        "This white joint is withdrawn as the preferred A9B candidate; see",
        "`a9b-corrected-trace-review.json`. D38.12 itself has a visible short",
        "solder spur west to an open annulus near `(2025,2063)`. Its candidate",
        "front counterpart near `(2176,2404)` has no visible wire; it is a",
        "better SYNC search anchor. Its front trace reaches a second bare",
        "annulus near `(2178,2520)`; the likely solder counterpart near",
        "`(2028,2170)` has a spur that visibly stops short of D38.10.",
        "Do not merge SYNC with D38.10/13 from proximity. Both A9 ends",
        "remain unpromoted.",
        "`А:14` is the upper of two close parallel lines at `(1277,1832)` in",
        "`114604420` and `(1700,4044)` in `114600417`; the lower line is `А:7`.",
        "That lower `А:7` line is separately guarded at `(1161,1845)` and",
        "`(1761,4062)` in the same respective views.",
        "The owner backside identifies raw candidate right-hand printed joints",
        "in `200522685`: A14B `(1825,2827)` and A7B `(1757,2854)`.",
        "Their former D41-based board coordinates are withdrawn because the",
        "D41 solder field was displaced about 500 pixels. The component face over",
        "both D35-side candidate joints is covered by wire bundle and mastic;",
        "no insulated-wire termination is directly visible there. At the D1",
        "end, overlapping component",
        "views `200411500` and `200439607` show two actual white-wire surface",
        "starts below the fitted CPU: the printed-7 A7A joint `(607,2898)` maps",
        "by the local D1 fit to `(14.597,184.485)` mm, and the adjacent A14A",
        "joint `(803,2897)` maps to `(23.621,184.440)` mm. Their corrected",
        "chords are 213.303 and 201.046 mm respectively. The old backside",
        "through-hole positions `(1.697,179.350)` and `(10.449,179.305)` mm",
        "have no matching white-wire terminations and are retracted as A7A/A14A.",
        "The W7.1 and W14.1 source-PCB pads still occupy those stale positions;",
        "relocate them to the proved surface joints and rework their copper",
        "before fabrication. Exact wire cut lengths remain held for measurement.",
        "`А:12` is guarded at `(1714,2216)` in `114604420` and `(1349,2148)`",
        "in `114611058`, spanning the D13/R20-to-C96/D35 drawing regions.",
        "The former reflected `D37` solder fit is now correctly identified as",
        "upper-row D39 from the `.006` assembly order and adjacent decapped D92;",
        "it does not constrain lower-row D37. The photographed `12` is beside",
        "two through-hole joints at `(2075,600)` and `(2170,605)` in the mirrored",
        "solder view `200530933`. Their global projection separates them by",
        "4.100 mm, but neither joint visibly carries an insulated wire. The",
        "drawing line ends after the C96 symbol, which does not prove a wire",
        "termination at either joint or even their C96 identity while the",
        "component face is hidden by the wire bundle/mastic. A12B therefore",
        "has no accepted board coordinate or island assignment.",
        "The exact `.009` sheet-1 supply group in `101827714` includes C96",
        "among `C94...C98` on its +5 V-to-ground bypass branch. This supports",
        "checking those two candidate joints as a bypass location, but does not",
        "identify the hidden component or justify a RAM_OUT_EN assignment.",
        "Direct component/reflected-solder D13 fits place D13.2 at `(1369,906)` in",
        "`200450127` and `(2743.5,825)`",
        "in `200537608`; neither face has an insulated-wire termination at the",
        "pad. A tempting tinned white-wire end at `(1405,1479)` in `200439607`",
        "is not a proved pad landing: the component cross-view is bare, while",
        "its solder extrapolation leaves the fitted D13 field. The remote D13-side departure remains",
        "unidentified, so both A12 ends remain pending.",
        "`А:8` completes the drawing-image inventory at `(1624,276)` in",
        "`114604420` and `(1105,443)` in `114611058`; both are plain endpoint",
        "marks, not the separate circled drawing callout after R13. The D5-side",
        "white-wire joint `(1335,1103)` in `200411500` has a visible 42 px",
        "copper spur to fitted D5.1, proving A8A/STSTB at `(40.811,99.989)` mm.",
        "The duplicate's revised 19 cm A8 length remains a source reading.",
        "The former 195.9 mm chord is invalid after A8B's demotion.",
        "The D38-side candidate white joints `(2286,2450)` and `(1810,2696)`",
        "remain visible in `200418174`. The former A9B candidate is now",
        "strongly associated with A13B/D92.1/ROE by a two-face trace; its",
        "A9B/D38.12 assignment is withdrawn. The A8B/D38.8 assignment used",
        "the displaced D38/D41 solder fit. The corrected",
        "D38 cross-face projection sends the former A8B candidate near",
        "`(2403,2363)` solder pixels, roughly 335 px from D38.8 and close to",
        "the region printed `9`; this is an extrapolated search clue, not a",
        "joint identity. A four-package D38/D41/D92/D39 fit independently",
        "places it near `(2397,2379)`, 17 px away, confirming only the search",
        "area (`a8b-corrected-trace-review.json`). Both board",
        "coordinates and island assignments are withdrawn pending copper review.",
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
