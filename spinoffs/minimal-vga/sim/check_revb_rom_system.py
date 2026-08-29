#!/usr/bin/env python3
"""R5.I6 firmware-wide sequencing against the executable Juku device model.

The HDL I/O twin proves the revised card's pins, clocks and register behavior;
this fast instruction-level gate executes the exact NETC10 and DIAG ROM bytes
through PIT/PPI/USART/framebuffer models and exercises layer-specific faults.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


HERE = Path(__file__).resolve().parent
MV = HERE.parent
ROOT = MV.parents[1]
COSIM = ROOT / "cosim"
ROMS = MV / "roms"
POST = [0x10, 0x20, 0x21, 0x30, 0x31, 0x40, 0x41, 0x50,
        0x51, 0x60, 0x61, 0x70, 0x71, 0x80, 0x81, 0xFF]
SERIAL = (b"D57 USART PASS\r\n" b"PPI PIC PASS\r\n"
          b"VGA PATTERN PASS\r\n" b"DIAG READY\r\n")
EVENT = re.compile(r"\[IOSEQ\] (OUT|IN ) port=0x([0-9A-Fa-f]{2}) "
                   r"value=0x([0-9A-Fa-f]{2}) cyc=(\d+).*g_vw=(\d+)")
WATCH = re.compile(r"\[WATCH\] MW D610=([0-9A-Fa-f]{2})")


@dataclass
class Run:
    events: list[tuple[str, int, int, int, int]]
    watched: list[int]
    state: dict[str, str]


def compile_trace(path: Path) -> None:
    subprocess.run([
        "cc", "-O2", "-I", str(COSIM), "-o", str(path),
        str(COSIM / "trace.c"), str(COSIM / "i8080.c"),
        str(COSIM / "juk_disk.c"), str(COSIM / "juku_fdc.c"),
    ], check=True)


def run(trace: Path, rom: Path, cycles: int, env: dict[str, str]) -> Run:
    with tempfile.TemporaryDirectory(prefix="revb-rom-run.") as td:
        prefix = Path(td) / "checkpoint"
        merged = {**os.environ, "JUKU_TRACE_IO": "1",
                  "JUKU_WATCH_ADDRESS": "0xD610",
                  "JUKU_CHECKPOINT_PREFIX": str(prefix), **env}
        proc = subprocess.run([str(trace), str(rom), str(cycles), "0"],
                              cwd=COSIM, env=merged, text=True,
                              stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                              check=True)
        events = [(m.group(1).strip(), int(m.group(2), 16), int(m.group(3), 16),
                   int(m.group(4)), int(m.group(5)))
                  for m in EVENT.finditer(proc.stderr)]
        watched = [int(x, 16) for x in WATCH.findall(proc.stderr)]
        state = {}
        for line in prefix.with_suffix(".state").read_text().splitlines():
            if "=" in line:
                key, value = line.split("=", 1); state[key] = value
        return Run(events, watched, state)


def outs(result: Run, port: int) -> list[int]:
    return [value for direction, p, value, _, _ in result.events
            if direction == "OUT" and p == port]


def ins(result: Run, port: int) -> list[int]:
    return [value for direction, p, value, _, _ in result.events
            if direction == "IN" and p == port]


def post_values(result: Run) -> list[int]:
    return outs(result, 0x20)


def ordered_subsequence(values: list[int], wanted: list[int]) -> bool:
    pos = 0
    for value in values:
        if pos < len(wanted) and value == wanted[pos]: pos += 1
    return pos == len(wanted)


def validate_netc(result: Run) -> list[str]:
    errors = []
    if not result.watched or result.watched[0] != 0x00:
        errors.append("NETC10 did not store quick-POST success D610=00")
    if not ordered_subsequence(outs(result, 0x07), [0x82, 0x0F, 0x0E]):
        errors.append("NETC10 PPI/POF sequence is not 82,0F,0E")
    if not ordered_subsequence(outs(result, 0x1B), [0x15, 0x00]) or \
            0x04 not in outs(result, 0x18):
        errors.append("NETC10 did not execute D57 mode2/count4/latch")
    if not any(1 <= value <= 4 for value in ins(result, 0x18)):
        errors.append("NETC10 D57 latch read did not return 1..4")
    if 0x05 not in ins(result, 0x09):
        errors.append("NETC10 did not observe initialized USART status 05")
    serial = outs(result, 0x08)
    if not serial or serial[0] != 0xC7:
        errors.append("NETC10 first V16 target-ready byte is not C7")
    if result.state.get("portc") != "01" or result.state.get("video_pof_released") != "1":
        errors.append("NETC10 did not leave Port C=01 / POF released for VGA")
    return errors


def validate_diag(result: Run) -> list[str]:
    errors = []
    if post_values(result) != POST:
        errors.append("DIAG retained POST sequence differs")
    serial = bytes(outs(result, 0x08))
    if serial != SERIAL:
        errors.append("DIAG detailed TTL transcript differs")
    if not ordered_subsequence(outs(result, 0x1B), [0x15, 0x00, 0x76, 0x50]):
        errors.append("DIAG PIT count/latch/tone/silence order differs")
    ready = [event for event in result.events
             if event[0] == "OUT" and event[1] == 0x20 and event[2] == 0xFF]
    if len(ready) != 1 or ready[0][4] != 40:
        errors.append("DIAG FF did not retain after exactly forty VGA writes")
    return errors


def validate_failure(result: Run, code: int) -> list[str]:
    errors = []
    values = post_values(result)
    if not values or values[-1] != code:
        errors.append(f"fault did not terminate at POST {code:02X}")
        return errors
    serial, video = outs(result, 0x08), int(result.state.get("vram_writes", "0"))
    tone = outs(result, 0x19)
    if code in (0x3F, 0x5F) and (serial or video or tone):
        errors.append(f"POST {code:02X} leaked into a later observability layer")
    if code == 0x6F and (serial or video or not tone):
        errors.append("POST 6F did not preserve PIT tone and suppress serial/VGA")
    return errors


def main() -> int:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="revb-rom-system.") as td:
        trace = Path(td) / "trace"
        compile_trace(trace)
        netc = run(trace, ROMS / "netc10_vjuga.bin", 1_000_000,
                   {"JUKU_USART_PTY": "auto"})
        errors += validate_netc(netc)
        netc_pit = run(trace, ROMS / "netc10_vjuga.bin", 1_000_000,
                       {"JUKU_USART_PTY": "auto",
                        "JUKU_PIT_FAULT": "18:FF:00"})
        if netc_pit.watched[-1:] != [0xC5] or outs(netc_pit, 0x08):
            errors.append("NETC10 missing-PIT control did not stop at C5 before target-ready")

        diag = run(trace, ROMS / "diag_vjuga.bin", 20_000_000,
                   {"JUKU_USART_PTY": "auto"})
        errors += validate_diag(diag)
        cases = [
            (0x3F, {"JUKU_USART_PTY": "auto", "JUKU_RAM_FAULT": "4000:01:00"}),
            (0x5F, {"JUKU_USART_PTY": "auto", "JUKU_PIT_FAULT": "18:FF:00"}),
            (0x6F, {}),  # absent USART reads back its last control byte, not 05h
        ]
        for code, env in cases:
            errors += validate_failure(run(trace, ROMS / "diag_vjuga.bin",
                                           20_000_000, env), code)

    if "--self-test" in sys.argv:
        bad = Run(list(netc.events), list(netc.watched), dict(netc.state))
        bad.state["portc"] = "81"
        if not validate_netc(bad): errors.append("POF mutation escaped")
        bad_diag = Run(list(diag.events), list(diag.watched), dict(diag.state))
        for i, event in enumerate(bad_diag.events):
            if event[0] == "OUT" and event[1] == 0x20 and event[2] == 0x40:
                bad_diag.events[i] = (event[0], event[1], 0x41, event[3], event[4]); break
        if not validate_diag(bad_diag): errors.append("POST-order mutation escaped")

    if errors:
        print("REVB-ROM-SYSTEM-CHECK: FAIL")
        for error in errors: print(f"- {error}")
        return 1
    print("REVB-ROM-SYSTEM-CHECK: PASS NETC10 POST/D57/USART/POF/C7; "
          "DIAG 16 POST -> tone -> 60-byte TTL -> 40-byte VGA; "
          "RAM/PIT/USART and two semantic mutations rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
