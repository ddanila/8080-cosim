#!/usr/bin/env python3
"""Probe a monitor command toward the BASIC cartridge."""
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
REPORT = Path(os.environ.get("BASIC_LAUNCH_REPORT", ROOT / "docs" / "basic-launch-probe.md"))
TRACE_C = ROOT / "cosim" / "trace.c"
VRAM = ROOT / "cosim" / "vram.bin"
VRAM_SIZE = 40 * 241
MAME_JUKU = ROOT / "ref" / "mame_juku.cpp"


@dataclass(frozen=True)
class ProbeCase:
    name: str
    rom: Path
    frame_cycles: int
    cart_name: str
    cart: Path


@dataclass(frozen=True)
class CartAnalysis:
    name: str
    size: int
    sha1: str
    first_bytes: str
    entry_jmp: int | None
    basic_offsets: tuple[int, ...]
    ready_offsets: tuple[int, ...]
    error_offsets: tuple[int, ...]


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
    r"basic_ram_first_write_pc\s+:\s+0x([0-9A-Fa-f]{4}).*?"
    r"basic_ram_last_write_pc\s+:\s+0x([0-9A-Fa-f]{4}).*?"
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
        "static unsigned basic_probe_ram_last_write = 0;\n"
        "static unsigned basic_probe_ram_first_write_pc = 0;\n"
        "static unsigned basic_probe_ram_last_write_pc = 0;\n",
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
        "    i8080* write_cpu = (i8080*)u;\n"
        "    if (basic_probe_ram_first_write == 0x10000) {\n"
        "      basic_probe_ram_first_write = a;\n"
        "      basic_probe_ram_first_write_pc = write_cpu ? write_cpu->pc : 0;\n"
        "    }\n"
        "    basic_probe_ram_last_write = a;\n"
        "    basic_probe_ram_last_write_pc = write_cpu ? write_cpu->pc : 0;\n"
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
        '  printf("  basic_ram_first_write_pc : 0x%04X\\n", basic_probe_ram_first_write_pc & 0xFFFF);\n'
        '  printf("  basic_ram_last_write_pc  : 0x%04X\\n", basic_probe_ram_last_write_pc & 0xFFFF);\n'
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
            "first_write_pc": 0,
            "last_write_pc": 0,
            "nonzero_bytes": 0,
            "byte_sum": 0,
        }
    (
        writes,
        nonzero_writes,
        first_write,
        last_write,
        first_write_pc,
        last_write_pc,
        nonzero_bytes,
        byte_sum,
    ) = match.groups()
    return {
        "writes": int(writes),
        "nonzero_writes": int(nonzero_writes),
        "first_write": int(first_write, 16),
        "last_write": int(last_write, 16),
        "first_write_pc": int(first_write_pc, 16),
        "last_write_pc": int(last_write_pc, 16),
        "nonzero_bytes": int(nonzero_bytes),
        "byte_sum": int(byte_sum),
    }


def visible_pixels(vram: bytes) -> int:
    if len(vram) != VRAM_SIZE:
        return 0
    return sum(byte.bit_count() for byte in vram)


def find_offsets(data: bytes, needle: bytes) -> tuple[int, ...]:
    offsets = []
    start = 0
    while True:
        pos = data.find(needle, start)
        if pos < 0:
            return tuple(offsets)
        offsets.append(pos)
        start = pos + 1


def format_offsets(offsets: tuple[int, ...]) -> str:
    if not offsets:
        return "-"
    return ", ".join(f"0x{offset:04X}" for offset in offsets)


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def analyze_cart(name: str, path: Path) -> CartAnalysis:
    data = path.read_bytes()
    entry_jmp = data[1] | (data[2] << 8) if len(data) >= 3 and data[0] == 0xC3 else None
    return CartAnalysis(
        name=name,
        size=len(data),
        sha1=hashlib.sha1(data).hexdigest(),
        first_bytes=data[:8].hex(" "),
        entry_jmp=entry_jmp,
        basic_offsets=find_offsets(data, b"BASIC"),
        ready_offsets=find_offsets(data, b"READY"),
        error_offsets=find_offsets(data, b"ERROR"),
    )


def mame_jmon33_note_present() -> bool:
    return "Does not seem to be compatible with JBASIC expansion cartridge" in MAME_JUKU.read_text(
        errors="replace"
    )


def decode_hex_bytes(path: Path) -> bytes:
    text = path.read_text(errors="replace")
    hex_digits = "".join(ch for ch in text if ch in "0123456789abcdefABCDEF")
    return bytes.fromhex(hex_digits)


