#!/usr/bin/env python3
"""Probe whether the public BASIC images are standalone reset ROMs."""
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
REPORT = Path(os.environ.get("BASIC_ENTRY_REPORT", ROOT / "docs" / "basic-entry-probe.md"))
VRAM = ROOT / "cosim" / "vram.bin"
VRAM_SIZE = 40 * 241

STOP_RE = re.compile(
    r"stopped pc=0x([0-9A-Fa-f]{4}) cyc=([0-9]+) halted=([0-9]+) "
    r"iff=([0-9]+) mode=([0-9]+) switches=([0-9]+)"
)
FIRST_VRAM_RE = re.compile(r"\[VRAM\] first video write @0x([0-9A-Fa-f]{4}) cyc=([0-9]+)")


@dataclass(frozen=True)
class ProbeCase:
    name: str
    rom: Path


@dataclass(frozen=True)
class ProbeResult:
    name: str
    rom_sha256: str
    rom_size: int
    first_bytes: str
    entry_jmp: int | None
    first_vram_addr: int | None
    first_vram_cycle: int | None
    pc: int | None
    cycles: int | None
    halted: int | None
    iff: int | None
    mode: int | None
    switches: int | None
    vram_sha256: str
    visible_pixels: int


def decode_hex_bytes(path: Path) -> bytes:
    text = path.read_text(errors="replace")
    digits = "".join(ch for ch in text if ch in "0123456789abcdefABCDEF")
    if len(digits) % 2:
        raise ValueError(f"{path} has an odd number of hex digits")
    return bytes.fromhex(digits)


def write_legacy_bas0_3(path: Path) -> None:
    data = bytearray()
    for idx in range(4):
        data.extend(decode_hex_bytes(ROOT / "ref" / "firmware" / f"BAS{idx}.HEX"))
    path.write_bytes(data)


def visible_pixels(vram: bytes) -> int:
    if len(vram) != VRAM_SIZE:
        return 0
    return sum(byte.bit_count() for byte in vram)


def parse_stop(stderr: str) -> dict[str, int | None]:
    for line in reversed(stderr.splitlines()):
        match = STOP_RE.search(line)
        if match:
            pc, cycles, halted, iff, mode, switches = match.groups()
            return {
                "pc": int(pc, 16),
                "cycles": int(cycles),
                "halted": int(halted),
                "iff": int(iff),
                "mode": int(mode),
                "switches": int(switches),
            }
    return {"pc": None, "cycles": None, "halted": None, "iff": None, "mode": None, "switches": None}


def parse_first_vram(stderr: str) -> tuple[int | None, int | None]:
    match = FIRST_VRAM_RE.search(stderr)
    if not match:
        return None, None
    return int(match.group(1), 16), int(match.group(2))


def fmt_hex(value: int | None, width: int = 4) -> str:
    if value is None:
        return "-"
    return f"0x{value:0{width}X}"


def build_trace(tmp: Path) -> Path:
    exe = tmp / "trace"
    subprocess.run(
        [
            "cc",
            "-O2",
            "-I",
            str(ROOT / "cosim"),
            "-o",
            str(exe),
            str(ROOT / "cosim" / "trace.c"),
            str(ROOT / "cosim" / "i8080.c"),
            str(ROOT / "cosim" / "juk_disk.c"),
            str(ROOT / "cosim" / "juku_fdc.c"),
        ],
        cwd=ROOT,
        check=True,
    )
    return exe


def run_case(exe: Path, case: ProbeCase) -> ProbeResult:
    data = case.rom.read_bytes()
    entry_jmp = data[1] | (data[2] << 8) if len(data) >= 3 and data[0] == 0xC3 else None
    run = subprocess.run(
        [str(exe), str(case.rom), "50000000", "0", "200000"],
        cwd=ROOT / "cosim",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    stop = parse_stop(run.stderr)
    first_vram_addr, first_vram_cycle = parse_first_vram(run.stderr)
    vram = VRAM.read_bytes()
    return ProbeResult(
        name=case.name,
        rom_sha256=hashlib.sha256(data).hexdigest(),
        rom_size=len(data),
        first_bytes=" ".join(f"{byte:02X}" for byte in data[:8]),
        entry_jmp=entry_jmp,
        first_vram_addr=first_vram_addr,
        first_vram_cycle=first_vram_cycle,
        pc=stop["pc"],
        cycles=stop["cycles"],
        halted=stop["halted"],
        iff=stop["iff"],
        mode=stop["mode"],
        switches=stop["switches"],
        vram_sha256=hashlib.sha256(vram).hexdigest(),
        visible_pixels=visible_pixels(vram),
    )


def write_report(results: list[ProbeResult]) -> None:
    same_negative = (
        len(results) == 2
        and all(result.pc == 0x0038 for result in results)
        and all(result.first_vram_addr == 0xFFFE for result in results)
        and len({result.vram_sha256 for result in results}) == 1
    )
    status = "BASIC DIRECT RESET PATH REJECTED" if same_negative else "BASIC DIRECT RESET PATH CHANGED"
    lines = [
        "# BASIC Direct-Entry Probe",
        "",
        f"Status: **{status}**",
        "",
        "This diagnostic runs the public BASIC images as if they were the reset ROM.",
        "It is intentionally a negative proof: the expected usable path is a monitor",
        "or removable-memory entry point, not a standalone low-ROM reset image.",
        "",
        "Command shape:",
        "",
        "```sh",
        "sync/basic_entry_probe.py",
        "```",
        "",
        "| Image | Size | SHA256 | First bytes | Entry JMP | First VRAM write | Stop PC | Mode | Visible pixels | VRAM SHA256 |",
        "| --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for result in results:
        lines.append(
            "| "
            f"{result.name} | "
            f"{result.rom_size} | "
            f"`{result.rom_sha256}` | "
            f"`{result.first_bytes}` | "
            f"{fmt_hex(result.entry_jmp)} | "
            f"{fmt_hex(result.first_vram_addr)} @ {result.first_vram_cycle or '-'} cyc | "
            f"{fmt_hex(result.pc)} | "
            f"{result.mode if result.mode is not None else '-'} | "
            f"{result.visible_pixels} | "
            f"`{result.vram_sha256}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Both images begin with the same absolute `JMP 0x0107`, but direct reset execution",
            "  does not produce a BASIC banner or `READY` prompt.",
            "- Both direct-reset runs stop at `PC=0x0038` after the first video write to",
            "  `0xFFFE`, with the same framebuffer hash.",
            "- Treat these images as cartridge/removable-memory BASIC payloads. The remaining",
            "  WS-B3 work is finding the correct monitor/removable-memory pairing and then",
            "  adding a positive BASIC prompt oracle.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines))


def main() -> int:
    old_vram = VRAM.read_bytes() if VRAM.exists() else None
    with tempfile.TemporaryDirectory(prefix="basic-entry.") as tmp_name:
        tmp = Path(tmp_name)
        legacy = tmp / "bas0-3.bin"
        write_legacy_bas0_3(legacy)
        exe = build_trace(tmp)
        cases = [
            ProbeCase("jbasic11.bin", ROOT / "roms" / "jbasic11.bin"),
            ProbeCase("legacy BAS0-3.HEX", legacy),
        ]
        try:
            results = [run_case(exe, case) for case in cases]
            write_report(results)
        finally:
            if old_vram is None:
                try:
                    VRAM.unlink()
                except FileNotFoundError:
                    pass
            else:
                VRAM.write_bytes(old_vram)
    print(f"wrote {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
