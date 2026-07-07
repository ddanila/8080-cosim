#!/usr/bin/env python3
"""Probe the EktaSoft B command toward the BASIC cartridge."""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "basic-launch-probe.md"
TRACE_C = ROOT / "cosim" / "trace.c"
VRAM = ROOT / "cosim" / "vram.bin"
VRAM_SIZE = 40 * 241


@dataclass(frozen=True)
class ProbeCase:
    name: str
    rom: Path
    frame_cycles: int

STOP_RE = re.compile(
    r"stopped pc=0x([0-9A-Fa-f]{4}) cyc=([0-9]+) halted=([0-9]+) "
    r"iff=([0-9]+) mode=([0-9]+) switches=([0-9]+)"
)
PROBE_RE = re.compile(
    r"pc_cart_count\s+:\s+([0-9]+).*?"
    r"pc_cart_mode1\s+:\s+([0-9]+).*?"
    r"pc_cart_mode2\s+:\s+([0-9]+).*?"
    r"pc_cart_opcode00\s+:\s+([0-9]+).*?"
    r"pchist_cart\s+:\s+([0-9]+)",
    re.S,
)
READ_RE = re.compile(
    r"cart_overlay_reads\s+:\s+([0-9]+).*?cart_pc_reads\s+:\s+([0-9]+)",
    re.S,
)
RAM_RE = re.compile(
    r"basic_ram_writes\s+:\s+([0-9]+).*?"
    r"basic_ram_nonzero_writes\s+:\s+([0-9]+).*?"
    r"basic_ram_first_write\s+:\s+0x([0-9A-Fa-f]{4}).*?"
    r"basic_ram_last_write\s+:\s+0x([0-9A-Fa-f]{4}).*?"
    r"basic_ram_nonzero_bytes\s+:\s+([0-9]+).*?"
    r"basic_ram_byte_sum\s+:\s+([0-9]+)",
    re.S,
)


