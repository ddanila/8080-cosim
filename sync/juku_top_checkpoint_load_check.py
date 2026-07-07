#!/usr/bin/env python3
"""Verify a cosim checkpoint loads into juku_top RAM plus visible state latches."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "juku-top-checkpoint-load.md"
ROM = ROOT / "roms" / "ekta37.bin"
DISK = ROOT / "media" / "disks" / "JUKU1.CPM"
EXPECTED_RAM_SHA = "eaa42964cdbc37bce58081edc085c5bcf94e95deed6454230e1aab8f1c3a38d4"
EXPECTED_VRAM_SHA = "0b94d9d02f9c53bdd86f6f0be9921253eb3f99400ee00e62203eeac17eda1c68"


def sha256(path: Path) -> str:
    return subprocess.check_output(["sha256sum", str(path)], text=True).split()[0]


def write_hex(src: Path, dst: Path) -> None:
    data = src.read_bytes()
    dst.write_text("".join(f"{byte:02x}\n" for byte in data))


def compile_trace(tmp: Path) -> Path:
    cc = os.environ.get("CC", "cc")
    trace = tmp / "trace"
    subprocess.run(
        [
            cc,
            "-O2",
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


def generate_checkpoint(tmp: Path) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
    trace = compile_trace(tmp)
    prefix = tmp / "ekdos-checkpoint"
    old_vram = tmp / "old-vram.bin"
    cosim_vram = ROOT / "cosim" / "vram.bin"
    had_vram = cosim_vram.exists()
    if had_vram:
        shutil.copyfile(cosim_vram, old_vram)

    env = os.environ.copy()
    env["JUKU_KEYS"] = "TDD"
    env["JUKU_DISK"] = str(DISK)
    env["JUKU_CHECKPOINT_PREFIX"] = str(prefix)
    proc = subprocess.run(
        [str(trace), str(ROM), "250000000", "30000", "200000"],
        cwd=ROOT / "cosim",
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    vram_copy = tmp / "cosim-vram.bin"
    if cosim_vram.exists():
        shutil.copyfile(cosim_vram, vram_copy)
    if had_vram:
        shutil.copyfile(old_vram, cosim_vram)
    elif cosim_vram.exists():
        cosim_vram.unlink()
    return proc, prefix.with_suffix(".ram"), vram_copy


def run_hdl_load(tmp: Path, ram_bin: Path) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
    ram_hex = tmp / "checkpoint.ram.hex"
    sim = tmp / "juku_top_checkpoint_load_tb"
    write_hex(ram_bin, ram_hex)

    old_ram_dump = tmp / "old-checkpoint-ram-top.bin"
    old_vram_dump = tmp / "old-checkpoint-vram-top.bin"
    ram_dump = ROOT / "hdl" / "sim" / "checkpoint_ram_top.bin"
    vram_dump = ROOT / "hdl" / "sim" / "checkpoint_vram_top.bin"
    had_ram_dump = ram_dump.exists()
    had_vram_dump = vram_dump.exists()
    if had_ram_dump:
        shutil.copyfile(ram_dump, old_ram_dump)
    if had_vram_dump:
        shutil.copyfile(vram_dump, old_vram_dump)

    subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-o",
            str(sim),
            str(ROOT / "hdl" / "vendor" / "vm80a.v"),
            str(ROOT / "hdl" / "devices.v"),
            str(ROOT / "hdl" / "juku_top.v"),
            str(ROOT / "hdl" / "sim" / "juku_top_checkpoint_load_tb.v"),
        ],
        cwd=ROOT,
        check=True,
    )
    proc = subprocess.run(
        [
            "vvp",
            str(sim),
            f"+checkpoint_ram={ram_hex}",
            "+load_checkpoint_state=1",
            "+disk=media/disks/JUKU1.CPM",
            "+disk_heads=2",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    ram_copy = tmp / "hdl-ram.bin"
    vram_copy = tmp / "hdl-vram.bin"
    if ram_dump.exists():
        shutil.copyfile(ram_dump, ram_copy)
    if vram_dump.exists():
        shutil.copyfile(vram_dump, vram_copy)

    if had_ram_dump:
        shutil.copyfile(old_ram_dump, ram_dump)
    elif ram_dump.exists():
        ram_dump.unlink()
    if had_vram_dump:
        shutil.copyfile(old_vram_dump, vram_dump)
    elif vram_dump.exists():
        vram_dump.unlink()

    return proc, ram_copy, vram_copy


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="juku-top-checkpoint-load.") as tmp_name:
        tmp = Path(tmp_name)
        cosim_proc, ram_bin, cosim_vram = generate_checkpoint(tmp)
        hdl_proc, hdl_ram, hdl_vram = run_hdl_load(tmp, ram_bin)
        cosim_ram_sha = sha256(ram_bin)
        cosim_vram_sha = sha256(cosim_vram)
        hdl_ram_sha = sha256(hdl_ram) if hdl_ram.exists() else "missing"
        hdl_vram_sha = sha256(hdl_vram) if hdl_vram.exists() else "missing"

    failures: list[str] = []
    if cosim_proc.returncode != 0:
        failures.append(f"cosim trace exited {cosim_proc.returncode}")
    if hdl_proc.returncode != 0:
        failures.append(f"HDL checkpoint loader exited {hdl_proc.returncode}")
    if "JUKU-TOP-CHECKPOINT-LOAD: PASS" not in hdl_proc.stdout:
        failures.append("HDL checkpoint loader did not report PASS")
    if "JUKU-TOP-CHECKPOINT-STATE: PASS" not in hdl_proc.stdout:
        failures.append("HDL checkpoint state loader did not report PASS")
    if cosim_ram_sha != EXPECTED_RAM_SHA:
        failures.append(f"cosim RAM SHA {cosim_ram_sha} expected {EXPECTED_RAM_SHA}")
    if hdl_ram_sha != EXPECTED_RAM_SHA:
        failures.append(f"HDL RAM SHA {hdl_ram_sha} expected {EXPECTED_RAM_SHA}")
    if cosim_vram_sha != EXPECTED_VRAM_SHA:
        failures.append(f"cosim VRAM SHA {cosim_vram_sha} expected {EXPECTED_VRAM_SHA}")
    if hdl_vram_sha != EXPECTED_VRAM_SHA:
        failures.append(f"HDL VRAM SHA {hdl_vram_sha} expected {EXPECTED_VRAM_SHA}")

    status = "PASS" if not failures else "FAIL"
    lines = [
        "# juku_top checkpoint load",
        "",
        f"Status: **{status}**",
        "",
        "This diagnostic regenerates the 30,000-write EKDOS/TDD cosim checkpoint,",
        "loads its 64 KiB RAM image into the LVS-checked `juku_top` D84..D91",
        "bit-sliced DRAM planes, and injects the checkpoint's visible CPU",
        "architectural registers plus key PPI/PIC/FDC latches. It then dumps RAM",
        "and framebuffer bytes back out of `juku_top` and compares hashes.",
        "",
        "This is not a CPU resume proof. It proves the RAM and visible-state",
        "halves of the future post-banner resume harness can be injected into the",
        "real top-level model without replaying the slow ROMBIOS draw.",
        "",
        "## Command",
        "",
        "```sh",
        "sync/juku_top_checkpoint_load_check.py",
        "```",
        "",
        "## Evidence",
        "",
        f"- Cosim trace exit code: `{cosim_proc.returncode}`",
        f"- HDL loader exit code: `{hdl_proc.returncode}`",
        f"- HDL RAM pass line: `{'yes' if 'JUKU-TOP-CHECKPOINT-LOAD: PASS' in hdl_proc.stdout else 'no'}`",
        f"- HDL state pass line: `{'yes' if 'JUKU-TOP-CHECKPOINT-STATE: PASS' in hdl_proc.stdout else 'no'}`",
        f"- Cosim RAM SHA256: `{cosim_ram_sha}`",
        f"- HDL RAM SHA256: `{hdl_ram_sha}`",
        f"- Cosim VRAM SHA256: `{cosim_vram_sha}`",
        f"- HDL VRAM SHA256: `{hdl_vram_sha}`",
        "",
        "## Boundary",
        "",
        "- CPU microcycle latches are still not initialized, so the die-accurate",
        "  core is not resumed from this state.",
        "- Peripheral state coverage is limited to the visible latches needed at",
        "  the 30,000-write pre-PIC boundary.",
        "- The next resume step is either microcycle-state initialization or a",
        "  narrower ROMBIOS subroutine harness starting from this loaded state.",
    ]
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("\n".join(lines))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
