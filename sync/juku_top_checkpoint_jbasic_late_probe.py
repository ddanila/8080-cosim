#!/usr/bin/env python3
"""Late checkpoint-resumed HDL diagnostic for EKDOS JBASIC READY."""
from __future__ import annotations

import hashlib
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
        "JUKU_TOP_CHECKPOINT_JBASIC_LATE_REPORT",
        ROOT / "docs" / "juku-top-checkpoint-jbasic-late-probe.md",
    )
)
ROM = ROOT / "roms" / "ekta37.bin"
DISK = ROOT / "media" / "disks" / "JUKPROG2.CPM"
VRAM_STRIDE = 40
VRAM_LINES = 241
VRAM_SIZE = VRAM_STRIDE * VRAM_LINES

SCREEN_GLYPHS = {
    "A": (
        "....#...",
        "...#.#..",
        "..#...#.",
        "..#...#.",
        "..#####.",
        "..#...#.",
        "..#...#.",
    ),
    "B": (
        "..####..",
        "...#..#.",
        "...#..#.",
        "...###..",
        "...#..#.",
        "...#..#.",
        "..####..",
    ),
    "C": (
        "...###..",
        "..#...#.",
        "..#.....",
        "..#.....",
        "..#.....",
        "..#...#.",
        "...###..",
    ),
    "D": (
        "..####..",
        "...#..#.",
        "...#..#.",
        "...#..#.",
        "...#..#.",
        "...#..#.",
        "..####..",
    ),
    "E": (
        "..#####.",
        "..#.....",
        "..#.....",
        "..####..",
        "..#.....",
        "..#.....",
        "..#####.",
    ),
    "I": (
        "...###..",
        "....#...",
        "....#...",
        "....#...",
        "....#...",
        "....#...",
        "...###..",
    ),
    "J": (
        "....###.",
        ".....#..",
        ".....#..",
        ".....#..",
        ".....#..",
        "..#..#..",
        "...##...",
    ),
    "R": (
        "..####..",
        "..#...#.",
        "..#...#.",
        "..#...#.",
        "..####..",
        "..#..#..",
        "..#...#.",
    ),
    "S": (
        "...###..",
        "..#...#.",
        "..#.....",
        "...###..",
        "......#.",
        "..#...#.",
        "...###..",
    ),
    "Y": (
        "..#...#.",
        "..#...#.",
        "...#.#..",
        "....#...",
        "....#...",
        "....#...",
        "....#...",
    ),
    ">": (
        "...#....",
        "....#...",
        ".....#..",
        "......#.",
        ".....#..",
        "....#...",
        "...#....",
    ),
}


def write_hex(src: Path, dst: Path) -> None:
    dst.write_text("".join(f"{byte:02x}\n" for byte in src.read_bytes()))


def parse_state(path: Path) -> dict[str, str]:
    state: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            state[key] = value
    return state


