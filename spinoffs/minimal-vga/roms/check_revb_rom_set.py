#!/usr/bin/env python3
"""R5.I3 ROM-set, early-stack and ordered diagnostic execution gate."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPECTED_POST = [0x10, 0x20, 0x21, 0x30, 0x31, 0x40, 0x41, 0x50,
                 0x51, 0x60, 0x61, 0x70, 0x71, 0x80, 0x81, 0xFF]


def validate_early(trace: list[dict[str, object]], stack_ready: int) -> list[str]:
    errors = []
    for row in trace:
        if int(row["address"]) >= stack_ready:
            continue
        mnemonic = str(row["mnemonic"])
        if mnemonic == "LXI SP" or mnemonic.startswith(("CALL", "PUSH", "POP")):
            errors.append(f"{mnemonic} at {int(row['address']):04X}h before RAM pass")
    return errors


def validate_post(values: list[int]) -> list[str]:
    return [] if values == EXPECTED_POST else [
        "POST order " + " ".join(f"{v:02X}" for v in values) +
        " != " + " ".join(f"{v:02X}" for v in EXPECTED_POST)
    ]


def main() -> int:
    errors: list[str] = []
    subprocess.run([sys.executable, str(HERE / "build_revb_rom.py"), "--check"], check=True)
    manifest = json.loads((HERE / "revb-rom-set.json").read_text())
    diag_map = json.loads((HERE / "diag_vjuga.map.json").read_text())

    stack_ready = int(diag_map["stack_ready_address"])
    errors += validate_early(diag_map["instruction_trace"], stack_ready)
    first = diag_map["first_stack_instruction"]
    if int(first["address"]) != stack_ready or first["mnemonic"] != "LXI SP":
        errors.append("first post-RAM stack instruction is not the frozen LXI SP")

    # Self-tests prove both semantic guards can reject a plausible regression.
    fake_trace = [{"address": stack_ready - 1, "mnemonic": "CALL", "bytes": [0xCD, 0, 0]}]
    if not validate_early(fake_trace, stack_ready):
        errors.append("early-stack validator accepted injected CALL")
    bad_order = EXPECTED_POST.copy(); bad_order[5], bad_order[6] = bad_order[6], bad_order[5]
    if not validate_post(bad_order):
        errors.append("POST-order validator accepted swapped RAM-address codes")

    c10_source = (ROOT / manifest["images"]["NETC10/VJUGA"]["source"]).read_bytes()
    c10_named = (ROOT / manifest["images"]["NETC10/VJUGA"]["derived_16k"]).read_bytes()
    c10_27 = (ROOT / manifest["images"]["NETC10/VJUGA"]["output"]).read_bytes()
    if c10_named != c10_source or c10_27 != c10_source * 2:
        errors.append("NETC10/VJUGA contains a production byte change or bad 27C256 layout")
    if bytes.fromhex("3E 15 D3 1B 3E 04 D3 18") not in c10_source:
        errors.append("NETC10 no longer contains D57 mode-2/count-4 initialization")
    if sum(c10_source) & 0xFF:
        errors.append("NETC10 complete-ROM additive checksum is not zero")

    with tempfile.TemporaryDirectory(prefix="revb-rom-set.") as temporary:
        tmp = Path(temporary)
        trace_exe = tmp / "trace"
        subprocess.run([
            "cc", "-O2", "-I", str(ROOT / "cosim"), "-o", str(trace_exe),
            str(ROOT / "cosim" / "trace.c"), str(ROOT / "cosim" / "i8080.c"),
            str(ROOT / "cosim" / "juk_disk.c"), str(ROOT / "cosim" / "juku_fdc.c"),
        ], check=True)
        run = subprocess.run(
            [str(trace_exe), str(HERE / "diag_vjuga.bin"), "20000000", "0"],
            cwd=ROOT / "cosim", env={**__import__("os").environ,
                                      "JUKU_TRACE_IO": "1",
                                      "JUKU_USART_PTY": "auto"},
            text=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True,
        )
    events: list[tuple[int, int, int, int]] = []
    pattern = re.compile(r"OUT port=0x([0-9A-Fa-f]{2}) value=0x([0-9A-Fa-f]{2}) cyc=(\d+).*g_vw=(\d+)")
    for match in pattern.finditer(run.stderr):
        events.append(tuple(int(value, 16 if i < 2 else 10) for i, value in enumerate(match.groups())))
    post_events = [event for event in events if event[0] == 0x20]
    post_values = [event[1] for event in post_events]
    errors += validate_post(post_values)
    cycles = {value: cycle for _, value, cycle, _ in post_events}
    if post_events and (post_events[0][3] != 0 or cycles.get(0x80, 0) >= cycles.get(0x81, 0)):
        errors.append("VGA diagnostic stage timing is malformed")
    ready = next((event for event in post_events if event[1] == 0xFF), None)
    if ready is None or ready[3] != 40:
        errors.append("DIAG ready did not follow exactly 40 visible-pattern writes")

    def between(port: int, lo: int, hi: int) -> list[int]:
        return [value for p, value, cycle, _ in events if p == port and cycles[lo] < cycle < cycles[hi]]

    if between(0x1B, 0x50, 0x51)[:2] != [0x15, 0x00] or between(0x18, 0x50, 0x51)[:1] != [0x04]:
        errors.append("DIAG D57 count/latch sequence changed")
    if between(0x1B, 0x51, 0x60)[:2] != [0x76, 0x50] or between(0x19, 0x51, 0x60)[:3] != [0xEE, 0x13, 0x01]:
        errors.append("DIAG sound escalation did not occur after D57 pass")
    serial = bytes(value for port, value, cycle, _ in events if port == 0x08 and cycle > cycles[0x61])
    for phrase in (b"D57 USART PASS\r\n", b"PPI PIC PASS\r\n", b"VGA PATTERN PASS\r\n", b"DIAG READY\r\n"):
        if phrase not in serial:
            errors.append(f"missing late TTL detail {phrase!r}")
    if any(port == 0x08 and cycle < cycles[0x61] for port, _, cycle, _ in events):
        errors.append("serial output occurred before USART pass")

    if errors:
        print("REVB-ROM-SET-CHECK: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "REVB-ROM-SET-CHECK: PASS three 27C256 images; NETC10 zero-byte/PIT-retained; "
        "DIAG no-stack-early and ordered LED -> tone -> TTL escalation"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