def legacy_bas_cart(tmpdir: Path) -> Path:
    out = tmpdir / "bas0-3.bin"
    out.write_bytes(
        b"".join(
            decode_hex_bytes(ROOT / "ref" / "firmware" / f"BAS{idx}.HEX")
            for idx in range(4)
        )
    )
    return out


def probe_cases(tmpdir: Path) -> list[ProbeCase]:
    rom_override = os.environ.get("BASIC_LAUNCH_ROM")
    frame_override = os.environ.get("BASIC_LAUNCH_FRAME_CYCLES")
    cart_override = os.environ.get("BASIC_LAUNCH_CART")
    default_cart = ROOT / "roms" / "jbasic11.bin"
    carts: list[tuple[str, Path]]
    if cart_override:
        cart = Path(cart_override)
        if not cart.is_absolute():
            cart = ROOT / cart
        carts = [(cart.name, cart)]
    else:
        carts = [
            ("jbasic11.bin", default_cart),
            ("BAS0-3.HEX", legacy_bas_cart(tmpdir)),
        ]
    if rom_override:
        rom = Path(rom_override)
        if not rom.is_absolute():
            rom = ROOT / rom
        return [
            ProbeCase(
                rom.stem,
                rom,
                int(frame_override or "40000"),
                cart_name,
                cart,
            )
            for cart_name, cart in carts
        ]
    return [
        ProbeCase("jmon33", ROOT / "roms" / "jmon33.bin", int(frame_override or "200000"), cart_name, cart)
        for cart_name, cart in carts
    ] + [
        ProbeCase("ekta37", ROOT / "roms" / "ekta37.bin", int(frame_override or "40000"), "jbasic11.bin", default_cart),
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
            env["JUKU_CART"] = str(case.cart)
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
    cart_analyses: dict[str, CartAnalysis] = {}
    mame_note = mame_jmon33_note_present()
    keys = os.environ.get("BASIC_LAUNCH_KEYS", "B")
    with tempfile.TemporaryDirectory(prefix="basic-launch-carts.") as cart_tmp:
        for case in probe_cases(Path(cart_tmp)):
            cart_analyses.setdefault(case.cart_name, analyze_cart(case.cart_name, case.cart))
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
        "This probe exercises the configured monitor/removable-memory BASIC",
        f"command with `JUKU_KEYS={keys}`. By default it checks Monitor 3.3 with both",
        "`roms/jbasic11.bin` and the legacy `ref/firmware/BAS0-3.HEX` image,",
        "plus the EktaSoft 3.43m #0037 ROM used by the main boot guard. It complements",
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
        f"- `BASIC_LAUNCH_KEYS` default `{keys}`",
        "- `BASIC_LAUNCH_ROM` default unset (runs `jmon33.bin` and `ekta37.bin`)",
        "- `BASIC_LAUNCH_CART` default unset (runs `jbasic11.bin` plus legacy `BAS0-3.HEX`; "
        "with `BASIC_LAUNCH_ROM`, both default cartridges are probed against that ROM)",
        f"- `BASIC_LAUNCH_REPORT` default `{display_path(REPORT)}`",
        f"- `BASIC_LAUNCH_MAX_CYCLES` default `{os.environ.get('BASIC_LAUNCH_MAX_CYCLES', '120000000')}`",
        "- `BASIC_LAUNCH_FRAME_CYCLES` default unset (`jmon33`: `200000`, `ekta37`: `40000`)",
        "",
        "## Cartridge compatibility signals",
        "",
        "| Cartridge | Bytes | SHA1 | First bytes | Entry jump | Strings |",
        "| --- | ---: | --- | --- | --- | --- |",
        *[
            (
                f"| `{analysis.name}` | `{analysis.size}` | `{analysis.sha1}` | "
                f"`{analysis.first_bytes}` | "
                f"{'`0x%04X`' % analysis.entry_jmp if analysis.entry_jmp is not None else '-'} | "
                f"`BASIC`: {format_offsets(analysis.basic_offsets)}; "
                f"`READY`: {format_offsets(analysis.ready_offsets)}; "
                f"`ERROR`: {format_offsets(analysis.error_offsets)} |"
            )
            for analysis in cart_analyses.values()
        ],
        "",
        "Compatibility notes:",
        "",
        "- `ref/mame_juku.cpp` records Monitor 3.3 as `Monitor/Bootstrap 3.3 \\w JBASIC`",
        "  and the local source contains the compatibility warning that it does not",
        f"  seem compatible with the JBASIC expansion cartridge: {'PASS' if mame_note else 'MISSING'}.",
        "- The BASIC images do contain `BASIC`, `READY`, and `ERROR` strings, but their",
        "  first instruction is an absolute `JMP 0x0107`; that is not a direct",
        "  `0x4000`-window entry point by itself.",
        "- Baltijets doc 003 acceptance notes mention BASIC launch from the removable",
        "  32K memory expander with command `A`, expecting a BASIC banner and `READY`.",
        "  That is a separate compatibility target from Monitor 3.3's current `B` path.",
        "",
        "## Evidence",
        "",
        "| Monitor | ROM | Cartridge | Frame cycles | Infra | Cart overlay reads | PC in `0x4000..0xBFFF` | Mode-1 PC cycles | Mode-2 PC cycles | `0x00` opcode cycles | RAM writes | RAM first/last write | RAM first/last write PCs | RAM nonzero bytes | RAM byte sum | Visible pixels | Stop PC | Mode | VRAM SHA256 |",
        "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | --- | ---: | --- |",
        *[
            (
                f"| {result['case'].name} | `{display_path(result['case'].rom)}` | "
                f"`{result['case'].cart_name}` | "
                f"`{result['case'].frame_cycles}` | "
                f"{'PASS' if result['proc'].returncode == 0 and result['cart_loaded'] and result['key_processed'] and result['vram_ok'] else 'FAIL'} | "
                f"`{result['cart_overlay_reads']}` | `{result['pc_cart_count']}` | "
                f"`{result['pc_cart_mode1']}` | `{result['pc_cart_mode2']}` | "
                f"`{result['pc_cart_opcode00']}` | "
                f"`{result['ram_probe']['writes']}` | "
                f"`0x{result['ram_probe']['first_write']:04X}..0x{result['ram_probe']['last_write']:04X}` | "
                f"`0x{result['ram_probe']['first_write_pc']:04X}..0x{result['ram_probe']['last_write_pc']:04X}` | "
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
                f"- `{result['case'].name}` with `{result['case'].cart_name}` reads "
                f"the BASIC cartridge and executes in "
                f"`0x4000..0xBFFF`; `{result['pc_cart_mode1']}` of those PC cycles are "
                f"in RAM/ROM mode 1 and `{result['pc_cart_mode2']}` are in cartridge "
                f"overlay mode 2. `{result['pc_cart_opcode00']}` PC cycles fetch a "
                f"`0x00` opcode there. The RAM window saw `{ram_probe['writes']}` "
                f"accepted writes, `{ram_probe['nonzero_writes']}` of them nonzero, "
                f"from PC range `0x{ram_probe['first_write_pc']:04X}` to "
                f"`0x{ram_probe['last_write_pc']:04X}` over addresses "
                f"`0x{ram_probe['first_write']:04X}`..`0x{ram_probe['last_write']:04X}`, "
                f"ending with `{ram_probe['nonzero_bytes']}` nonzero bytes and byte "
                f"sum `{ram_probe['byte_sum']}`. The captured framebuffer has "
                f"`{result['visible_pixels']}` visible pixels."
            )
            if result["case"].name == "jmon33" and ram_probe["first_write_pc"] == 0xF008:
                lines.append(
                    "  The write PC is sampled after opcode fetch; in the high-ROM "
                    "`jmon33.bin` mapping, `0xF008` is the byte after the `MOV M,A` "
                    "at `0xF007` in the local copy/clear loop."
                )
        else:
            lines.append(
                f"- `{result['case'].name}` with `{result['case'].cart_name}` does not "
                "select the cartridge overlay in this run."
            )
    lines.extend(
        [
            "- The current evidence is therefore a compatibility boundary, not just a",
            "  missing prompt: the tested Monitor 3.3 path reads the media but does not",
            "  execute the cartridge overlay as live BASIC code.",
            "- The remaining BASIC work is a user-visible BASIC prompt oracle and HDL-side",
            "  coverage of the correct monitor/removable-memory pairing once identified.",
        ]
    )
    lines.append("")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines))
    print(
        "BASIC-LAUNCH-PROBE: "
        f"{'PASS' if any_basic_entered and all_infra_ok else 'FAIL'}"
    )
    print(f"Wrote {display_path(REPORT)}")
    return 0 if any_basic_entered and all_infra_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