def compile_trace(tmp: Path) -> Path:
    trace = tmp / "trace"
    subprocess.run(
        [
            os.environ.get("CC", "cc"),
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


def generate_late_checkpoint(tmp: Path) -> tuple[subprocess.CompletedProcess[str], Path, dict[str, str]]:
    trace = compile_trace(tmp)
    prefix = tmp / "jbasic-late"
    old_vram = tmp / "old-vram.bin"
    cosim_vram = ROOT / "cosim" / "vram.bin"
    had_vram = cosim_vram.exists()
    if had_vram:
        shutil.copyfile(cosim_vram, old_vram)

    env = os.environ.copy()
    env["JUKU_DISK"] = str(DISK)
    env["JUKU_KEYS"] = os.environ.get("JUKU_TOP_CHECKPOINT_JBASIC_LATE_KEYS", "TDD|JBASIC\r")
    env["JUKU_KEY_HOLD_FRAMES"] = os.environ.get("JUKU_TOP_CHECKPOINT_JBASIC_LATE_HOLD_FRAMES", "6")
    env["JUKU_KEY_GAP_FRAMES"] = os.environ.get("JUKU_TOP_CHECKPOINT_JBASIC_LATE_GAP_FRAMES", "8")
    env["JUKU_STOP_FDC_DATA_READS"] = os.environ.get("JUKU_TOP_CHECKPOINT_JBASIC_LATE_FDC_READS", "19968")
    env["JUKU_CHECKPOINT_PREFIX"] = str(prefix)
    proc = subprocess.run(
        [
            str(trace),
            str(ROM),
            os.environ.get("JUKU_TOP_CHECKPOINT_JBASIC_LATE_COSIM_CYCLES", "900000000"),
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

    if had_vram:
        shutil.copyfile(old_vram, cosim_vram)
    elif cosim_vram.exists():
        cosim_vram.unlink()

    return proc, prefix.with_suffix(".ram"), parse_state(prefix.with_suffix(".state"))


def state_arg(state: dict[str, str], name: str, default: str = "00") -> str:
    return state.get(name, default)


def state_plusargs(state: dict[str, str]) -> list[str]:
    return [
        f"+state_vram_writes={state_arg(state, 'vram_writes', '73586')}",
        f"+state_pc={state_arg(state, 'pc', 'E5AA')}",
        f"+state_pc_bias={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_LATE_PC_BIAS', '0')}",
        f"+state_sp={state_arg(state, 'sp', 'D2EE')}",
        f"+state_bc={state_arg(state, 'b')}{state_arg(state, 'c')}",
        f"+state_de={state_arg(state, 'd')}{state_arg(state, 'e')}",
        f"+state_hl={state_arg(state, 'h')}{state_arg(state, 'l')}",
        f"+state_a={state_arg(state, 'a')}",
        f"+state_sf={state_arg(state, 'sf', '0')}",
        f"+state_zf={state_arg(state, 'zf', '0')}",
        f"+state_hf={state_arg(state, 'hf', '0')}",
        f"+state_pf={state_arg(state, 'pf', '0')}",
        f"+state_cf={state_arg(state, 'cf', '0')}",
        f"+state_iff={state_arg(state, 'iff', '0')}",
        f"+state_portc={state_arg(state, 'portc', '05')}",
        f"+state_kbd_col={state_arg(state, 'kbd_col', '00')}",
        f"+state_kbd_pos={state_arg(state, 'kbd_pos', '10')}",
        f"+state_kbd_phase={state_arg(state, 'kbd_phase', '8')}",
        f"+state_pic_icw1={state_arg(state, 'pic_icw1', 'D6')}",
        f"+state_pic_icw2={state_arg(state, 'pic_icw2', 'FE')}",
        f"+state_pic_mask={state_arg(state, 'pic_mask', 'FF')}",
        f"+state_pic_expect_icw2={state_arg(state, 'pic_expect_icw2', '0')}",
        f"+state_fdc_status={state_arg(state, 'fdc_status', '00')}",
        f"+state_fdc_track={state_arg(state, 'fdc_track', '14')}",
        f"+state_fdc_sector={state_arg(state, 'fdc_sector', '09')}",
        f"+state_fdc_data={state_arg(state, 'fdc_data', '00')}",
        f"+state_fdc_command={state_arg(state, 'fdc_command', '80')}",
        f"+state_fdc_buffer_pos={state_arg(state, 'fdc_buffer_pos', '0')}",
        f"+state_fdc_buffer_len={state_arg(state, 'fdc_buffer_len', '0')}",
    ]


def run_hdl(tmp: Path, ram_bin: Path, state: dict[str, str]) -> tuple[subprocess.CompletedProcess[str], bool, bytes]:
    ram_hex = tmp / "jbasic-late.ram.hex"
    rom_hex = tmp / "ekta37.hex"
    sim = tmp / "juku_top_checkpoint_resume_tb"
    out_path = tmp / "jbasic-late-hdl.out"
    err_path = tmp / "jbasic-late-hdl.err"
    old_vram = tmp / "old-checkpoint-vram.bin"
    checkpoint_vram = ROOT / "hdl" / "sim" / "checkpoint_vram_top.bin"
    had_vram = checkpoint_vram.exists()
    if had_vram:
        shutil.copyfile(checkpoint_vram, old_vram)

    write_hex(ram_bin, ram_hex)
    write_hex(ROM, rom_hex)
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
        f"+rom={rom_hex}",
        "+disk=media/disks/JUKPROG2.CPM",
        "+disk_heads=2",
        f"+max_mcyc={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_LATE_MAX_MCYC', '1200000')}",
        f"+timecap={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_LATE_TIMECAP', '4200000000')}",
        f"+frameirq={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_LATE_FRAMEIRQ', '80000')}",
        f"+trace_resume={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_LATE_TRACE_RESUME', '0')}",
        f"+trace_resume_after={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_LATE_TRACE_AFTER', '0')}",
        f"+trace_resume_after_count={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_LATE_TRACE_AFTER_COUNT', '0')}",
        f"+tracekbd={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_LATE_TRACE_KBD', '0')}",
        f"+tracefdc={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_LATE_TRACE_FDC', '0')}",
        f"+progress_mcyc={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_LATE_PROGRESS_MCYC', '25000')}",
        f"+stopfdc_data_read={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_LATE_STOP_DATA_READ', '0')}",
        f"+stopfdc_data_reads={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_LATE_STOP_DATA_READS', '0')}",
        "+stopjbasicready=1",
    ]
    args.extend(state_plusargs(state))

    def restore_vram() -> None:
        if had_vram:
            shutil.copyfile(old_vram, checkpoint_vram)
        elif checkpoint_vram.exists():
            checkpoint_vram.unlink()

    try:
        with out_path.open("w") as stdout, err_path.open("w") as stderr:
            proc = subprocess.run(
                args,
                cwd=ROOT,
                text=True,
                stdout=stdout,
                stderr=stderr,
                timeout=int(os.environ.get("JUKU_TOP_CHECKPOINT_JBASIC_LATE_TIMEOUT", "600")),
                check=False,
            )
        vram = checkpoint_vram.read_bytes() if checkpoint_vram.exists() else b""
        restore_vram()
        proc.stdout = out_path.read_text(errors="replace")
        proc.stderr = err_path.read_text(errors="replace")
        return proc, False, vram
    except subprocess.TimeoutExpired:
        vram = checkpoint_vram.read_bytes() if checkpoint_vram.exists() else b""
        restore_vram()
        return (
            subprocess.CompletedProcess(
                args,
                124,
                stdout=out_path.read_text(errors="replace") if out_path.exists() else "",
                stderr=err_path.read_text(errors="replace") if err_path.exists() else "",
            ),
            True,
            vram,
        )


def matching_lines(text: str, prefix: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith(prefix)]


def first_line(text: str, prefix: str) -> str:
    return next((line for line in text.splitlines() if line.startswith(prefix)), "none")


def last_line(text: str, prefix: str) -> str:
    return next((line for line in reversed(text.splitlines()) if line.startswith(prefix)), "none")


def screen_cell(vram: bytes, cell_x: int, y: int, height: int = 7) -> tuple[str, ...]:
    rows: list[str] = []
    for row_y in range(y, y + height):
        start = row_y * VRAM_STRIDE + cell_x
        if start < 0 or start >= len(vram):
            rows.append("........")
            continue
        byte = vram[start]
        rows.append("".join("#" if (byte >> (7 - bit)) & 1 else "." for bit in range(8)))
    return tuple(rows)


def screen_text_at(vram: bytes, text: str, y: int, cell_x: int = 0) -> bool:
    if len(vram) != VRAM_SIZE:
        return False
    for offset, char in enumerate(text):
        expected = SCREEN_GLYPHS.get(char)
        if expected is None or screen_cell(vram, cell_x + offset, y) != expected:
            return False
    return True


def row_hex(vram: bytes, y: int, cell_x: int = 0, cells: int = 10) -> str:
    if len(vram) != VRAM_SIZE:
        return "missing"
    start = y * VRAM_STRIDE + cell_x
    return " ".join(f"{byte:02x}" for byte in vram[start : start + cells])


def changed_cells(before: bytes, after: bytes, limit: int = 24) -> list[str]:
    if len(before) != VRAM_SIZE or len(after) != VRAM_SIZE:
        return []
    changes: list[str] = []
    for idx, (old, new) in enumerate(zip(before, after)):
        if old == new:
            continue
        y, x = divmod(idx, VRAM_STRIDE)
        changes.append(f"x={x} y={y} {old:02x}->{new:02x}")
        if len(changes) >= limit:
            break
    return changes


def data_read_count(text: str) -> int:
    counts = [int(match.group(1)) for match in re.finditer(r"fdc_data_reads=([0-9]+)", text)]
    return counts[-1] if counts else 0


def command_lines(total_reads: str, stop_reads: str) -> list[str]:
    env_bits: list[str] = []
    if total_reads != "19968":
        env_bits.append(f"JUKU_TOP_CHECKPOINT_JBASIC_LATE_FDC_READS={total_reads}")
    if stop_reads != "0":
        env_bits.append(f"JUKU_TOP_CHECKPOINT_JBASIC_LATE_STOP_DATA_READS={stop_reads}")
    if REPORT != ROOT / "docs" / "juku-top-checkpoint-jbasic-late-probe.md":
        env_bits.append(f"JUKU_TOP_CHECKPOINT_JBASIC_LATE_REPORT={REPORT}")
    command = " ".join(env_bits + ["sync/juku_top_checkpoint_jbasic_late_probe.py"])
    return ["```sh", command, "```"]


def main() -> int:
    total_reads = os.environ.get("JUKU_TOP_CHECKPOINT_JBASIC_LATE_FDC_READS", "19968")
    stop_reads = os.environ.get("JUKU_TOP_CHECKPOINT_JBASIC_LATE_STOP_DATA_READS", "0")
    stop_read_target = int(stop_reads)
    with tempfile.TemporaryDirectory(prefix="juku-top-checkpoint-jbasic-late.") as tmp_name:
        tmp = Path(tmp_name)
        cosim_proc, ram_bin, state = generate_late_checkpoint(tmp)
        checkpoint_ram = ram_bin.read_bytes()
        checkpoint_vram = checkpoint_ram[0xD800 : 0xD800 + VRAM_SIZE]
        hdl_proc, timed_out, hdl_vram = run_hdl(tmp, ram_bin, state)

    ready_line = first_line(hdl_proc.stdout, "[RESUME-JBASIC]")
    reached_ready = ready_line != "none"
    fdc_stop = first_line(hdl_proc.stdout, "[RESUME-FDC] stop")
    reached_fdc_stop = fdc_stop.startswith("[RESUME-FDC] stop reason=data-read-count")
    ready_visible = screen_text_at(hdl_vram, "READY", 121)
    command_visible = screen_text_at(hdl_vram, "A>JBASIC", 71)
    hdl_vram_ok = len(hdl_vram) == VRAM_SIZE
    fdc_lines = matching_lines(hdl_proc.stdout, "[RESUME-FDC]")
    vram_changes = changed_cells(checkpoint_vram, hdl_vram)
    failures: list[str] = []
    if cosim_proc.returncode != 0:
        failures.append(f"cosim late checkpoint exited {cosim_proc.returncode}")
    if hdl_proc.returncode not in (0, 124):
        failures.append(f"HDL late JBASIC run exited {hdl_proc.returncode}")
    if stop_read_target:
        if not reached_fdc_stop:
            failures.append(f"HDL did not stop at {stop_read_target} FDC data reads")
    else:
        if not reached_ready:
            failures.append("HDL did not report the JBASIC READY oracle")
        if not ready_visible:
            failures.append("HDL final framebuffer does not contain READY at scanline 121")

    status = (
        "HDL EKDOS JBASIC MID FDC DRAIN READY"
        if stop_read_target and not failures
        else "HDL EKDOS JBASIC LATE READY"
        if not failures
        else "REGRESSION"
    )
    lines = [
        "# juku_top checkpoint JBASIC late probe",
        "",
        f"Status: **{status}**",
        "",
        "This diagnostic starts from a generated cosim EKDOS `JBASIC` checkpoint",
        f"after `{total_reads}` total WD1793 data-register reads on",
        "`media/disks/JUKPROG2.CPM`. The command is already entered in the",
        "checkpoint, so the HDL resume runs with no keyboard stimulus.",
    ]
    if stop_read_target:
        lines.extend(
            [
                f"This run stops after `{stop_read_target}` additional HDL FDC data-register",
                "reads, preserving a bounded mid-transfer bridge between the prompt",
                "checkpoint and the final BASIC prompt checkpoint.",
            ]
        )
    else:
        lines.extend(
            [
                "It stops only when the fixed-`0xD800` BASIC `READY` glyph oracle appears.",
            ]
        )
    lines.extend(
        [
        "",
        "## Command",
        "",
        *command_lines(total_reads, stop_reads),
        "",
        "## Evidence",
        "",
        f"- Cosim checkpoint exit code: `{cosim_proc.returncode}`",
        f"- Cosim checkpoint cycle: `{state.get('cyc', 'missing')}`",
        f"- Cosim checkpoint VRAM writes: `{state.get('vram_writes', 'missing')}`",
        f"- Cosim checkpoint PC: `0x{state.get('pc', 'missing')}`",
        f"- Cosim checkpoint keyboard position/phase: `{state.get('kbd_pos', 'missing')}` / `{state.get('kbd_phase', 'missing')}`",
        f"- Cosim checkpoint FDC data reads: `{state.get('fdc_data_reads', 'missing')}`",
        f"- Cosim checkpoint FDC track/sector/data/status: `{state.get('fdc_track', 'missing')}` / `{state.get('fdc_sector', 'missing')}` / `{state.get('fdc_data', 'missing')}` / `{state.get('fdc_status', 'missing')}`",
        f"- HDL checkpoint PC bias: `{os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_LATE_PC_BIAS', '0')}`",
        f"- HDL resume exit code: `{hdl_proc.returncode}`",
        f"- Timed out: `{'yes' if timed_out else 'no'}`",
        f"- READY stop line: `{ready_line}`",
        f"- FDC stop line: `{fdc_stop}`",
        f"- HDL final visible `READY` at scanline 121: `{'yes' if ready_visible else 'no'}`",
        f"- HDL final visible `A>JBASIC` command line at scanline 71: `{'yes' if command_visible else 'no'}`",
        f"- HDL final VRAM size: `{len(hdl_vram)}` ({'ok' if hdl_vram_ok else 'missing/incomplete'})",
        f"- HDL final VRAM SHA256: `{hashlib.sha256(hdl_vram).hexdigest() if hdl_vram else 'missing'}`",
        f"- Checkpoint READY row bytes y=121 x=0..9: `{row_hex(checkpoint_vram, 121)}`",
        f"- HDL final READY row bytes y=121 x=0..9: `{row_hex(hdl_vram, 121)}`",
        f"- First changed VRAM cells: `{', '.join(vram_changes) if vram_changes else 'none'}`",
        f"- FDC trace lines: `{len(fdc_lines)}`",
        f"- Last observed HDL progress FDC data reads: `{data_read_count(hdl_proc.stdout)}`",
        f"- First progress line: `{first_line(hdl_proc.stdout, '[RESUME-PROGRESS]')}`",
        f"- Last progress line: `{last_line(hdl_proc.stdout, '[RESUME-PROGRESS]')}`",
        f"- Stop/fail line: `{first_line(hdl_proc.stdout, 'JUKU-TOP-CHECKPOINT-RESUME: FAIL')}`",
        "",
        "## Boundary",
        "",
        "- This is a checkpoint-resumed proof, not a replacement for the",
        "  prompt-checkpoint command-stimulus report.",
        "- The prompt-checkpoint report still owns the early HDL path: `JBASIC`",
        "  key sampling, command echo, and the first 4,096 post-command FDC data",
        "  reads.",
        ]
    )
    if stop_read_target:
        lines.extend(
            [
                "- This mid-transfer run proves that a later `JBASIC` checkpoint can",
                f"  drain `{stop_read_target}` additional decoded FDC data-register reads",
                "  under checkpoint-resumed `juku_top` execution.",
                "- The open gap remains the uninterrupted HDL bridge from the prompt",
                "  checkpoint through the later transfer checkpoints and then into",
                "  the final `READY` renderer.",
            ]
        )
    else:
        lines.extend(
            [
                "- This late-state run proves that checkpoint-resumed `juku_top` can",
                "  continue from the post-transfer JBASIC state to the user-visible",
                "  BASIC `READY` prompt.",
                "- The open gap is now the uninterrupted HDL bridge between those two",
                "  checkpoint windows, not the final BASIC prompt renderer itself.",
            ]
        )
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    lines.extend(["", "## HDL stdout tail", "", "```"])
    lines.extend(hdl_proc.stdout.splitlines()[-80:])
    lines.append("```")

    REPORT.write_text("\n".join(lines) + "\n")
    try:
        report_label = REPORT.relative_to(ROOT)
    except ValueError:
        report_label = REPORT
    print(f"Wrote {report_label}")
    print("\n".join(lines))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
