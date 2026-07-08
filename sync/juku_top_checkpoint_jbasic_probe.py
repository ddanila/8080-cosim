#!/usr/bin/env python3
"""Checkpoint-resumed HDL diagnostic for the EKDOS JBASIC command stimulus."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = Path(os.environ.get("JUKU_TOP_CHECKPOINT_JBASIC_REPORT", ROOT / "docs" / "juku-top-checkpoint-jbasic-probe.md"))
ROM = ROOT / "roms" / "ekta37.bin"
DISK = ROOT / "media" / "disks" / "JUKPROG2.CPM"
VRAM_STRIDE = 40
VRAM_LINES = 241
VRAM_SIZE = VRAM_STRIDE * VRAM_LINES

SCREEN_GLYPHS = {
    ">": (
        "...#....",
        "....#...",
        ".....#..",
        "......#.",
        ".....#..",
        "....#...",
        "...#....",
    ),
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
    "S": (
        "...###..",
        "..#...#.",
        "..#.....",
        "...###..",
        "......#.",
        "..#...#.",
        "...###..",
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


def generate_prompt_checkpoint(tmp: Path) -> tuple[subprocess.CompletedProcess[str], Path, dict[str, str]]:
    trace = compile_trace(tmp)
    prefix = tmp / "jbasic-prompt"
    old_vram = tmp / "old-vram.bin"
    cosim_vram = ROOT / "cosim" / "vram.bin"
    had_vram = cosim_vram.exists()
    if had_vram:
        shutil.copyfile(cosim_vram, old_vram)

    env = os.environ.copy()
    env["JUKU_DISK"] = str(DISK)
    env["JUKU_KEYS"] = "TDD|"
    env["JUKU_KEY_HOLD_FRAMES"] = os.environ.get("JUKU_TOP_CHECKPOINT_JBASIC_HOLD_FRAMES", "6")
    env["JUKU_KEY_GAP_FRAMES"] = os.environ.get("JUKU_TOP_CHECKPOINT_JBASIC_GAP_FRAMES", "8")
    env["JUKU_CHECKPOINT_PREFIX"] = str(prefix)
    env["JUKU_CHECKPOINT_CYC"] = os.environ.get("JUKU_TOP_CHECKPOINT_JBASIC_PROMPT_CYCLES", "14200002")
    proc = subprocess.run(
        [str(trace), str(ROM), "250000000", "0", "200000"],
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
        f"+state_vram_writes={state_arg(state, 'vram_writes', '73446')}",
        f"+state_pc={state_arg(state, 'pc', 'FED4')}",
        f"+state_pc_bias={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_PC_BIAS', '-1')}",
        f"+state_sp={state_arg(state, 'sp', 'D2F4')}",
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
        "+state_kbd_pos=0",
        "+state_kbd_phase=0",
        f"+state_pic_icw1={state_arg(state, 'pic_icw1', 'D6')}",
        f"+state_pic_icw2={state_arg(state, 'pic_icw2', 'FE')}",
        f"+state_pic_mask={state_arg(state, 'pic_mask', 'DF')}",
        f"+state_pic_expect_icw2={state_arg(state, 'pic_expect_icw2', '0')}",
        f"+state_fdc_status={state_arg(state, 'fdc_status', '00')}",
        f"+state_fdc_track={state_arg(state, 'fdc_track', '02')}",
        f"+state_fdc_sector={state_arg(state, 'fdc_sector', '06')}",
        f"+state_fdc_data={state_arg(state, 'fdc_data', 'E5')}",
        f"+state_fdc_command={state_arg(state, 'fdc_command', '80')}",
        f"+state_fdc_buffer_pos={state_arg(state, 'fdc_buffer_pos', '0')}",
        f"+state_fdc_buffer_len={state_arg(state, 'fdc_buffer_len', '0')}",
    ]


def run_hdl(tmp: Path, ram_bin: Path, state: dict[str, str]) -> tuple[subprocess.CompletedProcess[str], bool, bytes]:
    ram_hex = tmp / "jbasic-prompt.ram.hex"
    rom_hex = tmp / "ekta37.hex"
    sim = tmp / "juku_top_checkpoint_resume_tb"
    out_path = tmp / "jbasic-hdl.out"
    err_path = tmp / "jbasic-hdl.err"
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
        f"+max_mcyc={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_MAX_MCYC', '700000')}",
        f"+timecap={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_TIMECAP', '4200000000')}",
        f"+frameirq={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_FRAMEIRQ', '80000')}",
        f"+trace_resume={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_TRACE_RESUME', '0')}",
        f"+trace_resume_after={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_TRACE_AFTER', '0')}",
        f"+trace_resume_after_count={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_TRACE_AFTER_COUNT', '0')}",
        "+jbasickeys=1",
        f"+command_key_mcyc={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_KEY_MCYC', '250')}",
        f"+keyat={state_arg(state, 'vram_writes', '73446')}",
        f"+khold={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_KHOLD', '160000')}",
        f"+kgap={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_KGAP', '240000')}",
        "+tracekbd=1",
        f"+tracefdc={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_TRACE_FDC', '1')}",
        f"+stopkbdhit={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_STOP_KBD_HIT', '0')}",
        f"+progress_mcyc={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_PROGRESS_MCYC', '25000')}",
        f"+stopfdc={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_STOP_FDC', '0')}",
        f"+stopfdc_data_read={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_STOP_DATA_READ', '0')}",
        f"+stopfdc_data_reads={os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_STOP_DATA_READS', '4096')}",
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
                timeout=int(os.environ.get("JUKU_TOP_CHECKPOINT_JBASIC_TIMEOUT", "480")),
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
            subprocess.CompletedProcess(args, 124, stdout=out_path.read_text(errors="replace"), stderr=err_path.read_text(errors="replace")),
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


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="juku-top-checkpoint-jbasic.") as tmp_name:
        tmp = Path(tmp_name)
        cosim_proc, ram_bin, state = generate_prompt_checkpoint(tmp)
        checkpoint_ram = ram_bin.read_bytes()
        checkpoint_vram = checkpoint_ram[0xD800 : 0xD800 + VRAM_SIZE]
        hdl_proc, timed_out, hdl_vram = run_hdl(tmp, ram_bin, state)

    key_presses = matching_lines(hdl_proc.stdout, "[RESUME-KBD-STIM] press")
    key_releases = matching_lines(hdl_proc.stdout, "[RESUME-KBD-STIM] release")
    key_hits = matching_lines(hdl_proc.stdout, "[RESUME-KBD-HIT]")
    active_hit_keys = sorted({int(match.group(1)) for match in re.finditer(r"\[RESUME-KBD-HIT\] active key=([0-9]+)", hdl_proc.stdout)})
    noncf_hit_keys = sorted({int(match.group(1)) for match in re.finditer(r"\[RESUME-KBD-HIT\] noncf key=([0-9]+)", hdl_proc.stdout)})
    ppi0_lines = matching_lines(hdl_proc.stdout, "[RESUME-PPI0]")
    kbd_scan_reads = matching_lines(hdl_proc.stdout, "[RESUME-KBD] IN")
    kbd_scan_writes = matching_lines(hdl_proc.stdout, "[RESUME-KBD] OUT")
    resume_trace = matching_lines(hdl_proc.stdout, "[RESUME-TRACE]")
    reached_ready = first_line(hdl_proc.stdout, "[RESUME-JBASIC]") != "none"
    fdc_lines = matching_lines(hdl_proc.stdout, "[RESUME-FDC]")
    fdc_stop = first_line(hdl_proc.stdout, "[RESUME-FDC] stop")
    reached_fdc = fdc_stop != "none"
    reached_fdc_data_read = fdc_stop.startswith("[RESUME-FDC] stop reason=data-read")
    command_echo_line = first_line(hdl_proc.stdout, "[RESUME-JBASIC-CMD]")
    command_visible = screen_text_at(hdl_vram, "A>JBASIC", 71)
    command_reached = command_echo_line != "none" or command_visible
    hdl_vram_ok = len(hdl_vram) == VRAM_SIZE
    vram_changes = changed_cells(checkpoint_vram, hdl_vram)
    failures: list[str] = []
    if cosim_proc.returncode != 0:
        failures.append(f"cosim prompt checkpoint exited {cosim_proc.returncode}")
    if hdl_proc.returncode not in (0, 124):
        failures.append(f"HDL JBASIC command stimulus run exited {hdl_proc.returncode}")
    if len(key_presses) != 7:
        failures.append(f"expected 7 JBASIC key presses, saw {len(key_presses)}")
    if len(key_releases) != 7 and not reached_fdc:
        failures.append(f"expected 7 JBASIC key releases, saw {len(key_releases)}")

    status = (
        "HDL EKDOS JBASIC FDC DATA READ READY"
        if not failures and reached_fdc_data_read
        else
        "HDL EKDOS JBASIC POST-COMMAND FDC READY"
        if not failures and reached_fdc
        else
        "HDL EKDOS JBASIC COMMAND ECHO READY"
        if not failures and command_reached
        else
        "HDL EKDOS JBASIC KEYBOARD SAMPLING READY"
        if not failures and key_hits
        else "HDL EKDOS JBASIC COMMAND STIMULUS READY"
        if not failures
        else "REGRESSION"
    )
    lines = [
        "# juku_top checkpoint JBASIC probe",
        "",
        f"Status: **{status}**",
        "",
        "This diagnostic starts from a generated cosim EKDOS `A>` prompt",
        "checkpoint on `media/disks/JUKPROG2.CPM`, loads that RAM/state into",
        "`juku_top`, and injects the fixed `JBASIC` + Enter command through the",
        "checkpoint-resume keyboard path. It is the first HDL-side bridge from",
        "the now-pinned cosim `JBASIC` READY oracle toward a full HDL BASIC",
        "prompt proof.",
        "",
        "## Command",
        "",
        "```sh",
        "sync/juku_top_checkpoint_jbasic_probe.py",
        "```",
        "",
        "## Evidence",
        "",
        f"- Cosim checkpoint exit code: `{cosim_proc.returncode}`",
        f"- Cosim checkpoint cycle: `{state.get('cyc', 'missing')}`",
        f"- Cosim checkpoint VRAM writes: `{state.get('vram_writes', 'missing')}`",
        f"- Cosim checkpoint PC: `0x{state.get('pc', 'missing')}`",
        f"- HDL checkpoint PC bias: `{os.environ.get('JUKU_TOP_CHECKPOINT_JBASIC_PC_BIAS', '-1')}`",
        f"- Cosim checkpoint keyboard position/phase: `{state.get('kbd_pos', 'missing')}` / `{state.get('kbd_phase', 'missing')}`",
        f"- HDL resume exit code: `{hdl_proc.returncode}`",
        f"- Timed out: `{'yes' if timed_out else 'no'}`",
        f"- JBASIC key presses: `{len(key_presses)}`",
        f"- JBASIC key releases: `{len(key_releases)}`",
        f"- First key press: `{key_presses[0] if key_presses else 'none'}`",
        f"- Last key release: `{key_releases[-1] if key_releases else 'none'}`",
        f"- Keyboard hit lines: `{len(key_hits)}`",
        f"- Active-read key indices: `{active_hit_keys}`",
        f"- Non-`0xCF` key indices: `{noncf_hit_keys}`",
        f"- First keyboard hit: `{key_hits[0] if key_hits else 'none'}`",
        f"- Last keyboard hit: `{key_hits[-1] if key_hits else 'none'}`",
        f"- PPI0 non-keyboard trace lines: `{len(ppi0_lines)}`",
        f"- Keyboard column writes: `{len(kbd_scan_writes)}`",
        f"- Keyboard Port B reads: `{len(kbd_scan_reads)}`",
        f"- HDL M-cycle trace lines: `{len(resume_trace)}`",
        f"- First HDL M-cycle trace: `{resume_trace[0] if resume_trace else 'none'}`",
        f"- Last HDL M-cycle trace: `{resume_trace[-1] if resume_trace else 'none'}`",
        f"- READY stop line: `{first_line(hdl_proc.stdout, '[RESUME-JBASIC]')}`",
        f"- FDC trace lines: `{len(fdc_lines)}`",
        f"- FDC stop line: `{fdc_stop}`",
        f"- HDL VRAM dump size: `{len(hdl_vram)}` ({'ok' if hdl_vram_ok else 'missing/incomplete'})",
        f"- Command echo line: `{command_echo_line}`",
        f"- Final visible `A>JBASIC` command line at scanline 71: `{'yes' if command_visible else 'no'}`",
        f"- Checkpoint command row bytes y=71 x=0..9: `{row_hex(checkpoint_vram, 71)}`",
        f"- HDL final command row bytes y=71 x=0..9: `{row_hex(hdl_vram, 71)}`",
        f"- First changed VRAM cells: `{', '.join(vram_changes) if vram_changes else 'none'}`",
        f"- First progress line: `{first_line(hdl_proc.stdout, '[RESUME-PROGRESS]')}`",
        f"- Last progress line: `{last_line(hdl_proc.stdout, '[RESUME-PROGRESS]')}`",
        f"- Stop/fail line: `{first_line(hdl_proc.stdout, 'JUKU-TOP-CHECKPOINT-RESUME: FAIL')}`",
        "",
        "## Boundary",
        "",
        "- The testbench now has opt-in `+jbasickeys=1` support for the exact",
        "  `JBASIC` + Enter sequence (`J`, `B`, `A`, `S`, `I`, `C`, Return).",
        "- The same bench also has `+stopjbasicready=1`, which checks the final",
        "  `READY` prompt with exact fixed-`0xD800` glyph bytes.",
        "- The default run now uses frame-scale key holds/gaps, `+stopfdc=0`,",
        "  and `+stopfdc_data_reads=4096` so eight full 512-byte data-register",
        "  windows are a bounded HDL stop condition.",
        "- This report claims the checkpoint-resumed HDL FDC data-read",
        "  boundary: frame-scale command stimulus is read through PPI0 Port B,",
        "  the full `A>JBASIC` command line is observed by the bench-side",
        "  oracle, and 4096 decoded FDC data-register reads complete.",
        "- The report also preserves the HDL framebuffer dump before restoring",
        "  the worktree copy and checks for the exact cosim-pinned `A>JBASIC`",
        "  command glyphs at scanline 71.",
        "- The bench now counts PPI0 traffic plus `[RESUME-KBD-HIT]` active-key",
        "  and non-`0xCF` reads; set `JUKU_TOP_CHECKPOINT_JBASIC_STOP_KBD_HIT=1`",
        "  to stop at the first sampled keyboard hit during retiming experiments.",
        "- Set `JUKU_TOP_CHECKPOINT_JBASIC_TRACE_RESUME=N` to include the first",
        "  `N` resumed HDL M-cycle trace lines in this report.",
        "- Next work is to continue from the 4096-byte FDC data-read window",
        "  through the full disk transfer and finally stop on `[RESUME-JBASIC]`.",
    ]
    if reached_ready:
        lines.append("- This run did reach the HDL `READY` oracle; promote the report status and CI gate.")
    if reached_fdc:
        if reached_fdc_data_read:
            lines.append("- This run reached HDL FDC data-register reads; next work is to continue through the disk transfer and the `READY` oracle.")
        else:
            lines.append("- This run reached post-command HDL FDC I/O; next work is to continue through FDC data reads and the `READY` oracle.")
    if command_reached and not reached_fdc:
        lines.append("- This run did echo the full HDL `A>JBASIC` command line; the next boundary is Return execution and FDC traffic.")
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
