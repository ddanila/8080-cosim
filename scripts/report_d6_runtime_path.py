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
        "D6-RUNTIME-LOW-ROM ba=0484 mode=000 join_n=0 roe_n=1 d58_oe_n=1",
        "D6-RUNTIME-RAM ba=b37a mode=000 join_n=0 rev=0 roe_n=1 ram_out_en=0 d58_oe_n=1 oracle_ram_n=0 oracle_d58_oe_n=0",
        "D6-RUNTIME-ALL-MODES ba=b37a mode=000 word=8 d6_9=1 d13_2=0 d58_9=1",
        "D6-RUNTIME-ALL-MODES ba=b37a mode=001 word=f d6_9=1 d13_2=0 d58_9=1",
        "D6-RUNTIME-ALL-MODES ba=b37a mode=010 word=8 d6_9=1 d13_2=0 d58_9=1",
        "D6-RUNTIME-ALL-MODES ba=b37a mode=011 word=8 d6_9=1 d13_2=0 d58_9=1",
        "D6-RUNTIME-ALL-MODES ba=b37a mode=100 word=f d6_9=1 d13_2=0 d58_9=1",
        "D6-RUNTIME-ALL-MODES ba=b37a mode=101 word=f d6_9=1 d13_2=0 d58_9=1",
        "D6-RUNTIME-ALL-MODES ba=b37a mode=110 word=f d6_9=1 d13_2=0 d58_9=1",
        "D6-RUNTIME-ALL-MODES ba=b37a mode=111 word=f d6_9=1 d13_2=0 d58_9=1",
        "D6-RUNTIME-DISABLED ba=b37a word=f d6_9=1 d13_2=0 d58_9=1",
        "D6-RUNTIME-QUALIFIER mode=000 low_ba=0484 low_word=8 low_d8=ef ram_ba=b37a ram_word=8 ram_d8=ff",
        "D6-RUNTIME-PATH: BOUNDARY REPRODUCED",
    ]
    ok = compile_proc.returncode == 0 and run_proc is not None and run_proc.returncode == 0
    ok = ok and all(marker in output for marker in required)
    if not ok:
        print(output)
        raise SystemExit("D6 RUNTIME PATH DIAGNOSTIC: FAIL")

    lines = [
        "# D6 runnable-path diagnostic", "",
        "Status: **ALL PHYSICAL MODES EXHAUSTED AT THE RAM GATE BOUNDARY**", "",
        "This generated diagnostic preserves the exact combinational failure found",
        "while testing whether the runnable boot could use D6 `.038` directly. It is",
        "not a replacement memory decoder and does not bless the compatibility oracle.",
        "It exhaustively proves that changing the three D6 mode inputs cannot repair",
        "the observed RAM-read failure at the first checkpoint call target, then",
        "identifies the first address-sensitive physical distinction downstream.", "",
        "## Reproduction", "", "```sh",
        "python3 scripts/report_d6_runtime_path.py", "```", "",
        "The test reads the validated D6 table through `decode_prom`, then follows",
        "D6.9 through the modeled D13 Schmitt inverter and D37 NAND into D58 OE.",
        "It also samples `decode_prom_functional` only to state the established",
        "runnable behavior at the same addresses. The test then evaluates all eight",
        "PC4..PC2 combinations at `B37A` against the raw four-bit PROM word. The",
        "guarded checkpoint starts at PC `0484` with Port C `80`, hence physical",
        "mode `000`; the test also evaluates D8's physical pager output at that",
        "fetch and at `B37A`.", "",
        "## Result", "", "```text", *output.strip().splitlines(), "```", "",
        "At low-ROM address `0484`, physical word `8` correctly leaves D58 released",
        "while the joined D6 conductor enables the D8 pager. At RAM call target",
        "`B37A`, mode `000` emits word `8`. Exhaustive evaluation shows words `8`",
        "or `F` in every possible mode; both leave physical D6.9 high. Disabling the",
        "PROM would also release pin 9 high. The currently traced D13/D37 polarity",
        "therefore keeps D58 OE high regardless of PC2/PC3/PC4 or the unresolved V1/V2",
        "feed. The checkpoint-resume",
        "experiment consequently consumed `FF` at the RAM call and never reached the",
        "PIC/keyboard boundary. Restoring the explicit oracle returned the guard to",
        "`PASS` at 25,744 resumed machine cycles.", "",
        "D6 itself cannot distinguish the two mode-`000` addresses: both emit word",
        "`8`. D8 can: its pager word is `EF` at `0484` (D15 selected) and `FF` at",
        "`B37A` (all ROM sockets released). The current RAM-output model has no D8",
        "or equivalent address-sensitive qualifier between D13 and D58. This does",
        "not prove an unobserved D8 feedback net; it proves that the modeled D6-only",
        "gate lacks the information required to separate these two reads. Board JSON",
        "also confirms every D8 output currently has exactly one peer, its corresponding",
        "D15-D22 socket CE; there is no modeled feedback branch to the RAM gate.", "",
        "## Evidence boundary", "",
        "- The RT4 reader wiring and repeated table are guarded independently; this",
        "  result is not evidence to reorder or complement the dump.",
        "- The `.006` sheet shows separate D6 ROM/RAM outputs. Direct owner continuity",
        "  on the `.009` board instead reported D6.11, D6.12, and D13.12 joined and",
        "  found no D8/D9 continuation. The source model currently retains older-sheet",
        "  D8/D92 branches on that joined net, so this cross-revision contradiction",
        "  must be resolved before the oracle can be retired.",
        "- Mode selection and the D6 enable feed are now excluded as explanations for",
        "  the `B37A` D6.9 level: no physical row can pull pin 9 low there. The remaining",
        "  contradiction is in endpoint assignment, downstream polarity/function, or",
        "  the assumption that this RAM read reaches DB through D58.",
        "- In checkpoint mode `000`, every D6 output bit is identical at `0484` and",
        "  `B37A` (word `8`). Any authentic distinction therefore requires another",
        "  address-sensitive condition; D8's `EF` versus `FF` pager result is the first",
        "  proved such distinction, but no feedback branch is promoted without copper.",
        "- The decisive hardware check is an isolated, powered-off resistance map with",
        "  D6 and D13 removed: verify D6.9-D13.1, D13.2-D37.4, and D37.6-D58.9",
        "  independently, as well as D6.11/.12 against D13.12, D8.15, D92.5, R11.2,",
        "  and R12.2. Then record live D6.9, D13.2, D37.6, D58.9, and D58.11 during",
        "  the known `B37A` RAM read. Do not infer a new net merely to make boot pass.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("D6 RUNTIME PATH DIAGNOSTIC: PASS (all modes exhausted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
