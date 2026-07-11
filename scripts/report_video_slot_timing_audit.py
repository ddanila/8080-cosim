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
            marker("docs/video-readout-readiness.md", "Status: **RUNNABLE VIDEO READOUT GUARDED**", "byte-identical"),
            "`docs/video-readout-readiness.md` / `sync/video_readout_check.sh`",
        ),
        (
            "Physical D42/D43 ИР16 serializers are identified in the board model",
            chip_type(board, "D42") == "IR16" and chip_type(board, "D43") == "IR16",
            "`kicad/juku.board.json` D42/D43 identities",
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
            "D42/D43 serializer control/serial nets are present in the board JSON",
            serializer_ok,
            "`kicad/juku.board.json` LOAD_VID / D43_DS / D42_Q",
        ),
        (
            "D41 latch-chain output boundary is guarded",
            marker(
                "docs/d41-timing-boundary.md",
                "Status: **D41 OUTPUTS GUARDED / INPUT TIMING BUS PENDING**",
                "D41.QA selects D50",
                "pins 1-6/8-10",
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
            "Owner photo survey confirms a socketed top-center РЕ3 is dumpable",
            marker("ref/photos/juku-pcb-2/SURVEY.md", "К155РЕ3", "SOCKETED", "timing PROM", "dumpable"),
            "`ref/photos/juku-pcb-2/SURVEY.md`",
        ),
        (
            "Scanned `.113/.117` РЕ3 tables are guarded but not D94 `.092`",
            marker("docs/re3-firmware-inspection.md", "Status: **PASS**", "D94 `.092`", "neither table is present"),
            "`docs/re3-firmware-inspection.md`",
        ),
        (
            "No D94 `.092` programming table or dump is present under `ref/firmware`",
            not any(path.name.lower().endswith((".092", ".092.hex", "_092.hex")) for path in (ROOT / "ref" / "firmware").glob("*")),
            "`ref/firmware/` has no `.092` artifact",
        ),
        (
            "D94 FDC-control role is separated from video timing",
            marker(
                "docs/d94-reconstruction-constraints.md",
                "Status: **D94 RECONSTRUCTION CONSTRAINED / DUMP REQUIRED**",
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
            "- `docs/d41-timing-boundary.md`: generated D41 output-side net",
            "  guard plus explicit input/control timing-bus boundary.",
            "",
            "## Interpretation",
            "",
            "- The runnable path is guarded: raster geometry and byte-to-pixel serialization produce the",
            "  expected 40 x 241 framebuffer stream.",
            "- The physical chips for the serializer and mux/decode path are present in",
            "  the structural model, so this is no longer a vague video-output gap.",
            "- D41's output-side role is now narrowed: QA/QB are modeled, while",
            "  serial input/output, parallel inputs, load, gate, and clock remain a timing-bus",
            "  source-read/continuity boundary.",
            "- The missing piece is the exact video-read slot schedule around D41, D52,",
            "  D53, D56, and the adjacent one-shot/counter timing. D94 is not used as",
            "  video-timing evidence: its only proved outputs terminate at FDC D93.",
            "- Until those physical slot-control paths are traced, the honest",
            "  model keeps `VA/VQ` and `video_raster` as a sim-only runnable adjunct rather",
            "  than inventing a board-critical DRAM arbitration schedule.",
        ]
    )

    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if all(ok for _, ok, _ in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
