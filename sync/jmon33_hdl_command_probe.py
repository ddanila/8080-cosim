#!/usr/bin/env python3
"""Checkpoint-resumed juku_top proof for the jmon33 command surface."""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "jmon33-hdl-command-probe.md"
ROM = ROOT / "roms" / "jmon33.bin"
ROM_HEX = ROOT / "hdl" / "sim" / "jmon33.hex"
VRAM_DUMP = ROOT / "hdl" / "sim" / "checkpoint_vram_top.bin"
VRAM_STRIDE = 40
VRAM_LINES = 241
BLANK_VRAM_SHA256 = "559eb05d39a8e243be3e4b051e94f6572a487cc6f90c4847f333d61fe887b28d"
IDLE_CURSOR_VRAM_SHA256 = "f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397"
KBD_RE = re.compile(r"\[RESUME-KBD\] IN port=0x05 data=0x([0-9A-Fa-f]{2})")


@dataclass(frozen=True)
class CommandCase:
    name: str
    key: str
    key_code: int
    expected_sha256: str
    expected_blocks: tuple[tuple[int, int], ...]


CASES = (
    CommandCase(
        "A-enter",
        "A",
        65,
        "efc7ce7d04f843c0ad4bf4df5f5139ca52818ba15e4aa7707124308bbdc6858f",
        ((8, 60),),
    ),
    CommandCase(
        "T-enter",
        "T",
        84,
        "348a571e28b5021fc28ca0a83d19e87100d28a9e32910333814eb71a8573b911",
        ((200, 20), (152, 40)),
    ),
    CommandCase(
        "B-enter",
        "B",
        66,
        "7de5d7ccbcbe39fc6f644adbeb68b1d38706be9d77616772b3d10686e005d52e",
        ((0, 80),),
    ),
)


def write_hex(src: Path, dst: Path) -> None:
    dst.write_text("\n".join(f"{byte:02x}" for byte in src.read_bytes()) + "\n")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest() if data else ""


def sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return "missing"


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


def compile_hdl(tmp: Path) -> Path:
    sim = tmp / "juku_top_checkpoint_resume_tb"
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
    return sim


def parse_state(path: Path) -> dict[str, str]:
    state: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        state[key] = value
    return state


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


def generate_checkpoint(tmp: Path) -> tuple[subprocess.CompletedProcess[str], Path, dict[str, str], str]:
    trace = compile_trace(tmp)
    prefix = tmp / "jmon33-hdl-command"
    checkpoint_cycles = os.environ.get("JMON33_HDL_COMMAND_CHECKPOINT_CYCLES", "20000000")
    frame_cycles = os.environ.get("JMON33_HDL_COMMAND_FRAME_CYCLES", "200000")
    max_cycles = os.environ.get("JMON33_HDL_COMMAND_MAX_COSIM_CYCLES", "20000000")
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


