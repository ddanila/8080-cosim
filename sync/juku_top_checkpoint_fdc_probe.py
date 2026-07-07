#!/usr/bin/env python3
"""Probe checkpoint-resumed juku_top toward the first EKDOS FDC I/O."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "juku-top-checkpoint-fdc-probe.md"
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


def run_resume_to_fdc(tmp: Path, ram_bin: Path) -> tuple[subprocess.CompletedProcess[str], bool]:
    ram_hex = tmp / "checkpoint.ram.hex"
    sim = tmp / "juku_top_checkpoint_resume_tb"
    out_path = tmp / "checkpoint-fdc.out"
    err_path = tmp / "checkpoint-fdc.err"
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

    frameirq = os.environ.get("JUKU_TOP_CHECKPOINT_FDC_FRAMEIRQ", "80000")
    keyat = os.environ.get("JUKU_TOP_CHECKPOINT_FDC_KEYAT", "42000")
    khold = os.environ.get("JUKU_TOP_CHECKPOINT_FDC_KHOLD", "900000")
    kgap = os.environ.get("JUKU_TOP_CHECKPOINT_FDC_KGAP", "900000")
    max_mcyc = os.environ.get("JUKU_TOP_CHECKPOINT_FDC_MAX_MCYC", "1000000")
    timecap = os.environ.get("JUKU_TOP_CHECKPOINT_FDC_TIMECAP", "900000000")
    timeout_s = int(os.environ.get("JUKU_TOP_CHECKPOINT_FDC_TIMEOUT", "300"))

    args = [
        "vvp",
        str(sim),
        f"+checkpoint_ram={ram_hex}",
        "+disk=media/disks/JUKU1.CPM",
        "+disk_heads=2",
        f"+max_mcyc={max_mcyc}",
        f"+timecap={timecap}",
        f"+frameirq={frameirq}",
        "+ekdoskeys=1",
        f"+keyat={keyat}",
        f"+khold={khold}",
        f"+kgap={kgap}",
        "+traceirq=1",
        "+tracekbd=1",
        "+tracefdc=1",
        "+stopfdc=1",
    ]

    try:
        with out_path.open("w") as stdout, err_path.open("w") as stderr:
            proc = subprocess.run(
                args,
                cwd=ROOT,
                text=True,
                stdout=stdout,
                stderr=stderr,
                timeout=timeout_s,
                check=False,
            )
        proc.stdout = out_path.read_text(errors="replace") if out_path.exists() else ""
        proc.stderr = err_path.read_text(errors="replace") if err_path.exists() else ""
        return proc, False
    except subprocess.TimeoutExpired as exc:
        return (
            subprocess.CompletedProcess(
                args,
                124,
                stdout=out_path.read_text(errors="replace") if out_path.exists() else text_output(exc.stdout),
                stderr=err_path.read_text(errors="replace") if err_path.exists() else text_output(exc.stderr),
            ),
            True,
        )


def text_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def first_line(text: str, prefix: str) -> str:
    return next((line for line in text.splitlines() if line.startswith(prefix)), "none")


def last_line(text: str, prefix: str) -> str:
    return next((line for line in reversed(text.splitlines()) if line.startswith(prefix)), "none")


def count_lines(text: str, prefix: str) -> int:
    return sum(1 for line in text.splitlines() if line.startswith(prefix))


def last_complete_vram_line(text: str) -> str:
    pattern = re.compile(r"^\[RESUME-VRAM\] writes=[0-9]+ mcyc=[0-9]+ pc=0x[0-9a-fA-F]+$")
    return next((line for line in reversed(text.splitlines()) if pattern.match(line)), "none")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="juku-top-checkpoint-fdc.") as tmp_name:
        tmp = Path(tmp_name)
        cosim_proc, ram_bin = generate_checkpoint(tmp)
        resume_proc, timed_out = run_resume_to_fdc(tmp, ram_bin)

    fdc_stop = first_line(resume_proc.stdout, "[RESUME-FDC] stop")
    fdc_first = first_line(resume_proc.stdout, "[RESUME-FDC]")
    reached_fdc = fdc_stop != "none"
    failures: list[str] = []
    if cosim_proc.returncode != 0:
        failures.append(f"cosim checkpoint exited {cosim_proc.returncode}")
    if resume_proc.returncode not in (0, 124):
        failures.append(f"HDL checkpoint FDC run exited {resume_proc.returncode}")
    if not reached_fdc:
        failures.append("checkpoint-resumed HDL run did not reach decoded FDC I/O")

    status = "PASS" if not failures else "BOUNDARY NOT YET FDC"
    lines = [
        "# juku_top checkpoint FDC probe",
        "",
        f"Status: **{status}**",
        "",
        "This diagnostic starts from the 30,000-write EKDOS/TDD cosim",
        "checkpoint, loads it into `juku_top`, enables frame IRQs and the",
        "fixed `TDD` keyboard stimulus, and runs toward the first decoded",
        "WD1793/VG93 I/O. It is the checkpointed counterpart to",
        "`sync/juku_top_fdc_probe.sh`.",
        "",
        "## Command",
        "",
        "```sh",
        "sync/juku_top_checkpoint_fdc_probe.py",
        "```",
        "",
        "Environment overrides:",
        "",
        "- `JUKU_TOP_CHECKPOINT_FDC_TIMEOUT` default `300` seconds",
        "- `JUKU_TOP_CHECKPOINT_FDC_FRAMEIRQ` default `80000`",
        "- `JUKU_TOP_CHECKPOINT_FDC_KEYAT` default `42000`",
        "- `JUKU_TOP_CHECKPOINT_FDC_KHOLD` default `900000`",
        "- `JUKU_TOP_CHECKPOINT_FDC_KGAP` default `900000`",
        "- `JUKU_TOP_CHECKPOINT_FDC_MAX_MCYC` default `1000000`",
        "- `JUKU_TOP_CHECKPOINT_FDC_TIMECAP` default `900000000`",
        "",
        "## Evidence",
        "",
        f"- Cosim checkpoint exit code: `{cosim_proc.returncode}`",
        f"- HDL resume exit code: `{resume_proc.returncode}`",
        f"- Timed out: `{'yes' if timed_out else 'no'}`",
        f"- First PIC line: `{first_line(resume_proc.stdout, '[RESUME-PIC]')}`",
        f"- First no-key keyboard line: `{first_line(resume_proc.stdout, '[RESUME-KBD]')}`",
        f"- First key stimulus line: `{first_line(resume_proc.stdout, '[RESUME-KBD-STIM]')}`",
        f"- Last key stimulus line: `{last_line(resume_proc.stdout, '[RESUME-KBD-STIM]')}`",
        f"- First IRQ line: `{first_line(resume_proc.stdout, '[RESUME-IRQ]')}`",
        f"- Last IRQ line: `{last_line(resume_proc.stdout, '[RESUME-IRQ]')}`",
        f"- First VRAM line: `{first_line(resume_proc.stdout, '[RESUME-VRAM]')}`",
        f"- Last complete VRAM line: `{last_complete_vram_line(resume_proc.stdout)}`",
        f"- First FDC line: `{fdc_first}`",
        f"- FDC stop line: `{fdc_stop}`",
        f"- Stop/fail line: `{first_line(resume_proc.stdout, 'JUKU-TOP-CHECKPOINT-RESUME: FAIL')}`",
        "",
        "| Trace | Lines |",
        "| --- | ---: |",
        f"| PIC writes | `{count_lines(resume_proc.stdout, '[RESUME-PIC]')}` |",
        f"| keyboard reads | `{count_lines(resume_proc.stdout, '[RESUME-KBD]')}` |",
        f"| key stimulus | `{count_lines(resume_proc.stdout, '[RESUME-KBD-STIM]')}` |",
        f"| IRQ events | `{count_lines(resume_proc.stdout, '[RESUME-IRQ]')}` |",
        f"| VRAM progress | `{count_lines(resume_proc.stdout, '[RESUME-VRAM]')}` |",
        f"| FDC events | `{count_lines(resume_proc.stdout, '[RESUME-FDC]')}` |",
        "",
        "## Boundary",
        "",
        "- This is not a prompt proof until decoded FDC I/O and then EKDOS `A>`",
        "  are reached through CPU execution.",
        "- A timeout with PIC/KBD/IRQ/key evidence is still useful: it proves the",
        "  checkpointed run is past the previous no-frame/no-key boundary and",
        "  identifies the next missing event.",
    ]
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
        lines.extend(["", "## HDL stdout tail", ""])
        lines.append("```")
        lines.extend(resume_proc.stdout.splitlines()[-60:])
        lines.append("```")

    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("\n".join(lines))
    return 0 if cosim_proc.returncode == 0 and resume_proc.returncode in (0, 124) else 1


if __name__ == "__main__":
    sys.exit(main())
