#!/usr/bin/env python3
"""Validate repeated KR556RT4 serial captures and export lossless tables."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROW = re.compile(r"^([0-9A-Fa-f]{2}),([0-9A-Fa-f]),([0-9A-Fa-f]),(OK|UNSTABLE)$")


@dataclass(frozen=True)
class Capture:
    source: str
    raw: bytes
    asserted: bytes


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def finish(source: str, rows: dict[int, tuple[int, int, str]]) -> Capture:
    missing = sorted(set(range(256)) - set(rows))
    if missing:
        raise ValueError(f"{source}: missing {len(missing)} addresses; first is {missing[0]:02X}")
    unstable = [address for address, (_, _, state) in rows.items() if state != "OK"]
    if unstable:
        raise ValueError(f"{source}: unstable addresses: " + ",".join(f"{value:02X}" for value in unstable))
    raw = bytes(rows[address][0] for address in range(256))
    asserted = bytes(rows[address][1] for address in range(256))
    for address, (pin_level, active_low, _) in rows.items():
        if active_low != ((~pin_level) & 0x0F):
            raise ValueError(
                f"{source}: address {address:02X} asserted nibble {active_low:X} "
                f"is not complement of raw {pin_level:X}"
            )
    return Capture(source, raw, asserted)


def parse(path: Path) -> list[Capture]:
    captures: list[Capture] = []
    rows: dict[int, tuple[int, int, str]] = {}
    section = 0
    active = False
    for line_number, text in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        line = text.strip()
        if line == "# KR556RT4 dump":
            if rows:
                captures.append(finish(f"{path}#{section}", rows))
            rows = {}
            section += 1
            active = True
            continue
        match = ROW.fullmatch(line)
        if not match:
            continue
        if not active:
            section += 1
            active = True
        address, raw, asserted = (int(value, 16) for value in match.groups()[:3])
        if address in rows:
            raise ValueError(f"{path}#{section}: duplicate address {address:02X} at line {line_number}")
        rows[address] = (raw, asserted, match.group(4))
    if rows:
        captures.append(finish(f"{path}#{section}", rows))
    if not captures:
        raise ValueError(f"{path}: no RT4 CSV rows found")
    return captures


def validate(paths: list[Path], allow_single: bool) -> list[Capture]:
    captures = [capture for path in paths for capture in parse(path)]
    if len(captures) < 2 and not allow_single:
        raise ValueError("at least two complete captures are required; use --allow-single only for diagnostics")
    reference = captures[0]
    for capture in captures[1:]:
        if capture.raw != reference.raw:
            differences = [index for index, (left, right) in enumerate(zip(reference.raw, capture.raw))
                           if left != right]
            first = differences[0]
            raise ValueError(
                f"repeat mismatch: {reference.source} vs {capture.source}; "
                f"{len(differences)} addresses differ, first {first:02X}: "
                f"{reference.raw[first]:X}!={capture.raw[first]:X}"
            )
    return captures


def write_outputs(directory: Path, name: str, captures: list[Capture], inputs: list[Path]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    raw = captures[0].raw
    asserted = captures[0].asserted
    raw_path = directory / f"{name}.raw.bin"
    asserted_path = directory / f"{name}.asserted.bin"
    hex_path = directory / f"{name}.raw.hex"
    report_path = directory / f"{name}.dump.json"
    raw_path.write_bytes(raw)
    asserted_path.write_bytes(asserted)
    hex_path.write_text("".join(f"{value:02X}\n" for value in raw), encoding="ascii")
    report = {
        "schema_version": 1,
        "device": "KR556RT4 256x4",
        "name": name,
        "capture_count": len(captures),
        "raw_pin_level_sha256": sha256(raw),
        "active_low_asserted_sha256": sha256(asserted),
        "packing": "256 bytes in address order; low nibble significant; high nibble zero",
        "comparison_rule": "raw pin-level table is authoritative; asserted table is bitwise low-nibble complement",
        "inputs": [{"path": str(path), "sha256": sha256(path.read_bytes())} for path in inputs],
        "captures": [capture.source for capture in captures],
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {raw_path}, {asserted_path}, {hex_path}, {report_path}")


def self_test() -> None:
    def capture(mutate: tuple[int, int] | None = None, unstable: int | None = None) -> str:
        lines = ["# KR556RT4 dump", "# addr,raw_pins,logical_active_low,stable"]
        for address in range(256):
            raw = ((address >> 4) ^ address) & 0x0F
            if mutate and address == mutate[0]:
                raw = mutate[1]
            state = "UNSTABLE" if address == unstable else "OK"
            lines.append(f"{address:02X},{raw:X},{(~raw)&15:X},{state}")
        lines.append("# END")
        return "\n".join(lines) + "\n"

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        first, second = root / "first.txt", root / "second.txt"
        first.write_text(capture()); second.write_text(capture())
        captures = validate([first, second], False)
        assert len(captures) == 2 and len(captures[0].raw) == 256

        def expect_error(needle: str) -> None:
            try:
                validate([first, second], False)
                raise AssertionError(f"{needle} failure was accepted")
            except ValueError as error:
                assert needle in str(error), str(error)

        second.write_text(capture((0x5A, 0x0)))
        expect_error("repeat mismatch")
        second.write_text(capture(unstable=0xA5))
        expect_error("unstable addresses")
        lines = capture().splitlines()
        second.write_text("\n".join(line for line in lines if not line.startswith("7F,")) + "\n")
        expect_error("missing 1 addresses")
        lines = capture().splitlines()
        lines.insert(-1, next(line for line in lines if line.startswith("42,")))
        second.write_text("\n".join(lines) + "\n")
        expect_error("duplicate address 42")
        lines = capture().splitlines()
        index = next(index for index, line in enumerate(lines) if line.startswith("3C,"))
        fields = lines[index].split(",")
        fields[2] = fields[1]
        lines[index] = ",".join(fields)
        second.write_text("\n".join(lines) + "\n")
        expect_error("is not complement")
        second.write_text(capture())
        try:
            validate([first], False)
            raise AssertionError("single capture was accepted without --allow-single")
        except ValueError as error:
            assert "at least two complete captures" in str(error)
    print("RT4 dump validator self-test: PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("captures", nargs="*", type=Path)
    parser.add_argument("--allow-single", action="store_true")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--name", default="rt4")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.captures:
        parser.error("provide capture files or --self-test")
    try:
        captures = validate(args.captures, args.allow_single)
    except ValueError as error:
        raise SystemExit(f"RT4 dump validation FAIL: {error}")
    raw = captures[0].raw
    print(f"RT4 dump validation PASS: {len(captures)} captures; raw SHA256 {sha256(raw)}")
    if args.out_dir:
        write_outputs(args.out_dir, args.name, captures, args.captures)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