def instrumented_trace_source() -> str:
    src = TRACE_C.read_text()
    src = src.replace(
        "static int      cart_enabled = 0;\n",
        "static int      cart_enabled = 0;\n"
        "static unsigned long basic_probe_cart_reads = 0;\n"
        "static unsigned long basic_probe_cart_pc_reads = 0;\n"
        "static unsigned long basic_probe_ram_writes = 0;\n"
        "static unsigned long basic_probe_ram_nonzero_writes = 0;\n"
        "static unsigned basic_probe_ram_first_write = 0x10000;\n"
        "static unsigned basic_probe_ram_last_write = 0;\n",
    )
    src = src.replace(
        "  (void)u; unsigned idx = 0;\n",
        "  i8080* cpu = (i8080*)u; unsigned idx = 0;\n",
        1,
    )
    src = src.replace(
        "  if (ov == 2) return cart_enabled ? cart[a - 0x4000] : 0xFF;\n",
        "  if (ov == 2) {\n"
        "    basic_probe_cart_reads++;\n"
        "    if (cpu && cpu->pc >= 0x4000 && cpu->pc <= 0xBFFF) basic_probe_cart_pc_reads++;\n"
        "    return cart_enabled ? cart[a - 0x4000] : 0xFF;\n"
        "  }\n",
        1,
    )
    src = src.replace(
        "  ram[a] = v;\n"
        "  wpage[a >> 8]++;\n",
        "  ram[a] = v;\n"
        "  if (a >= 0x4000 && a <= 0xBFFF) {\n"
        "    basic_probe_ram_writes++;\n"
        "    if (v != 0x00) basic_probe_ram_nonzero_writes++;\n"
        "    if (basic_probe_ram_first_write == 0x10000) basic_probe_ram_first_write = a;\n"
        "    basic_probe_ram_last_write = a;\n"
        "  }\n"
        "  wpage[a >> 8]++;\n",
        1,
    )
    src = src.replace(
        "  unsigned long last_write_total = 0, writes_total, idle_cyc = 0;\n"
        "  static uint32_t pchist[MEM_SIZE];\n",
        "  unsigned long last_write_total = 0, writes_total, idle_cyc = 0;\n"
        "  unsigned long pc_cart_count = 0, pc_cart_mode1 = 0, pc_cart_mode2 = 0, pc_cart_opcode00 = 0, cart_hist_count = 0;\n"
        "  static uint32_t pchist[MEM_SIZE];\n",
    )
    src = src.replace(
        "    pchist[cpu.pc]++;\n",
        "    if (cpu.pc >= 0x4000 && cpu.pc <= 0xBFFF) {\n"
        "      pc_cart_count++;\n"
        "      if (mode == 1) pc_cart_mode1++;\n"
        "      if (mode == 2) pc_cart_mode2++;\n"
        "      uint8_t op = (mode == 2 && cart_enabled) ? cart[cpu.pc - 0x4000] : ram[cpu.pc];\n"
        "      if (op == 0x00) pc_cart_opcode00++;\n"
        "    }\n"
        "    pchist[cpu.pc]++;\n",
        1,
    )
    src = src.replace(
        '  printf("\\n==== RAM write density (pages >0) ====\\n");\n',
        '  for (int a = 0x4000; a <= 0xBFFF; a++) cart_hist_count += pchist[a];\n'
        '  unsigned long basic_ram_nonzero = 0, basic_ram_sum = 0;\n'
        '  for (int a = 0x4000; a <= 0xBFFF; a++) {\n'
        '    if (ram[a] != 0x00) basic_ram_nonzero++;\n'
        '    basic_ram_sum += ram[a];\n'
        '  }\n'
        '  printf("\\n==== BASIC probe ====\\n");\n'
        '  printf("  pc_cart_count : %8lu\\n", pc_cart_count);\n'
        '  printf("  pc_cart_mode1 : %8lu\\n", pc_cart_mode1);\n'
        '  printf("  pc_cart_mode2 : %8lu\\n", pc_cart_mode2);\n'
        '  printf("  pc_cart_opcode00 : %8lu\\n", pc_cart_opcode00);\n'
        '  printf("  pchist_cart   : %8lu\\n", cart_hist_count);\n'
        '  printf("  cart_overlay_reads : %8lu\\n", basic_probe_cart_reads);\n'
        '  printf("  cart_pc_reads      : %8lu\\n", basic_probe_cart_pc_reads);\n'
        '  printf("  basic_ram_writes   : %8lu\\n", basic_probe_ram_writes);\n'
        '  printf("  basic_ram_nonzero_writes : %8lu\\n", basic_probe_ram_nonzero_writes);\n'
        '  printf("  basic_ram_first_write    : 0x%04X\\n", basic_probe_ram_first_write & 0xFFFF);\n'
        '  printf("  basic_ram_last_write     : 0x%04X\\n", basic_probe_ram_last_write & 0xFFFF);\n'
        '  printf("  basic_ram_nonzero_bytes  : %8lu\\n", basic_ram_nonzero);\n'
        '  printf("  basic_ram_byte_sum       : %8lu\\n", basic_ram_sum);\n'
        '  printf("\\n==== RAM write density (pages >0) ====\\n");\n',
    )
    return src


def parse_stop(stderr: str) -> dict[str, int]:
    for line in reversed(stderr.splitlines()):
        match = STOP_RE.search(line)
        if match:
            pc, cycles, halted, iff, mode, switches = match.groups()
            return {
                "pc": int(pc, 16),
                "cycles": int(cycles),
                "halted": int(halted),
                "iff": int(iff),
                "mode": int(mode),
                "switches": int(switches),
            }
    return {}


def parse_probe(stdout: str) -> tuple[int, int, int, int, int]:
    match = PROBE_RE.search(stdout)
    if not match:
        return 0, 0, 0, 0, 0
    return tuple(int(group) for group in match.groups())


def parse_cart_reads(stdout: str) -> tuple[int, int]:
    match = READ_RE.search(stdout)
    if not match:
        return 0, 0
    return int(match.group(1)), int(match.group(2))


def parse_ram_probe(stdout: str) -> dict[str, int]:
    match = RAM_RE.search(stdout)
    if not match:
        return {
            "writes": 0,
            "nonzero_writes": 0,
            "first_write": 0,
            "last_write": 0,
            "nonzero_bytes": 0,
            "byte_sum": 0,
        }
    writes, nonzero_writes, first_write, last_write, nonzero_bytes, byte_sum = match.groups()
    return {
        "writes": int(writes),
        "nonzero_writes": int(nonzero_writes),
        "first_write": int(first_write, 16),
        "last_write": int(last_write, 16),
        "nonzero_bytes": int(nonzero_bytes),
        "byte_sum": int(byte_sum),
    }


def visible_pixels(vram: bytes) -> int:
    if len(vram) != VRAM_SIZE:
        return 0
    return sum(byte.bit_count() for byte in vram)


