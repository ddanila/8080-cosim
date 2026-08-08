#!/usr/bin/env python3
"""Compare the C and Verilog FDCs over generated public-bus scenarios."""

from __future__ import annotations

import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


TRACKS = 80
HEADS = 2
SECTORS = 10
SECTOR_SIZE = 512
TRACK_SIZE = 6250
DELETED_MARK_BYTES = TRACKS * HEADS * SECTORS

Operation = tuple[str, int, int]
Metadata = dict[str, Any]


def sector_bytes(track: int, head: int, sector: int) -> bytes:
    data = bytearray(SECTOR_SIZE)
    data[0:3] = bytes((track, head, sector))
    for index in range(3, SECTOR_SIZE):
        data[index] = (track + (head << 5) + sector + index) & 0xFF
    return bytes(data)


def write_disk(path: Path) -> None:
    with path.open("wb") as handle:
        for track in range(TRACKS):
            for head in range(HEADS):
                for sector in range(1, SECTORS + 1):
                    handle.write(sector_bytes(track, head, sector))


def crc_byte(crc: int, data: int) -> int:
    crc ^= data << 8
    for _ in range(8):
        crc = ((crc << 1) ^ (0x1021 if crc & 0x8000 else 0)) & 0xFFFF
    return crc


def crc_bytes(values: list[int]) -> tuple[int, int]:
    crc = 0xFFFF
    for value in values:
        crc = crc_byte(crc, value)
    return crc >> 8, crc & 0xFF


def expected_track(
    track: int, head: int, payloads: dict[int, bytes], deleted: set[int]
) -> list[int]:
    output: list[int] = [0x4E] * 32
    for sector in range(1, SECTORS + 1):
        output.extend([0x00] * 12)
        id_field = [0xA1, 0xA1, 0xA1, 0xFE, track, head, sector, 2]
        output.extend(id_field)
        output.extend(crc_bytes(id_field))
        output.extend([0x4E] * 22)
        output.extend([0x00] * 12)
        mark = 0xF8 if sector in deleted else 0xFB
        data_field = [0xA1, 0xA1, 0xA1, mark, *payloads[sector]]
        output.extend(data_field)
        output.extend(crc_bytes(data_field))
        output.extend([0x4E] * 35)
    output.extend([0x4E] * (TRACK_SIZE - len(output)))
    assert len(output) == TRACK_SIZE
    return output


def format_stream(track: int, head: int, deleted_sector: int) -> list[int]:
    stream: list[int] = []
    output_length = 0

    def add(value: int) -> None:
        nonlocal output_length
        stream.append(value)
        output_length += 2 if value == 0xF7 else 1

    for _ in range(32):
        add(0x4E)
    for sector in range(1, SECTORS + 1):
        for _ in range(12):
            add(0x00)
        for _ in range(3):
            add(0xF5)
        for value in (0xFE, track, head, sector, 2, 0xF7):
            add(value)
        for _ in range(22):
            add(0x4E)
        for _ in range(12):
            add(0x00)
        for _ in range(3):
            add(0xF5)
        add(0xF8 if sector == deleted_sector else 0xFB)
        for _ in range(SECTOR_SIZE):
            add(0x30 + sector)
        add(0xF7)
        for _ in range(35):
            add(0x4E)
    while output_length < TRACK_SIZE:
        add(0x4E)
    assert output_length == TRACK_SIZE and len(stream) == 6230
    return stream


