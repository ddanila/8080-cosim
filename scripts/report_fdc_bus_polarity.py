#!/usr/bin/env python3
"""Pin the firmware-visible D100/D93 data-bus polarity contradiction."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "fdc-bus-polarity.md"
BOARD = ROOT / "kicad" / "juku.board.json"
TOP = ROOT / "hdl" / "juku_top.v"
DEVICES = ROOT / "hdl" / "devices.v"
OFFICIAL_CENSUS = ROOT / "ref" / "juku-official-009-ic-census.json"
ROM = ROOT / "roms" / "ekta37.bin"
D15_IMAGE = ROOT / "ref" / "eprom-images" / "d15_ekta37_low.bin"
D16_IMAGE = ROOT / "ref" / "eprom-images" / "d16_ekta37_high.bin"
ROM_SHA256 = "fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27"
IO_RE = re.compile(
    r"^\[IOSEQ\] OUT port=0x1C value=0x([0-9A-Fa-f]{2}) "
    r"cyc=([0-9]+) pc=([0-9A-Fa-f]{4}) g_vw=([0-9]+) count=1$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class Scenario:
    name: str
    rom: str
    max_cycles: str
    env: dict[str, str]
    expected_value: int
    expected_pc: int


SCENARIOS = (
    Scenario(
        "EKDOS TDD first command",
        "ekta37.bin",
        "6700000",
        {
            "JUKU_KEYS": "TDD",
            "JUKU_DISK": str(ROOT / "media" / "disks" / "JUKU1.CPM"),
        },
        0x02,
        0xE5DE,
    ),
    Scenario(
        "Monitor 3.3 T command",
        "jmon33.bin",
        "9300000",
        {
            "JUKU_KEYBOARD_ENABLE": "1",
            "JUKU_KEYS": "T\n",
            "JUKU_KEY_START_VRAM": "210",
            "JUKU_KEY_HOLD_FRAMES": "20",
            "JUKU_KEY_GAP_FRAMES": "6",
        },
        0xFD,
        0xE2B7,
    ),
)


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def compile_trace(tmp: Path) -> Path:
    trace = tmp / "trace"
    subprocess.run(
        [
            os.environ.get("CC", "cc"),
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(ROOT / "cosim"),
            "-o",
            str(trace),
            str(ROOT / "cosim" / "trace.c"),
            str(ROOT / "cosim" / "i8080.c"),
            str(ROOT / "cosim" / "juk_disk.c"),
            str(ROOT / "cosim" / "juku_fdc.c"),
        ],
        cwd=ROOT,
        check=True,
    )
    return trace


def run_scenario(trace: Path, scenario: Scenario) -> dict[str, int]:
    env = os.environ.copy()
    env.update(scenario.env)
    env["JUKU_TRACE_IO"] = "1"
    proc = subprocess.run(
        [
            str(trace),
            str(ROOT / "roms" / scenario.rom),
            scenario.max_cycles,
            "0",
            "200000",
        ],
        cwd=ROOT / "cosim",
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{scenario.name}: trace exited {proc.returncode}")
    match = IO_RE.search(proc.stderr)
    if not match:
        raise RuntimeError(f"{scenario.name}: first FDC command was not reached")
    value, cycles, pc, vram_writes = match.groups()
    return {
        "value": int(value, 16),
        "cycles": int(cycles),
        "pc": int(pc, 16),
        "vram_writes": int(vram_writes),
    }


def chip(board: dict[str, object], ref: str) -> dict[str, object]:
    return next(item for item in board["chips"] if item["ref"] == ref)


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="fdc-bus-polarity.") as tmp_name:
        trace = compile_trace(Path(tmp_name))
        results = [(scenario, run_scenario(trace, scenario)) for scenario in SCENARIOS]

    for scenario, result in results:
        require(
            result["value"] == scenario.expected_value,
            f"{scenario.name}: value 0x{result['value']:02X}, expected 0x{scenario.expected_value:02X}",
            failures,
        )
        require(
            result["pc"] == scenario.expected_pc,
            f"{scenario.name}: PC 0x{result['pc']:04X}, expected 0x{scenario.expected_pc:04X}",
            failures,
        )

    board = json.loads(BOARD.read_text(encoding="utf-8"))
    d93 = chip(board, "D93")
    d100 = chip(board, "D100")
    d1 = chip(board, "D1")
    d5 = chip(board, "D5")
    d15 = chip(board, "D15")
    d16 = chip(board, "D16")
    require(d93["type"] == "VG93_FDC", f"D93 type changed to {d93['type']}", failures)
    require(d100["type"] == "BUF8287", f"D100 type changed to {d100['type']}", failures)
    require(d1["type"] == "CPU8080", f"D1 type changed to {d1['type']}", failures)
    require(d5["type"] == "SYS8238", f"D5 type changed to {d5['type']}", failures)
    require(d15["type"] == "EPROM8K", f"D15 type changed to {d15['type']}", failures)
    require(d16["type"] == "EPROM8K", f"D16 type changed to {d16['type']}", failures)

    cpu_pins = (10, 9, 8, 7, 3, 4, 5, 6)
    d5_cpu_pins = (19, 17, 10, 21, 6, 15, 12, 8)
    d5_db_pins = (18, 16, 9, 20, 5, 13, 11, 7)
    rom_data_pins = (11, 12, 13, 15, 16, 17, 18, 19)
    for bit in range(8):
        dc_nodes = {tuple(node) for node in board["nets"][f"DC{bit}"]["nodes"]}
        require(
            dc_nodes == {("D1", str(cpu_pins[bit])), ("D5", str(d5_cpu_pins[bit]))},
            f"DC{bit} no longer exclusively joins D1.{cpu_pins[bit]} to D5.{d5_cpu_pins[bit]}",
            failures,
        )
        db_nodes = {tuple(node) for node in board["nets"][f"DB{bit}"]["nodes"]}
        for node in (
            ("D5", str(d5_db_pins[bit])),
            ("D15", str(rom_data_pins[bit])),
            ("D16", str(rom_data_pins[bit])),
            ("D100", str(1 + bit)),
        ):
            require(node in db_nodes, f"DB{bit} no longer contains {node[0]}.{node[1]}", failures)
    for bit in range(8):
        net = board["nets"][f"FDC_DAL{bit}"]
        nodes = {tuple(node) for node in net["nodes"]}
        require(
            ("D100", str(19 - bit)) in nodes and ("D93", str(7 + bit)) in nodes,
            f"FDC_DAL{bit} no longer joins D100.{19 - bit} to D93.{7 + bit}",
            failures,
        )

    census = json.loads(OFFICIAL_CENSUS.read_text(encoding="utf-8"))
    d5_census = next(row for row in census["rows"] if "D5" in row["refs"])
    d100_census = next(row for row in census["rows"] if "D100" in row["refs"])
    require(d5_census["marking"] == "КР580ВК38", "official D5 marking changed", failures)
    require(d100_census["marking"] == "КР580ВА87", "official D100 marking changed", failures)

    rom = ROM.read_bytes()
    d15_image = D15_IMAGE.read_bytes()
    d16_image = D16_IMAGE.read_bytes()
    require(len(rom) == 0x4000, f"ekta37 size changed to {len(rom)}", failures)
    require(hashlib.sha256(rom).hexdigest() == ROM_SHA256, "ekta37 SHA256 changed", failures)
    require(d15_image + d16_image == rom, "D15+D16 programming images no longer reproduce ekta37", failures)
    require(rom[:3] == bytes((0xC3, 0x17, 0x00)), "ekta37 reset vector is no longer JMP 0x0017", failures)

    top = TOP.read_text(encoding="utf-8")
    devices = DEVICES.read_text(encoding="utf-8")
    require(
        "buf_8287   U_D100 (.a(DB), .b(fdc_dal)" in top,
        "D100 no longer spans DB and fdc_dal",
        failures,
    )
    require(
        "fdc_1793  U_FDC  (.A(BA[1:0]), .D(DB)" in top,
        "behavioral FDC no longer consumes logical DB directly",
        failures,
    )
    require(
        "module buf_8287" in devices and "assign b = 8'hzz" in devices,
        "physical D100 is no longer an explicitly non-driving structural stub",
        failures,
    )
    require(
        "assign D  = (dbin  & ~busen_n) ? DB : 8'bz" in devices
        and "assign DB = (~wr_n & ~busen_n) ? D  : 8'bz" in devices,
        "D5 behavioral bridge is no longer explicitly bit-for-bit",
        failures,
    )
    require(
        "eprom_8k #(.HALF(0)) U_D15" in top and "eprom_8k #(.HALF(1)) U_D16" in top,
        "D15/D16 no longer expose the exact low/high ROM halves on DB",
        failures,
    )

    status = "FIRMWARE/PART POLARITY CONTRADICTION ISOLATED" if not failures else "FDC BUS POLARITY AUDIT FAILED"
    lines = [
        "# FDC data-bus polarity audit",
        "",
        f"Status: **{status}**",
        "",
        "The `.009` population, straight D100-to-D93 channel wiring, and exact",
        "firmware command bytes do not yet form one electrically coherent claim.",
        "This report keeps the runnable logical FDC model separate from that physical",
        "contradiction and turns it into a decisive operating-level measurement.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_fdc_bus_polarity.py",
        "```",
        "",
        "## Exact firmware observations",
        "",
        "| Path | CPU-visible OUT 0x1C | Direct VG93 meaning | Through one 8287 inversion | Cycle | PC | VRAM writes |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: |",
    ]
    meanings = {
        0x02: ("restore, step-rate 2", "write track (0xF? family)"),
        0xFD: ("write track (0xF? family)", "restore, step-rate 2"),
    }
    for scenario, result in results:
        direct, inverted = meanings[result["value"]]
        lines.append(
            f"| {scenario.name} | `0x{result['value']:02X}` | {direct} | {inverted} | "
            f"`{result['cycles']}` | `0x{result['pc']:04X}` | `{result['vram_writes']}` |"
        )

    lines.extend(
        [
            "",
            "The EKDOS path only succeeds when its first `0x02` is interpreted as",
            "Restore; interpreting it as `0xFD` would request an entire-track write",
            "before the boot-sector reads. Monitor 3.3 deliberately emits the opposite",
            "byte at its `T` command boundary. The two observations exchange meanings",
            "under a single inversion, so this is not a one-command decoder ambiguity.",
            "",
            "## Upstream D5 cancellation excluded",
            "",
            "D5 cannot supply a second, hidden complement that makes D100 electrically",
            "transparent:",
            "",
            "- The official population identifies D5 as `КР580ВК38`. The 1988 Soviet",
            "  КР580 reference, section 3.12, draws every D0..D7 channel directly to its",
            "  same-numbered DB0..DB7 channel with bidirectional arrows and no inversion",
            "  bubbles (figures 3.73 and 3.74, printed page 161). It says the ВК28 and",
            "  ВК38 differ only in the duration/source timing of the two write strobes.",
            "- The same reference explicitly calls `КР580ВА87` the inverting variant",
            "  beside non-inverting `КР580ВА86`, and draws bubbles on all ВА87 B-side",
            "  channels (section 3.14, figure 3.79, printed page 166). The notation is",
            "  therefore polarity-significant rather than an omitted drawing detail.",
            "- Board topology is bit-for-bit from D1 CPU `DC0..DC7` through D5 to system",
            "  `DB0..DB7`. Those same DB rails directly join D15/D16 data pins and D100",
            "  A0..A7; there is no intervening data permutation or inverter.",
            "- The guarded functional D15+D16 images concatenate exactly to the known",
            f"  `{ROM_SHA256}`",
            "  ekta37 image. Its reset bytes are `C3 17 00` (8080",
            "  `JMP 0017`); one complement would be `3C E8 FF`, which is not that boot",
            "  vector. This is a logical replica constraint, not a substitute for the",
            "  still-requested Tier-3 physical D15/D16 repeat dumps.",
            "",
            "The runnable `sysctl_8238` bridge therefore remains non-inverting. Making",
            "D5 invert merely to cancel D100 would contradict the device symbol, the",
            "straight board topology, and every direct system-bus ROM/peripheral path.",
            "",
            "## Physical evidence",
            "",
            "- Factory `.009` census position D100 is `КР580ВА87`, the inverting",
            "  Intel-8287-compatible bidirectional transceiver; the target component",
            "  photograph independently shows that marking.",
            "- D100 channels are straight: A0..A7 on system `DB0..DB7` pair with",
            "  B0..B7 on D93 `DAL0..DAL7`; no bit permutation can cancel a bitwise",
            "  complement.",
            "- D93 is the populated `КР1818ВГ93`. Its documented command families use",
            "  the normal logical codes (`0x0?` Restore, `0xF?` Write Track), matching",
            "  the FD1793 command set.",
            "- D100 `/OE` pin 9 and direction `T` pin 11 remain physical singleton",
            "  boundaries. Their control sources have not been measured.",
            "",
            "Primary references: Intel M8286/M8287 data sheet",
            "(<https://www.silicon-ark.co.uk/datasheets/m8286-m8287-datasheet-intel.pdf>);",
            "КР580ВА87 device sheet",
            "(<https://static.chipdip.ru/lib/052/DOC016052028.pdf>); local Western",
            "Digital `FD179X-01` data sheet at",
            "`ref/wd1772-vg93/fd179x-01-datasheet.pdf`; V. A. Shakhnov (ed.),",
            "*Микропроцессоры и микропроцессорные комплекты интегральных микросхем*,",
            "vol. 1 (1988), sections 3.12 and 3.14",
            "(<https://djvu.online/file/iEIJ8fbnBceel>), printed pp. 161 and 166.",
            "",
            "## Runnable-model boundary",
            "",
            "`juku_top` instantiates the physical D100 package and its separate DAL nets",
            "for LVS, but that package is deliberately non-driving while `/OE` and `T`",
            "are unknown. The behavioral `fdc_1793` remains connected directly to logical",
            "system `DB`, which is why EKDOS currently boots. This is an explicit",
            "functional bypass, not proof that the populated D100 path is correct.",
            "",
            "## Decisive bench capture",
            "",
            "1. During the already pinned first EKDOS command at CPU PC `0xE5DE`, capture",
            "   system DB, D100 B-side/D93 DAL, D100.9 `/OE`, D100.11 `T`, D93.2 `/WE`,",
            "   and D93 STEP/WG if channels permit. The CPU-side byte must be `0x02`.",
            "2. Record whether D93 DAL receives `0x02` or `0xFD`, and whether the",
            "   controller performs Restore (STEP toward track zero) or Write Track (WG).",
            "3. Repeat one status read to prove B-to-A direction and inversion rather than",
            "   inferring it from command-side behavior.",
            "",
            "Disposition:",
            "",
            "- `DAL=0x02` makes the populated path functionally non-inverting; identify",
            "  the physical cancellation or correct D100 to the proved part/topology.",
            "- `DAL=0xFD` plus Restore would prove a nonstandard/inverted D93 bus sense.",
            "- `DAL=0xFD` plus WG proves the `.009` hardware and preserved firmware are",
            "  not the same working configuration; do not hide that with a simulator fit.",
        ]
    )
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"FDC-BUS-POLARITY: {'PASS' if not failures else 'FAIL'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
