#!/usr/bin/env python3
"""Reproduce and document the physical-D6 runnable boundary across every mode."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "d6-runtime-path-diagnostic.md"
CHECKPOINT_REPORT = ROOT / "docs" / "ekdos-checkpoint-reference.md"
BOARD_JSON = ROOT / "kicad" / "juku.board.json"
EXPECTED_D8_OUTPUTS = {
    "1": ("D19", "20"), "2": ("D20", "20"),
    "3": ("D21", "20"), "4": ("D22", "20"),
    "5": ("D15", "20"), "6": ("D16", "20"),
    "7": ("D17", "20"), "9": ("D18", "20"),
}


def main() -> int:
    checkpoint = CHECKPOINT_REPORT.read_text(encoding="utf-8")
    checkpoint_ok = "| `pc` | `0484` |" in checkpoint and "| `portc` | `80` |" in checkpoint
    if not checkpoint_ok:
        raise SystemExit("D6 RUNTIME PATH DIAGNOSTIC: checkpoint PC/Port-C evidence is stale")
    board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    d8_output_nets = {}
    for name, record in board["nets"].items():
        nodes = {(str(ref), str(pin)) for ref, pin in record.get("nodes", [])}
        for pin in EXPECTED_D8_OUTPUTS:
            if ("D8", pin) in nodes:
                d8_output_nets[pin] = (name, nodes)
    d8_outputs_socket_only = all(
        pin in d8_output_nets
        and d8_output_nets[pin][1] == {("D8", pin), peer}
        for pin, peer in EXPECTED_D8_OUTPUTS.items()
    )
    if not d8_outputs_socket_only:
        raise SystemExit("D6 RUNTIME PATH DIAGNOSTIC: D8 output fanout changed; review qualifier evidence")
    with tempfile.TemporaryDirectory(prefix="d6-runtime-path.") as tmp_name:
        sim = Path(tmp_name) / "d6_runtime_path_tb"
        compile_proc = subprocess.run(
            [
                "iverilog", "-g2012", "-s", "d6_runtime_path_tb", "-o", str(sim),
                "hdl/devices.v",
                "hdl/sim/d6_runtime_path_tb.v",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        run_proc = subprocess.run(
            ["vvp", str(sim)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        ) if compile_proc.returncode == 0 else None

    output = run_proc.stdout if run_proc else compile_proc.stdout
    required = [
        "D6-RUNTIME-LOW-ROM ba=0484 mode=011 select_and_n=0 roe_n=1 d58_oe_n=1",
        "D6-RUNTIME-RAM ba=b37a mode=011 select_and_n=0 rev=0 roe_n=0 ram_out_en=1 d58_oe_n=0 oracle_ram_n=0 oracle_d58_oe_n=0",
        "D6-RUNTIME-ALL-MODES ba=b37a mode=000 word=1 d6_9=0 d13_2=1 d58_9=0",
        "D6-RUNTIME-ALL-MODES ba=b37a mode=001 word=f d6_9=1 d13_2=0 d58_9=1",
        "D6-RUNTIME-ALL-MODES ba=b37a mode=010 word=1 d6_9=0 d13_2=1 d58_9=0",
        "D6-RUNTIME-ALL-MODES ba=b37a mode=011 word=1 d6_9=0 d13_2=1 d58_9=0",
        "D6-RUNTIME-ALL-MODES ba=b37a mode=100 word=f d6_9=1 d13_2=0 d58_9=1",
        "D6-RUNTIME-ALL-MODES ba=b37a mode=101 word=f d6_9=1 d13_2=0 d58_9=1",
        "D6-RUNTIME-ALL-MODES ba=b37a mode=110 word=f d6_9=1 d13_2=0 d58_9=1",
        "D6-RUNTIME-ALL-MODES ba=b37a mode=111 word=f d6_9=1 d13_2=0 d58_9=1",
        "D6-RUNTIME-DISABLED ba=b37a word=f d6_9=1 d13_2=0 d58_9=1",
        "D6-RUNTIME-QUALIFIER mode=011 low_ba=0484 low_word=8 low_d8=ef ram_ba=b37a ram_word=1 ram_d8=ff",
        "D6-RUNTIME-PATH: CORRECTED TABLE MATCHES MEASURED MODE PATH",
    ]
    ok = compile_proc.returncode == 0 and run_proc is not None and run_proc.returncode == 0
    ok = ok and all(marker in output for marker in required)
    if not ok:
        print(output)
        raise SystemExit("D6 RUNTIME PATH DIAGNOSTIC: FAIL")

    lines = [
        "# D6 runnable-path diagnostic", "",
        "Status: **CORRECTED TABLE MATCHES MEASURED MODE PATH**", "",
        "This generated diagnostic guards the corrected 2026-07-19 D6 channel order",
        "through the exact D6/D8 and D13/D37/D58 combinational paths. It retains the",
        "former functional decoder only as a comparison at the RAM target.", "",
        "## Reproduction", "", "```sh",
        "python3 scripts/report_d6_runtime_path.py", "```", "",
        "The test reads the validated D6 table through `decode_prom`, then follows",
        "D6.9 through the modeled D13 Schmitt inverter and D37 NAND into D58 OE.",
        "It also samples `decode_prom_functional` only at `B37A`. The measured",
        "A6/A5=`/PC1,/PC0` mapping makes Port C `80` supply suffix `11`; with the",
        "temporarily forced-low unresolved A7, the runnable row is `011`.", "",
        "## Result", "", "```text", *output.strip().splitlines(), "```", "",
        "At low-ROM address `0484`, measured mode `011` emits word `8`: D6.12 sinks",
        "and enables the D8 pager. At RAM target `B37A`, the same mode emits word `1`:",
        "ROM releases, RAM and ROE sink, D13 output rises, and D37 enables D58. This",
        "matches the comparison oracle without any per-output inversion. D8 is `EF`",
        "at `0484` and `FF` at `B37A`.", "",
        "## Evidence boundary", "",
        "- Reader-3 socket continuity fixes D0..D3 as pins 12,11,10,9; three",
        "  identical D6 captures include a separate power cycle.",
        "- Chip-removed `.009` continuity proves the `.006` sheet's separate D6",
        "  ROM/RAM outputs are real: D6.12 reaches D8.15; D6.11 does not, and the",
        "  two socket pads are isolated. D6.11 instead reaches D2.15/-WREQ. The",
        "  earlier installed-PROM D6.11/D6.12 joined reading is invalidated. Follow-up",
        "  continuity proves D6.11 also reaches D92.5/R12.2 on the same -WREQ net.",
        "- The former all-mode failure was an artifact of the old reversed channel",
        "  packing. The corrected mode-011 row closes the observed runnable path.",
        "- Powered-off owner continuity now confirms the entire endpoint chain:",
        "  D6.9-D13.1, D13.2-D37.4, and D37.6-D58.9.",
        "  The second D37 NAND input is independently source-closed by the native",
        "  sheet-2 MEMR-D33.3/D33.4-D37.5 route; it is not a remaining probe ask.",
        "  Live probes remain useful corroboration but no longer gate D6 adoption.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("D6 RUNTIME PATH DIAGNOSTIC: PASS (corrected table matches measured mode)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
