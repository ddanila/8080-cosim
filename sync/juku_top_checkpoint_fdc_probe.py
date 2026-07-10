#!/usr/bin/env python3
"""Probe checkpoint-resumed juku_top toward EKDOS FDC I/O."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = Path(
    os.environ.get(
        "JUKU_TOP_CHECKPOINT_FDC_REPORT",
        str(Path(tempfile.gettempdir()) / "juku-top-checkpoint-fdc-probe.md"),
    )
)
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


def parse_state(path: Path) -> dict[str, str]:
    state: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        state[key] = value
    return state


def generate_checkpoint(tmp: Path) -> tuple[subprocess.CompletedProcess[str], Path, dict[str, str]]:
    trace = compile_trace(tmp)
    prefix = tmp / "ekdos-checkpoint"
    checkpoint_writes = os.environ.get("JUKU_TOP_CHECKPOINT_FDC_WRITES", "63085")
    checkpoint_cycles = os.environ.get("JUKU_TOP_CHECKPOINT_FDC_CYCLES", "8711550")
    old_vram = tmp / "old-vram.bin"
    cosim_vram = ROOT / "cosim" / "vram.bin"
    had_vram = cosim_vram.exists()
    if had_vram:
        shutil.copyfile(cosim_vram, old_vram)

    env = os.environ.copy()
    env["JUKU_KEYS"] = "TDD"
    env["JUKU_DISK"] = str(DISK)
    env["JUKU_CHECKPOINT_PREFIX"] = str(prefix)
    if checkpoint_cycles and checkpoint_cycles != "0":
        env["JUKU_CHECKPOINT_CYC"] = checkpoint_cycles
        checkpoint_writes = "0"
    proc = subprocess.run(
        [str(trace), str(ROM), "250000000", checkpoint_writes, "200000"],
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
    return proc, prefix.with_suffix(".ram"), parse_state(prefix.with_suffix(".state"))


def state_plusargs(state: dict[str, str]) -> list[str]:
    def hex_pair(name: str) -> str:
        return state.get(name, "00")

    return [
        f"+state_vram_writes={state.get('vram_writes', '30000')}",
        f"+state_pc={state.get('pc', '0484')}",
        f"+state_sp={state.get('sp', 'D44C')}",
        f"+state_bc={hex_pair('b')}{hex_pair('c')}",
        f"+state_de={hex_pair('d')}{hex_pair('e')}",
        f"+state_hl={hex_pair('h')}{hex_pair('l')}",
        f"+state_a={state.get('a', 'A1')}",
        f"+state_sf={state.get('sf', '1')}",
        f"+state_zf={state.get('zf', '0')}",
        f"+state_hf={state.get('hf', '0')}",
        f"+state_pf={state.get('pf', '0')}",
        f"+state_cf={state.get('cf', '0')}",
        f"+state_iff={state.get('iff', '0')}",
        f"+state_portc={state.get('portc', '80')}",
        f"+state_kbd_col={state.get('kbd_col', '0F')}",
        f"+state_kbd_pos={state.get('kbd_pos', '0')}",
        f"+state_kbd_phase={state.get('kbd_phase', '0')}",
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


def run_resume_to_fdc(tmp: Path, ram_bin: Path, state: dict[str, str]) -> tuple[subprocess.CompletedProcess[str], bool]:
    ram_hex = tmp / "checkpoint.ram.hex"
    sim = tmp / "juku_top_checkpoint_resume_tb"
    out_path = tmp / "checkpoint-fdc.out"
    err_path = tmp / "checkpoint-fdc.err"
    prompt_vram = ROOT / "hdl" / "sim" / "checkpoint_vram_top.bin"
    old_prompt_vram = tmp / "old-checkpoint-vram-top.bin"
    had_prompt_vram = prompt_vram.exists()
    if had_prompt_vram:
        shutil.copyfile(prompt_vram, old_prompt_vram)
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
    stopfdc_data_reads = os.environ.get("JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS", "6656")
    stopfdc = os.environ.get("JUKU_TOP_CHECKPOINT_FDC_STOP_IO", "0")
    stopprompt = os.environ.get("JUKU_TOP_CHECKPOINT_FDC_STOP_PROMPT", "0")
    default_stop_data_read = "0" if int(stopfdc_data_reads) or stopprompt != "0" else "1"
    stopfdc_data_read = os.environ.get("JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READ", default_stop_data_read)

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
        f"+stopfdc={stopfdc}",
        f"+stopfdc_data_read={stopfdc_data_read}",
        f"+stopfdc_data_reads={stopfdc_data_reads}",
        f"+stopprompt={stopprompt}",
    ]
    args.extend(state_plusargs(state))

    def restore_prompt_vram() -> None:
        if had_prompt_vram:
            shutil.copyfile(old_prompt_vram, prompt_vram)
        elif prompt_vram.exists():
            prompt_vram.unlink()

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
        restore_prompt_vram()
        proc.stdout = out_path.read_text(errors="replace") if out_path.exists() else ""
        proc.stderr = err_path.read_text(errors="replace") if err_path.exists() else ""
        return proc, False
    except subprocess.TimeoutExpired as exc:
        restore_prompt_vram()
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


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def last_complete_vram_line(text: str) -> str:
    pattern = re.compile(r"^\[RESUME-VRAM\] writes=[0-9]+ mcyc=[0-9]+ pc=0x[0-9a-fA-F]+$")
    return next((line for line in reversed(text.splitlines()) if pattern.match(line)), "none")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="juku-top-checkpoint-fdc.") as tmp_name:
        tmp = Path(tmp_name)
        cosim_proc, ram_bin, state = generate_checkpoint(tmp)
        resume_proc, timed_out = run_resume_to_fdc(tmp, ram_bin, state)

    fdc_stop = first_line(resume_proc.stdout, "[RESUME-FDC] stop")
    prompt_stop = first_line(resume_proc.stdout, "[RESUME-PROMPT]")
    fdc_first = first_line(resume_proc.stdout, "[RESUME-FDC]")
    want_data_reads = int(os.environ.get("JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS", "6656"))
    want_prompt = os.environ.get("JUKU_TOP_CHECKPOINT_FDC_STOP_PROMPT", "0") != "0"
    default_want_data_read = "0" if want_data_reads or want_prompt else "1"
    want_data_read = os.environ.get("JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READ", default_want_data_read) != "0"
    reached_data_read = fdc_stop.startswith("[RESUME-FDC] stop reason=data-read")
    reached_data_reads = fdc_stop.startswith("[RESUME-FDC] stop reason=data-read-count")
    reached_prompt = prompt_stop.startswith("[RESUME-PROMPT]")
    reached_fdc = fdc_stop != "none"
    failures: list[str] = []
    if cosim_proc.returncode != 0:
        failures.append(f"cosim checkpoint exited {cosim_proc.returncode}")
    if resume_proc.returncode not in (0, 124):
        failures.append(f"HDL checkpoint FDC run exited {resume_proc.returncode}")
    if not reached_fdc and not reached_prompt:
        failures.append("checkpoint-resumed HDL run did not reach decoded FDC I/O")
    if want_data_reads and not reached_data_reads:
        failures.append(f"checkpoint-resumed HDL run did not reach {want_data_reads} FDC data register reads")
    elif want_data_read and not reached_data_read:
        failures.append("checkpoint-resumed HDL run did not reach FDC data register reads")
    if want_prompt and not reached_prompt:
        failures.append("checkpoint-resumed HDL run did not render the EKDOS `A>` prompt bitmap")

    status = "PASS" if not failures else "BOUNDARY NOT YET FDC"
    if want_data_reads:
        target = f"{want_data_reads} FDC data-register reads"
    elif want_prompt:
        target = "EKDOS `A>` prompt bitmap"
    else:
        target = "FDC data-register read" if want_data_read else "first decoded FDC I/O"
    effective_cycles = os.environ.get("JUKU_TOP_CHECKPOINT_FDC_CYCLES", "8711550")
    effective_writes = os.environ.get("JUKU_TOP_CHECKPOINT_FDC_WRITES", "63085")
    lines = [
        "# juku_top checkpoint FDC probe",
        "",
        f"Status: **{status}**",
        "",
        "This diagnostic starts from a generated EKDOS/TDD cosim checkpoint",
        f"(`JUKU_TOP_CHECKPOINT_FDC_CYCLES={effective_cycles}` or",
        f"`JUKU_TOP_CHECKPOINT_FDC_WRITES={effective_writes}` when cycle stop is disabled),",
        "loads it into `juku_top`, enables frame IRQs and the",
        f"fixed `TDD` keyboard stimulus, and runs toward the {target}.",
        "It is the checkpointed counterpart to",
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
        "- `JUKU_TOP_CHECKPOINT_FDC_CYCLES` default `8711550`; set to `0` to use",
        "  the framebuffer-write checkpoint stop instead",
        "- `JUKU_TOP_CHECKPOINT_FDC_WRITES` default `63085` when cycle stop is disabled",
        "- `JUKU_TOP_CHECKPOINT_FDC_FRAMEIRQ` default `80000`",
        "- `JUKU_TOP_CHECKPOINT_FDC_KEYAT` default `42000`",
        "- `JUKU_TOP_CHECKPOINT_FDC_KHOLD` default `900000`",
        "- `JUKU_TOP_CHECKPOINT_FDC_KGAP` default `900000`",
        "- `JUKU_TOP_CHECKPOINT_FDC_MAX_MCYC` default `1000000`",
        "- `JUKU_TOP_CHECKPOINT_FDC_TIMECAP` default `900000000`",
        "- `JUKU_TOP_CHECKPOINT_FDC_STOP_IO` default `0`",
        "- `JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READ` default `0` when",
        "  `JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS` is nonzero, otherwise `1`",
        "- `JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS` default `6656` (13 sectors);",
        "  set to `512` for the first sector or `0` for the first data-register read",
        "- `JUKU_TOP_CHECKPOINT_FDC_STOP_PROMPT` default `0`; set to `1` to stop",
        "  on the EKDOS `A>` prompt bitmap at `x=0`, `y=70`",
        "- `JUKU_TOP_CHECKPOINT_FDC_REPORT` defaults to a temporary file; set it",
        "  explicitly to retain a diagnostic report",
        "",
        "Known useful windows:",
        "",
        "- Default `JUKU_TOP_CHECKPOINT_FDC_CYCLES=8711550` proves the first",
        "  13 sectors / 6,656 data-register reads.",
        "- `JUKU_TOP_CHECKPOINT_FDC_CYCLES=10066690",
        "  JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS=4096` proves the later",
        "  8 sectors / 4,096 data-register reads.",
        "- `JUKU_TOP_CHECKPOINT_FDC_CYCLES=10066690",
        "  JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS=0",
        "  JUKU_TOP_CHECKPOINT_FDC_STOP_PROMPT=1` proves the checkpoint-resumed",
        "  EKDOS `A>` prompt bitmap.",
        "",
        "## Evidence",
        "",
        f"- Cosim checkpoint exit code: `{cosim_proc.returncode}`",
        f"- Cosim checkpoint cycle: `{state.get('cyc', 'missing')}`",
        f"- Cosim checkpoint writes: `{state.get('vram_writes', 'missing')}`",
        f"- Cosim checkpoint PC: `0x{state.get('pc', 'missing')}`",
        f"- Cosim checkpoint key position/phase: `{state.get('kbd_pos', 'missing')}` / `{state.get('kbd_phase', 'missing')}`",
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
        f"- Prompt stop line: `{prompt_stop}`",
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
        f"| prompt events | `{count_lines(resume_proc.stdout, '[RESUME-PROMPT]')}` |",
        "",
        "## Boundary",
        "",
        (
            "- This run is a checkpoint-resumed HDL EKDOS prompt proof: `juku_top`"
            " rendered the `A>` bitmap at `x=0`, `y=70`."
            if reached_prompt
            else "- This is not a prompt proof until EKDOS `A>` is reached through"
        ),
        (
            "- The prompt was reached after decoded FDC I/O, keyboard/PIC service,"
            " and VRAM writes from checkpoint-resumed CPU execution."
            if reached_prompt
            else "  checkpoint-resumed `juku_top` CPU execution."
        ),
        "- The default proves the ROMBIOS FDC path drains 13 full 512-byte sectors",
        "  through FDC data-register reads from a checkpointed CPU run.",
        "- A second clean late-sector window at",
        "  `JUKU_TOP_CHECKPOINT_FDC_CYCLES=10066690` resumes at PC `0xE5A0`,",
        "  issues `OUT 0x1C = 0x80`, and drains the remaining 8 full sectors",
        "  (4,096 data-register reads).",
        "- With `JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS=0` and",
        "  `JUKU_TOP_CHECKPOINT_FDC_STOP_PROMPT=1`, the same late checkpoint",
        "  continues past those data reads and reaches the EKDOS `A>` prompt.",
        "- A single full cosim-prompt-count target,",
        "  `JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS=10752`, currently times out",
        "  after the 6,656-byte boundary while looping through keyboard/IRQ",
        "  service around VRAM write count 63,155, so the current proof is split",
        "  across the first and late FDC checkpoint windows.",
        "- Use `JUKU_TOP_CHECKPOINT_FDC_CYCLES=0 JUKU_TOP_CHECKPOINT_FDC_WRITES=63085",
        "  JUKU_TOP_CHECKPOINT_FDC_STOP_IO=1 JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READ=0`",
        "  for the older first-command boundary.",
        "- Use `JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS=0` for the older",
        "  first-data-register-read boundary.",
        "- Use `JUKU_TOP_CHECKPOINT_FDC_CYCLES=0 JUKU_TOP_CHECKPOINT_FDC_WRITES=42000`",
        "  for the earlier key-window narrowing run.",
    ]
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
        lines.extend(["", "## HDL stdout tail", ""])
        lines.append("```")
        lines.extend(resume_proc.stdout.splitlines()[-60:])
        lines.append("```")

    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {display_path(REPORT)}")
    print("\n".join(lines))
    return 0 if cosim_proc.returncode == 0 and resume_proc.returncode in (0, 124) else 1


if __name__ == "__main__":
    sys.exit(main())
