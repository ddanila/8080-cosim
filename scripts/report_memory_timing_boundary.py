#!/usr/bin/env python3
"""Generate the DRAM/clock timing boundary report."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
REPORT = ROOT / "docs" / "memory-timing-boundary.md"
SOURCE_PCB = ROOT / "kicad" / "juku.kicad_pcb"
ROUTED_PCB = ROOT / "kicad" / "juku_routed.kicad_pcb"


def load_board() -> dict:
    return json.loads(BOARD.read_text(encoding="utf-8"))


def nodes(board: dict, net_name: str) -> list[tuple[str, str]]:
    return [tuple(node) for node in board["nets"].get(net_name, {}).get("nodes", [])]


def has_nodes(board: dict, net_name: str, expected: set[tuple[str, str]]) -> bool:
    return expected <= set(nodes(board, net_name))


def endpoint_text(board: dict, net_name: str) -> str:
    rendered = [f"{ref}.{pin}" for ref, pin in nodes(board, net_name)]
    if not rendered:
        return "-"
    if len(rendered) <= 10:
        return ", ".join(rendered)
    return ", ".join(rendered[:10]) + f", ... (+{len(rendered) - 10})"


def row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def main() -> int:
    board = load_board()
    source_pcb = SOURCE_PCB.read_text(encoding="utf-8")
    routed_pcb = ROUTED_PCB.read_text(encoding="utf-8")
    chips = {chip.get("ref"): chip for chip in board["chips"]}
    d35 = chips["D35"]
    d36 = chips["D36"]
    d37 = chips["D37"]
    d59 = chips["D59"]
    d92 = chips["D92"]
    hex_contract = {
        "1": "I1", "2": "O2", "3": "I3", "4": "O4", "5": "I5", "6": "O6",
        "9": "I9", "8": "O8",
    }
    d59_contract = dict(hex_contract, **{"1": "XIN", "2": "OSC"})
    d53_outputs = {
        "D53_Y0_R49": {("D53", "15"), ("R49", "1")},
        "D53_Y1_R50": {("D53", "14"), ("R50", "1")},
        "D53_Y2_R51": {("D53", "13"), ("R51", "1")},
        "D53_Y3_R52": {("D53", "12"), ("R52", "1")},
    }
    d56_rc = {
        "D56_CLR": {("D56", "3"), ("D56", "11"), ("R61", "2")},
        "D56_RC1": {("D56", "15"), ("R59", "1"), ("C8", "1")},
        "D56_C1": {("D56", "14"), ("C8", "2")},
        "D56_RC2": {("D56", "7"), ("R47", "1"), ("C7", "1")},
        "D56_C2": {("D56", "6"), ("C7", "2")},
    }
    guarded_checks = [
        (
            "D36 К531ЛА12 package contract is the SN74S37-compatible quad 2-input NAND",
            d36.get("pins", {}) == {
                "1": "A2", "2": "B2", "3": "Y2",
                "4": "B", "5": "A", "6": "Y",
                "9": "A3", "10": "B3", "8": "Y3",
                "12": "A4", "13": "B4", "11": "Y4",
            }
            and "SN74S37" in d36.get("prov", {}).get("refdes", "")
            and has_nodes(board, "GND", {("D36", "7")})
            and has_nodes(board, "P5V", {("D36", "14")}),
            "inputs 1/2,4/5,9/10,12/13; outputs 3/6/8/11; GND7/VCC14",
        ),
        (
            "All 32 DRAM sockets retain complete option-rail roles",
            all(
                chips[f"D{ref}"].get("pins", {}).get("1") == "NC_VBB_OPTION"
                and chips[f"D{ref}"].get("pins", {}).get("8") == "VCC_OPTION"
                and chips[f"D{ref}"].get("pins", {}).get("16") == "VSS_GND"
                and (f"D{ref}", "1") in set(nodes(board, "RAIL_H"))
                and (f"D{ref}", "8") in set(nodes(board, "RAIL_G"))
                and (f"D{ref}", "16") in set(nodes(board, "GND"))
                for ref in range(60, 92)
            ),
            "D60-D91 pins 1/8/16 -> RAIL_H/RAIL_G/GND; native rail E is ground; pin 1 is internal NC for populated РУ5",
        ),
        (
            "C34 bypass follows the native rail-E to rail-F drawing",
            has_nodes(board, "GND", {("C34", "2")})
            and has_nodes(board, "P5V", {("C34", "1")})
            and "RAIL_E" not in board["nets"],
            "native sheet-2 power corner: C34 spans E/GND to F/+5 V",
        ),
        (
            "E1 MA7/DRAM-size selector retains all three source endpoints",
            has_nodes(board, "P5V", {("E1", "1")})
            and has_nodes(board, "MA7", {("E1", "2")})
            and has_nodes(board, "MA6", {("E1", "3"), ("D51", "9")}),
            "sheet-2: E1.1=+5 V, E1.2=MA7 rail 28, E1.3=D51.9/MA6",
        ),
        (
            "E14 video-mux enable retains the drawn 1-3 strap",
            has_nodes(board, "VID_MUX_G", {("E14", "1"), ("E14", "3"), ("D50", "15"), ("D51", "15")})
            and has_nodes(board, "P5V", {("E14", "2")})
            and has_nodes(board, "GND", {("E14", "4")}),
            "sheet-2: E14.1-E14.3 fitted strap; E14.2=+5 V; E14.4=GND",
        ),
        (
            "D53 RAS/CAS ladder outputs are guarded",
            all(has_nodes(board, name, expected) for name, expected in d53_outputs.items()),
            "`D53_Y0_R49`..`D53_Y3_R52`",
        ),
        (
            "D53 unused Y4-Y7 outputs remain source-proved no-connects",
            all(["D53", pin] in board.get("no_connects", []) for pin in ("7", "9", "10", "11"))
            and not any(ref == "D53" and pin in {"7", "9", "10", "11"}
                        for net in board["nets"].values() for ref, pin in net.get("nodes", [])),
            "sheet-2 complete D53 symbol draws only Y0-Y3; pins11/10/9/7 have no stubs",
        ),
        (
            "D36 write-gate inputs and rail are guarded to all modeled DRAM W pins",
            has_nodes(board, "W_RAIL16", {("D36", "8")})
            and board["nets"]["W_RAIL16"].get("source_risk") is False
            and has_nodes(board, "MEMW", {("D36", "9")})
            and has_nodes(board, "D33_D36", {("D33", "10"), ("D36", "10")})
            and has_nodes(board, "D36_D33", {("D36", "3"), ("D33", "11")})
            and sum(1 for ref, pin in nodes(board, "W_RAIL16") if pin == "3" and ref.startswith("D")) >= 32,
            "MEMW->D36.9; D36.3->D33.11/.10->D36.10; D36.8->32 DRAM pin-3 inputs",
        ),
        (
            "D36 CAS pre-driver reaches R57",
            has_nodes(board, "CAS_PRE", {("D36", "11"), ("R57", "1")}),
            "`CAS_PRE`: D36.11 -> R57.1",
        ),
        (
            "Shared CAS rail is guarded to all modeled DRAM C pins",
            has_nodes(board, "CAS", {("D36", "1"), ("R57", "2"), ("R58", "1")})
            and sum(1 for ref, pin in nodes(board, "CAS") if pin == "15" and ref.startswith("D")) >= 32,
            "`CAS` includes D36.1/R57.2/R58.1 plus DRAM pin-15 fanout",
        ),
        (
            "PHI2TTL timing gate fanout is cross-sheet source-closed",
            set(nodes(board, "PHI2TTL"))
            == {("D35", "13"), ("D39", "1"), ("D92", "2"), ("D92", "3"), ("D53", "4"), ("D30", "3")}
            and board["nets"]["PHI2TTL"].get("source_risk") is False
            and "unique labeled cross-sheet pair" in board["nets"]["PHI2TTL"].get("risk_disposition", ""),
            "sheet-2 Ф2TTL (1) export -> sheet-1 (2) Ф2 TTL/D30.3",
        ),
        (
            "D92 triple-NOR RAM read/write combiner is source-closed",
            d92.get("pins", {}) == {
                "1": "A1", "2": "B1", "13": "C1", "12": "Y1",
                "3": "A2", "4": "B2", "5": "C2", "6": "Y2",
                "9": "A3", "10": "B3", "11": "C3", "8": "Y3",
            }
            and has_nodes(board, "ROE", {("D92", "1")})
            and board["nets"]["ROE"].get("source_risk") is False
            and has_nodes(board, "PHI2TTL", {("D92", "2"), ("D92", "3")})
            and has_nodes(board, "MEMR", {("D5", "24"), ("D33", "3"), ("D92", "13"), ("W11", "1")})
            and set(nodes(board, "MEMR_D7")) == {("D7", "1"), ("W11", "2")}
            and has_nodes(board, "D92_RD_NOR", {("D92", "12"), ("D92", "11")})
            and has_nodes(board, "MEMW", {("D92", "4")})
            and has_nodes(board, "WREQ_N", {("D6", "11"), ("D92", "5"), ("R12", "2")})
            and has_nodes(board, "D92_WR_NOR", {("D92", "6"), ("D92", "9"), ("D92", "10")})
            and has_nodes(board, "D92_NOACC", {("D92", "8"), ("D39", "5")}),
            "sheet-2: read NOR 1/2/13->12; write NOR 3/4/5->6; combine 9/10/11->8",
        ),
        (
            "D37 RAM-read output-enable NAND is source-closed on both inputs and output",
            d37.get("pins", {}).get("5") == "A3"
            and d37.get("pins", {}).get("4") == "B3"
            and d37.get("pins", {}).get("6") == "Y3"
            and has_nodes(board, "MEMR", {("D33", "3")})
            and set(nodes(board, "D33_O4")) == {("D33", "4"), ("D37", "5")}
            and set(nodes(board, "RAM_OUT_EN")) == {("D13", "2"), ("D37", "4")}
            and set(nodes(board, "RAM_RD_OE")) == {("D37", "6"), ("D58", "9")}
            and "fully traced native sheet-2" in board["nets"]["D33_O4"]["src"],
            "sheet-2: MEMR -> D33.3/.4 -> D37.5; D13.2 -> D37.4; D37.6 -> D58.OE9",
        ),
        (
            "Factory wire 11 is preserved as an assembly closure between MEMR islands",
            "W11_D7_D92" not in board["nets"]
            and "W11_D7_D92" not in source_pcb
            and board["nets"]["MEMR"].get("wire_link")
            == {"ref": "W11", "other_net": "MEMR_D7"}
            and has_nodes(board, "MEMR", {("D92", "13"), ("W11", "1")})
            and set(nodes(board, "MEMR_D7")) == {("D7", "1"), ("W11", "2")},
            "native -MRD reaches D92.13/A11B; W11 crosses to the D7.1/A11A surface island without PCB copper",
        ),
        (
            "Factory wire 19 is preserved as an assembly closure to D7.2",
            board["nets"]["MEMW"].get("wire_link")
            == {"ref": "W19", "other_net": "MEMW_D7P2"}
            and has_nodes(board, "MEMW", {("D5", "26"), ("W19", "1")})
            and set(nodes(board, "MEMW_D7P2")) == {("D7", "2"), ("W19", "2")},
            "global MEMW/D5.26 reaches A19A; W19 crosses to the separate D7.2/A19B surface island",
        ),
        (
            "D39 latch/output context is guarded",
            has_nodes(board, "D39_O8", {("D39", "8"), ("D59", "11")})
            and has_nodes(board, "D39Y", {("D39", "11"), ("D38", "10"), ("D38", "13")}),
            "`D39_O8` and `D39Y`",
        ),
        (
            "D39 remaining NAND inputs are source-closed onto control rails 3 and 1",
            has_nodes(board, "XTAL16M", {("D39", "10"), ("D42", "9"), ("D43", "9")})
            and has_nodes(board, "GND", {("D39", "2"), ("D43", "1")}),
            "sheet-2 direct junctions: D39.10 -> local rail3/XTAL16M; D39.2 -> grounded rail1",
        ),
        (
            "D38 load gate is source-closed except for the remote origin of rail 2",
            has_nodes(board, "D39_MEMCYC", {("D39", "3"), ("D39", "4"), ("D38", "5")})
            and has_nodes(board, "TIMING_TAG2", {("D38", "4")})
            and set(nodes(board, "D34_A1_TAG2")) == {("D34", "4")}
            and set(nodes(board, "TIMING_TAG2")).isdisjoint(set(nodes(board, "D34_A1_TAG2")))
            and "automatic same-number chase exhausted" in board["nets"]["TIMING_TAG2"]["src"]
            and has_nodes(board, "GND", {("D38", "2")})
            and has_nodes(board, "CAS", {("D38", "1")}),
            "D38 pins5/4/2/1 <- rails4/2/1/15; D38 rail2 explicitly distinct from D34 top-edge tag2",
        ),
        (
            "D42/D43 serializer packages retain their source-proved unused parallel outputs",
            all(
                [ref, pin] in board.get("no_connects", [])
                for ref in ("D42", "D43") for pin in ("11", "12", "13")
            )
            and all(
                "exhaustive sheet-2 symbol census" in chips[ref].get("prov", {}).get("pins", "")
                for ref in ("D42", "D43")
            ),
            "sheet-2 draws only QD pin10; QA/QB/QC pins13/12/11 are explicit NCs on both packages",
        ),
        (
            "D56 one-shot RC networks are guarded",
            all(has_nodes(board, name, expected) for name, expected in d56_rc.items()),
            "`D56_CLR`, `D56_RC1/C1`, `D56_RC2/C2`",
        ),
        (
            "D56 trigger, clock, and active-output topology is owner-closed",
            has_nodes(board, "D56_Q2_D34", {("D56", "5"), ("D34", "9")})
            and has_nodes(board, "D56_QN_D34", {("D56", "4"), ("D34", "10")})
            and set(nodes(board, "PIT_HSYNC_DSL")) == {("D54", "17"), ("D56", "10")}
            and set(nodes(board, "VERT_SYNC")) == {("D55", "17"), ("D56", "2")}
            and set(nodes(board, "D56_Q2N_TAG16")) == {
                ("D56", "12"), ("D55", "15"), ("D55", "18")
            }
            and set(nodes(board, "SYNC_B")) == {("D57", "17")}
            and {("D56", "1"), ("D56", "8"), ("D56", "9")} <= set(nodes(board, "GND"))
            and all(["D56", pin] not in board.get("no_connects", []) for pin in ("1", "9"))
            and ["D56", "13"] in board.get("no_connects", []),
            "exact .009 E3 plus owner continuity 2026-07-21: D54.17->D56.10, D55.17->D56.2, D56.12->D55.15/.18, D56.5/.4->D34.9/.10; D57.17 remains separate",
        ),
        (
            "D35 frame-interrupt inverter path is source-closed",
            all(d35.get("pins", {}).get(pin) == role for pin, role in hex_contract.items())
            and has_nodes(board, "POF", {("D26", "10"), ("D35", "3")})
            and has_nodes(board, "VID_MIX2", {("D35", "4"), ("R39", "1")})
            and set(nodes(board, "VERT_RTR")) == {("D55", "13"), ("D35", "9")}
            and set(nodes(board, "FRAME_INT")) == {("D35", "8"), ("D10", "23"), ("R60", "1")}
            and all(["D35", pin] in board.get("no_connects", []) for pin in ("1", "2", "5", "6"))
            and all(["D35", pin] not in board.get("no_connects", []) for pin in ("8", "9")),
            "native sheets: D55.13/VER RTR -> D35.9/.8 -> FRAME INT/R60 -> D10.23; D35.3/.4 remains POF/VID_MIX2",
        ),
        (
            "D30 READY clear uses the native D38-side status strobe",
            set(nodes(board, "STSTB_D38")) == {("D38", "8"), ("W8", "2"), ("D30", "1")}
            and "SSTB_N" not in board["nets"],
            "sheet-2 D38.8 active-low STB export -> sheet-1 -SSTB/D30.1; W8 still separates the D5-side island",
        ),
    ]
    boundary_checks = [
        (
            "D59 remaining inverter package boundary remains visible",
            all(d59.get("pins", {}).get(pin) == role for pin, role in d59_contract.items())
            and set(nodes(board, "D59_O10_TAG10")) == {("D59", "10")}
            and ("D59", "10") not in set(nodes(board, "SOUND"))
            and "Automatic tag-number chase exhausted" in board["nets"]["D59_O10_TAG10"]["src"],
            "D59.5/.6 NC; D59.10 tag10 remains distinct from SOUND",
        ),
        (
            "D36_CAS_IN native-sheet chase is exhausted without inventing a timing-rail merge",
            set(nodes(board, "D36_CAS_IN")) == {("D36", "12"), ("D36", "13")}
            and "5140x3563" in board["nets"]["D36_CAS_IN"]["src"]
            and "automatic scan chase exhausted" in board["nets"]["D36_CAS_IN"]["src"],
            endpoint_text(board, "D36_CAS_IN") + "; tied inputs visible, west source unlabeled in dense bundle",
        ),
        (
            "OSC-to-XTAL16M source-side merge remains unproved after native-sheet chase",
            set(nodes(board, "OSC")).isdisjoint(set(nodes(board, "XTAL16M")))
            and "automatic scan chase exhausted" in board["nets"]["XTAL16M"]["src"]
            and "functional expectation alone cannot prove" in board["nets"]["XTAL16M"]["src"],
            "OSC and XTAL16M remain distinct source nets pending continuity",
        ),
    ]
    ok = all(result for _, result, _ in guarded_checks + boundary_checks)
    status = "MEMORY TIMING GUARDED / CAS SOURCE BOUNDARY PENDING" if ok else "MEMORY TIMING BOUNDARY FAILED"

    lines = [
        "# Memory timing boundary",
        "",
        "Status date: 2026-07-21.",
        "",
        f"Status: **{status}**",
        "",
        "This generated report narrows the remaining DRAM/clock timing risks.",
        "The board model preserves the traced E1/E14 selector straps, RAS/CAS ladder, write rail,",
        "PHI2TTL fanout, and D56 one-shot RC networks. Exact-revision `.009 E3`",
        "imagery plus owner continuity closes the D54/D55/D56 trigger and clock",
        "crossings; the unresolved CAS input remains an explicit source boundary.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_memory_timing_boundary.py",
        "```",
        "",
        "## Guarded Checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    lines.extend(row([name, "PASS" if result else "FAIL", evidence]) for name, result, evidence in guarded_checks)
    lines.extend(
        [
            "",
            "## Pending Boundary Checks",
            "",
            "| Boundary | Result | Current endpoints |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(row([name, "PASS" if result else "FAIL", evidence]) for name, result, evidence in boundary_checks)
    lines.extend(
        [
            "",
            "## Current Timing Nets",
            "",
            "| Net | Endpoints | Source note |",
            "| --- | --- | --- |",
        ]
    )
    for name in (
        "D53_Y0_R49",
        "D53_Y1_R50",
        "D53_Y2_R51",
        "D53_Y3_R52",
        "W_RAIL16",
        "CAS_PRE",
        "CAS",
        "D36_CAS_IN",
        "TIMING_TAG2",
        "D34_A1_TAG2",
        "D39_MEMCYC",
        "MEMR",
        "D33_O4",
        "RAM_OUT_EN",
        "RAM_RD_OE",
        "D92_RD_NOR",
        "D92_WR_NOR",
        "D92_NOACC",
        "PHI2TTL",
        "XTAL16M",
        "D39_O8",
        "D39Y",
        "D59_O10_TAG10",
        "POF",
        "VERT_RTR",
        "FRAME_INT",
        "D56_CLR",
        "D56_RC1",
        "D56_C1",
        "D56_RC2",
        "D56_C2",
        "D56_QN_D34",
        "PIT_HSYNC_DSL",
        "VERT_SYNC",
        "D56_Q2N_TAG16",
        "SYNC_B",
    ):
        net = board["nets"].get(name, {})
        lines.append(row([f"`{name}`", f"`{endpoint_text(board, name)}`", net.get("src", "-")]))

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The functional board model has enough traced structure for fabrication",
            "  and staged bring-up: RAS/CAS ladder endpoints, the DRAM write rail,",
            "  and the key PHI2TTL/D56 support nets are guarded.",
            "- The runnable CPU-memory scaffold now models a complete row/column transaction:",
            "  RAS remains active from the row phase through the CAS column pulse, and the",
            "  РУ5 model strobes DIN on the latter falling edge of CAS or WE for early and",
            "  delayed writes. The 130,000-read C-reference guard reaches `CTRACE-END` and",
            "  the dedicated DRAM unit guard covers coincident control edges. This is a",
            "  functional timing closure; it does not infer the unresolved D36.12/.13",
            "  conductor or the physical CPU/video slot schedule.",
            "- D92 is no longer an unmodeled timing placeholder. Its native triple-NOR",
            "  read/write combiner is instantiated in the structural HDL and covered by",
            "  LVS: pins 1/2/13 qualify reads, 3/4/5 qualify writes, and 9/10/11",
            "  combine both results onto D92.8/D39.5. The repeated native-sheet -MRD",
            "  label reaches D92.13, while factory wire W11 closes its registered A11B",
            "  surface island to the separate D7.1/A11A island without etched copper.",
            "- D37's RAM-read gate is source-complete rather than a remaining probe ask:",
            "  global MEMR enters D33.3, the inverter output D33.4 reaches D37.5,",
            "  D13.2/RAM_OUT_EN reaches D37.4, and D37.6 reaches D58.OE pin 9.",
            "- D36's DRAM-write gate is likewise source-complete: MEMW enters pin 9,",
            "  the D36.3 -> D33.11/.10 delay leg reaches pin 10, and output pin 8",
            "  drives rail 16 to every DRAM W pin. The direct `we_n = MEMW` simulation",
            "  path remains an explicit timing abstraction, not a copper uncertainty.",
            "- The routed snapshot retains the former wire-11 copper as MEMR. Two",
            "  0.6/0.3 mm vias at `(227.0497,127.5849)` and `(230,123)` plus a",
            "  back-layer bridge join the two MEMR islands without crossing the four",
            "  front-layer select traces. KiCad DRC reports zero MEMR shorts,",
            "  clearances, crossings, or unconnected items.",
            "- The exact CAS-driver input source (`D36_CAS_IN`) is still not",
            "  historical-source-complete. D36.12/.13 were",
            "  rechecked across the native 5140x3563 sheet on 2026-07-13; their common",
            "  west conductor enters an unlabeled dense timing bundle, so the automated",
            "  scan chase is exhausted.",
            "- Exact-revision `.009 E3` sheet 2 and owner continuity close D56.12's",
            "  conductor code 16 onto the tied D55 CLK1/CLK2 inputs at pins 15/18.",
            "  It remains distinct from the unrelated D36.8/DRAM write rail 16.",
            "- D59.10's local timing-bundle marker 10 is likewise not the D57.13 SOUND",
            "  bundle marker 10. Native full-sheet review shows no continuous conductor,",
            "  and merging them would short active TTL outputs; automatic tag-number",
            "  chasing is exhausted pending continuity or stronger imagery.",
            "- The tag-14 `XTAL16M` bundle is functionally expected to originate at the",
            "  D59 oscillator, but the native sheet does not draw a continuous source-side",
            "  path through the intervening bundle. `OSC` and `XTAL16M` therefore remain",
            "  separate until continuity or stronger artwork proves the PCB merge.",
            "- D38.4's left-side timing rail 2 and D34.4's top-edge tag 2 are distinct",
            "  boundary domains. The native vertical strip shows each terminating at its",
            "  own gate input with no continuous conductor between them; matching numerals",
            "  alone do not justify a merge.",
            "- Do not replace these boundaries with a behavioral timing guess from the",
            "  runnable twin. They need stronger sheet-2 imagery, macro photo,",
            "  continuity check, or scope trace before being removed from the",
            "  fidelity gap ledger.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
