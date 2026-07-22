#!/usr/bin/env python3
"""Guard source-proved physical video probes and their controlled event export."""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "video-physical-probes.md"
BOARD = ROOT / "kicad" / "juku.board.json"
TOP = ROOT / "hdl" / "juku_top.v"
TB = ROOT / "hdl" / "sim" / "video_physical_probe_tb.v"


def nodes(board: dict, name: str) -> set[tuple[str, str]]:
    return {tuple(item) for item in board["nets"][name]["nodes"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--events",
        type=Path,
        help="preserve the generated controlled-stimulus CSV at this path",
    )
    args = parser.parse_args()

    board = json.loads(BOARD.read_text(encoding="utf-8"))
    top = TOP.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="juku-video-probes-") as tmp_name:
        tmp = Path(tmp_name)
        sim = tmp / "video_physical_probe"
        event_path = args.events.resolve() if args.events else tmp / "events.csv"
        event_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "iverilog", "-g2012", "-s", "video_physical_probe_tb",
                "-o", str(sim),
                "hdl/vendor/vm80a.v", "hdl/devices.v", "hdl/juku_top.v",
                "hdl/sim/video_physical_probe_tb.v",
            ],
            cwd=ROOT,
            check=True,
        )
        run = subprocess.run(
            ["vvp", str(sim), f"+events={event_path}"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        with event_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

    def at(time_ns: float) -> dict[str, str]:
        return next(row for row in rows if float(row["time_ns"]) == time_ns)

    checks = [
        (
            "Probe testbench passes its pulse/truth assertions",
            "VIDEO-PHYSICAL-PROBE: PASS" in run.stdout,
            "iverilog/vvp controlled-stimulus test",
        ),
        (
            "Explicit top-level probes expose only bounded contributors",
            all(
                marker in top
                for marker in (
                    "probe_d42_q", "probe_d43_q", "probe_d37_pixel_n",
                    "probe_d34_sync", "probe_d56_q_n", "probe_d56_q2",
                    "probe_pit_hsync", "probe_pit_vsync", "probe_load_vid",
                )
            )
            and "probe_d34_sig" not in top.lower(),
            "D34_SIG is intentionally absent while its input function remains open",
        ),
        (
            "Shared-DRAM slot uncertainty is machine-visible",
            "assign probe_slot_schedule_known = 1'b0" in top
            and rows
            and all(row["slot_schedule_known"] == "0" for row in rows),
            "every exported row carries slot_schedule_known=0",
        ),
        (
            "D56 section-2 pulse is the guarded 5.04 us diagnostic",
            at(100.0)["d56_q2"] == "1"
            and at(5140.0)["d56_q2"] == "0",
            "R47=20k/C7=560pF typical model: 100..5140 ns",
        ),
        (
            "D56 section-1 pulse is the guarded 223 us diagnostic",
            at(10000.0)["d56_q_n"] == "0"
            and at(233000.0)["d56_q_n"] == "1",
            "R59=33k/C8=15nF typical model: 10000..233000 ns",
        ),
        (
            "D34 sync probe obeys the traced XOR inputs",
            all(
                int(row["d34_sync"])
                == (int(row["d56_q2"]) ^ int(row["d56_q_n"]))
                for row in rows
            ),
            "D34 pins 9,10 -> 8: D56.Q2 XOR D56.Q_N",
        ),
        (
            "Board endpoints for the probed physical sync chain remain exact",
            nodes(board, "D34_SYNC") == {("D34", "8"), ("R62", "1")}
            and nodes(board, "D56_Q2_D34") == {("D56", "5"), ("D34", "9")}
            and nodes(board, "D56_QN_D34") == {("D56", "4"), ("D34", "10")},
            "board JSON exact endpoint sets",
        ),
    ]
    ok = all(result for _, result, _ in checks)

    lines = [
        "# Physical video contributor probes",
        "",
        "Status: **PHYSICAL CONTRIBUTORS PROBED / CONTROLLED STIMULUS ONLY / SLOT + D34_SIG OPEN**."
        if ok else "Status: **PHYSICAL VIDEO PROBE CHECK FAILED**.",
        "",
        "This generated report guards explicit simulation observability for the",
        "source-proved D42/D43/D37 and D54/D55/D56/D34_SYNC contributors. The",
        "event export uses controlled PIT trigger stimulus solely to prove the traced",
        "component chain and modeled one-shot durations. It is not a Juku raster,",
        "D34_SIG waveform, transistor waveform, composite voltage, or X7 sample stream.",
        "",
        "## Commands",
        "",
        "```sh",
        "python3 scripts/report_video_physical_probes.py",
        "python3 scripts/report_video_physical_probes.py --events /tmp/video-events.csv",
        "```",
        "",
        "## Checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    for name, result, evidence in checks:
        lines.append(f"| {name} | {'PASS' if result else 'FAIL'} | {evidence} |")
    lines.extend([
        "",
        "## Exported event schema",
        "",
        "`time_ns,pit_hsync,pit_vsync,d56_q_n,d56_q2,d56_q2_n,d34_sync,`",
        "`d42_q,d43_q,d37_pixel_n,load_vid,slot_schedule_known`",
        "",
        "The controlled run emits the following transition times:",
        "",
        "| Event | Time |",
        "| --- | ---: |",
        "| D56.Q2 asserted | 100 ns |",
        "| D56.Q2 released | 5,140 ns |",
        "| D56.Q_N asserted low | 10,000 ns |",
        "| D56.Q_N released high | 233,000 ns |",
        "",
        "## Deliberate boundaries",
        "",
        "- `probe_slot_schedule_known` is hard-low until the physical shared-DRAM",
        "  arbitration schedule is source-complete.",
        "- D34_SIG is not exported because its input function remains described only",
        "  as the open `pixel^REV?` boundary in the board evidence.",
        "- D42/D43/D37 probes are physical-net observability only; under this controlled",
        "  test they do not claim a valid fetched framebuffer byte.",
        "- D34 output-drive current, VT2, the 75-ohm load, C94, and X7 voltage remain",
        "  separate WP4/physical-calibration boundaries.",
        "",
    ])
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(lines[2])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
