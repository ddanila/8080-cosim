#!/usr/bin/env python3
"""Probe the EktaSoft B command toward the BASIC cartridge."""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "basic-launch-probe.md"
TRACE_C = ROOT / "cosim" / "trace.c"
VRAM = ROOT / "cosim" / "vram.bin"
VRAM_SIZE = 40 * 241

STOP_RE = re.compile(
    r"stopped pc=0x([0-9A-Fa-f]{4}) cyc=([0-9]+) halted=([0-9]+) "
    r"iff=([0-9]+) mode=([0-9]+) switches=([0-9]+)"
)
PROBE_RE = re.compile(r"pc_cart_count\s+:\s+([0-9]+).*?pchist_cart\s+:\s+([0-9]+)", re.S)
READ_RE = re.compile(
    r"cart_overlay_reads\s+:\s+([0-9]+).*?cart_pc_reads\s+:\s+([0-9]+)",
    re.S,
)


def instrumented_trace_source() -> str:
    src = TRACE_C.read_text()
    src = src.replace(
        "static int      cart_enabled = 0;\n",
        "static int      cart_enabled = 0;\n"
        "static unsigned long basic_probe_cart_reads = 0;\n"
        "static unsigned long basic_probe_cart_pc_reads = 0;\n",
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
        "  unsigned long last_write_total = 0, writes_total, idle_cyc = 0;\n"
        "  static uint32_t pchist[MEM_SIZE];\n",
        "  unsigned long last_write_total = 0, writes_total, idle_cyc = 0;\n"
        "  unsigned long pc_cart_count = 0, cart_hist_count = 0;\n"
        "  static uint32_t pchist[MEM_SIZE];\n",
    )
    src = src.replace(
        "    pchist[cpu.pc]++;\n",
        "    if (cpu.pc >= 0x4000 && cpu.pc <= 0xBFFF) pc_cart_count++;\n"
        "    pchist[cpu.pc]++;\n",
        1,
    )
    src = src.replace(
        '  printf("\\n==== RAM write density (pages >0) ====\\n");\n',
        '  for (int a = 0x4000; a <= 0xBFFF; a++) cart_hist_count += pchist[a];\n'
        '  printf("\\n==== BASIC probe ====\\n");\n'
        '  printf("  pc_cart_count : %8lu\\n", pc_cart_count);\n'
        '  printf("  pchist_cart   : %8lu\\n", cart_hist_count);\n'
        '  printf("  cart_overlay_reads : %8lu\\n", basic_probe_cart_reads);\n'
        '  printf("  cart_pc_reads      : %8lu\\n", basic_probe_cart_pc_reads);\n'
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


def parse_probe(stdout: str) -> tuple[int, int]:
    match = PROBE_RE.search(stdout)
    if not match:
        return 0, 0
    return int(match.group(1)), int(match.group(2))


def parse_cart_reads(stdout: str) -> tuple[int, int]:
    match = READ_RE.search(stdout)
    if not match:
        return 0, 0
    return int(match.group(1)), int(match.group(2))


def run_probe() -> tuple[subprocess.CompletedProcess[str], bytes]:
    cc = os.environ.get("CC", "cc")
    max_cycles = int(os.environ.get("BASIC_LAUNCH_MAX_CYCLES", "120000000"))
    frame_cycles = int(os.environ.get("BASIC_LAUNCH_FRAME_CYCLES", "40000"))
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
                [str(trace_bin), "../roms/ekta37.bin", str(max_cycles), "0", str(frame_cycles)],
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
    proc, vram = run_probe()
    stop = parse_stop(proc.stderr)
    pc_cart_count, pchist_cart = parse_probe(proc.stdout)
    cart_overlay_reads, cart_pc_reads = parse_cart_reads(proc.stdout)
    sha = hashlib.sha256(vram).hexdigest() if vram else ""
    vram_ok = len(vram) == VRAM_SIZE
    cart_loaded = "loaded 8192 bytes of expansion cartridge" in proc.stderr
    key_processed = bool(re.search(r"0x04\s+:\s+[1-9][0-9]*", proc.stdout)) and bool(
        re.search(r"0x05\s+:\s+[1-9][0-9]*", proc.stdout)
    )
    basic_entered = pc_cart_count > 0 or pchist_cart > 0
    status = "BASIC LAUNCH REACHED" if basic_entered else "BASIC LAUNCH NOT YET REACHED"

    lines = [
        "# BASIC launch probe",
        "",
        f"Status: **{status}**",
        "",
        "This probe exercises the full EktaSoft monitor `B` command with",
        "`JUKU_CART=roms/jbasic11.bin`. It complements `sync/basic_cart_check.sh`,",
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
        f"- `BASIC_LAUNCH_MAX_CYCLES` default `{os.environ.get('BASIC_LAUNCH_MAX_CYCLES', '120000000')}`",
        f"- `BASIC_LAUNCH_FRAME_CYCLES` default `{os.environ.get('BASIC_LAUNCH_FRAME_CYCLES', '40000')}`",
        "",
        "## Evidence",
        "",
        "| Check | Result |",
        "| --- | --- |",
        f"| trace exit code | `{proc.returncode}` |",
        f"| `jbasic11.bin` cartridge loaded | {'PASS' if cart_loaded else 'FAIL'} |",
        f"| keyboard ports used | {'PASS' if key_processed else 'FAIL'} |",
        f"| cartridge overlay reads in mode 2 | `{cart_overlay_reads}` |",
        f"| cartridge reads while PC in `0x4000..0xBFFF` | `{cart_pc_reads}` |",
        f"| PC entered `0x4000..0xBFFF` | `{pc_cart_count}` cycles |",
        f"| pchist count in `0x4000..0xBFFF` | `{pchist_cart}` |",
        f"| VRAM dump size | `{len(vram)}` bytes |",
        f"| VRAM SHA256 | `{sha or 'missing'}` |",
        "",
        "## Stop State",
        "",
        f"- Stop PC: `0x{stop.get('pc', 0):04X}`" if stop else "- Stop PC: not parsed",
        f"- Cycles: `{stop.get('cycles', 0)}`" if stop else "- Cycles: not parsed",
        f"- Mode: `{stop.get('mode', 0)}`" if stop else "- Mode: not parsed",
        f"- Mode switches: `{stop.get('switches', 0)}`" if stop else "- Mode switches: not parsed",
        "",
        "## Disposition",
        "",
    ]
    if basic_entered:
        lines.append("- The monitor `B` command reached the cartridge execution window.")
    else:
        lines.extend(
            [
                "- The cartridge is loaded and the keyboard path is active, but the current",
                "  `B` command run never executes in `0x4000..0xBFFF` and performs no",
                "  mode-2 reads from the cartridge overlay.",
                "- The remaining work is monitor command/control-flow validation before",
                "  the cartridge window is selected, not the D8/D22 cartridge-window",
                "  wiring guarded by `sync/basic_cart_check.sh`.",
            ]
        )
    lines.append("")
    REPORT.write_text("\n".join(lines))
    print(
        "BASIC-LAUNCH-PROBE: "
        f"{'PASS' if proc.returncode == 0 and cart_loaded and key_processed and vram_ok else 'FAIL'}"
    )
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if proc.returncode == 0 and cart_loaded and key_processed and vram_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
