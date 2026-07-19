#!/usr/bin/env python3
"""Guard the two firmware FDC profiles against the recovered direct D93 bus."""
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
        0xBB,  # logical Type-I 0x44 (WRITE PROTECT | TRACK 0), inverted by D100
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
            ("D93", str(7 + bit)),
        ):
            require(node in db_nodes, f"DB{bit} no longer contains {node[0]}.{node[1]}", failures)
    require(
        not any(name.startswith("FDC_DAL") for name in board["nets"]),
        "retired inferred FDC_DAL nets reappeared",
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
        "vg93_fdc   U_D93" in top and ".dal(DB)" in top,
        "physical D93 no longer lands directly on DB",
        failures,
    )
    require(
        "U_FDC_PROFILE_BUF" in top
        and "fdc_profile_dal" in top
        and "fdc_1793  U_FDC" in top,
        "diagnostic inverting firmware-profile adjunct is absent",
        failures,
    )
    require(
        "assign b = (!oe_n &&  t) ? ~a : 8'hzz" in devices
        and "assign a = (!oe_n && !t) ? ~b : 8'hzz" in devices,
        "generic 8287 diagnostic model no longer implements its truth table",
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
        "FIRMWARE PROFILES PROVED / PHYSICAL D100 ATTRIBUTION RETIRED / TARGET EPROM DUMPS PENDING"
        if not failures
        else "FDC BUS POLARITY AUDIT FAILED"
    )
    lines = [
        "# FDC data-bus polarity audit",
        "",
        f"Status: **{status}**",
        "",
        "Preserved firmware contains two complete VG93 I/O profiles: one complements",
        "every transfer, while the other replaces every complement with a NOP.",
        "Factory sheet 1 now proves D93 DAL0..DAL7 connect directly to system",
        "DB0..DB7 and D100 instead buffers eight floppy-drive outputs. Therefore the",
        "old attribution of the firmware split to D100 is retired; the installed ROM",
        "pair and the historical reason for the two profiles remain open.",
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
            "The diagnostic checkpoint proves the controller-side byte, not merely the",
            "CPU log: Monitor 3.3's `0xFD` crosses the optional modeled complement and",
            "latches as `0x02` in the VG93 model. On the read-only Track-0 fixture, the",
            "dynamic Type-I status is `0x44` (WRITE PROTECT | TRACK 0); it returns",
            "through that diagnostic adjunct as CPU `0xBB`, then the following `CMA`",
            "restores logical `0x44`.",
            "",
            "## Preserved firmware profiles",
            "",
            "| Firmware | Opcode at every VG93 write/read boundary | Writes | Reads | Required data path |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for profile, result in firmware_results:
        opcode = "`CMA` (`0x2F`)" if profile.bridge_opcode == 0x2F else "`NOP` (`0x00`)"
        path = "one diagnostic inversion" if profile.bridge_opcode == 0x2F else "direct bus"
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
            "- Factory sheet 1 requires a direct physical D93 data bus; D100 cannot",
            "  explain or select either firmware profile.",
            "- EktaSoft 3.1, 3.5, and 3.7 match the recovered direct bus. EktaSoft 2.4",
            "  and Monitor 3.3 retain systematic CMA sites whose hardware context is",
            "  not yet identified.",
            "- The public ROM names do not prove which pair was installed in this exact",
            "  board. Repeatable physical D15/D16 dumps remain the Tier-3 configuration",
            "  authority and must be preserved as a variant if they differ.",
            "",
            "## Direct physical bus constraint",
            "",
            "The data path is now source-proved without an intervening D100:",
            "",
            "- The official population identifies D5 as `КР580ВК38`. The 1988 Soviet",
            "  КР580 reference, section 3.12, draws every D0..D7 channel directly to its",
            "  same-numbered DB0..DB7 channel with bidirectional arrows and no inversion",
            "  bubbles (figures 3.73 and 3.74, printed page 161). It says the ВК28 and",
            "  ВК38 differ only in the duration/source timing of the two write strobes.",
            "- Board topology is bit-for-bit from D1 CPU `DC0..DC7` through D5 to system",
            "  `DB0..DB7`. Those same rails directly join D15/D16 and D93 pins 7..14;",
            "  factory sheet 1 shows no intervening permutation or inverter.",
            "- The guarded functional D15+D16 images concatenate exactly to the known",
            f"  `{ROM_SHA256}`",
            "  ekta37 image. Its reset bytes are `C3 17 00` (8080",
            "  `JMP 0017`); one complement would be `3C E8 FF`, which is not that boot",
            "  vector. This is a logical replica constraint, not a substitute for the",
            "  still-requested Tier-3 physical D15/D16 repeat dumps.",
            "",
            "The runnable `sysctl_8238` bridge therefore remains non-inverting. Making",
            "D5 invert merely to explain the CMA profile would contradict the device symbol, the",
            "straight board topology, and every direct system-bus ROM/peripheral path.",
            "",
            "## Physical evidence",
            "",
            "- Factory sheet 1 directly joins D93 pins 7..14 to DB0..DB7.",
            "- The same sheet assigns D100 inputs to D93 DIR/STEP/HLD/TG43/WG, a",
            "  write-data/precompensation boundary, and PPI motor/side-select outputs.",
            "  D100 outputs land on X4 drive-control contacts 9..20.",
            "- D93 is the populated `КР1818ВГ93`. Its documented command families use",
            "  the normal logical codes (`0x0?` Restore, `0xF?` Write Track), matching",
            "  the FD1793 command set. The original Soviet paper defines pins 7..14 as",
            "  the bidirectional DB0..DB7 bus, `/W` as loading that bus into the selected",
            "  register, and Table 3 as the command-register bit codes.",
            "- D100 pins 9 and 11 are factory-drawn at quoted logic level `1`; the",
            "  D100.6 write-data input is source-closed to D101.9.",
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
            "`juku_top` now instantiates physical D93 directly on DB and physical D100",
            "on its recovered drive-output vector. The former opt-in inverted-bus builds",
            "remain as an explicitly unmapped diagnostic firmware-profile adjunct. They",
            "continue to guard the systematic CMA behavior without claiming board copper.",
            "",
            "## Remaining physical closure",
            "",
            "1. Dump D15 and D16 twice each and identify the installed polarity profile.",
            "2. Identify why the preserved CMA-profile firmware exists; do not attribute",
            "   it to physical D100 without new primary evidence.",
            "3. Bench-check the source-closed D100 pins 9/11 logic-high control and",
            "   D100.6 write-data/precompensation path during drive bring-up.",
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
