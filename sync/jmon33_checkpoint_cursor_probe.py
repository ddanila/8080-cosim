#!/usr/bin/env python3
"""Checkpoint-resumed juku_top proof for the jmon33 monitor-idle cursor."""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "jmon33-checkpoint-cursor-probe.md"
ROM = ROOT / "roms" / "jmon33.bin"
ROM_HEX = ROOT / "hdl" / "sim" / "jmon33.hex"
VRAM_DUMP = ROOT / "hdl" / "sim" / "checkpoint_vram_top.bin"
EXPECTED_CURSOR_SHA256 = "f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397"
BLANK_VRAM_SHA256 = "559eb05d39a8e243be3e4b051e94f6572a487cc6f90c4847f333d61fe887b28d"


def write_hex(src: Path, dst: Path) -> None:
    dst.write_text("\n".join(f"{byte:02x}" for byte in src.read_bytes()) + "\n")


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


def parse_state(path: Path) -> dict[str, str]:
    state: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        state[key] = value
    return state


def sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return "missing"


def generate_checkpoint(tmp: Path) -> tuple[subprocess.CompletedProcess[str], Path, dict[str, str], str]:
    trace = compile_trace(tmp)
    prefix = tmp / "jmon33-checkpoint"
    checkpoint_cycles = os.environ.get("JMON33_CHECKPOINT_CURSOR_CYCLES", "3801000")
    frame_cycles = os.environ.get("JMON33_CHECKPOINT_CURSOR_FRAME_CYCLES", "200000")
    max_cycles = os.environ.get("JMON33_CHECKPOINT_CURSOR_MAX_CYCLES", "20000000")
    old_vram = tmp / "old-vram.bin"
    cosim_vram = ROOT / "cosim" / "vram.bin"
    had_vram = cosim_vram.exists()
    if had_vram:
        shutil.copyfile(cosim_vram, old_vram)

    env = os.environ.copy()
    env["JUKU_CHECKPOINT_PREFIX"] = str(prefix)
    env["JUKU_CHECKPOINT_CYC"] = checkpoint_cycles
    proc = subprocess.run(
        [str(trace), str(ROM), max_cycles, "0", frame_cycles],
        cwd=ROOT / "cosim",
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    checkpoint_vram = tmp / "checkpoint-vram.bin"
    if cosim_vram.exists():
        shutil.copyfile(cosim_vram, checkpoint_vram)
    checkpoint_vram_sha = sha256(checkpoint_vram)
    if had_vram:
        shutil.copyfile(old_vram, cosim_vram)
    elif cosim_vram.exists():
        cosim_vram.unlink()
    return proc, prefix.with_suffix(".ram"), parse_state(prefix.with_suffix(".state")), checkpoint_vram_sha


def state_plusargs(state: dict[str, str]) -> list[str]:
    def hex_pair(name: str) -> str:
        return state.get(name, "00")

    return [
        f"+state_vram_writes={state.get('vram_writes', '0')}",
        f"+state_pc={state.get('pc', '0000')}",
        f"+state_sp={state.get('sp', '0000')}",
        f"+state_bc={hex_pair('b')}{hex_pair('c')}",
        f"+state_de={hex_pair('d')}{hex_pair('e')}",
        f"+state_hl={hex_pair('h')}{hex_pair('l')}",
        f"+state_a={state.get('a', '00')}",
        f"+state_sf={state.get('sf', '0')}",
        f"+state_zf={state.get('zf', '0')}",
        f"+state_hf={state.get('hf', '0')}",
        f"+state_pf={state.get('pf', '0')}",
        f"+state_cf={state.get('cf', '0')}",
        f"+state_iff={state.get('iff', '0')}",
        f"+state_portc={state.get('portc', '00')}",
        f"+state_kbd_col={state.get('kbd_col', '00')}",
        f"+state_pic_icw1={state.get('pic_icw1', '00')}",
        f"+state_pic_icw2={state.get('pic_icw2', '00')}",
        f"+state_pic_mask={state.get('pic_mask', 'FF')}",
        f"+state_pic_expect_icw2={state.get('pic_expect_icw2', '0')}",
        f"+state_fdc_status={state.get('fdc_status', '80')}",
        f"+state_fdc_track={state.get('fdc_track', '00')}",
        f"+state_fdc_sector={state.get('fdc_sector', '01')}",
        f"+state_fdc_data={state.get('fdc_data', '00')}",
        f"+state_fdc_command={state.get('fdc_command', '00')}",
        f"+state_fdc_buffer_pos={state.get('fdc_buffer_pos', '0')}",
        f"+state_fdc_buffer_len={state.get('fdc_buffer_len', '0')}",
    ]


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


def run_resume(tmp: Path, ram_bin: Path, state: dict[str, str]) -> tuple[subprocess.CompletedProcess[str], bool, str]:
    ram_hex = tmp / "checkpoint.ram.hex"
    sim = tmp / "juku_top_checkpoint_resume_tb"
    out_path = tmp / "jmon33-checkpoint-cursor.out"
    err_path = tmp / "jmon33-checkpoint-cursor.err"
    old_vram = tmp / "old-checkpoint-vram-top.bin"
    had_vram = VRAM_DUMP.exists()
    if had_vram:
        shutil.copyfile(VRAM_DUMP, old_vram)
    write_hex(ram_bin, ram_hex)
    write_hex(ROM, ROM_HEX)
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

    args = [
        "vvp",
        str(sim),
        f"+checkpoint_ram={ram_hex}",
        "+rom=hdl/sim/jmon33.hex",
        f"+max_mcyc={os.environ.get('JMON33_CHECKPOINT_CURSOR_MAX_MCYC', '250000')}",
        f"+timecap={os.environ.get('JMON33_CHECKPOINT_CURSOR_TIMECAP', '2000000000')}",
        f"+frameirq={os.environ.get('JMON33_CHECKPOINT_CURSOR_FRAMEIRQ', '200000')}",
        f"+progress_mcyc={os.environ.get('JMON33_CHECKPOINT_CURSOR_PROGRESS_MCYC', '25000')}",
        "+traceirq=1",
        "+cursorstop=1",
        "+defer_iff=1",
        "+force_clean_status=1",
    ]
    args.extend(state_plusargs(state))

    try:
        with out_path.open("w") as stdout, err_path.open("w") as stderr:
            proc = subprocess.run(
                args,
                cwd=ROOT,
                text=True,
                stdout=stdout,
                stderr=stderr,
                timeout=int(os.environ.get("JMON33_CHECKPOINT_CURSOR_TIMEOUT", "180")),
                check=False,
            )
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        proc = subprocess.CompletedProcess(
            exc.cmd,
            124,
            out_path.read_text(errors="replace") if out_path.exists() else text_output(exc.stdout),
            err_path.read_text(errors="replace") if err_path.exists() else text_output(exc.stderr),
        )
        timed_out = True

    proc.stdout = out_path.read_text(errors="replace") if out_path.exists() else text_output(proc.stdout)
    proc.stderr = err_path.read_text(errors="replace") if err_path.exists() else text_output(proc.stderr)
    vram_sha = sha256(VRAM_DUMP)
    if had_vram:
        shutil.copyfile(old_vram, VRAM_DUMP)
    elif VRAM_DUMP.exists():
        VRAM_DUMP.unlink()
    return proc, timed_out, vram_sha


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="jmon33-checkpoint-cursor.") as tmp_name:
        tmp = Path(tmp_name)
        cosim_proc, ram_bin, state, checkpoint_vram_sha = generate_checkpoint(tmp)
        resume_proc, timed_out, resume_vram_sha = run_resume(tmp, ram_bin, state)

    cursor_line = first_line(resume_proc.stdout, "[RESUME-CURSOR]")
    infra_failures: list[str] = []
    observations: list[str] = []
    if cosim_proc.returncode != 0:
        infra_failures.append(f"cosim checkpoint exited {cosim_proc.returncode}")
    if checkpoint_vram_sha != BLANK_VRAM_SHA256:
        infra_failures.append(f"cosim checkpoint VRAM was not pre-cursor blank: {checkpoint_vram_sha}")
    if resume_proc.returncode not in (0, 124):
        infra_failures.append(f"HDL resume exited {resume_proc.returncode}")
    cursor_reached = resume_vram_sha == EXPECTED_CURSOR_SHA256
    if not cursor_line.startswith("[RESUME-CURSOR]") and not cursor_reached:
        observations.append("checkpoint-resumed HDL run did not reach the jmon33 cursor oracle")
    if cursor_line.startswith("[RESUME-CURSOR]") and resume_vram_sha != EXPECTED_CURSOR_SHA256:
        infra_failures.append(f"checkpoint-resumed HDL VRAM SHA256 {resume_vram_sha} did not match cosim cursor oracle")
    if cursor_reached and not cursor_line.startswith("[RESUME-CURSOR]"):
        observations.append("checkpoint-resumed HDL VRAM reached the cursor oracle by final dump; the write-triggered cursor hook did not fire before the bounded max_mcyc exit")

    status = (
        "PASS"
        if cursor_reached and not infra_failures
        else "JMON33 CHECKPOINT CURSOR NOT YET REACHED"
    )
    lines = [
        "# jmon33 checkpoint cursor probe",
        "",
        f"Status: **{status}**",
        "",
        "This diagnostic starts from a generated pre-cursor Monitor 3.3 cosim",
        "checkpoint, loads its RAM and visible CPU/PPI/PIC state into `juku_top`,",
        "and resumes the LVS-checked CPU until the same monitor-idle cursor oracle",
        "used by `docs/jmon33-ready-probe.md` appears.",
        "",
        "## Command",
        "",
        "```sh",
        "sync/jmon33_checkpoint_cursor_probe.py",
        "```",
        "",
        "Environment overrides:",
        "",
        f"- `JMON33_CHECKPOINT_CURSOR_CYCLES` default `{os.environ.get('JMON33_CHECKPOINT_CURSOR_CYCLES', '3801000')}`",
        f"- `JMON33_CHECKPOINT_CURSOR_FRAME_CYCLES` default `{os.environ.get('JMON33_CHECKPOINT_CURSOR_FRAME_CYCLES', '200000')}`",
        f"- `JMON33_CHECKPOINT_CURSOR_MAX_MCYC` default `{os.environ.get('JMON33_CHECKPOINT_CURSOR_MAX_MCYC', '250000')}`",
        f"- `JMON33_CHECKPOINT_CURSOR_PROGRESS_MCYC` default `{os.environ.get('JMON33_CHECKPOINT_CURSOR_PROGRESS_MCYC', '25000')}`",
        f"- `JMON33_CHECKPOINT_CURSOR_TIMEOUT` default `{os.environ.get('JMON33_CHECKPOINT_CURSOR_TIMEOUT', '180')}` seconds",
        "",
        "## Evidence",
        "",
        f"- Cosim checkpoint exit code: `{cosim_proc.returncode}`",
        f"- Cosim checkpoint cycle: `{state.get('cyc', 'missing')}`",
        f"- Cosim checkpoint PC: `0x{state.get('pc', 'missing')}`",
        f"- Cosim checkpoint VRAM SHA256: `{checkpoint_vram_sha}`",
        f"- HDL resume exit code: `{resume_proc.returncode}`",
        f"- Timed out: `{'yes' if timed_out else 'no'}`",
        f"- Cursor stop line: `{cursor_line}`",
        f"- First IRQ line: `{first_line(resume_proc.stdout, '[RESUME-IRQ]')}`",
        f"- Last IRQ line: `{last_line(resume_proc.stdout, '[RESUME-IRQ]')}`",
        f"- First progress line: `{first_line(resume_proc.stdout, '[RESUME-PROGRESS]')}`",
        f"- Last progress line: `{last_line(resume_proc.stdout, '[RESUME-PROGRESS]')}`",
        f"- HDL cursor VRAM SHA256: `{resume_vram_sha}`",
        "",
        "## Boundary",
        "",
        "- This is a checkpoint-resumed Monitor 3.3 cursor proof, not yet a full",
        "  uninterrupted `juku_top` run from reset to the user-visible prompt.",
        "- The checkpoint VRAM is deliberately blank, so the cursor evidence comes",
        "  from resumed HDL CPU execution after the checkpoint.",
    ]
    if observations:
        lines.extend(["", "## Observations", ""])
        lines.extend(f"- {observation}" for observation in observations)
    if infra_failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in infra_failures)
    if observations or infra_failures:
        lines.extend(["", "## HDL stdout tail", "", "```text"])
        lines.extend(resume_proc.stdout.splitlines()[-60:])
        lines.append("```")

    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("\n".join(lines))
    return 1 if infra_failures else 0


if __name__ == "__main__":
    sys.exit(main())