def vectors_for(seed: int) -> tuple[list[Operation], Metadata]:
    rng = random.Random(seed)
    two_mhz = bool(seed & 1)
    portc = 0x04 | (0x08 if two_mhz else 0x00)
    rate = rng.randrange(4)
    destination = rng.randrange(1, 5)
    rate_ticks = (6000, 12000, 20000, 30000)[rate]
    if not two_mhz:
        rate_ticks *= 2
    sector = rng.randrange(1, 11)
    ops: list[Operation] = []
    meta: Metadata = {"destination": destination}

    def add(op: str, a: int = 0, b: int = 0) -> int:
        ops.append((op, a, b))
        return len(ops) - 1

    def read_bytes(count: int) -> list[int]:
        return [add("R", 3) for _ in range(count)]

    add("P", portc)
    add("H", 1)
    add("T", 0)
    add("Y", 1)
    add("R", 0)

    # Timed SEEK: command load issues the first step and the selected interval
    # follows every step, including the last.
    add("W", 3, destination)
    add("W", 0, 0x10 | rate)
    meta["seek_done"] = add("K", destination * rate_ticks)
    add("R", 1)
    add("R", 0)

    # A randomized serviced prefix followed by a silent abort.
    add("W", 2, sector)
    add("W", 0, 0x80)
    prefix = rng.randrange(1, 12)
    meta["initial_read"] = (read_bytes(prefix), sector)
    add("W", 0, 0xD0)
    add("R", 0)

    # The unserviced read byte is valid through tick 63 and overwritten on 64.
    add("W", 2, 2)
    add("W", 0, 0x80)
    meta["read_deadline_63"] = add("K", 63)
    meta["read_deadline_64"] = add("K", 1)
    add("W", 0, 0xD0)

    # Write Sector's first-byte preload is accepted through tick 1407 and
    # fails without touching media at the exact 1408 boundary.
    add("W", 2, 3)
    add("W", 0, 0xA1)
    meta["write_deadline_1407"] = add("K", 1407)
    meta["write_deadline_1408"] = add("K", 1)

    # Successful deleted-sector write: preload, cross both halves of the exact
    # boundary, stream the remaining bytes, then read it back.
    deleted_payload = bytes((0xD0 ^ seed ^ index) & 0xFF for index in range(SECTOR_SIZE))
    add("W", 2, 4)
    add("W", 0, 0xA1)
    add("W", 3, deleted_payload[0])
    meta["write_preload_1407"] = add("K", 1407)
    meta["write_preload_1408"] = add("K", 1)
    for value in deleted_payload[1:]:
        add("W", 3, value)
    meta["deleted_write_done"] = len(ops) - 1
    add("W", 2, 4)
    add("W", 0, 0x80)
    meta["deleted_readback"] = (read_bytes(SECTOR_SIZE), deleted_payload)

    # Multiple deleted writes must re-arm the preload interval, advance across
    # sectors 9/10, and finish with sector 11 + RNF.
    multi_payloads: dict[int, bytes] = {}
    add("W", 2, 9)
    add("W", 0, 0xB1)
    for record in (9, 10):
        payload = bytes(((0x90 if record == 9 else 0x50) ^ seed ^ index) & 0xFF
                        for index in range(SECTOR_SIZE))
        multi_payloads[record] = payload
        add("W", 3, payload[0])
        add("K", 1408)
        for value in payload[1:]:
            add("W", 3, value)
    meta["multi_done"] = len(ops) - 1
    multi_reads: list[tuple[list[int], bytes]] = []
    for record in (9, 10):
        add("W", 2, record)
        add("W", 0, 0x80)
        multi_reads.append((read_bytes(SECTOR_SIZE), multi_payloads[record]))
    meta["multi_readbacks"] = multi_reads

    # Read Address returns the deterministic first ID field and its real CRC.
    add("W", 2, 7)
    add("W", 0, 0xC0)
    meta["read_address"] = read_bytes(6)

    # One seed carries the long Type-III streams. Read Track is checked against
    # independently reconstructed bytes after the sector writes above.
    if seed == 0:
        payloads = {number: sector_bytes(destination, 0, number)
                    for number in range(1, SECTORS + 1)}
        payloads[4] = deleted_payload
        payloads.update(multi_payloads)
        add("W", 2, 7)
        add("W", 0, 0xE0)
        meta["read_track_before_index"] = len(ops) - 1
        add("I", 1)
        add("I", 0)
        meta["read_track"] = (
            read_bytes(TRACK_SIZE), expected_track(destination, 0, payloads, {4, 9, 10})
        )

        # A complete canonical 6,230-write formatter, including F5/F7 tokens
        # and a deleted sector, followed by sector-level proof of persistence.
        stream = format_stream(destination, 0, 4)
        add("W", 0, 0xF0)
        add("W", 3, stream[0])
        meta["write_track_preindex"] = len(ops) - 1
        add("I", 1)
        add("I", 0)
        for value in stream[1:]:
            add("W", 3, value)
        meta["write_track_done"] = len(ops) - 1
        add("W", 2, 4)
        add("W", 0, 0x80)
        meta["format_readback"] = (read_bytes(SECTOR_SIZE), bytes([0x34]) * SECTOR_SIZE)

    # Missing sector ID consumes four rising index edges before RNF.
    add("W", 2, 0)
    add("W", 0, 0x80)
    meta["missing_rises"] = []
    for _ in range(4):
        meta["missing_rises"].append(add("I", 1))
        add("I", 0)
    add("R", 0)

    # Exercise every Force Interrupt source and acknowledgement behavior.
    for op, a, b in (
        ("W", 0, 0xD1), ("Y", 0, 0), ("Y", 1, 0), ("R", 0, 0),
        ("W", 0, 0xD2), ("Y", 0, 0), ("R", 0, 0), ("Y", 1, 0),
        ("W", 0, 0xD4), ("I", 1, 0), ("I", 0, 0), ("R", 0, 0),
        ("I", 1, 0), ("I", 0, 0), ("R", 0, 0),
        ("W", 0, 0xD8), ("R", 0, 0), ("R", 0, 0),
        ("W", 0, 0xD0), ("R", 0, 0),
    ):
        add(op, a, b)
    return ops, meta