def probe_cases() -> list[ProbeCase]:
    rom_override = os.environ.get("BASIC_LAUNCH_ROM")
    frame_override = os.environ.get("BASIC_LAUNCH_FRAME_CYCLES")
    if rom_override:
        rom = Path(rom_override)
        if not rom.is_absolute():
            rom = ROOT / rom
        return [
            ProbeCase(
                rom.stem,
                rom,
                int(frame_override or "40000"),
            )
        ]
    return [
        ProbeCase("jmon33", ROOT / "roms" / "jmon33.bin", int(frame_override or "200000")),
        ProbeCase("ekta37", ROOT / "roms" / "ekta37.bin", int(frame_override or "40000")),
    ]


def run_probe(case: ProbeCase) -> tuple[subprocess.CompletedProcess[str], bytes]:
    cc = os.environ.get("CC", "cc")
    max_cycles = int(os.environ.get("BASIC_LAUNCH_MAX_CYCLES", "120000000"))
    keys = os.environ.get("BASIC_LAUNCH_KEYS", "B")
    old_vram = VRAM.read_bytes() if VRAM.exists() else None
    try:
        with tempfile.TemporaryDirectory(prefix="basic-launch.") as tmp:
            tmpdir = Path(tmp)
            trace_src = tmpdir / "trace_basic.c"
            trace_bin = tmpdir / "trace"
            trace_src.write_text(instrumented_trace_source())
            build = subprocess.run(
                [
                    cc,
                    "-O2",
                    "-I",
                    str(ROOT / "cosim"),
                    "-o",
                    str(trace_bin),
                    str(trace_src),
                    str(ROOT / "cosim" / "i8080.c"),
                    str(ROOT / "cosim" / "juk_disk.c"),
                    str(ROOT / "cosim" / "juku_fdc.c"),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if build.returncode != 0:
                return build, b""
            env = os.environ.copy()
            env["JUKU_CART"] = "../roms/jbasic11.bin"
            env["JUKU_KEYS"] = keys
            proc = subprocess.run(
                [str(trace_bin), str(case.rom), str(max_cycles), "0", str(case.frame_cycles)],
                cwd=ROOT / "cosim",
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        vram = VRAM.read_bytes() if VRAM.exists() else b""
    finally:
        if old_vram is None:
            VRAM.unlink(missing_ok=True)
        else:
            VRAM.write_bytes(old_vram)
    return proc, vram


def main() -> int:
    results = []
    for case in probe_cases():
        proc, vram = run_probe(case)
        stop = parse_stop(proc.stderr)
        pc_cart_count, pc_cart_mode1, pc_cart_mode2, pc_cart_opcode00, pchist_cart = parse_probe(proc.stdout)
        cart_overlay_reads, cart_pc_reads = parse_cart_reads(proc.stdout)
        ram_probe = parse_ram_probe(proc.stdout)
        sha = hashlib.sha256(vram).hexdigest() if vram else ""
        vram_ok = len(vram) == VRAM_SIZE
        pixels = visible_pixels(vram)
        cart_loaded = "loaded 8192 bytes of expansion cartridge" in proc.stderr
        key_processed = bool(re.search(r"0x04\s+:\s+[1-9][0-9]*", proc.stdout)) and bool(
            re.search(r"0x05\s+:\s+[1-9][0-9]*", proc.stdout)
        )
        basic_entered = pc_cart_count > 0 or pchist_cart > 0
        results.append(
            {
                "case": case,
                "proc": proc,
                "vram": vram,
                "stop": stop,
                "pc_cart_count": pc_cart_count,
                "pc_cart_mode1": pc_cart_mode1,
                "pc_cart_mode2": pc_cart_mode2,
                "pc_cart_opcode00": pc_cart_opcode00,
                "pchist_cart": pchist_cart,
                "cart_overlay_reads": cart_overlay_reads,
                "cart_pc_reads": cart_pc_reads,
                "ram_probe": ram_probe,
                "sha": sha,
                "visible_pixels": pixels,
                "vram_ok": vram_ok,
                "cart_loaded": cart_loaded,
                "key_processed": key_processed,
                "basic_entered": basic_entered,
            }
        )
    any_basic_entered = any(result["basic_entered"] for result in results)
    all_infra_ok = all(
        result["proc"].returncode == 0
        and result["cart_loaded"]
        and result["key_processed"]
        and result["vram_ok"]
        for result in results
    )
    status = "BASIC RAM EXECUTION REACHED" if any_basic_entered else "BASIC LAUNCH NOT YET REACHED"

    lines = [
        "# BASIC launch probe",
        "",
        f"Status: **{status}**",
        "",
        "This probe exercises the monitor `B` command with",
        "`JUKU_CART=roms/jbasic11.bin`. By default it checks Monitor 3.3,",
        "which MAME tags as `Monitor/Bootstrap 3.3 \\w JBASIC`, plus the",
        "EktaSoft 3.43m #0037 ROM used by the main boot guard. It complements",
        "`sync/basic_cart_check.sh`,",
        "which already proves the cartridge window wiring independently.",
        "",
        "## Command",
        "",
        "```sh",
        "sync/basic_launch_probe.py",
        "```",
        "",
        "Environment overrides:",
        "",
        f"- `BASIC_LAUNCH_KEYS` default `{os.environ.get('BASIC_LAUNCH_KEYS', 'B')}`",
        "- `BASIC_LAUNCH_ROM` default unset (runs `jmon33.bin` and `ekta37.bin`)",
        f"- `BASIC_LAUNCH_MAX_CYCLES` default `{os.environ.get('BASIC_LAUNCH_MAX_CYCLES', '120000000')}`",
        "- `BASIC_LAUNCH_FRAME_CYCLES` default unset (`jmon33`: `200000`, `ekta37`: `40000`)",
        "",
        "## Evidence",
        "",
        "| Monitor | ROM | Frame cycles | Infra | Cart overlay reads | PC in `0x4000..0xBFFF` | Mode-1 PC cycles | Mode-2 PC cycles | `0x00` opcode cycles | RAM writes | RAM nonzero bytes | RAM byte sum | Visible pixels | Stop PC | Mode | VRAM SHA256 |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |",
        *[
            (
                f"| {result['case'].name} | `{result['case'].rom.relative_to(ROOT)}` | "
                f"`{result['case'].frame_cycles}` | "
                f"{'PASS' if result['proc'].returncode == 0 and result['cart_loaded'] and result['key_processed'] and result['vram_ok'] else 'FAIL'} | "
                f"`{result['cart_overlay_reads']}` | `{result['pc_cart_count']}` | "
                f"`{result['pc_cart_mode1']}` | `{result['pc_cart_mode2']}` | "
                f"`{result['pc_cart_opcode00']}` | "
                f"`{result['ram_probe']['writes']}` | "
                f"`{result['ram_probe']['nonzero_bytes']}` | "
                f"`{result['ram_probe']['byte_sum']}` | "
                f"`{result['visible_pixels']}` | "
                f"`0x{result['stop'].get('pc', 0):04X}` | `{result['stop'].get('mode', 0)}` | "
                f"`{result['sha'] or 'missing'}` |"
            )
            for result in results
        ],
        "",
        "## Disposition",
        "",
    ]
    for result in results:
        if result["basic_entered"]:
            ram_probe = result["ram_probe"]
            lines.append(
                f"- `{result['case'].name}` reads the BASIC cartridge and executes in "
                f"`0x4000..0xBFFF`; `{result['pc_cart_mode1']}` of those PC cycles are "
                f"in RAM/ROM mode 1 and `{result['pc_cart_mode2']}` are in cartridge "
                f"overlay mode 2. `{result['pc_cart_opcode00']}` PC cycles fetch a "
                f"`0x00` opcode there. The RAM window saw `{ram_probe['writes']}` "
                f"accepted writes, `{ram_probe['nonzero_writes']}` of them nonzero, "
                f"ending with `{ram_probe['nonzero_bytes']}` nonzero bytes and byte "
                f"sum `{ram_probe['byte_sum']}`. The captured framebuffer has "
                f"`{result['visible_pixels']}` visible pixels."
            )
        else:
            lines.append(
                f"- `{result['case'].name}` does not select the cartridge overlay in this run."
            )
    lines.extend(
        [
            "- The remaining BASIC work is a user-visible BASIC prompt oracle and HDL-side",
            "  coverage of this stronger Monitor 3.3 path.",
        ]
    )
    lines.append("")
    REPORT.write_text("\n".join(lines))
    print(
        "BASIC-LAUNCH-PROBE: "
        f"{'PASS' if any_basic_entered and all_infra_ok else 'FAIL'}"
    )
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if any_basic_entered and all_infra_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
