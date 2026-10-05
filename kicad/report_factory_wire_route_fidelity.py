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
            "FACTORY WIRE ROUTE/CONSTRUCTION HOLD"
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
        "separates those two claims. Source/routed parity and electrical DRC are held,",
        "but factory-construction release remains held until all ten links are",
        "represented as explicit assembly wires between split copper islands.",
        "",
        "## Command and scope",
        "",
        "Run `/usr/bin/python3 kicad/report_factory_wire_route_fidelity.py`",
        "with KiCad Python bindings available. It reruns the landing evidence",
        "guards and DRC on both routed variants, then compares source pad",
        "identities, nets, and centers. A successful exit means the invoked",
        "evidence guards passed; release additionally requires the report status",
        "and every parity, DRC, and construction condition below to be ready.",
        "The report counts DRC unconnected items; it does not summarize or gate",
        "electrical violations in the DRC violation list. Review the full DRC",
        "before release, even if the report status becomes ready.",
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
        "- Routed-candidate board audit:",
        f"  - Candidate/source pad identities equal: `{'PASS' if pad_identity_match else 'FAIL'}`",
        f"  - Candidate/source pad-net mismatches: `{pad_net_mismatches}`",
        f"  - Candidate/source moved pads (>50 nm): `{moved_pads}`",
        f"  - Link nets carrying candidate copper: `{candidate_copper_nets}/{len(LINKS)}`",
        f"  - Candidate DRC unconnected items: `{candidate_unconnected}`",
        "- Required release state: twenty registered and modeled landing terminals,",
        "  ten split island pairs, ten explicit assembly-wire closures, exact source",
        "  parity, and zero electrical/unconnected DRC findings.",
        "",
        "The current parity and DRC results above remain release blockers. Seven",
        "links (A7/A8/A10/A11/A14/A19/A20) are explicit W-footprint assembly wires",
        "between separately named copper islands. A9/A12/A13 lack five evidence-gated",
        "landing coordinates, so their endpoints remain same-net copper routes. A7B",
        "and A14B are also masked candidates, and W7.1/W14.1 still need relocation. This",
        "construction hold is additional to the electrical and placement holds.",
        "The candidate results are regenerated from `kicad/juku_routed_candidate.kicad_pcb`;",
        "they do not authorize the promoted board.",
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
        "A7B/A14B wire terminations are hidden by mastic; their landing coordinates",
        "and cut lengths remain under measurement hold.",
        "The routed board and fabrication package remain under design",
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
        "   only the affected islands, and achieve zero electrical/unconnected DRC",
        "   findings.",
        "3. Regenerate the fabrication package and emit a wire cut/installation table",
        "   with physically qualified cut lengths and the source lengths shown separately.",
        "",
        '## Landing dispositions',
        '',
        'Detailed coordinates, image hashes, rejected candidates and probe waypoints',
        'belong to `ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json`',
        "and the per-link physical-fit guards listed in this report's generator.",
        'Current dispositions are:',
        '',
        '| Link | Accepted evidence and remaining action |',
        '| --- | --- |',
        '| A7/A14 | CPU-side surface joints are accepted. W7.1/W14.1 still occupy obsolete through-hole positions and need relocation plus copper rework. The remote joints are mastic-covered; their former D41-based coordinates are withdrawn. Cut lengths require measurement. |',
        '| A8 | D5-side A8A is accepted. A8B lacks a proved copper/island assignment; the 19 cm table value is not an approved cut length. See `a8b-corrected-trace-review.json`. |',
        '| A9 | Both ends remain unpromoted. The former remote candidate traces to D92.1/ROE, not D38.12/SYNC. Do not merge SYNC with nearby D38.10/13. See `a9b-corrected-trace-review.json`. |',
        '| A10 | A10A is fitted to D50.1. A10B lacks an identified wire landing; require cable-to-D41.13 continuity. The 13.5 cm source reading is not a qualified replacement cut length. |',
        '| A11 | Both distinct surface landings are fitted on MEMR. Their 119.177 mm chord exceeds the 11.5 cm source reading; measure the replacement cut length. |',
        '| A12 | Both coordinates/island assignments remain held. Candidate joints near the C96 supply-group region do not prove a RAM_OUT_EN wire termination. See `c96-a12-solder-review.json`. |',
        '| A13 | A13A lacks ROE continuity and a traced cable destination; A13B has a strong D92.1/ROE photo-trace candidate but still requires continuity. See `a13a-c95-d50-candidate-review.json` and the A13 boundary guard. |',
        '| A19 | Both distinct MEMW surface landings are fitted; the 94.721 mm span agrees with the approximate 9.5 cm source length. |',
        '| A20 | The D3.10-side surface joint and shared A23.1/X3.3 through-hole landing are fitted on S_TTL. Keep this wire separate from D14/SER_TXD. |',
        '',
        'Photo-review JSON names above are under `ref/photos/juku-pcb-2/`.',

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
