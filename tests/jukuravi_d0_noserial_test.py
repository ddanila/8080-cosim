#!/usr/bin/env python3
"""Prove the cumulative audible diagnostic has no USART dependency."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "spinoffs" / "jukuravi"),
                str(ROOT / "spinoffs" / "jukuravi" / "firmware")]
import build_d0_noserial as firmware  # noqa: E402
import jukuravi_d0_pit_test as pit_test  # noqa: E402
import jukuravi_d0_ppi_test as ppi_test  # noqa: E402
import jukuravi_d0_ram_fallback_test as fallback_test  # noqa: E402


IO_RE = re.compile(r"^JUKU-IO\s+(IN |OUT)\s+([0-9A-F]{2})\s+([0-9A-F]{2})$")


def events(proc) -> list[tuple[str, int, int]]:
    result = []
    for line in proc.stderr.splitlines():
        if match := IO_RE.match(line):
            result.append((match.group(1).strip(), int(match.group(2), 16),
                           int(match.group(3), 16)))
    return result


def verify_run(label, result, metadata, *, dead: bool) -> list[str]:
    proc, state, outbound, ram = result
    failures: list[str] = []
    expected_pc = int(metadata["no_windows_halt" if dead else "windows_found_halt"]) + 1
    for key, expected in (
        ("pc", f"{expected_pc:04X}"), ("halted", "1"), ("sp", "0000"),
        ("iff", "0"), ("mode", "0"), ("mode_switches", "0"),
        ("usart_tx_bytes", "0"), ("usart_rx_bytes", "0"),
        ("e", "00" if dead else "03"),
    ):
        if state.get(key) != expected:
            failures.append(f"{label}: {key}={state.get(key)} != {expected}")
    if proc.returncode != 0:
        failures.append(f"{label}: cosim exited {proc.returncode}")
    if outbound:
        failures.append(f"{label}: unexpected serial output {outbound.hex()}")
    io = events(proc)
    if any(port in (0x08, 0x09) for _, port, _ in io):
        failures.append(f"{label}: touched USART despite no-serial contract")
    expected_pit = pit_test.expected_pit_io()
    actual_pit = pit_test.pit_slice(proc)[:len(expected_pit)]
    if actual_pit != expected_pit:
        failures.append(f"{label}: cumulative PIT sequence differs")
    failures.extend(ppi_test.verify_safe_state(label, state))
    for start, size in firmware.FALLBACK_WINDOWS:
        if ram[start:start + size] != bytes((0x55,)) * size:
            failures.append(f"{label}: RAM window {start:04X} final fill differs")
    return failures


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} trace diag-d0-noserial.bin",
              file=sys.stderr)
        return 2
    trace, rom = map(lambda value: Path(value).resolve(), sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        print("trace executable or exact no-serial image is missing", file=sys.stderr)
        return 2
    failures = []
    failures.extend(verify_run(
        "clean", fallback_test.run_fallback(trace, image, "noserial-clean"),
        metadata, dead=False,
    ))
    failures.extend(verify_run(
        "dead-d87", fallback_test.run_fallback(
            trace, image, "noserial-dead", ram_fault="*:08:00"
        ), metadata, dead=True,
    ))
    if failures:
        print("JUKURAVI-D0-NOSERIAL: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("JUKURAVI-D0-NOSERIAL: PASS (no USART I/O; PIT; RAM success/dead-D87)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
