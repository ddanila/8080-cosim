#!/usr/bin/env python3
"""Compare the C and Verilog FDCs over generated public-bus scenarios."""

from __future__ import annotations

import random
import subprocess
import sys
import tempfile
from pathlib import Path


TRACKS = 80
HEADS = 2
SECTORS = 10
SECTOR_SIZE = 512


def write_disk(path: Path) -> None:
    with path.open("wb") as handle:
        for track in range(TRACKS):
            for head in range(HEADS):
                for sector in range(1, SECTORS + 1):
                    data = bytearray(SECTOR_SIZE)
                    data[0:3] = bytes((track, head, sector))
                    for index in range(3, SECTOR_SIZE):
                        data[index] = (track + (head << 5) + sector + index) & 0xFF
                    handle.write(data)


def vectors_for(seed: int) -> list[tuple[str, int, int]]:
    rng = random.Random(seed)
    two_mhz = bool(seed & 1)
    portc = 0x04 | (0x08 if two_mhz else 0x00)
    rate = rng.randrange(4)
    destination = rng.randrange(1, 5)
    rate_ticks = (6000, 12000, 20000, 30000)[rate]
    if not two_mhz:
        rate_ticks *= 2
    sector = rng.randrange(1, 11)
    ops: list[tuple[str, int, int]] = [
        ("P", portc, 0), ("H", 1, 0), ("T", 0, 0), ("Y", 1, 0),
        ("R", 0, 0),
        # Timed SEEK: the first step is issued at command load and the selected
        # interval follows every step, including the last.
        ("W", 3, destination), ("W", 0, 0x10 | rate),
        ("K", destination * rate_ticks, 0),
        ("R", 1, 0), ("R", 0, 0),
        # Read a generated sector and service a randomized prefix before a
        # silent force interrupt. Both models use the same disk bytes.
        ("W", 2, sector), ("W", 0, 0x80),
    ]
    ops.extend(("R", 3, 0) for _ in range(rng.randrange(1, 12)))
    ops.extend((("W", 0, 0xD0), ("R", 0, 0)))
    # Missing sector ID consumes four rising index edges before RNF.
    ops.extend((("W", 2, 0), ("W", 0, 0x80)))
    for _ in range(4):
        ops.extend((("I", 1, 0), ("I", 0, 0)))
    ops.append(("R", 0, 0))
    # Exercise every Force Interrupt source and acknowledgement behavior.
    ops.extend(
        (
            ("W", 0, 0xD1), ("Y", 0, 0), ("Y", 1, 0), ("R", 0, 0),
            ("W", 0, 0xD2), ("Y", 0, 0), ("R", 0, 0), ("Y", 1, 0),
            ("W", 0, 0xD4), ("I", 1, 0), ("I", 0, 0), ("R", 0, 0),
            ("I", 1, 0), ("I", 0, 0), ("R", 0, 0),
            ("W", 0, 0xD8), ("R", 0, 0), ("R", 0, 0),
            ("W", 0, 0xD0), ("R", 0, 0),
        )
    )
    return ops


def transcript(output: str) -> list[str]:
    return [
        line.strip().lower()
        for line in output.splitlines()
        if line.startswith("STATE ") or line.startswith("READ ")
    ]


def parse_transcript(lines: list[str]) -> tuple[dict[int, tuple[int, ...]], dict[int, int]]:
    states: dict[int, tuple[int, ...]] = {}
    reads: dict[int, int] = {}
    for line in lines:
        fields = line.split()
        if fields[0] == "state":
            states[int(fields[1])] = tuple(
                int(value, 16) for value in fields[2:7]
            ) + tuple(int(value) for value in fields[7:])
        elif fields[0] == "read":
            reads[int(fields[1])] = int(fields[2], 16)
    return states, reads


