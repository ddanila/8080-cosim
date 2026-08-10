#!/usr/bin/env python3
"""Run the complete CS00024 host-driven diagnostic set in one loader session."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import host
import local_ram
import protocol

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIRMWARE = HERE / "firmware"
LOAD_ADDRESS = 0x4000
CPU_TIMEBASE_LONG_ADDRESS = 0x4006
DEFAULT_REFRESH_WRAPPER_ADDRESS = 0x6F00
DEFAULT_RAM_LANE_ADDRESS = 0x4D00
FULL_RAM_START = protocol.LOADER_V2_LOAD_MIN
FULL_RAM_END = protocol.LOADER_V2_LOAD_END
DRAM_LANE_PACKAGES = tuple(f"D{number}" for number in range(84, 92))


@dataclass(frozen=True)
class RomProfile:
    name: str
    version: int
    crc16: int
    boot_votes: int
    config_first: bool
    cpu_timebase_source: str
    cpu_timebase_delta_tstates: int
    d57_source: str
    refresh_api: int | None


ROM_PROFILES = {
    "t34": RomProfile(
        "t34",
        0x1C,
        0xA637,
        protocol.LOADER_V2_BOOT_VOTES,
        True,
        "cpu-host-timebase-4000.asm",
        1_200_000,
        "d57-raw-4000.asm",
        None,
    ),
    "t35": RomProfile(
        "t35",
        0x1D,
        0x45C4,
        protocol.LOADER_V2_T35_BOOT_VOTES,
        False,
        "cpu-host-timebase-refresh-4000.asm",
        1_078_000,
        "d57-raw-refresh-4000.asm",
        protocol.LOADER_V2_REFRESH_API,
    ),
    "t36": RomProfile(
        "t36",
        0x1E,
        0xC617,
        protocol.LOADER_V2_T36_BOOT_VOTES,
        False,
        "cpu-host-timebase-refresh-4000.asm",
        1_078_000,
        "d57-raw-refresh-4000.asm",
        protocol.LOADER_V2_REFRESH_API,
    ),
}


@dataclass(frozen=True)
class Probe:
    name: str
    source: str
    result_address: int
    expected: bytes


def parse_guard_list(value: str) -> tuple[float, ...]:
    try:
        guards = tuple(float(item.strip()) for item in value.split(",") if item.strip())
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "guards must be comma-separated numbers"
        ) from error
    if not guards or any(guard < 0 for guard in guards):
        raise argparse.ArgumentTypeError("at least one nonnegative guard is required")
    if len(guards) > 32:
        raise argparse.ArgumentTypeError("at most 32 retention guards are supported")
    return guards


def parse_hex_address(value: str) -> int:
    try:
        address = int(value, 16)
    except ValueError as error:
        raise argparse.ArgumentTypeError("address must be hexadecimal") from error
    if not 0 <= address <= 0xFFFF:
        raise argparse.ArgumentTypeError("address must be in 0000..FFFF")
    return address


def lhld_classes() -> bytes:
    result = bytearray(b"L12C\xa5\x04\0\0")
    for lower, upper in (
        ((0x10, 0x11), (0x20, 0x21)),
        ((0x30, 0x31), (0x40, 0x41)),
        ((0x50, 0x51), (0x60, 0x61)),
        ((0x70, 0x71), (0x80, 0x81)),
    ):
        result.extend((*lower, *upper))
        result.extend(lower * 4)
        result.extend(upper * 4)
    return bytes(result)


def write_map() -> bytes:
    result = bytearray(b"W12M\xa5\x04\0\0")
    result.extend((0, 0, 0, 0))
    result.extend((0x10, 0x11, 0, 0))
    result.extend((0x10, 0x11, 0x20, 0x21))
    result.extend((0x10, 0x11) * 4)
    result.extend((0x20, 0x21) * 4)
    result.extend((0, 0, 0, 0))
    result.extend((0, 0, 0x80, 0x81))
    result.extend((0x70, 0x71, 0x80, 0x81))
    result.extend((0x70, 0x71) * 4)
    result.extend((0x80, 0x81) * 4)
    return bytes(result)


def instruction_classes() -> bytes:
    result = bytearray(b"I12C\xa5\x55\x55\x55")
    result.extend((0x10, 0x11, 0x20, 0x21))
    result.extend((0x30, 0x31, 0x40, 0x41))
    result.extend((0x50, 0x51, 0x60, 0x61))
    result.extend((0x50, 0x51, 0xAA, 0xBB))
    result.extend(b"\x55" * 8)
    return bytes(result)


def ready_classes() -> bytes:
    result = bytearray(b"R12C\xa5\x04\x55\x55")
    for lower, upper in (
        ((0x10, 0x11), (0x20, 0x21)),
        ((0x30, 0x31), (0x40, 0x41)),
        ((0x50, 0x51), (0x60, 0x61)),
        ((0x70, 0x71), (0x80, 0x81)),
    ):
        result.extend((*lower, *upper))
        result.extend(upper * 4)
    return bytes(result)


def boundary() -> bytes:
    return b"B12C\xa5\x55\x55\x55\x1f\x20\x2f\x40\x55\x55\x55\x55"


def increment_registers() -> bytes:
    return bytes.fromhex("58313243A55555550010011A015A019A011A555555555555")


def ram_lane_analysis(expected: bytes, observed: bytes) -> dict[str, object]:
    if len(expected) != len(observed):
        raise ValueError("RAM lane comparison lengths differ")
    xor_or = 0
    stuck_low_or = 0
    stuck_high_or = 0
    lanes: list[dict[str, object]] = []
    for bit, package in enumerate(DRAM_LANE_PACKAGES):
        mask = 1 << bit
        low_count = sum(
            bool((want & mask) and not (got & mask))
            for want, got in zip(expected, observed)
        )
        high_count = sum(
            bool(not (want & mask) and (got & mask))
            for want, got in zip(expected, observed)
        )
        if low_count or high_count:
            lanes.append(
                {
                    "bit": bit,
                    "mask": f"0x{mask:02X}",
                    "package": package,
                    "one_to_zero": low_count,
                    "zero_to_one": high_count,
                    "mismatches": low_count + high_count,
                }
            )
    for want, got in zip(expected, observed):
        xor_or |= want ^ got
        stuck_low_or |= want & ~got & 0xFF
        stuck_high_or |= ~want & got & 0xFF
    return {
        "bytes": len(expected),
        "mismatching_bytes": sum(want != got for want, got in zip(expected, observed)),
        "xor_or": f"0x{xor_or:02X}",
        "one_to_zero_or": f"0x{stuck_low_or:02X}",
        "zero_to_one_or": f"0x{stuck_high_or:02X}",
        "single_lane_candidate": (
            DRAM_LANE_PACKAGES[xor_or.bit_length() - 1]
            if xor_or and xor_or & (xor_or - 1) == 0
            else None
        ),
        "lanes": lanes,
    }


def ram_lane_patterns() -> tuple[tuple[str, bytes], ...]:
    walking = bytes(
        (1 << (index % 8)) if index < 16 else (0xFF ^ (1 << (index % 8)))
        for index in range(32)
    )
    return (
        ("zeros", bytes(32)),
        ("ones", bytes((0xFF,)) * 32),
        ("alternating", bytes((0xAA, 0x55)) * 16),
        ("walking", walking),
    )


def full_ram_patterns(
    start: int = FULL_RAM_START,
    end: int = FULL_RAM_END,
) -> tuple[tuple[str, bytes], ...]:
    """Patterns spanning every host-safe byte, including address aliases."""
    addresses = range(start, end)
    return (
        ("zeros", bytes(end - start)),
        ("ones", bytes((0xFF,)) * (end - start)),
        (
            "checkerboard",
            bytes(0xAA if address & 1 else 0x55 for address in addresses),
        ),
        (
            "address",
            bytes(
                (address * 109 + (address >> 8) * 37 + 0x5A ^ (address >> 3)) & 0xFF
                for address in addresses
            ),
        ),
    )


def full_ram_failure_map(
    expected: bytes,
    observed: bytes,
    start: int = FULL_RAM_START,
) -> dict[str, object]:
    analysis = ram_lane_analysis(expected, observed)
    row_counts = [0] * 128
    first_mismatches: list[dict[str, str]] = []
    for offset, (want, got) in enumerate(zip(expected, observed)):
        if want == got:
            continue
        address = start + offset
        row_counts[address & 0x7F] += 1
        if len(first_mismatches) < 256:
            first_mismatches.append(
                {
                    "address": f"0x{address:04X}",
                    "expected": f"0x{want:02X}",
                    "observed": f"0x{got:02X}",
                    "xor": f"0x{want ^ got:02X}",
                }
            )
    analysis["failing_rows"] = [
        {"row": f"0x{row:02X}", "mismatching_bytes": count}
        for row, count in enumerate(row_counts)
        if count
    ]
    analysis["first_mismatches"] = first_mismatches
    return analysis


PROBES = (
    Probe("a12-write-map", "ram-a12-write-map-4000.asm", 0x4600, write_map()),
    Probe("a12-lhld", "ram-a12-lhld-classes-4000.asm", 0x4800, lhld_classes()),
    Probe(
        "a12-instruction",
        "ram-a12-instruction-classes-4000.asm",
        0x4C00,
        instruction_classes(),
    ),
    Probe(
        "a12-ready-classes",
        "ram-a12-ready-classes-4000.asm",
        0x4F00,
        ready_classes(),
    ),
    Probe("a12-boundary", "ram-a12-boundary-4000.asm", 0x4E00, boundary()),
    Probe(
        "cpu-increment-registers",
        "ram-a12-increment-registers-4000.asm",
        0x4D00,
        increment_registers(),
    ),
)


def build_payloads(directory: Path, profile: RomProfile) -> dict[str, Path]:
    sources = {probe.source for probe in PROBES}
    sources.update((profile.cpu_timebase_source, profile.d57_source))
    payloads: dict[str, Path] = {}
    for source in sorted(sources):
        output = directory / source.replace(".asm", ".bin")
        subprocess.run(
            ["nasm", "-f", "bin", "-o", str(output), str(FIRMWARE / source)],
            cwd=ROOT,
            check=True,
        )
        payloads[source] = output
    return payloads


def marker_program(marker: int) -> bytes:
    # MVI A,marker / STA 4100h / MVI A,marker / RET
    return bytes((0x3E, marker, 0x32, 0x00, 0x41, 0x3E, marker, 0xC9))


def result_bytes(operation: dict[str, object]) -> bytes:
    run = operation.get("run")
    if not isinstance(run, dict):
        raise host.SessionError("batch operation has no RUN evidence")
    result = run.get("result")
    if not isinstance(result, dict) or not isinstance(result.get("hex"), str):
        raise host.SessionError("batch operation has no returned result block")
    return bytes.fromhex(str(result["hex"]))


def refresh_wrapper(target: int, refresh_api: int) -> bytes:
    """CALL refresh, target, refresh while preserving target A/flags."""
    return bytes(
        (
            0xCD,
            refresh_api & 0xFF,
            refresh_api >> 8,
            0xCD,
            target & 0xFF,
            target >> 8,
            0xF5,
            0xCD,
            refresh_api & 0xFF,
            refresh_api >> 8,
            0xF1,
            0xC9,
        )
    )


def run_payload(
    session: host.HostSession,
    payload: bytes,
    name: str,
    timeout: float,
    result_address: int,
    result_length: int,
    *,
    address: int = LOAD_ADDRESS,
    refresh_api: int | None = None,
    refresh_wrapper_address: int = DEFAULT_REFRESH_WRAPPER_ADDRESS,
) -> dict[str, object]:
    print(f"JUKURAVI-BATCH: {name} upload/run", flush=True)
    if refresh_api is not None:
        upload = session.run_resident_loader_v2(
            payload,
            f"<batch:{name}:payload>",
            address,
            None,
            timeout,
        )
        wrapper = refresh_wrapper(address, refresh_api)
        operation = session.run_resident_loader_v2(
            wrapper,
            f"<batch:{name}:refresh-wrapper>",
            refresh_wrapper_address,
            refresh_wrapper_address,
            timeout,
            result_address=result_address,
            result_length=result_length,
            run_mode="call",
        )
        operation["payload_upload"] = upload
        operation["refresh_wrapper"] = {
            "address": f"0x{refresh_wrapper_address:04X}",
            "target": f"0x{address:04X}",
            "api": f"0x{refresh_api:04X}",
        }
        return operation
    return session.run_resident_loader_v2(
        payload,
        f"<batch:{name}>",
        address,
        address,
        timeout,
        result_address=result_address,
        result_length=result_length,
        run_mode="call",
    )


def evaluate_exact(
    session: host.HostSession,
    payload: bytes,
    probe: Probe,
    timeout: float,
    refresh_api: int | None = None,
    refresh_wrapper_address: int = DEFAULT_REFRESH_WRAPPER_ADDRESS,
) -> dict[str, object]:
    operation = run_payload(
        session,
        payload,
        probe.name,
        timeout,
        probe.result_address,
        len(probe.expected),
        refresh_api=refresh_api,
        refresh_wrapper_address=refresh_wrapper_address,
    )
    observed = result_bytes(operation)
    passed = observed == probe.expected
    print(
        f"JUKURAVI-BATCH: {probe.name} {'PASS' if passed else 'FAIL'}",
        flush=True,
    )
    result: dict[str, object] = {
        "name": probe.name,
        "verdict": "pass" if passed else "fail",
        "expected_hex": probe.expected.hex().upper(),
        "observed_hex": observed.hex().upper(),
        "operation": operation,
    }
    if not passed:
        result["ram_lane_analysis"] = ram_lane_analysis(probe.expected, observed)
    return result


def evaluate_ram_lanes(
    session: host.HostSession,
    timeout: float,
    address: int,
    hold_ms: float,
) -> dict[str, object]:
    patterns: list[dict[str, object]] = []
    aggregate_low = [0] * 8
    aggregate_high = [0] * 8
    print(
        f"JUKURAVI-BATCH: ram-lanes address=0x{address:04X} hold={hold_ms:g}ms",
        flush=True,
    )
    for name, expected in ram_lane_patterns():
        write = session.run_resident_loader_v2(
            expected,
            f"<batch:ram-lanes:{name}:write>",
            address,
            None,
            timeout,
        )
        if hold_ms:
            time.sleep(hold_ms / 1000.0)
        read = session.run_resident_loader_v2(
            b"",
            f"<batch:ram-lanes:{name}:read>",
            LOAD_ADDRESS,
            None,
            timeout,
            control_read_address=address,
            control_read_length=len(expected),
        )
        observed = bytes.fromhex(str(read["control_read"]["hex"]))
        analysis = ram_lane_analysis(expected, observed)
        for lane in analysis["lanes"]:
            bit = int(lane["bit"])
            aggregate_low[bit] += int(lane["one_to_zero"])
            aggregate_high[bit] += int(lane["zero_to_one"])
        passed = observed == expected
        print(
            f"JUKURAVI-BATCH: ram-lanes {name} "
            f"{'PASS' if passed else 'FAIL'} xor={analysis['xor_or']}",
            flush=True,
        )
        patterns.append(
            {
                "name": name,
                "verdict": "pass" if passed else "fail",
                "expected_hex": expected.hex().upper(),
                "observed_hex": observed.hex().upper(),
                "analysis": analysis,
                "write": write,
                "read": read,
            }
        )
    lanes = [
        {
            "bit": bit,
            "mask": f"0x{1 << bit:02X}",
            "package": DRAM_LANE_PACKAGES[bit],
            "one_to_zero": aggregate_low[bit],
            "zero_to_one": aggregate_high[bit],
            "mismatches": aggregate_low[bit] + aggregate_high[bit],
        }
        for bit in range(8)
        if aggregate_low[bit] or aggregate_high[bit]
    ]
    return {
        "name": "ram-lanes",
        "verdict": "pass" if not lanes else "fail",
        "address": f"0x{address:04X}",
        "bytes_per_pattern": 32,
        "hold_ms": hold_ms,
        "patterns": patterns,
        "lanes": lanes,
        "candidate_packages": [lane["package"] for lane in lanes],
    }


def evaluate_full_ram_sweep(
    session: host.HostSession,
    timeout: float,
    hold_ms: float,
    start: int = FULL_RAM_START,
    end: int = FULL_RAM_END,
) -> dict[str, object]:
    pattern_results: list[dict[str, object]] = []
    print(
        "JUKURAVI-BATCH: full-ram "
        f"range=0x{start:04X}..0x{end - 1:04X} "
        f"hold={hold_ms:g}ms",
        flush=True,
    )
    for name, expected in full_ram_patterns(start, end):
        print(f"JUKURAVI-BATCH: full-ram {name} write", flush=True)
        write = session.run_resident_loader_v2(
            expected,
            f"<batch:full-ram:{name}:write>",
            start,
            None,
            timeout,
        )
        if hold_ms:
            time.sleep(hold_ms / 1000.0)
        print(f"JUKURAVI-BATCH: full-ram {name} read", flush=True)
        read = session.run_resident_loader_v2(
            b"",
            f"<batch:full-ram:{name}:read>",
            LOAD_ADDRESS,
            None,
            timeout,
            control_read_address=start,
            control_read_length=len(expected),
        )
        observed = bytes.fromhex(str(read["control_read"]["hex"]))
        analysis = full_ram_failure_map(expected, observed, start)
        passed = observed == expected
        print(
            f"JUKURAVI-BATCH: full-ram {name} "
            f"{'PASS' if passed else 'FAIL'} "
            f"bytes={analysis['mismatching_bytes']} xor={analysis['xor_or']}",
            flush=True,
        )
        pattern_results.append(
            {
                "name": name,
                "verdict": "pass" if passed else "fail",
                "expected_crc16": (f"{protocol.crc16_ccitt_false(expected):04X}"),
                "observed_crc16": (f"{protocol.crc16_ccitt_false(observed):04X}"),
                "analysis": analysis,
                "write": write,
                "read": read,
            }
        )
    failed = [item["name"] for item in pattern_results if item["verdict"] != "pass"]
    return {
        "name": "full-ram-sweep",
        "verdict": "pass" if not failed else "fail",
        "start": f"0x{start:04X}",
        "end_exclusive": f"0x{end:04X}",
        "bytes_per_pattern": end - start,
        "hold_ms": hold_ms,
        "failed_patterns": failed,
        "patterns": pattern_results,
    }


def evaluate_local_full_ram_sweep(
    session: host.HostSession,
    timeout: float,
    hold_ms: float,
) -> dict[str, object]:
    """Test all host-safe RAM locally from two non-overlapping code homes."""
    pattern_results: list[dict[str, object]] = []
    print(
        "JUKURAVI-BATCH: local-full-ram "
        f"range=0x{FULL_RAM_START:04X}..0x{FULL_RAM_END - 1:04X} "
        f"hold={hold_ms:g}ms",
        flush=True,
    )
    for pattern_name, pattern_id in local_ram.PATTERNS:
        stage_results: list[dict[str, object]] = []
        for stage in local_ram.STAGES:
            payload = local_ram.build_probe(stage, pattern_id)
            print(
                f"JUKURAVI-BATCH: local-full-ram {pattern_name} {stage.name} fill",
                flush=True,
            )
            fill = session.run_resident_loader_v2(
                payload,
                f"<batch:local-full-ram:{pattern_name}:{stage.name}:fill>",
                stage.origin,
                stage.fill_entry,
                timeout,
                run_mode="call",
            )
            if fill.get("run", {}).get("return_a") != "0x00":
                raise host.SessionError(
                    f"local full-RAM {pattern_name}/{stage.name} fill "
                    "returned a nonzero accumulator"
                )
            if hold_ms:
                time.sleep(hold_ms / 1000.0)
            print(
                f"JUKURAVI-BATCH: local-full-ram {pattern_name} {stage.name} verify",
                flush=True,
            )
            verify = session.run_resident_loader_v2(
                b"",
                f"<batch:local-full-ram:{pattern_name}:{stage.name}:verify>",
                LOAD_ADDRESS,
                stage.verify_entry,
                timeout,
                result_address=stage.result_address,
                result_length=local_ram.RESULT_SIZE,
                run_mode="call",
            )
            decoded = local_ram.decode_result(result_bytes(verify), stage, pattern_id)
            decoded["fill_operation"] = fill
            decoded["verify_operation"] = verify
            print(
                f"JUKURAVI-BATCH: local-full-ram {pattern_name} "
                f"{stage.name} {str(decoded['verdict']).upper()} "
                f"bytes={decoded['mismatching_bytes']} "
                f"xor={decoded['xor_or']}",
                flush=True,
            )
            stage_results.append(decoded)

        mismatches = sum(int(item["mismatching_bytes"]) for item in stage_results)
        xor_or = 0
        for item in stage_results:
            xor_or |= int(str(item["xor_or"]), 16)
        pattern_results.append(
            {
                "name": pattern_name,
                "verdict": "pass" if mismatches == 0 else "fail",
                "mismatching_bytes": mismatches,
                "xor_or": f"0x{xor_or:02X}",
                "candidate_packages": [
                    DRAM_LANE_PACKAGES[bit] for bit in range(8) if xor_or & (1 << bit)
                ],
                "stages": stage_results,
            }
        )
    failed = [item["name"] for item in pattern_results if item["verdict"] != "pass"]
    return {
        "name": "local-full-ram-sweep",
        "verdict": "pass" if not failed else "fail",
        "start": f"0x{FULL_RAM_START:04X}",
        "end_exclusive": f"0x{FULL_RAM_END:04X}",
        "bytes_per_pattern": FULL_RAM_END - FULL_RAM_START,
        "locally_tested_bytes_per_pattern": sum(
            stage.end - stage.start for stage in local_ram.STAGES
        ),
        "hold_ms": hold_ms,
        "refresh_interval_bytes": 128,
        "failed_patterns": failed,
        "patterns": pattern_results,
    }


def evaluate_cpu_timebase(
    session: host.HostSession,
    payload: bytes,
    timeout: float,
    delta_tstates: int = 1_200_000,
) -> dict[str, object]:
    print("JUKURAVI-BATCH: cpu-host-timebase upload", flush=True)
    upload = session.run_resident_loader_v2(
        payload, "<batch:cpu-host-timebase>", LOAD_ADDRESS, None, timeout
    )
    baseline = session.run_resident_loader_v2(
        b"",
        "<batch:cpu-host-timebase-baseline>",
        LOAD_ADDRESS,
        LOAD_ADDRESS,
        timeout,
    )
    long_sample = session.run_resident_loader_v2(
        b"",
        "<batch:cpu-host-timebase-long>",
        LOAD_ADDRESS,
        CPU_TIMEBASE_LONG_ADDRESS,
        timeout,
    )
    baseline_run = baseline.get("run", {})
    long_run = long_sample.get("run", {})
    baseline_seconds = float(baseline_run.get("return_seconds", 0))
    long_seconds = float(long_run.get("return_seconds", 0))
    delta_seconds = long_seconds - baseline_seconds
    clean = (
        baseline_run.get("return_replays") == 0
        and long_run.get("return_replays") == 0
        and delta_seconds > 0
    )
    cpu_mhz = delta_tstates / delta_seconds / 1_000_000 if clean else None
    verdict = "measured" if cpu_mhz is not None else "fail"
    rendered = (
        f"MEASURED cpu={cpu_mhz:.6f}MHz delta={delta_seconds:.6f}s"
        if cpu_mhz is not None
        else "FAIL invalid paired RUN timing"
    )
    print(f"JUKURAVI-BATCH: cpu-host-timebase {rendered}", flush=True)
    return {
        "name": "cpu-host-timebase",
        "verdict": verdict,
        "delta_tstates": delta_tstates,
        "baseline_seconds": baseline_seconds,
        "long_seconds": long_seconds,
        "delta_seconds": round(delta_seconds, 6),
        "cpu_clock_mhz": None if cpu_mhz is None else round(cpu_mhz, 6),
        "operations": [upload, baseline, long_sample],
    }


def evaluate_d57(
    session: host.HostSession,
    payload: bytes,
    timeout: float,
) -> dict[str, object]:
    operation = run_payload(session, payload, "d57-raw", timeout, 0x4580, 56)
    observed = result_bytes(operation)
    valid = len(observed) == 56 and observed[:8] == b"D57R\xa5\x01\x08\0"
    failures: list[dict[str, object]] = []
    if valid:
        for repetition in range(8):
            record = observed[8 + repetition * 6 : 14 + repetition * 6]
            for channel in range(3):
                high, low = record[channel * 2 : channel * 2 + 2]
                if not high & 0x80 or low & 0x80:
                    failures.append(
                        {
                            "repetition": repetition + 1,
                            "channel": channel,
                            "high": f"{high:02X}",
                            "low": f"{low:02X}",
                        }
                    )
    passed = valid and not failures
    print(
        f"JUKURAVI-BATCH: d57-raw {'PASS' if passed else 'FAIL'} "
        f"bad_samples={len(failures)}",
        flush=True,
    )
    return {
        "name": "d57-raw",
        "verdict": "pass" if passed else "fail",
        "observed_hex": observed.hex().upper(),
        "bad_samples": failures,
        "operation": operation,
    }


def evaluate_address_execution(
    session: host.HostSession,
    timeout: float,
) -> dict[str, object]:
    marker40 = marker_program(0x40)
    marker50 = marker_program(0x50)
    print("JUKURAVI-BATCH: execution-address separation", flush=True)
    load40 = session.run_resident_loader_v2(
        marker40, "<batch:marker-4000>", 0x4000, None, timeout
    )
    load50 = session.run_resident_loader_v2(
        marker50, "<batch:marker-5000>", 0x5000, None, timeout
    )
    read40 = session.run_resident_loader_v2(
        b"",
        "<batch:read-marker-4000>",
        0x4000,
        None,
        timeout,
        control_read_address=0x4000,
        control_read_length=len(marker40),
    )
    read50 = session.run_resident_loader_v2(
        b"",
        "<batch:read-marker-5000>",
        0x4000,
        None,
        timeout,
        control_read_address=0x5000,
        control_read_length=len(marker50),
    )
    call50 = session.run_resident_loader_v2(
        b"",
        "<batch:call-marker-5000>",
        0x4000,
        0x5000,
        timeout,
        result_address=0x4100,
        result_length=1,
        run_mode="call",
    )
    got40 = bytes.fromhex(str(read40["control_read"]["hex"]))
    got50 = bytes.fromhex(str(read50["control_read"]["hex"]))
    marker = result_bytes(call50)
    returned_a = call50.get("run", {}).get("return_a")
    passed = (
        got40 == marker40
        and got50 == marker50
        and marker == b"\x50"
        and returned_a == "0x50"
    )
    print(
        f"JUKURAVI-BATCH: execution-address {'PASS' if passed else 'FAIL'}",
        flush=True,
    )
    return {
        "name": "execution-address",
        "verdict": "pass" if passed else "fail",
        "read_4000_hex": got40.hex().upper(),
        "read_5000_hex": got50.hex().upper(),
        "executed_marker_hex": marker.hex().upper(),
        "returned_a": returned_a,
        "operations": [load40, load50, read40, read50, call50],
    }


def retention_sweep(
    session: host.HostSession,
    guards_ms: tuple[float, ...],
    recovery_guard_ms: float,
    timeout: float,
) -> list[dict[str, object]]:
    cookie = b"RETENTION-AGE!!!"
    evidence: list[dict[str, object]] = []
    original_guard = session.loader_guard_seconds
    original_retries = session.loader_retries
    try:
        for index, guard_ms in enumerate(guards_ms):
            session.loader_guard_seconds = guard_ms / 1000.0
            session.loader_retries = 1
            started = time.monotonic()
            item: dict[str, object] = {
                "guard_ms": guard_ms,
                "cookie_bytes": len(cookie),
            }
            try:
                detail, echoed, _, attempts = session._loader_v2_data_command(
                    protocol.TYPE_LOADER_V2_PROBE,
                    0xC0 + index,
                    cookie,
                    len(session.frames),
                    timeout,
                    f"retention sweep {guard_ms:g} ms",
                )
                passed = (
                    detail["status"] == protocol.LOADER_STATUS_OK and echoed == cookie
                )
                item.update(
                    verdict="pass" if passed else "fail",
                    attempts=attempts,
                    echoed_hex=echoed.hex().upper(),
                )
            except (host.SessionError, OSError) as error:
                item.update(verdict="fail", error=str(error))
            item["seconds"] = round(time.monotonic() - started, 6)
            session.loader_guard_seconds = recovery_guard_ms / 1000.0
            try:
                recovery, _, recovery_attempts = session._loader_v2_result_command(
                    protocol.TYPE_LOADER_V2_CONFIG,
                    0xE0 + index,
                    b"\x01",
                    len(session.frames),
                    timeout,
                    f"retention recovery {guard_ms:g} ms",
                )
                recovered = (
                    recovery["status"] == protocol.LOADER_STATUS_OK
                    and recovery["count"] == 1
                )
                session.host_symbol_repetitions = 1
                item.update(
                    recovery="pass" if recovered else "fail",
                    recovery_attempts=recovery_attempts,
                )
            except (host.SessionError, OSError) as error:
                item.update(recovery="fail", recovery_error=str(error))
            print(
                f"JUKURAVI-BATCH: retention guard={guard_ms:g}ms "
                f"{str(item['verdict']).upper()} recovery={item['recovery']}",
                flush=True,
            )
            evidence.append(item)
            if item["recovery"] != "pass":
                break
    finally:
        session.loader_guard_seconds = original_guard
        session.loader_retries = original_retries
    return evidence


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the complete T34/T35/T36 CS00024 batch after one RESET"
    )
    transport = parser.add_mutually_exclusive_group(required=True)
    transport.add_argument("--port", help="serial device, e.g. /dev/ttyUSB0")
    transport.add_argument("--fd", type=int, help="inherited cosim PTY descriptor")
    parser.add_argument(
        "--rom",
        choices=tuple(ROM_PROFILES),
        default="t34",
        help="exact ROM/refresh policy to expect (default: t34)",
    )
    parser.add_argument("--baud", type=int, default=host.DEFAULT_BAUD)
    parser.add_argument("--timeout", type=float, default=host.DEFAULT_TIMEOUT)
    parser.add_argument("--banner-timeout", type=float, default=90.0)
    parser.add_argument(
        "--loader-timeout", type=float, default=host.DEFAULT_LOADER_TIMEOUT
    )
    parser.add_argument(
        "--loader-guard-ms",
        type=host.parse_nonnegative_float,
        default=host.SOLICITED_RESPONSE_GUARD_SECONDS * 1000.0,
    )
    parser.add_argument("--loader-retries", type=host.parse_positive_int, default=3)
    parser.add_argument("--log-dir", type=Path)
    parser.add_argument(
        "--retention-guards-ms",
        type=parse_guard_list,
        default=(6.0, 12.0, 24.0, 36.0),
        help="one-vote full-cookie guard sweep (default: 6,12,24,36)",
    )
    parser.add_argument(
        "--no-retention-sweep",
        action="store_true",
        help="skip the intentionally slow parser-aging characterization",
    )
    parser.add_argument(
        "--skip-write-map",
        action="store_true",
        help=(
            "defer the potentially loader-destructive all-RAM A12 write-map "
            "probe to an isolated RESET session"
        ),
    )
    parser.add_argument(
        "--skip-probe",
        action="append",
        choices=tuple(probe.name for probe in PROBES),
        default=[],
        help="defer a named RAM/CPU probe to an isolated RESET session",
    )
    parser.add_argument(
        "--only-probe",
        choices=tuple(probe.name for probe in PROBES),
        help=(
            "after verified return and CPU timing, run only this probe and stop; "
            "intended for isolated fault discrimination"
        ),
    )
    parser.add_argument(
        "--only-ram-lanes",
        action="store_true",
        help=(
            "after verified return and CPU timing, run only host-driven "
            "known-pattern RAM readback with D84-D91 bit-lane reporting"
        ),
    )
    parser.add_argument(
        "--only-d57",
        action="store_true",
        help=(
            "after verified return and CPU timing, run only the raw D57 "
            "channel discriminator; intended for isolated electrical follow-up"
        ),
    )
    parser.add_argument(
        "--ram-lane-address",
        type=parse_hex_address,
        default=DEFAULT_RAM_LANE_ADDRESS,
        help="scratch start address for --only-ram-lanes (default: 4D00)",
    )
    parser.add_argument(
        "--ram-lane-hold-ms",
        type=host.parse_nonnegative_float,
        default=6000.0,
        help=(
            "refresh-on idle hold between each lane-pattern write and read "
            "in milliseconds (default: 6000)"
        ),
    )
    parser.add_argument(
        "--full-ram-sweep",
        action="store_true",
        help=(
            "destructively test all 32 KiB at 4000..BFFF with zero, one, "
            "checkerboard, and address-dependent patterns"
        ),
    )
    parser.add_argument(
        "--full-ram-hold-ms",
        type=host.parse_nonnegative_float,
        default=6000.0,
        help=(
            "refresh-on hold between each full-RAM pattern write and final "
            "readback in milliseconds (default: 6000)"
        ),
    )
    parser.add_argument(
        "--full-ram-start",
        type=parse_hex_address,
        default=FULL_RAM_START,
        help="full-sweep start address (default: 4000)",
    )
    parser.add_argument(
        "--full-ram-end",
        type=parse_hex_address,
        default=FULL_RAM_END,
        help="full-sweep exclusive end address (default: C000)",
    )
    parser.add_argument(
        "--local-full-ram-sweep",
        action="store_true",
        help=(
            "test all 32 KiB locally from two RAM-resident cooperative-refresh "
            "probes and return compact failure summaries"
        ),
    )
    parser.add_argument(
        "--local-full-ram-hold-ms",
        type=host.parse_nonnegative_float,
        default=6000.0,
        help=(
            "refresh-on hold between each local full-RAM fill and verify "
            "in milliseconds (default: 6000)"
        ),
    )
    parser.add_argument(
        "--direct-probe",
        action="append",
        choices=tuple(probe.name for probe in PROBES),
        default=[],
        help=(
            "run a named short probe directly at 4000 instead of through the "
            "refresh-capable pre/post wrapper; the probe must finish within its "
            "DRAM retention budget"
        ),
    )
    parser.add_argument(
        "--refresh-wrapper-address",
        type=parse_hex_address,
        default=DEFAULT_REFRESH_WRAPPER_ADDRESS,
        help="cooperative-refresh wrapper address in hex (default: 6F00)",
    )
    return parser


def main() -> int:
    args = make_parser().parse_args()
    focused_modes = sum(
        (args.only_probe is not None, args.only_ram_lanes, args.only_d57)
    )
    if focused_modes > 1:
        print(
            "JUKURAVI-BATCH: --only-probe, --only-ram-lanes, and --only-d57 "
            "are exclusive",
            file=sys.stderr,
        )
        return 2
    if args.full_ram_sweep and args.local_full_ram_sweep:
        print(
            "JUKURAVI-BATCH: --full-ram-sweep and --local-full-ram-sweep are exclusive",
            file=sys.stderr,
        )
        return 2
    if not (
        protocol.LOADER_V2_LOAD_MIN
        <= args.ram_lane_address
        <= protocol.LOADER_V2_LOAD_END - 32
    ):
        print(
            "JUKURAVI-BATCH: RAM lane scratch must fit in 4000..BFFF",
            file=sys.stderr,
        )
        return 2
    if not (
        protocol.LOADER_V2_LOAD_MIN
        <= args.full_ram_start
        < args.full_ram_end
        <= protocol.LOADER_V2_LOAD_END
    ):
        print(
            "JUKURAVI-BATCH: full RAM range must fit in 4000..BFFF",
            file=sys.stderr,
        )
        return 2
    profile = ROM_PROFILES[args.rom]
    if args.local_full_ram_sweep and profile.refresh_api is None:
        print(
            "JUKURAVI-BATCH: local full-RAM sweep requires T35/T36 refresh",
            file=sys.stderr,
        )
        return 2
    skipped_probes = set(args.skip_probe)
    direct_probes = set(args.direct_probe)
    if args.skip_write_map:
        skipped_probes.add("a12-write-map")
    if args.only_probe is not None:
        skipped_probes.update(
            probe.name for probe in PROBES if probe.name != args.only_probe
        )
    if args.only_ram_lanes or args.only_d57:
        skipped_probes.update(probe.name for probe in PROBES)
    log_dir = (
        HERE / "sessions" / f"cs00024-{profile.name}-batch"
        if args.log_dir is None
        else args.log_dir
    )
    if args.timeout <= 0 or args.banner_timeout <= 0 or args.loader_timeout <= 0:
        print("JUKURAVI-BATCH: timeouts must be positive", file=sys.stderr)
        return 2
    try:
        fd, transport = host.open_transport(args.port, args.fd, args.baud)
    except host.SessionError as error:
        print(f"JUKURAVI-BATCH: ERROR {error}", file=sys.stderr)
        return 1

    logs = host.SessionLogs(log_dir, transport)
    session = host.HostSession(
        fd=fd,
        logs=logs,
        timeout=args.timeout,
        banner_timeout=args.banner_timeout,
        expect_rom_version=profile.version,
        expect_crc16=profile.crc16,
        nano_reset_requested=False,
        loader_guard_seconds=args.loader_guard_ms / 1000.0,
        loader_retries=args.loader_retries,
        loader_votes=1,
        loader_config_first=profile.config_first,
        loader_bootstrap_votes=profile.boot_votes,
        loader_refresh_mode="auto",
    )
    results: list[dict[str, object]] = []
    retention: list[dict[str, object]] = []
    try:
        with tempfile.TemporaryDirectory(
            prefix=f"jukuravi-{profile.name}-batch-"
        ) as name:
            payloads = build_payloads(Path(name), profile)
            print(
                f"JUKURAVI-BATCH: {profile.name.upper()} listening on "
                f"{transport} at {args.baud}; "
                "press RESET once",
                flush=True,
            )
            session.begin_attempt(1)
            session.run()
            session.run_loader(
                b"",
                "<batch bootstrap control>",
                LOAD_ADDRESS,
                None,
                args.loader_timeout,
                control_only=True,
            )
            policy = "CONFIG-first" if profile.config_first else "native one-vote"
            print(f"JUKURAVI-BATCH: {policy} PROBE PASS", flush=True)

            return_operation = run_payload(
                session,
                (FIRMWARE / "return-4000.bin").read_bytes(),
                "verified-return",
                args.loader_timeout,
                0x4100,
                8,
            )
            return_observed = result_bytes(return_operation)
            return_a = return_operation.get("run", {}).get("return_a")
            return_passed = return_observed == b"T28RET!\0" and return_a == "0x42"
            results.append(
                {
                    "name": "verified-return",
                    "verdict": "pass" if return_passed else "fail",
                    "observed_hex": return_observed.hex().upper(),
                    "returned_a": return_a,
                    "operation": return_operation,
                }
            )
            print(
                f"JUKURAVI-BATCH: verified-return "
                f"{'PASS' if return_passed else 'FAIL'}",
                flush=True,
            )

            # Run every non-invasive test first.  A board whose boot bitmap
            # already reports D57 may lose its serial clock when an exploratory
            # snippet reprograms that PIT, so D57 raw sampling is deliberately
            # the final operation in the session.
            results.append(
                evaluate_cpu_timebase(
                    session,
                    payloads[profile.cpu_timebase_source].read_bytes(),
                    args.loader_timeout,
                    profile.cpu_timebase_delta_tstates,
                )
            )
            for probe in PROBES:
                if probe.name in skipped_probes:
                    continue
                results.append(
                    evaluate_exact(
                        session,
                        payloads[probe.source].read_bytes(),
                        probe,
                        args.loader_timeout,
                        (None if probe.name in direct_probes else profile.refresh_api),
                        args.refresh_wrapper_address,
                    )
                )
            if args.only_ram_lanes:
                results.append(
                    evaluate_ram_lanes(
                        session,
                        args.loader_timeout,
                        args.ram_lane_address,
                        args.ram_lane_hold_ms,
                    )
                )
            if args.full_ram_sweep:
                results.append(
                    evaluate_full_ram_sweep(
                        session,
                        args.loader_timeout,
                        args.full_ram_hold_ms,
                        args.full_ram_start,
                        args.full_ram_end,
                    )
                )
            if args.local_full_ram_sweep:
                results.append(
                    evaluate_local_full_ram_sweep(
                        session,
                        args.loader_timeout,
                        args.local_full_ram_hold_ms,
                    )
                )
            isolated = (
                args.only_probe is not None or args.only_ram_lanes or args.only_d57
            )
            if not isolated:
                results.append(evaluate_address_execution(session, args.loader_timeout))
            if not isolated and not args.no_retention_sweep:
                retention = retention_sweep(
                    session,
                    args.retention_guards_ms,
                    args.loader_guard_ms,
                    args.loader_timeout,
                )
            if not (args.only_probe is not None or args.only_ram_lanes):
                results.append(
                    evaluate_d57(
                        session,
                        payloads[profile.d57_source].read_bytes(),
                        args.loader_timeout,
                    )
                )
            session.finish_attempt("ok")
    except KeyboardInterrupt:
        error = "interrupted by operator"
        if session._attempt_number is not None:
            session.finish_attempt("error", error)
        summary = session.summary("error", error)
        summary["batch"] = {"results": results, "retention_sweep": retention}
        logs.finish(summary)
        print(f"JUKURAVI-BATCH: INTERRUPTED; logs {logs.json_path}", file=sys.stderr)
        return 130
    except (host.SessionError, OSError, subprocess.CalledProcessError) as error:
        if session._attempt_number is not None:
            session.finish_attempt("error", str(error))
        summary = session.summary("error", str(error))
        summary["batch"] = {"results": results, "retention_sweep": retention}
        logs.finish(summary)
        print(f"JUKURAVI-BATCH: ERROR {error}", file=sys.stderr)
        print(f"JUKURAVI-BATCH: logs {logs.json_path}", file=sys.stderr)
        return 1
    finally:
        os.close(fd)

    core_failures = [item["name"] for item in results if item["verdict"] == "fail"]
    boot = host.diagnostic_status_json(session.diagnostic_status)
    overall_pass = (
        not core_failures
        and bool(boot)
        and all(
            bool(boot[name])
            for name in ("pic", "ppi", "d54", "d55", "d57", "ram_4000", "ram_c000")
        )
    )
    summary = session.summary("ok")
    summary["batch"] = {
        "rom_profile": profile.name,
        "rom_version": f"0x{profile.version:02X}",
        "rom_crc16": f"0x{profile.crc16:04X}",
        "overall_verdict": "pass" if overall_pass else "findings",
        "core_failures": core_failures,
        "results": results,
        "retention_sweep": retention,
        "skipped": sorted(skipped_probes),
        "direct_probes": sorted(direct_probes),
        "ram_lane_test": args.only_ram_lanes,
        "d57_only": args.only_d57,
        "full_ram_sweep": args.full_ram_sweep,
        "local_full_ram_sweep": args.local_full_ram_sweep,
    }
    logs.finish(summary)
    print(
        f"JUKURAVI-BATCH: {'PASS' if overall_pass else 'COMPLETE WITH FINDINGS'}; "
        f"logs {logs.json_path}",
        flush=True,
    )
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
