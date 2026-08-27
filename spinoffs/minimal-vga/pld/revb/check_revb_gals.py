#!/usr/bin/env python3
"""R5.P1 pin, oracle, artifact, and JEDEC guard for the Memory and I/O GALs."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REVB = HERE.parents[1] / "kicad" / "revb"

ALIASES = {
    "memory-u3": {
        "MREQn": "MREQ_N", "RDn": "RD_N", "WRn": "WR_N",
        "ROMCEn": "ROM_CE_N", "RAMCEn": "RAM_CE_N",
        "MEMRDn": "MEM_RD_N", "MEMWRn": "MEM_WR_N",
        "GND": "GND", "VCC": "VCC5",
    },
    "io-u2": {
        "IORQn": "IORQ_N", "RESETn": "RESET_N", "M1n": "M1_N",
        "PICINT": "PIC_INT", "PICCSn": "PIC_CS_N", "PPICSn": "PPI_CS_N",
        "UARTCSn": "UART_CS_N", "IORESET": "IO_RESET", "INTn": "INT_N",
        "INTAn": "INTA_N", "GND": "GND", "VCC": "VCC5",
    },
}
BOARD_REF = {"memory-u3": ("mem", "U3"), "io-u2": ("io", "U2")}


def source(base: str) -> tuple[str, list[str], dict[str, str]]:
    raw = (HERE / f"{base}.pld").read_text()
    lines = []
    for line in raw.splitlines():
        line = line.split(";", 1)[0].strip()
        if line:
            lines.append(line)
    device, _title = lines[:2]
    pin_count = 24 if device == "GAL22V10" else 20
    pins = lines[2].split() + lines[3].split()
    if len(pins) != pin_count:
        raise AssertionError(f"{base}: {len(pins)} pins, expected {pin_count}")
    assignments: dict[str, str] = {}
    current = ""
    for line in lines[4:]:
        if line == "DESCRIPTION":
            break
        if "=" in line:
            current, expr = (part.strip() for part in line.split("=", 1))
            assignments[current] = expr
        elif line.startswith("+") and current:
            assignments[current] += " " + line
    return device, pins, assignments


def eval_sop(expr: str, env: dict[str, bool]) -> bool:
    for term in expr.split("+"):
        value = True
        for literal in term.split("*"):
            literal = literal.strip()
            invert = literal.startswith("/")
            name = literal[1:] if invert else literal
            if name == "GND":
                bit = False
            elif name == "VCC":
                bit = True
            else:
                bit = env[name]
            value &= not bit if invert else bit
        if value:
            return True
    return False


def physical(assignments: dict[str, str], name: str, env: dict[str, bool]) -> bool:
    if name in assignments:
        return eval_sop(assignments[name], env)
    inverted = "/" + name
    if inverted in assignments:
        return not eval_sop(assignments[inverted], env)
    raise AssertionError(f"missing equation for {name}")


def check_pins(base: str, device: str, pins: list[str]) -> None:
    board_name, ref = BOARD_REF[base]
    board = json.loads((REVB / f"{board_name}.board.json").read_text())
    part = next(part for part in board["chips"] if part["ref"] == ref)
    expected_device = "GAL22V10" if base == "memory-u3" else "GAL16V8_IOSEL"
    assert part["type"] == expected_device, (base, part["type"])
    aliases = ALIASES[base]
    for number, pld_name in enumerate(pins, 1):
        board_name = part["pins"][str(number)]
        if pld_name == "NC":
            assert "NC" in board_name, (base, number, pld_name, board_name)
        else:
            expected = aliases.get(pld_name, pld_name)
            assert expected == board_name, (base, number, pld_name, board_name)
    if base == "io-u2":
        assert pins[18] == "NC", "ATF16V8 complex-mode pin 19 must not be an input"


def check_memory(assignments: dict[str, str]) -> None:
    for mode in range(4):
        for address in range(0x10000):
            env = {
                "MREQn": False, "RDn": True, "WRn": True,
                "MODE0": bool(mode & 1), "MODE1": bool(mode & 2),
                **{f"A{bit}": bool(address & (1 << bit)) for bit in range(11, 16)},
            }
            rom = (mode == 0 and address <= 0x3FFF) or (
                mode in (1, 2) and address >= 0xD800
            )
            cart = mode == 2 and 0x4000 <= address <= 0xBFFF
            video = mode in (0, 3) and address >= 0xD800
            ram = not (rom or cart or video)
            rom_ce = physical(assignments, "ROMCEn", env)
            ram_ce = physical(assignments, "RAMCEn", env)
            assert rom_ce == (not rom), (mode, hex(address), "ROM", rom_ce)
            assert ram_ce == (not ram), (mode, hex(address), "RAM", ram_ce)
            assert rom_ce or ram_ce, (mode, hex(address), "ROM/RAM contention")
    base_env = {"MREQn": True, "RDn": True, "WRn": True, "MODE0": False,
                "MODE1": False, **{f"A{bit}": False for bit in range(11, 16)}}
    assert physical(assignments, "ROMCEn", base_env)
    assert physical(assignments, "RAMCEn", base_env)
    for mreq_n in (False, True):
        for rd_n in (False, True):
            for wr_n in (False, True):
                env = base_env | {"MREQn": mreq_n, "RDn": rd_n, "WRn": wr_n}
                assert physical(assignments, "MEMRDn", env) == (mreq_n or rd_n)
                assert physical(assignments, "MEMWRn", env) == (mreq_n or wr_n)
    assert len(assignments["/ROMCEn"].split("+")) <= 8
    assert len(assignments["/RAMCEn"].split("+")) <= 10


def check_io(assignments: dict[str, str]) -> None:
    for iorq_n in (False, True):
        for port in range(256):
            env = {"IORQn": iorq_n, "RESETn": True, "M1n": True,
                   "PICINT": False,
                   **{f"A{bit}": bool(port & (1 << bit)) for bit in range(2, 8)}}
            for name, window in (("PICCSn", 0x00), ("PPICSn", 0x04),
                                 ("UARTCSn", 0x08)):
                selected = not iorq_n and (port & 0xFC) == window
                assert physical(assignments, name, env) == (not selected), (
                    name, iorq_n, hex(port))
    env = {"IORQn": True, "RESETn": True, "M1n": True, "PICINT": False,
           **{f"A{bit}": False for bit in range(2, 8)}}
    for reset_n in (False, True):
        assert physical(assignments, "IORESET", env | {"RESETn": reset_n}) == (not reset_n)
    for iorq_n in (False, True):
        for m1_n in (False, True):
            got = physical(assignments, "INTAn", env | {"IORQn": iorq_n, "M1n": m1_n})
            assert got == (iorq_n or m1_n)
    assert eval_sop(assignments["INTn.T"], env) is False
    for pic_int in (False, True):
        assert eval_sop(assignments["INTn.E"], env | {"PICINT": pic_int}) == pic_int


def check_manifest() -> None:
    manifest = json.loads((HERE / "manifest.json").read_text())
    assert manifest["compiler"] == "Galette 0.3.0"
    assert manifest["compiler_revision"] == "af529870729b1da8794b002cd522f5bf2d53f230"
    for name, record in manifest["artifacts"].items():
        data = (HERE / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == record["sha256"], name
        assert len(data) == record["bytes"], name
        if name.endswith(".jed"):
            text = data.decode("ascii")
            assert int(re.search(r"\*QF(\d+)", text).group(1)) == record["qf"]
            assert re.search(r"\*C([0-9A-Fa-f]+)", text).group(1).upper() == record["jedec_checksum"]


def main() -> int:
    for base in ("memory-u3", "io-u2"):
        device, pins, assignments = source(base)
        check_pins(base, device, pins)
        (check_memory if base == "memory-u3" else check_io)(assignments)
    check_manifest()
    print("REVB-GAL-CHECK: PASS full memory overlay, I/O decode/reset/open-drain INT, pins and artifacts")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, KeyError, ValueError) as error:
        print(f"REVB-GAL-CHECK: FAIL {error}", file=sys.stderr)
        sys.exit(1)
