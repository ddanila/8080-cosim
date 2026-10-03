#!/usr/bin/env python3
"""Generate an audit for the remaining faithful video/DRAM slot timing gap."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
REPORT = ROOT / "docs" / "video-slot-timing-audit.md"


def read(path: str) -> str:
    return (ROOT / path).read_text(errors="replace")


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def marker(path: str, *needles: str) -> bool:
    text = read(path)
    return all(needle in text for needle in needles)


def row(name: str, ok: bool, evidence: str) -> str:
    return f"| {name} | {'PASS' if ok else 'FAIL'} | {evidence} |"


def load_board() -> dict:
    return json.loads(BOARD.read_text())


def net_has(board: dict, net_name: str, *nodes: tuple[str, str]) -> bool:
    net = board["nets"].get(net_name)
    if net is None:
        return False
    have = {tuple(node) for node in net.get("nodes", [])}
    return all(node in have for node in nodes)


def chip_type(board: dict, ref: str) -> str:
    for chip in board["chips"]:
        if chip.get("ref") == ref:
            return str(chip.get("type", ""))
    return ""


def main() -> int:
    board = load_board()
    va_ok = all(
        net_has(board, f"VA{bit}", (f"D{44 + bit // 4}", str(pin)))
        for bit, pin in enumerate((3, 2, 6, 7, 3, 2, 6, 7, 3, 2, 6, 7, 3, 2, 6, 7))
    )
    d53_outputs = (
        ("D53_Y0_R49", "15", "R49"),
        ("D53_Y1_R50", "14", "R50"),
        ("D53_Y2_R51", "13", "R51"),
        ("D53_Y3_R52", "12", "R52"),
    )
    d53_ok = all(net_has(board, name, ("D53", pin), (res, "1")) for name, pin, res in d53_outputs)
    serializer_ok = all(
        net_has(board, net, (ref, pin))
        for net, ref, pin in (
            ("LOAD_VID", "D42", "6"),
            ("LOAD_VID", "D43", "6"),
            ("D43_DS", "D42", "1"),
            ("D43_DS", "D43", "10"),
            ("D42_Q", "D42", "10"),
            ("SHIFT_G", "D42", "8"),
            ("SHIFT_G", "D43", "8"),
        )
    )
    checks: list[tuple[str, bool, str]] = [
        (
            "Runnable raster geometry is guarded",
            marker("docs/video-timing-reference.md", "Status: **VIDEO RASTER GEOMETRY GUARDED**", "40 x 241 byte raster"),
            "`docs/video-timing-reference.md` / `sync/video_timing_check.sh`",
        ),
        (
            "Runnable byte-to-pixel readout is guarded",
            marker(
                "docs/video-readout-readiness.md",
                "Status: **RUNNABLE ABSTRACT VIDEO READOUT GUARDED**",
                "byte-identical",
                "not composite voltage",
            ),
            "`docs/video-readout-readiness.md` / `sync/video_readout_check.sh`",
        ),
        (
            "ROM-programmed autonomous raster timing is guarded",
            marker(
                "docs/video-pit-timing.md",
                "AUTONOMOUS PIT RASTER TIMING GUARDED",
                "15.625 kHz",
                "320x241",
                "DRAM SLOT",
            ),
            "`docs/video-pit-timing.md`: D54/D55/D56/D34_SYNC timing",
        ),
        (
            "Physical D42/D43 ИР16 serializers are identified in the board model",
            chip_type(board, "D42") == "IR16" and chip_type(board, "D43") == "IR16",
            "`kicad/juku.board.json` D42/D43 identities",
        ),
        (
            "D41/D42/D43 ИР16 primitive semantics are datasheet-guarded",
            marker(
                "docs/ir16-readiness.md",
                "DATASHEET-EXACT ИР16 PRIMITIVE GUARDED",
                "falling clock edge",
                "active-high three-state output control",
                "SHIFT_G",
            ),
            "`docs/ir16-readiness.md`: LD/SH, clock edge, and OC behavior",
        ),
        (
            "Physical serializer instances exist in `juku_top`",
            marker("hdl/juku_top.v", "ir16 U_D42", "ir16 U_D43", "load_vid"),
            "`hdl/juku_top.v`",
        ),
        (
            "Physical CPU/video mux and D53 decode instances exist in `juku_top`",
            marker("hdl/juku_top.v", "kp14_mux U_D48", "kp14_mux U_D49", "kp14_mux U_D50", "kp14_mux U_D51", "rascas_dec U_D53"),
            "`hdl/juku_top.v`",
        ),
        (
            "D48-D52 КП14 inversion and three-state behavior are datasheet-guarded",
            marker(
                "docs/kp14-readiness.md",
                "DATASHEET-EXACT INVERTING КП14 PRIMITIVE GUARDED",
                "selected A or B input is inverted",
                "/G=1 produces Z",
            ),
            "`docs/kp14-readiness.md`: SN74LS/S258 truth table",
        ),
        (
            "D59 complementary CPU/video mux-enable inverter is source-traced",
            net_has(board, "LATCH_B", ("D40", "11"), ("D59", "5"), ("E14", "1"), ("E14", "3"), ("D50", "15"), ("D51", "15"))
            and net_has(board, "CPU_MUX_G", ("D59", "6"), ("E13", "1"), ("E13", "3"), ("D48", "15"), ("D49", "15"))
            and ["D59", "5"] not in board.get("no_connects", [])
            and ["D59", "6"] not in board.get("no_connects", []),
            "sheet-2 D59.5->E14/video /G; inverted D59.6->E13/CPU /G",
        ),
        (
            "Video counter address nets VA0-VA15 are present in the board JSON",
            va_ok,
            "`kicad/juku.board.json` VA0-VA15 from D44-D47 into the mux stage",
        ),
        (
            "D53 bank/RAS ladder outputs are present in the board JSON",
            d53_ok,
            "`kicad/juku.board.json` D53_Y0_R49..D53_Y3_R52",
        ),
        (
            "PIT video/baud timing endpoints are source-complete",
            net_has(board, "HOR_RTR", ("D54", "13"))
            and net_has(board, "VERT_SYNC", ("D55", "17"))
            and net_has(board, "CLK_123M", ("D103", "11"), ("D57", "9"))
            and net_has(board, "VERT_RTR", ("D55", "13"), ("D57", "18"))
            and net_has(board, "P5V", ("D57", "11")),
            "exact .009 E3 D54 HOR RTR, D55 VERT SYNC, D57 CLK0/GATE0, and D57 CLK2=/VER RTR labels",
        ),
        (
            "D42/D43 serializer control/serial nets are present in the board JSON",
            serializer_ok,
            "`kicad/juku.board.json` LOAD_VID / D43_DS / D42_Q",
        ),
        (
            "D41 package timing connectivity is source-closed",
            marker(
                "docs/d41-timing-boundary.md",
                "Status: **D41 PACKAGE CONNECTIVITY SOURCE-CLOSED**",
                "D41.QA selects both D50/D51",
                "LD joins numbered timing rail 17; CK joins numbered rail 8",
            ),
            "`docs/d41-timing-boundary.md`",
        ),
        (
            "Runnable video still uses the abstract raster/read port",
            marker("hdl/juku_top.v", "video_raster U_VRAS", "ir16_sr U_IR16", "sim-only 2nd port"),
            "`hdl/juku_top.v` runnable adjunct",
        ),
        (
            "The DRAM model still exposes sim-only video read pins",
            marker("hdl/devices.v", "input wire [15:0] va, output wire vq", "SIM-ONLY 2nd read port"),
            "`hdl/devices.v::dram_64kx1`",
        ),
        (
            "LVS explicitly treats the sim-only video read pins as non-board pins",
            marker("sync/lvs.py", '"VA", "VQ"', "sim-only 2nd (video) read port"),
            "`sync/lvs.py` SIM_ONLY contract",
        ),
        (
            "Owner photo survey separates socketed РЕ3 from an assumed video role",
            marker("ref/photos/juku-pcb-2/SURVEY.md", "К155РЕ3", "SOCKETED", "does not", "video-timing role", "dumpable"),
            "`ref/photos/juku-pcb-2/SURVEY.md`",
        ),
        (
            "Scanned `.113/.117` РЕ3 tables are guarded but not D94 `.092`",
            marker("docs/re3-firmware-inspection.md", "Status: **PASS**", "D94 `.092`", "neither scanned table represents those parts"),
            "`docs/re3-firmware-inspection.md`",
        ),
        (
            "Owner-scan firmware directory has no mislabeled D94 `.092` table",
            not any(path.name.lower().endswith((".092", ".092.hex", "_092.hex")) for path in (ROOT / "ref" / "firmware").glob("*")),
            "`ref/firmware/` has no `.092` artifact",
        ),
        (
            "D94 FDC-control role is separated from video timing",
            marker(
                "docs/d94-reconstruction-constraints.md",
                "Status: **D94 PHYSICAL TABLE ADOPTED / CONNECTIVITY GUARDED**",
                "D94 is now classified as an FDC control/decode PROM",
            ),
            "`docs/d94-reconstruction-constraints.md`; only proved outputs terminate at D93",
        ),
    ]

    status = "VIDEO SLOT TIMING AUDITED / PHYSICAL SLOT SCHEDULE PENDING" if all(ok for _, ok, _ in checks) else "VIDEO SLOT TIMING AUDIT FAILED"

    lines = [
        "# Video slot timing audit",
        "",
        f"Status: **{status}**",
        "",
        "This generated audit tracks the remaining faithful-video boundary: replacing the",
        "runnable sim-only framebuffer read path with the faithful КП14/ИД7/АГ3/РЕ3",
        "shared-DRAM video slot schedule.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_video_slot_timing_audit.py",
        "```",
        "",
        "## Checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    lines.extend(row(name, ok, evidence) for name, ok, evidence in checks)
    lines.extend(
        [
            "",
            "## Guarded Inputs",
            "",
            f"- `ref/firmware/re3_dgsh5.106.113.hex`: `{sha256('ref/firmware/re3_dgsh5.106.113.hex')}`",
            f"- `ref/firmware/re3_dgsh5.106.117.hex`: `{sha256('ref/firmware/re3_dgsh5.106.117.hex')}`",
            "- `docs/d94-reconstruction-constraints.md`: generated D94 `.092` FDC",
            "  control/address/firmware boundary; D94 is not used as video-timing evidence.",
            "- [D41 boundary](d41-timing-boundary.md): complete package connectivity",
            "  disposition and the remaining remote rail-17 source boundary.",
            "",
            "## Interpretation",
            "",
            "- This audit checks board endpoints, HDL text and recorded-report markers.",
            "  It does not execute the raster, serializer or mux tests; use the commands",
            "  cited in the table to refresh their runtime evidence.",
            "- The runnable video adjunct reads 40 bytes per line for 241 lines from",
            "  a second, simulation-only DRAM port. Physical serializer and mux",
            "  instances coexist with that adjunct in `juku_top`.",
            "- The ИР16 model uses falling-edge clocks, high LD/SH for parallel load,",
            "  low LD/SH for shift, and active-high output control. `SHIFT_G` drives",
            "  D42/D43 OC; its sheet-traced D35.6/R38.1 connection has no owner-board",
            "  continuity measurement.",
            "- D48-D52 preserve КП14 inversion and three-state disable behavior; the",
            "  DRAM model normalizes the inversion at its internal address index.",
            "- D59.5 reaches the video /G rail and D59.6 the CPU /G rail. The measured",
            "  D40.11 1 MHz branch is documented in the",
            "  [clock-route report](d40-d59-d92-d95-1mhz-route.md). Yosys/LVS uses",
            "  the complementary enables; runnable simulation keeps CPU MA selected.",
            "- D41 package connectivity is source-closed. Its remote rail-17 origin",
            "  remains a timing-chain boundary. The exact shared-DRAM slot schedule",
            "  around D41/D50-D53 and the D34 signal input remain unresolved.",
            "- D94 is FDC control and provides no video-slot timing evidence.",

        ]
    )

    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if all(ok for _, ok, _ in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