def check_properties(
    seed: int,
    operations: list[tuple[str, int, int]],
    lines: list[str],
) -> list[str]:
    """Check expected public behavior independently of either implementation."""
    errors: list[str] = []
    states, reads = parse_transcript(lines)
    if len(states) != len(operations):
        return [f"expected {len(operations)} STATE lines, got {len(states)}"]

    destination = next(
        b for op, a, b in operations if op == "W" and a == 3
    )
    sector = next(
        b for index, (op, a, b) in enumerate(operations)
        if op == "W" and a == 2 and b != 0
        and operations[index + 1] == ("W", 0, 0x80)
    )
    data_offset = 0
    missing_search = False
    missing_rises = 0
    force_mode: int | None = None
    expected_force_intrq = 0
    ready = 1
    index_line = 0

    for index, (op, a, b) in enumerate(operations):
        status, track, physical, _sector, _data, drq, intrq, _hld, _direction = states[index]
        if op == "K":
            if track != destination or physical != destination or status & 1 or not intrq:
                errors.append(
                    f"seed {seed} SEEK completion state={states[index]} destination={destination}"
                )
        if op == "R" and a == 3:
            if index not in reads:
                errors.append(f"seed {seed} data read {index} has no READ record")
            else:
                if data_offset == 0:
                    expected = destination
                elif data_offset == 1:
                    expected = 0
                elif data_offset == 2:
                    expected = sector
                else:
                    expected = (destination + sector + data_offset) & 0xFF
                if reads[index] != expected:
                    errors.append(
                        f"seed {seed} sector byte {data_offset}: {reads[index]:02x} != {expected:02x}"
                    )
                data_offset += 1

        if op == "W" and a == 2:
            missing_search = b == 0
            missing_rises = 0
        elif missing_search and op == "I" and a and not index_line:
            missing_rises += 1
            if missing_rises < 4 and (not status & 1 or drq or intrq):
                errors.append(
                    f"seed {seed} missing-ID rise {missing_rises} completed early: {states[index]}"
                )
            if missing_rises == 4 and (status & 1 or drq or not intrq or not status & 0x10):
                errors.append(
                    f"seed {seed} missing-ID fourth rise lacks RNF completion: {states[index]}"
                )
                missing_search = False

        if op == "W" and a == 0 and b in (0xD0, 0xD1, 0xD2, 0xD4, 0xD8):
            force_mode = None if b == 0xD0 else b
            expected_force_intrq = int(b == 0xD8)
            if b == 0xD0 and (status & 1 or drq or intrq):
                errors.append(
                    f"seed {seed} D0 did not silently clear BUSY/DRQ/INTRQ: {states[index]}"
                )
        elif force_mode is not None:
            if op == "Y":
                if force_mode == 0xD1 and not ready and a:
                    expected_force_intrq = 1
                if force_mode == 0xD2 and ready and not a:
                    expected_force_intrq = 1
                ready = a
            elif op == "I":
                if force_mode == 0xD4 and not index_line and a:
                    expected_force_intrq = 1
                index_line = a
            elif op == "R" and a == 0:
                expected_force_intrq = int(force_mode == 0xD8)
            if intrq != expected_force_intrq:
                errors.append(
                    f"seed {seed} Force {force_mode:02x} event {index}: INTRQ={intrq} expected {expected_force_intrq}"
                )

        if op == "Y":
            ready = a
        if op == "I":
            index_line = a
    return errors


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} C_RUNNER HDL_VVP", file=sys.stderr)
        return 2
    c_runner = Path(sys.argv[1]).resolve()
    hdl_vvp = Path(sys.argv[2]).resolve()
    failures: list[str] = []
    compared = 0
    with tempfile.TemporaryDirectory(prefix="juku-fdc-cross-") as tmp_name:
        tmp = Path(tmp_name)
        disk = tmp / "disk.juk"
        write_disk(disk)
        for seed in range(12):
            vector_path = tmp / f"seed-{seed}.vec"
            operations = vectors_for(seed)
            vector_path.write_text(
                "".join(f"{op} {a:x} {b:x}\n" for op, a, b in operations),
                encoding="ascii",
            )
            c_proc = run([str(c_runner), str(vector_path), str(disk)])
            hdl_proc = run(
                ["vvp", str(hdl_vvp), f"+vectors={vector_path}",
                 f"+disk={disk}", "+disk_heads=2"]
            )
            if c_proc.returncode or hdl_proc.returncode:
                failures.append(
                    f"seed {seed}: runner exit C={c_proc.returncode} HDL={hdl_proc.returncode}\n"
                    f"C stderr: {c_proc.stderr}\nHDL stderr: {hdl_proc.stderr}"
                )
                continue
            c_lines = transcript(c_proc.stdout)
            hdl_lines = transcript(hdl_proc.stdout)
            if c_lines != hdl_lines:
                mismatch = next(
                    (index for index, pair in enumerate(zip(c_lines, hdl_lines))
                     if pair[0] != pair[1]),
                    min(len(c_lines), len(hdl_lines)),
                )
                failures.append(
                    f"seed {seed}: transcript mismatch at line {mismatch}\n"
                    f"C:   {c_lines[mismatch] if mismatch < len(c_lines) else '<end>'}\n"
                    f"HDL: {hdl_lines[mismatch] if mismatch < len(hdl_lines) else '<end>'}"
                )
                continue
            property_errors = check_properties(seed, operations, c_lines)
            if property_errors:
                failures.extend(property_errors)
                continue
            compared += len(operations)
    if failures:
        print("FDC-CROSS-MODEL: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        f"FDC-CROSS-MODEL: PASS (12 deterministic seeds, {compared} state "
        "transitions, independent completion/data/error/interrupt properties)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
