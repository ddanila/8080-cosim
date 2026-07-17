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
STATUS_RE = re.compile(
    r"^\[IOSEQ\] IN  port=0x1C value=0x([0-9A-Fa-f]{2}) ",
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
    expected_fdc_command: int
    bus_invert: bool
    expected_cpu_status: int | None


@dataclass(frozen=True)
class FirmwareProfile:
    name: str
    rom: str
    bridge_opcode: int


FIRMWARE_PROFILES = (
    FirmwareProfile("EktaSoft 2.4", "ekta24.bin", 0x2F),
    FirmwareProfile("EktaSoft 3.1", "ekta31.bin", 0x00),
    FirmwareProfile("EktaSoft 3.5", "ekta35.bin", 0x00),
    FirmwareProfile("EktaSoft 3.7", "ekta37.bin", 0x00),
    FirmwareProfile("Monitor 3.3", "jmon33.bin", 0x2F),
)


SCENARIOS = (
    Scenario(
        "EKDOS TDD first command",
        "ekta37.bin",
        "6666450",
        {
            "JUKU_KEYS": "TDD",
            "JUKU_DISK": str(ROOT / "media" / "disks" / "JUKU1.CPM"),
        },
        0x02,
        0xE5DE,
        0x02,
        False,
        None,
    ),
    Scenario(
        "Monitor 3.3 T command",
        "jmon33.bin",
        "9237350",
        {
            "JUKU_KEYBOARD_ENABLE": "1",
            "JUKU_KEYS": "T\n",
            "JUKU_KEY_START_VRAM": "210",
            "JUKU_KEY_HOLD_FRAMES": "20",
            "JUKU_KEY_GAP_FRAMES": "6",
            "JUKU_DISK": str(ROOT / "media" / "disks" / "JUKU1.CPM"),
        },
        0xFD,
        0xE2B7,
        0x02,
        True,
        0xFF,
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


def run_scenario(trace: Path, scenario: Scenario, tmp: Path) -> dict[str, int]:
    env = os.environ.copy()
    env.update(scenario.env)
    env["JUKU_TRACE_IO"] = "1"
    env["JUKU_FDC_BUS_INVERT"] = "1" if scenario.bus_invert else "0"
    checkpoint = tmp / re.sub(r"[^a-z0-9]+", "-", scenario.name.lower()).strip("-")
    env["JUKU_CHECKPOINT_PREFIX"] = str(checkpoint)
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
    status_match = STATUS_RE.search(proc.stderr)
    state = {}
    for line in checkpoint.with_suffix(".state").read_text(encoding="utf-8").splitlines():
        key, separator, state_value = line.partition("=")
        if separator:
            state[key] = state_value
    return {
        "value": int(value, 16),
        "cycles": int(cycles),
        "pc": int(pc, 16),
        "vram_writes": int(vram_writes),
        "fdc_command": int(state["fdc_command"], 16),
        "fdc_bus_invert": int(state["fdc_bus_invert"]),
        "cpu_status": int(status_match.group(1), 16) if status_match else -1,
    }


def profile_firmware(profile: FirmwareProfile) -> dict[str, object]:
    data = (ROOT / "roms" / profile.rom).read_bytes()
    writes = []
    reads = []
    all_writes = []
    all_reads = []
    for offset in range(1, len(data) - 2):
        if data[offset] == 0xD3 and 0x1C <= data[offset + 1] <= 0x1F:
            all_writes.append(offset)
            if data[offset - 1] == profile.bridge_opcode:
                writes.append(offset)
        if data[offset] == 0xDB and 0x1C <= data[offset + 1] <= 0x1F:
            all_reads.append(offset)
            if data[offset + 2] == profile.bridge_opcode:
                reads.append(offset)
    return {
        "writes": writes,
        "reads": reads,
        "all_writes": all_writes,
        "all_reads": all_reads,
    }


def chip(board: dict[str, object], ref: str) -> dict[str, object]:
    return next(item for item in board["chips"] if item["ref"] == ref)


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="fdc-bus-polarity.") as tmp_name:
        tmp = Path(tmp_name)
        trace = compile_trace(tmp)
        results = [(scenario, run_scenario(trace, scenario, tmp)) for scenario in SCENARIOS]

    firmware_results = [(profile, profile_firmware(profile)) for profile in FIRMWARE_PROFILES]

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
        require(
            result["fdc_command"] == scenario.expected_fdc_command,
            f"{scenario.name}: VG93 command 0x{result['fdc_command']:02X}, expected "
            f"0x{scenario.expected_fdc_command:02X}",
            failures,
        )
        require(
            result["fdc_bus_invert"] == scenario.bus_invert,
            f"{scenario.name}: checkpoint bus-invert state changed",
            failures,
        )
        if scenario.expected_cpu_status is not None:
            require(
                result["cpu_status"] == scenario.expected_cpu_status,
                f"{scenario.name}: CPU status 0x{result['cpu_status']:02X}, expected "
                f"0x{scenario.expected_cpu_status:02X}",
                failures,
            )

    for profile, result in firmware_results:
        require(
            len(result["all_writes"]) == 12 and result["writes"] == result["all_writes"],
            f"{profile.name}: not all 12 VG93 writes use the expected bridge opcode",
            failures,
        )
        require(
            len(result["all_reads"]) == 6 and result["reads"] == result["all_reads"],
            f"{profile.name}: not all 6 VG93 reads use the expected bridge opcode",
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
        "`define JUKU_FDC_DATA_BUS fdc_dal" in top
        and "`define JUKU_FDC_DATA_BUS DB" in top
        and "fdc_1793  U_FDC  (.A(BA[1:0]), .D(`JUKU_FDC_DATA_BUS)" in top,
        "behavioral FDC no longer supports logical DB plus opt-in physical DAL paths",
        failures,
    )
    require(
        "assign b = (!oe_n &&  t) ? ~a : 8'hzz" in devices
        and "assign a = (!oe_n && !t) ? ~b : 8'hzz" in devices,
        "D100 no longer implements the bidirectional inverting 8287 truth table",
        failures,
    )
    require(
        "assign Aout = (~oe_n & t) ? ~Ain : 8'bz" in devices
        and "assign Ain  = (~oe_n & ~t) ? ~Aout : 8'bz" in devices,
        "D23-D25 no longer implement the bidirectional inverting 8287 truth table",
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

    status = (
        "FIRMWARE/HARDWARE POLARITY PROFILES PROVED / TARGET EPROM DUMPS PENDING"
        if not failures
        else "FDC BUS POLARITY AUDIT FAILED"
    )
    lines = [
        "# FDC data-bus polarity audit",
        "",
        f"Status: **{status}**",
        "",
        "The apparent D100/firmware contradiction is a configuration split, not an",
        "unknown controller polarity. Preserved firmware contains two complete VG93",
        "I/O profiles: one complements every transfer for an inverting КР580ВА87,",
        "while the other replaces every complement with a NOP for a non-inverting",
        "path. The target `.009` board visibly carries the former part.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_fdc_bus_polarity.py",
        "```",
        "",
        "## Exact firmware observations",
        "",
        "| Path | CPU-visible OUT 0x1C | Modeled bus | VG93 receives | Meaning | Cycle | PC |",
        "| --- | ---: | --- | ---: | --- | ---: | ---: |",
    ]
    for scenario, result in results:
        lines.append(
            f"| {scenario.name} | `0x{result['value']:02X}` | "
            f"{'inverting' if scenario.bus_invert else 'non-inverting'} | "
            f"`0x{result['fdc_command']:02X}` | Restore, step-rate 2 | "
            f"`{result['cycles']}` | `0x{result['pc']:04X}` |"
        )

    lines.extend(
        [
            "",
            "The trace checkpoint proves the controller-side byte, not merely the CPU",
            "log: Monitor 3.3's `0xFD` crosses the modeled ВА87 complement and latches",
            "as `0x02` in the VG93 model. Status `0x00` returns to the CPU as `0xFF`,",
            "then the firmware's following `CMA` restores the logical status.",
            "",
            "## Preserved firmware profiles",
            "",
            "| Firmware | Opcode at every VG93 write/read boundary | Writes | Reads | Required data path |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for profile, result in firmware_results:
        opcode = "`CMA` (`0x2F`)" if profile.bridge_opcode == 0x2F else "`NOP` (`0x00`)"
        path = "one inversion (КР580ВА87)" if profile.bridge_opcode == 0x2F else "non-inverting (КР580ВА86/bypass)"
        lines.append(
            f"| {profile.name} | {opcode} | `{len(result['writes'])}` | "
            f"`{len(result['reads'])}` | {path} |"
        )

    lines.extend(
        [
            "",
            "This is a whole-interface convention, not a patched command constant.",
            "Each listed ROM has exactly 12 writes to ports `0x1C..0x1F` and six",
            "reads. In the ВА87 profiles every OUT is immediately preceded by `CMA`",
            "and every IN immediately followed by `CMA`; in the non-inverting profiles",
            "all 18 positions are deliberately occupied by one-byte `NOP`s. EktaSoft",
            "3.2/4.3 and Monitor 2.2 use a different port-1C/1D bit-stream routine and",
            "are not falsely classified as this register-mapped VG93 template.",
            "",
            "Configuration consequence:",
            "",
            "- Stock `.009` D100=`КР580ВА87` is compatible with EktaSoft 2.4 and",
            "  Monitor 3.3's guarded VG93 routines.",
            "- EktaSoft 3.1, 3.5, and 3.7 require a non-inverting D100 replacement or",
            "  an explicit bypass. Programming `ekta37` into an otherwise stock `.009`",
            "  board would turn its first Restore `0x02` into Write Track `0xFD`.",
            "- The public ROM names do not prove which pair was installed in this exact",
            "  board. Repeatable physical D15/D16 dumps remain the Tier-3 configuration",
            "  authority and must be preserved as a variant if they differ.",
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
            "  the FD1793 command set. The original Soviet paper defines pins 7..14 as",
            "  the bidirectional DB0..DB7 bus, `/W` as loading that bus into the selected",
            "  register, and Table 3 as the command-register bit codes.",
            "- D100 `/OE` pin 9 and direction `T` pin 11 remain physical singleton",
            "  boundaries. Their control sources have not been measured. The component",
            "  model itself is no longer a stub: an exhaustive 256-byte HDL guard proves",
            "  both inverting directions and the disabled high-impedance state.",
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
            "`juku_top` still instantiates physical D100 and separate DAL nets for LVS,",
            "but keeps its control sources disconnected while `/OE` and `T` are unknown.",
            "The exact device truth table constrains cycle states without uniquely",
            "identifying the copper:",
            "",
            "| Cycle | Required `/OE`,`T` state | ВА87 action |",
            "| --- | --- | --- |",
            "| Unselected or D94-suppressed read | `/OE=1`, or `/OE=0,T=1` | released, or A/DB -> B/DAL only; never drive DB |",
            "| FDC write | `/OE=0,T=1` | CPU A/DB -> complemented B/DAL |",
            "| FDC read | `/OE=0,T=0` | B/DAL -> complemented A/DB |",
            "",
            "Two minimal sufficient families are now executable guards:",
            "",
            "- Qualified enable: `/OE=FDC_CS_N`, `T=D93_RE_N` (D94 D2).",
            "- Same-board ВА87 precedent: `/OE=GND`, `T=D93_RE_N` (D94 D2), so",
            "  the device remains A->B except during an actual selected read. D23-D25",
            "  likewise ground pin 9; D25 alone uses its traced D7.6 turnaround input.",
            "",
            "Raw `IORD` is deliberately excluded as `T`: D94's low-A4 register-3",
            "branch can release D93 `/RE` during an I/O read, so `T=IORD` could point",
            "D100 B->A while DAL is released. Both safe families pass all 256 values",
            "in both directions and the suppressed-`/RE` case. This is a functional",
            "constraint, not a copper promotion. Pin 9's",
            "visible trace ends at an isolated component-side circular landing whose",
            "backside projection is bare substrate; pin 11 disappears beneath the",
            "factory wire/tape bundle. Direct continuity must select a family or expose",
            "an equivalent decoded implementation.",
            "",
            "Its behavioral `fdc_1793` consumes logical DB by default, matching the",
            "ekta37 regression profile. Two opt-in HDL builds instead place it behind",
            "physical D100/DAL and pass restore, seek, vendored-media read, and a",
            "512-byte write/readback using CMA-profile CPU bytes under both safe control",
            "families. The C trace also exposes `JUKU_FDC_BUS_INVERT=1`; the",
            "guarded Monitor 3.3 run uses it to model the populated `.009` ВА87 path",
            "without changing the controller's logical command semantics.",
            "",
            "## Remaining physical closure",
            "",
            "1. Dump D15 and D16 twice each and identify the installed polarity profile.",
            "2. Continuity-map D100.9 `/OE` and D100.11 `T`; their remote sources remain",
            "   singleton boundaries even though the required data polarity is resolved.",
            "3. With a matching CMA-profile ROM, capture the first command write and one",
            "   status read: CPU `0xFD` must become DAL `0x02` on write, and logical VG93",
            "   status `0x00` must become CPU-side `0xFF` before firmware `CMA`.",
            "4. If the installed ROM is a NOP profile, record the board modification that",
            "   replaces or bypasses D100; do not silently mix the two configurations.",
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