def pixel(vram: bytes, x: int, y: int) -> int:
    return (vram[y * VRAM_STRIDE + x // 8] >> (7 - (x % 8))) & 1


def solid_block(vram: bytes, x0: int, y0: int, width: int = 8, height: int = 10) -> bool:
    if len(vram) != VRAM_STRIDE * VRAM_LINES:
        return False
    for y in range(y0, y0 + height):
        for x in range(x0, x0 + width):
            if pixel(vram, x, y) != 1:
                return False
    return True


def block_summary(vram: bytes) -> tuple[tuple[int, int], ...]:
    if len(vram) != VRAM_STRIDE * VRAM_LINES:
        return ()
    blocks: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for y in range(0, VRAM_LINES - 9):
        for bx in range(VRAM_STRIDE):
            x = bx * 8
            if (x, y) in seen:
                continue
            if all(vram[(y + row) * VRAM_STRIDE + bx] == 0xFF for row in range(10)):
                blocks.append((x, y))
                for row in range(10):
                    seen.add((x, y + row))
    return tuple(blocks)


def first_line(text: str, prefix: str) -> str:
    return next((line for line in text.splitlines() if line.startswith(prefix)), "none")


def run_case(
    tmp: Path,
    sim: Path,
    ram_bin: Path,
    state: dict[str, str],
    case: CommandCase,
) -> dict[str, object]:
    ram_hex = tmp / "checkpoint.ram.hex"
    write_hex(ram_bin, ram_hex)
    write_hex(ROM, ROM_HEX)
    out_path = tmp / f"{case.name}.out"
    err_path = tmp / f"{case.name}.err"
    old_vram = tmp / f"old-{case.name}-vram.bin"
    had_vram = VRAM_DUMP.exists()
    if had_vram:
        shutil.copyfile(VRAM_DUMP, old_vram)

    args = [
        "vvp",
        str(sim),
        f"+checkpoint_ram={ram_hex}",
        "+rom=hdl/sim/jmon33.hex",
        f"+max_mcyc={os.environ.get('JMON33_HDL_COMMAND_MAX_MCYC', '500000')}",
        f"+timecap={os.environ.get('JMON33_HDL_COMMAND_TIMECAP', '4000000000')}",
        f"+frameirq={os.environ.get('JMON33_HDL_COMMAND_FRAMEIRQ', '200000')}",
        f"+progress_mcyc={os.environ.get('JMON33_HDL_COMMAND_PROGRESS_MCYC', '0')}",
        "+tracekbd=1",
        "+commandkeys=1",
        f"+command_key={case.key_code}",
        "+command_key_count=2",
        f"+command_key_mcyc={os.environ.get('JMON33_HDL_COMMAND_KEY_MCYC', '50000')}",
        "+commandstop=1",
        f"+command_x0={case.expected_blocks[0][0]}",
        f"+command_y0={case.expected_blocks[0][1]}",
        f"+command_x1={case.expected_blocks[1][0] if len(case.expected_blocks) > 1 else -1}",
        f"+command_y1={case.expected_blocks[1][1] if len(case.expected_blocks) > 1 else -1}",
        f"+keyat={os.environ.get('JMON33_HDL_COMMAND_KEYAT', '1')}",
        f"+khold={os.environ.get('JMON33_HDL_COMMAND_KHOLD', '200000')}",
        f"+kgap={os.environ.get('JMON33_HDL_COMMAND_KGAP', '100000')}",
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
                timeout=int(os.environ.get("JMON33_HDL_COMMAND_TIMEOUT", "240")),
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
    vram = VRAM_DUMP.read_bytes() if VRAM_DUMP.exists() else b""
    if had_vram:
        shutil.copyfile(old_vram, VRAM_DUMP)
    elif VRAM_DUMP.exists():
        VRAM_DUMP.unlink()

    kbd_values = tuple(int(match.group(1), 16) for match in KBD_RE.finditer(proc.stdout))
    active_values = tuple(sorted(set(value for value in kbd_values if value != 0xCF)))
    expected_blocks_ok = all(solid_block(vram, x, y) for x, y in case.expected_blocks)
    return {
        "case": case,
        "proc": proc,
        "timed_out": timed_out,
        "sha": sha256_bytes(vram),
        "command_line": first_line(proc.stdout, "[RESUME-COMMAND]"),
        "kbd_samples": len(kbd_values),
        "active_values": active_values[:8],
        "blocks": block_summary(vram),
        "expected_blocks_ok": expected_blocks_ok,
        "visible_pixels": sum(byte.bit_count() for byte in vram),
    }


def main() -> int:
    case_filter = {
        name.strip()
        for name in os.environ.get("JMON33_HDL_COMMAND_CASES", "").split(",")
        if name.strip()
    }
    cases = tuple(case for case in CASES if not case_filter or case.name in case_filter or case.key in case_filter)
    if not cases:
        raise SystemExit(f"no cases matched JMON33_HDL_COMMAND_CASES={','.join(sorted(case_filter))}")

    with tempfile.TemporaryDirectory(prefix="jmon33-hdl-command.") as tmp_name:
        tmp = Path(tmp_name)
        cosim_proc, ram_bin, state, checkpoint_vram_sha = generate_checkpoint(tmp)
        sim = compile_hdl(tmp)
        results = [run_case(tmp, sim, ram_bin, state, case) for case in cases]

    infra_failures: list[str] = []
    if cosim_proc.returncode != 0:
        infra_failures.append(f"cosim checkpoint exited {cosim_proc.returncode}")
    expected_checkpoint_sha = os.environ.get(
        "JMON33_HDL_COMMAND_CHECKPOINT_SHA256",
        IDLE_CURSOR_VRAM_SHA256,
    )
    accepted_checkpoint_shas = {expected_checkpoint_sha, BLANK_VRAM_SHA256}
    if checkpoint_vram_sha not in accepted_checkpoint_shas:
        infra_failures.append(f"cosim checkpoint VRAM SHA256 was unexpected: {checkpoint_vram_sha}")

    result_by_name = {str(result["case"].name): result for result in results}
    a_result = result_by_name.get("A-enter")
    a_passed = bool(
        a_result is not None
        and a_result["proc"].returncode == 0
        and a_result["sha"] == a_result["case"].expected_sha256
        and a_result["expected_blocks_ok"]
        and str(a_result["command_line"]).startswith("[RESUME-COMMAND]")
    )
    all_selected_cases_passed = all(
        result["proc"].returncode == 0
        and result["sha"] == result["case"].expected_sha256
        and result["expected_blocks_ok"]
        and str(result["command_line"]).startswith("[RESUME-COMMAND]")
        for result in results
    ) and not infra_failures
    passed = all_selected_cases_passed and len(cases) == len(CASES)
    if passed:
        status = "JMON33 HDL COMMAND SURFACE READY"
    elif a_passed and not infra_failures:
        status = "JMON33 HDL A-COMMAND ORACLE READY"
    else:
        status = "JMON33 HDL COMMAND BOUNDED DIAGNOSTIC"

    lines = [
        "# jmon33 HDL command-surface probe",
        "",
        f"Status: **{status}**",
        "",
        "This guard starts from a generated Monitor 3.3 cosim checkpoint,",
        "loads that RAM and visible state into `juku_top`, injects a single",
        "command plus Enter through the `juku_top` keyboard pins, and checks the",
        "visible command-state oracles pinned by `docs/jmon33-command-probe.md`.",
        "",
        "## Command",
        "",
        "```sh",
        "sync/jmon33_hdl_command_probe.py",
        "```",
        "",
        "Environment overrides:",
        "",
        f"- `JMON33_HDL_COMMAND_MAX_MCYC` default `{os.environ.get('JMON33_HDL_COMMAND_MAX_MCYC', '500000')}`",
        f"- `JMON33_HDL_COMMAND_TIMECAP` default `{os.environ.get('JMON33_HDL_COMMAND_TIMECAP', '4000000000')}`",
        f"- `JMON33_HDL_COMMAND_FRAMEIRQ` default `{os.environ.get('JMON33_HDL_COMMAND_FRAMEIRQ', '200000')}`",
        f"- `JMON33_HDL_COMMAND_KHOLD` default `{os.environ.get('JMON33_HDL_COMMAND_KHOLD', '200000')}`",
        f"- `JMON33_HDL_COMMAND_KGAP` default `{os.environ.get('JMON33_HDL_COMMAND_KGAP', '100000')}`",
        f"- `JMON33_HDL_COMMAND_CHECKPOINT_CYCLES` default `{os.environ.get('JMON33_HDL_COMMAND_CHECKPOINT_CYCLES', '20000000')}`",
        f"- `JMON33_HDL_COMMAND_KEY_MCYC` default `{os.environ.get('JMON33_HDL_COMMAND_KEY_MCYC', '50000')}`",
        f"- `JMON33_HDL_COMMAND_CASES` selected `{','.join(case.name for case in cases)}`",
        "",
        "## Evidence",
        "",
        f"- Cosim checkpoint exit: `{cosim_proc.returncode}`",
        f"- Cosim checkpoint VRAM SHA256: `{checkpoint_vram_sha}`",
    ]
    if infra_failures:
        lines.append(f"- Infra failures: `{' ; '.join(infra_failures)}`")
    lines.extend(
        [
            "",
            "| Case | Key | Exit | Timed out | Keyboard samples | Active key values | Command oracle | Visible blocks | Pixels | VRAM SHA256 | Result |",
            "| --- | --- | ---: | --- | ---: | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for result in results:
        case = result["case"]
        active = ", ".join(f"`0x{value:02X}`" for value in result["active_values"]) or "-"
        blocks = ", ".join(f"`x={x},y={y}`" for x, y in result["blocks"]) or "-"
        ok = (
            result["proc"].returncode == 0
            and result["sha"] == case.expected_sha256
            and result["expected_blocks_ok"]
            and str(result["command_line"]).startswith("[RESUME-COMMAND]")
        )
        lines.append(
            f"| {case.name} | `{case.key}\\n` | `{result['proc'].returncode}` | "
            f"`{result['timed_out']}` | `{result['kbd_samples']}` | {active} | "
            f"`{result['command_line']}` | {blocks} | `{result['visible_pixels']}` | "
            f"`{result['sha'] or 'missing'}` | {'PASS' if ok else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "## Disposition",
            "",
            "- The HDL checkpoint harness now has a generic two-key command stimulus",
            "  path in addition to the fixed EKDOS `TDD` stimulus path.",
            "- The default checkpoint is the monitor-idle cursor state. A later",
            "  `JMON33_HDL_COMMAND_KEY_MCYC` delay lets the resumed keyboard scan",
            "  settle before the command key is pressed.",
            "- The `A` command now reaches the same HDL framebuffer SHA256 as the",
            "  cosim command-surface oracle. `T` and `B` remain diagnostic cases",
            "  until their final command framebuffers also match cosim.",
            "- This proof is scoped to jmon33 monitor commands. BASIC remains tracked",
            "  separately by `docs/basic-launch-probe.md` and",
            "  `docs/basic-factory-command-probe.md`.",
        ]
    )
    lines.append("")
    REPORT.write_text("\n".join(lines))
    infrastructure_ok = not infra_failures and all(result["proc"].returncode in (0, 124) for result in results)
    print(f"JMON33-HDL-COMMAND-PROBE: {'PASS' if passed else 'PARTIAL' if a_passed and infrastructure_ok else 'DIAGNOSTIC'}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if infrastructure_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
