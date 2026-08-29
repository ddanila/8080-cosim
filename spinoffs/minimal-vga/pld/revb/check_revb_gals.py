#!/usr/bin/env python3
"""Pin, oracle, artifact, and JEDEC guard for all five rev-B GALs."""
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
        "GND": "GND", "GND0": "GND", "GND1": "GND", "VCC": "VCC5",
    },
    "io-u2": {
        "IORQn": "IORQ_N", "RESETn": "RESET_N", "M1n": "M1_N",
        "PICINT": "PIC_INT", "PICCSn": "PIC_CS_N", "PPICSn": "PPI_CS_N",
        "UARTCSn": "UART_CS_N", "PITCSn": "PIT_CS_N", "POSTCLK": "POST_CLK",
        "WRn": "WR_N", "IORESET": "IO_RESET", "INTn": "INT_N",
        "INTAn": "INTA_N", "GND": "GND", "GND0": "GND", "VCC": "VCC5",
    },
    "video-hdec-u5": {
        "RESETn": "RESET_N", "HEND": "H_END", "/HSYNCn": "HSYNC_N",
        "HACTIVE": "H_ACTIVE", "BYTETICK": "BYTE_TICK",
        "/FILOADn": "FI_LOAD_N", "/SRLOADn": "SR_LOAD_N",
        "SRINH": "SR_INH", "RBSTROBE": "RB_STROBE",
        "GND": "GND", "VCC": "VCC5",
    },
    "video-vdec-u6": {
        "RBSTROBE": "RB_STROBE", "RESETn": "RESET_N", "VEND": "V_END", "/VSYNCn": "VSYNC_N",
        "FDIV2": "FRAME_DIV2_NC", "FDIV1": "FRAME_DIV1_NC", "FDIV0": "FRAME_DIV0_NC",
        "/FRAMETOPn": "FRAME_TOP_N", "FRAMETICK": "FRAME_TICK",
        "RBCLK": "RB_CLK", "VACTIVE": "V_ACTIVE", "GND": "GND", "VCC": "VCC5",
    },
    "video-ctrl-u7": {
        "MREQn": "MREQ_N", "RDn": "RD_N", "WRn": "WR_N",
        "RESETn": "RESET_N", "WAITn": "WAIT_N", "MUXSEL": "MUX_SEL",
        "D245DIR": "D245_DIR", "/D245OE": "D245_OE", "/FBCEn": "FB_CE_N",
        "/FBWEn": "FB_WE_N", "/FBOEn": "FB_OE_N",
        "CPUACC": "VID_CTRL_CPUACC_NC", "GND": "GND", "VCC": "VCC5",
    },
}
BOARD_REF = {
    "memory-u3": ("mem", "U3"), "io-u2": ("io", "U2"),
    "video-hdec-u5": ("video", "U5"), "video-vdec-u6": ("video", "U6"),
    "video-ctrl-u7": ("video", "U7"),
}


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
        elif current:
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
    expected_device = {
        "memory-u3": "GAL22V10", "io-u2": "GAL22V10_IOSEL",
        "video-hdec-u5": "GAL22V10_HDEC", "video-vdec-u6": "GAL22V10_VDEC",
        "video-ctrl-u7": "GAL22V10_CTRL",
    }[base]
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
        assert device == "GAL22V10"
        assert pins[12] == "GND0", "unused ATF22V10 pin 13 input must not float"
        assert pins[21:23] == ["NC", "NC"], "unused ATF22V10 I/O pins must be NC"


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
        for m1_n in (False, True):
            for wr_n in (False, True):
                for port in range(256):
                    env = {"IORQn": iorq_n, "RESETn": True, "M1n": m1_n,
                           "WRn": wr_n, "PICINT": False,
                           **{f"A{bit}": bool(port & (1 << bit)) for bit in range(2, 8)}}
                    for name, window in (("PICCSn", 0x00), ("PPICSn", 0x04),
                                         ("UARTCSn", 0x08), ("PITCSn", 0x18)):
                        selected = not iorq_n and m1_n and (port & 0xFC) == window
                        assert physical(assignments, name, env) == (not selected), (
                            name, iorq_n, m1_n, hex(port))
                    post_low = not iorq_n and m1_n and not wr_n and (port & 0xFC) == 0x20
                    assert physical(assignments, "POSTCLK", env) == (not post_low), (
                        "POSTCLK", iorq_n, m1_n, wr_n, hex(port))
    env = {"IORQn": True, "RESETn": True, "M1n": True, "WRn": True, "PICINT": False,
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


def check_io_mutations(assignments: dict[str, str]) -> None:
    mutations = {
        "PIT address A2 polarity": ("/PITCSn", "/IORQn * M1n * /A7 * /A6 * /A5 * A4 * A3 * A2"),
        "POST clock fixed-low polarity": ("POSTCLK", "GND"),
        "PIC select missing M1 exclusion": ("/PICCSn", "/IORQn * /A7 * /A6 * /A5 * /A4 * /A3 * /A2"),
    }
    for label, (name, expression) in mutations.items():
        changed = dict(assignments)
        changed[name] = expression
        try:
            check_io(changed)
        except AssertionError:
            continue
        raise AssertionError(f"I/O equation mutation escaped: {label}")


def counter_env(prefix: str, value: int) -> dict[str, bool]:
    return {f"{prefix}{bit}": bool(value & (1 << bit)) for bit in range(10)}


def check_video_hdec(assignments: dict[str, str]) -> None:
    for reset_n in (False, True):
        for h in range(1024):
            env = {"RESETn": reset_n, **counter_env("HC", h)}
            assert physical(assignments, "HEND", env) == ((not reset_n) or h == 800), h
            assert physical(assignments, "HSYNCn", env) == (
                (not reset_n) or not (656 <= h <= 751)), h
            assert physical(assignments, "HACTIVE", env) == (reset_n and h < 640), h
            assert physical(assignments, "FETCH", env) == (
                reset_n and (h & 15) >= 12), h
            assert physical(assignments, "SRLOADn", env) == (
                not (reset_n and (h & 15) == 0)), h
            assert physical(assignments, "SRINH", env) == (reset_n and bool(h & 1)), h
            assert physical(assignments, "BYTETICK", env) == (
                reset_n and h < 640 and (h & 15) == 0), h
            assert physical(assignments, "FILOADn", env) == (
                not (reset_n and h == 784)), h
            assert physical(assignments, "RBSTROBE", env) == (
                reset_n and h == 640), h


def check_video_vdec(assignments: dict[str, str]) -> None:
    state_names = ("FDIV0", "FDIV1", "FDIV2")
    for reset_n in (False, True):
        for v in range(1024):
            base = {"RESETn": reset_n, "RBSTROBE": True, **counter_env("VC", v)}
            assert physical(assignments, "VEND", base) == ((not reset_n) or v == 525), v
            assert physical(assignments, "VSYNCn", base) == (
                (not reset_n) or not (490 <= v <= 491)), v
            assert physical(assignments, "VACTIVE", base) == (reset_n and v < 480), v
            assert physical(assignments, "FRAMETOPn", base) == (
                reset_n and v != 0), v
            assert physical(assignments, "RBCLK", base) == (
                reset_n and bool(v & 1)), v
            for state in range(8):
                env = base | {name: bool(state & (1 << bit))
                              for bit, name in enumerate(state_names)}
                got = sum(eval_sop(assignments[f"{name}.R"], env) << bit
                          for bit, name in enumerate(state_names))
                if not reset_n:
                    want = 0
                elif v != 524:
                    want = state
                elif state < 5:
                    want = state + 1
                elif state == 5:
                    want = 0
                else:
                    want = 0
                assert got == want, (reset_n, v, state, got, want)
                tick = physical(assignments, "FRAMETICK", env)
                assert tick == (reset_n and v == 524 and state == 5), (
                    reset_n, v, state, tick)


def check_video_ctrl(assignments: dict[str, str]) -> None:
    assert assignments["WAITn.T"] == "GND"
    for reset_n in (False, True):
        for mode in range(4):
            # The GAL sees A11..A15, so all 32 distinguishable address classes
            # exhaust the hardware decoder (the lower 11 bits are irrelevant).
            for address_class in range(32):
                address = address_class << 11
                window = mode in (0, 3) and address >= 0xD800
                address_env = {
                    "RESETn": reset_n, "MODE0": bool(mode & 1),
                    "MODE1": bool(mode & 2),
                    **{f"A{bit}": bool(address & (1 << bit)) for bit in range(11, 16)},
                }
                for mreq_n, rd_n, wr_n in (
                        (True, True, True), (False, True, True),
                        (False, False, True), (False, True, False)):
                    for fetch in (False, True):
                        env = address_env | {"MREQn": mreq_n, "RDn": rd_n,
                                             "WRn": wr_n, "FETCH": fetch}
                        cpu = reset_n and window and not mreq_n and (not rd_n or not wr_n)
                        assert physical(assignments, "CPUACC", env) == cpu
                        assert physical(assignments, "MUXSEL", env) == (
                            (not fetch) or (not reset_n))
                        assert eval_sop(assignments["WAITn.E"], env | {"CPUACC": cpu}) == (
                            cpu and fetch)
                        assert physical(assignments, "D245DIR", env) == rd_n
                        assert physical(assignments, "D245OE", env | {"CPUACC": cpu}) == (
                            not (cpu and not fetch))
                        assert physical(assignments, "FBCEn", env | {"CPUACC": cpu}) == (
                            not ((reset_n and fetch) or (cpu and not fetch)))
                        assert physical(assignments, "FBOEn", env | {"CPUACC": cpu}) == (
                            not ((reset_n and fetch) or (cpu and not fetch and not rd_n)))
                        assert physical(assignments, "FBWEn", env | {"CPUACC": cpu}) == (
                            not (cpu and not fetch and not wr_n))


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
    checks = {
        "memory-u3": check_memory, "io-u2": check_io,
        "video-hdec-u5": check_video_hdec, "video-vdec-u6": check_video_vdec,
        "video-ctrl-u7": check_video_ctrl,
    }
    for base, check in checks.items():
        device, pins, assignments = source(base)
        check_pins(base, device, pins)
        check(assignments)
        if base == "io-u2":
            check_io_mutations(assignments)
    check_manifest()
    print("REVB-GAL-CHECK: PASS memory/I-O decode plus I/O address/M1/POST-polarity mutations, exact Video timing, /6 tick, arbitration, pins and artifacts")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (AssertionError, KeyError, ValueError) as error:
        print(f"REVB-GAL-CHECK: FAIL {error}", file=sys.stderr)
        sys.exit(1)