def transcript(output: str) -> list[str]:
    return [line.strip().lower() for line in output.splitlines()
            if line.startswith("STATE ") or line.startswith("READ ")]


def parse_transcript(lines: list[str]) -> tuple[dict[int, tuple[int, ...]], dict[int, int]]:
    states: dict[int, tuple[int, ...]] = {}
    reads: dict[int, int] = {}
    for line in lines:
        fields = line.split()
        if fields[0] == "state":
            states[int(fields[1])] = tuple(int(value, 16) for value in fields[2:7]) + tuple(
                int(value) for value in fields[7:])
        elif fields[0] == "read":
            reads[int(fields[1])] = int(fields[2], 16)
    return states, reads


def check_properties(seed: int, operations: list[Operation], lines: list[str], meta: Metadata) -> list[str]:
    """Check expected public behavior independently of either implementation."""
    errors: list[str] = []
    states, reads = parse_transcript(lines)
    if len(states) != len(operations):
        return [f"expected {len(operations)} STATE lines, got {len(states)}"]

    def state(index: int) -> tuple[int, ...]:
        return states[index]

    def expect_bytes(label: str, indices: list[int], expected: bytes | list[int]) -> None:
        got = [reads.get(index, -1) for index in indices]
        if got != list(expected):
            mismatch = next((i for i, pair in enumerate(zip(got, expected)) if pair[0] != pair[1]),
                            min(len(got), len(expected)))
            got_value = got[mismatch] if mismatch < len(got) else -1
            want_value = expected[mismatch] if mismatch < len(expected) else -1
            errors.append(f"seed {seed} {label} byte {mismatch}: {got_value:02x} != {want_value:02x}")

    destination = meta["destination"]
    seek = state(meta["seek_done"])
    if seek[1] != destination or seek[2] != destination or seek[0] & 1 or not seek[6]:
        errors.append(f"seed {seed} SEEK completion state={seek} destination={destination}")

    initial_indices, initial_sector = meta["initial_read"]
    expect_bytes("initial read", initial_indices,
                 sector_bytes(destination, 0, initial_sector)[:len(initial_indices)])

    before = state(meta["read_deadline_63"])
    after = state(meta["read_deadline_64"])
    if before[0] & 0x04 or not before[0] & 1 or not before[5] or before[6]:
        errors.append(f"seed {seed} read tick 63 boundary state={before}")
    if not after[0] & 0x04 or not after[0] & 1 or not after[5] or after[6]:
        errors.append(f"seed {seed} read tick 64 boundary state={after}")

    before = state(meta["write_deadline_1407"])
    after = state(meta["write_deadline_1408"])
    if before[0] & 0x04 or not before[0] & 1 or not before[5] or before[6]:
        errors.append(f"seed {seed} write preload tick 1407 state={before}")
    if not after[0] & 0x04 or after[0] & 1 or after[5] or not after[6]:
        errors.append(f"seed {seed} write preload tick 1408 state={after}")

    held = state(meta["write_preload_1407"])
    started = state(meta["write_preload_1408"])
    if held[0] & 0x04 or not held[0] & 1 or held[5] or held[6]:
        errors.append(f"seed {seed} serviced preload tick 1407 state={held}")
    if started[0] & 0x04 or not started[0] & 1 or not started[5] or started[6]:
        errors.append(f"seed {seed} serviced preload tick 1408 state={started}")
    done = state(meta["deleted_write_done"])
    if done[0] & 0x03 or not done[6]:
        errors.append(f"seed {seed} deleted write completion state={done}")

    indices, expected = meta["deleted_readback"]
    expect_bytes("deleted-sector readback", indices, expected)
    if not state(indices[-1])[0] & 0x20:
        errors.append(f"seed {seed} deleted-sector read lacks RECORD TYPE")

    multi = state(meta["multi_done"])
    if multi[0] & 1 or not multi[0] & 0x10 or multi[3] != 11 or not multi[6]:
        errors.append(f"seed {seed} multi-write end-of-track state={multi}")
    for number, (indices, expected) in enumerate(meta["multi_readbacks"], start=9):
        expect_bytes(f"multi sector {number}", indices, expected)
        if not state(indices[-1])[0] & 0x20:
            errors.append(f"seed {seed} multi sector {number} lacks RECORD TYPE")

    address = [destination, 0, 1, 2]
    address.extend(crc_bytes([0xFE, *address]))
    expect_bytes("Read Address", meta["read_address"], address)
    if state(meta["read_address"][-1])[3] != destination:
        errors.append(f"seed {seed} Read Address did not copy track to sector register")

    if "read_track" in meta:
        waiting = state(meta["read_track_before_index"])
        if not waiting[0] & 1 or waiting[5]:
            errors.append(f"seed {seed} Read Track exposed DRQ before index: {waiting}")
        indices, expected = meta["read_track"]
        expect_bytes("Read Track", indices, expected)
        final = state(indices[-1])
        if final[0] & 0x13 or final[5] or not final[6]:
            errors.append(f"seed {seed} Read Track completion state={final}")

        preindex = state(meta["write_track_preindex"])
        if not preindex[0] & 1 or preindex[5] or preindex[6]:
            errors.append(f"seed {seed} Write Track preload-before-index state={preindex}")
        final = state(meta["write_track_done"])
        if final[0] & 0x33 or final[5] or not final[6]:
            errors.append(f"seed {seed} Write Track completion state={final}")
        indices, expected = meta["format_readback"]
        expect_bytes("Write Track persisted sector 4", indices, expected)
        if not state(indices[-1])[0] & 0x20:
            errors.append(f"seed {seed} formatted deleted sector lacks RECORD TYPE")

    for rise_number, index in enumerate(meta["missing_rises"], start=1):
        current = state(index)
        if rise_number < 4 and (not current[0] & 1 or current[5] or current[6]):
            errors.append(f"seed {seed} missing-ID rise {rise_number} completed early: {current}")
        if rise_number == 4 and (current[0] & 1 or current[5] or not current[6]
                                 or not current[0] & 0x10):
            errors.append(f"seed {seed} missing-ID fourth rise lacks RNF completion: {current}")

    force_mode: int | None = None
    expected_intrq = 0
    ready = 1
    index_line = 0
    force_commands = (0xD0, 0xD1, 0xD2, 0xD4, 0xD8)
    force_start = max(meta["missing_rises"]) + 2
    for index in range(force_start, len(operations)):
        op, a, b = operations[index]
        status, _track, _physical, _sector, _data, drq, intrq, _hld, _direction = states[index]
        if op == "W" and a == 0 and b in force_commands:
            force_mode = None if b == 0xD0 else b
            expected_intrq = int(b == 0xD8)
            if b == 0xD0 and (status & 1 or drq or intrq):
                errors.append(f"seed {seed} D0 did not silently clear BUSY/DRQ/INTRQ: {states[index]}")
        elif force_mode is not None:
            if op == "Y":
                if force_mode == 0xD1 and not ready and a:
                    expected_intrq = 1
                if force_mode == 0xD2 and ready and not a:
                    expected_intrq = 1
                ready = a
            elif op == "I":
                if force_mode == 0xD4 and not index_line and a:
                    expected_intrq = 1
                index_line = a
            elif op == "R" and a == 0:
                expected_intrq = int(force_mode == 0xD8)
            if intrq != expected_intrq:
                errors.append(f"seed {seed} Force {force_mode:02x} event {index}: "
                              f"INTRQ={intrq} expected {expected_intrq}")
        if op == "Y":
            ready = a
        if op == "I":
            index_line = a
    return errors


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=False)


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
        pristine = tmp / "pristine.juk"
        write_disk(pristine)
        for seed in range(12):
            vector_path = tmp / f"seed-{seed}.vec"
            c_disk = tmp / f"seed-{seed}-c.juk"
            hdl_disk = tmp / f"seed-{seed}-hdl.juk"
            c_marks = tmp / f"seed-{seed}-c.deleted"
            hdl_marks = tmp / f"seed-{seed}-hdl.deleted"
            shutil.copyfile(pristine, c_disk)
            shutil.copyfile(pristine, hdl_disk)
            c_marks.write_bytes(bytes(DELETED_MARK_BYTES))
            hdl_marks.write_bytes(bytes(DELETED_MARK_BYTES))
            operations, meta = vectors_for(seed)
            vector_path.write_text("".join(f"{op} {a:x} {b:x}\n" for op, a, b in operations),
                                   encoding="ascii")
            c_proc = run([str(c_runner), str(vector_path), str(c_disk), str(c_marks)])
            hdl_proc = run([
                "vvp", str(hdl_vvp), f"+vectors={vector_path}", f"+disk={hdl_disk}",
                "+disk_heads=2", "+disk_writable", f"+disk_deleted_marks={hdl_marks}",
            ])
            if c_proc.returncode or hdl_proc.returncode:
                failures.append(f"seed {seed}: runner exit C={c_proc.returncode} "
                                f"HDL={hdl_proc.returncode}\nC stderr: {c_proc.stderr}\n"
                                f"HDL stderr: {hdl_proc.stderr}")
                continue
            c_lines = transcript(c_proc.stdout)
            hdl_lines = transcript(hdl_proc.stdout)
            if c_lines != hdl_lines:
                mismatch = next((index for index, pair in enumerate(zip(c_lines, hdl_lines))
                                 if pair[0] != pair[1]), min(len(c_lines), len(hdl_lines)))
                failures.append(f"seed {seed}: transcript mismatch at line {mismatch}\n"
                                f"C:   {c_lines[mismatch] if mismatch < len(c_lines) else '<end>'}\n"
                                f"HDL: {hdl_lines[mismatch] if mismatch < len(hdl_lines) else '<end>'}")
                continue
            property_errors = check_properties(seed, operations, c_lines, meta)
            if property_errors:
                failures.extend(property_errors)
                continue
            compared += len(operations)
    if failures:
        print("FDC-CROSS-MODEL: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"FDC-CROSS-MODEL: PASS (12 deterministic seeds, {compared} state transitions, "
          "independent seek/read/write/deleted/address/track/deadline/interrupt properties)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
