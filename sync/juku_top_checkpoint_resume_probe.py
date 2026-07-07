#!/usr/bin/env python3
"""Probe whether juku_top can resume from the 30,000-write EKDOS checkpoint."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "juku-top-checkpoint-resume.md"
ROM = ROOT / "roms" / "ekta37.bin"
DISK = ROOT / "media" / "disks" / "JUKU1.CPM"


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


def generate_checkpoint(tmp: Path) -> tuple[subprocess.CompletedProcess[str], Path]:
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
    if had_vram:
        shutil.copyfile(old_vram, cosim_vram)
    elif cosim_vram.exists():
        cosim_vram.unlink()
    return proc, prefix.with_suffix(".ram")


def run_resume(tmp: Path, ram_bin: Path) -> subprocess.CompletedProcess[str]:
    ram_hex = tmp / "checkpoint.ram.hex"
    sim = tmp / "juku_top_checkpoint_resume_tb"
    write_hex(ram_bin, ram_hex)
    subprocess.run(
        [
            "iverilog",
            "-g2012",
            "-o",
            str(sim),
            str(ROOT / "hdl" / "vendor" / "vm80a.v"),
            str(ROOT / "hdl" / "devices.v"),
            str(ROOT / "hdl" / "juku_top.v"),
            str(ROOT / "hdl" / "sim" / "juku_top_checkpoint_resume_tb.v"),
        ],
        cwd=ROOT,
        check=True,
    )
    return subprocess.run(
        [
            "vvp",
            str(sim),
            f"+checkpoint_ram={ram_hex}",
            "+disk=media/disks/JUKU1.CPM",
            "+disk_heads=2",
            "+max_mcyc=200000",
            "+timecap=200000000",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def first_line(text: str, prefix: str) -> str:
    return next((line for line in text.splitlines() if line.startswith(prefix)), "none")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="juku-top-checkpoint-resume.") as tmp_name:
        tmp = Path(tmp_name)
        cosim_proc, ram_bin = generate_checkpoint(tmp)
        resume_proc = run_resume(tmp, ram_bin)

    failures: list[str] = []
    if cosim_proc.returncode != 0:
        failures.append(f"cosim checkpoint exited {cosim_proc.returncode}")
    if resume_proc.returncode != 0:
        failures.append(f"HDL resume probe exited {resume_proc.returncode}")
    if "JUKU-TOP-CHECKPOINT-RESUME: PASS" not in resume_proc.stdout:
        failures.append("HDL resume probe did not reach both first PIC restore-window event and no-key keyboard read")

    status = "PASS" if not failures else "FAIL"
    lines = [
        "# juku_top checkpoint resume probe",
        "",
        f"Status: **{status}**",
        "",
        "This probe regenerates the 30,000-write EKDOS/TDD cosim checkpoint,",
        "loads its RAM image into the LVS-checked `juku_top`, injects the",
        "visible CPU/PPI/PIC/FDC latches, seeds the vm80a core at a clean M1",
        "fetch boundary, and lets the real top-level bus run forward.",
        "",
        "The pass condition is deliberately narrow: reach the first post-checkpoint",
        "ROMBIOS PIC programming event and the no-key keyboard poll through the",
        "actual decoded top-level ports. It is not an EKDOS prompt proof.",
        "",
        "## Command",
        "",
        "```sh",
        "sync/juku_top_checkpoint_resume_probe.py",
        "```",
        "",
        "## Evidence",
        "",
        f"- Cosim checkpoint exit code: `{cosim_proc.returncode}`",
        f"- HDL resume exit code: `{resume_proc.returncode}`",
        f"- Resume pass line: `{first_line(resume_proc.stdout, 'JUKU-TOP-CHECKPOINT-RESUME: PASS')}`",
        f"- First PIC line: `{first_line(resume_proc.stdout, '[RESUME-PIC]')}`",
        f"- First keyboard line: `{first_line(resume_proc.stdout, '[RESUME-KBD]')}`",
        f"- Stop/fail line: `{first_line(resume_proc.stdout, 'JUKU-TOP-CHECKPOINT-RESUME: FAIL')}`",
        "",
        "## Boundary",
        "",
        "- This remains a checkpoint-resume diagnostic, not the full `TDD` to `A>`",
        "  CPU path.",
        "- The seeded core state intentionally starts from an instruction-fetch",
        "  boundary rather than a transistor-exact mid-instruction microstate.",
        "- This probe is intentionally not a mandatory CI gate yet; the next",
        "  hardening step is making the seeded vm80a microstate portable across",
        "  all CI runner schedules before extending it toward FDC I/O.",
    ]
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
        lines.extend(["", "## HDL stdout tail", ""])
        lines.append("```")
        lines.extend(resume_proc.stdout.splitlines()[-40:])
        lines.append("```")

    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("\n".join(lines))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
