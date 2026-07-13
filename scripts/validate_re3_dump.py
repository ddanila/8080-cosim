#!/usr/bin/env python3
"""Validate repeated K155RE3 32x8 serial captures and export raw tables."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROW = re.compile(r"^([0-9A-Fa-f]{2}),([0-9A-Fa-f]{2}),(OK|UNSTABLE)$")


@dataclass(frozen=True)
class Capture:
    source: str
    raw: bytes


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def finish(source: str, rows: dict[int, tuple[int, str]]) -> Capture:
    out_of_range = sorted(address for address in rows if address >= 32)
    if out_of_range:
        raise ValueError(f"{source}: out-of-range address {out_of_range[0]:02X}")
    missing = sorted(set(range(32)) - set(rows))
    if missing:
        raise ValueError(f"{source}: missing {len(missing)} addresses; first is {missing[0]:02X}")
    unstable = [address for address, (_, state) in rows.items() if state != "OK"]
    if unstable:
        raise ValueError(f"{source}: unstable addresses: " + ",".join(f"{value:02X}" for value in unstable))
    return Capture(source, bytes(rows[address][0] for address in range(32)))


def parse(path: Path) -> list[Capture]:
    captures: list[Capture] = []
    rows: dict[int, tuple[int, str]] = {}
    section = 0
    active = False
    for line_number, text in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        line = text.strip()
        if line == "# K155RE3 dump":
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
        address, raw = int(match.group(1), 16), int(match.group(2), 16)
        if address in rows:
            raise ValueError(f"{path}#{section}: duplicate address {address:02X} at line {line_number}")
        rows[address] = (raw, match.group(3))
    if rows:
        captures.append(finish(f"{path}#{section}", rows))
    if not captures:
        raise ValueError(f"{path}: no RE3 CSV rows found")
    return captures


def validate(paths: list[Path], allow_single: bool) -> list[Capture]:
    captures = [capture for path in paths for capture in parse(path)]
    if len(captures) < 2 and not allow_single:
        raise ValueError("at least two complete captures are required; use --allow-single only for diagnostics")
    reference = captures[0]
    for capture in captures[1:]:
        if capture.raw != reference.raw:
            differences = [index for index, pair in enumerate(zip(reference.raw, capture.raw))
                           if pair[0] != pair[1]]
            first = differences[0]
            raise ValueError(
                f"repeat mismatch: {reference.source} vs {capture.source}; "
                f"{len(differences)} addresses differ, first {first:02X}: "
                f"{reference.raw[first]:02X}!={capture.raw[first]:02X}"
            )
    return captures


def write_outputs(
    directory: Path,
    name: str,
    captures: list[Capture],
    inputs: list[Path],
    independent_capture_count: int | None,
    alias_note: str | None,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    raw = captures[0].raw
    asserted = bytes((~value) & 0xFF for value in raw)
    paths = {
        "raw": directory / f"{name}.raw.bin",
        "asserted": directory / f"{name}.asserted.bin",
        "hex": directory / f"{name}.raw.hex",
        "report": directory / f"{name}.dump.json",
    }
    paths["raw"].write_bytes(raw)
    paths["asserted"].write_bytes(asserted)
    paths["hex"].write_text("".join(f"{value:02X}\n" for value in raw), encoding="ascii")
    report = {
        "schema_version": 2,
        "device": "K155RE3 32x8",
        "name": name,
        "capture_count": len(captures),
        "independent_capture_count": independent_capture_count or len(captures),
        "raw_pin_level_sha256": sha256(raw),
        "active_low_asserted_sha256": sha256(asserted),
        "packing": "32 raw bytes in A0..A4 address order; D0..D7 map to bits 0..7",
        "comparison_rule": "raw pin-level table is authoritative; asserted table is byte complement",
        "inputs": [{"path": str(path), "sha256": sha256(path.read_bytes())} for path in inputs],
        "captures": [capture.source for capture in captures],
    }
    if alias_note:
        report["alias_note"] = alias_note
    paths["report"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("wrote " + ", ".join(str(path) for path in paths.values()))


def self_test() -> None:
    def capture(mutate: tuple[int, int] | None = None, unstable: int | None = None) -> str:
        lines = ["# K155RE3 dump", "# addr,raw_pins,stable"]
        for address in range(32):
            raw = ((address * 0x29) ^ 0xA5) & 0xFF
            if mutate and address == mutate[0]:
                raw = mutate[1]
            state = "UNSTABLE" if address == unstable else "OK"
            lines.append(f"{address:02X},{raw:02X},{state}")
        lines.append("# END")
        return "\n".join(lines) + "\n"

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        first, second = root / "first.txt", root / "second.txt"
        first.write_text(capture()); second.write_text(capture())
        assert len(validate([first, second], False)[0].raw) == 32

        def expect_error(needle: str) -> None:
            try:
                validate([first, second], False)
                raise AssertionError(f"{needle} failure was accepted")
            except ValueError as error:
                assert needle in str(error), str(error)

        second.write_text(capture((0x0E, 0x00))); expect_error("repeat mismatch")
        second.write_text(capture(unstable=0x12)); expect_error("unstable addresses")
        lines = capture().splitlines()
        second.write_text("\n".join(line for line in lines if not line.startswith("0F,")) + "\n")
        expect_error("missing 1 addresses")
        lines = capture().splitlines(); lines.insert(-1, next(line for line in lines if line.startswith("0A,")))
        second.write_text("\n".join(lines) + "\n"); expect_error("duplicate address 0A")
        second.write_text(capture() + "20,00,OK\n"); expect_error("out-of-range address 20")
        try:
            validate([first], False)
            raise AssertionError("single capture was accepted without --allow-single")
        except ValueError as error:
            assert "at least two complete captures" in str(error)
    print("RE3 dump validator self-test: PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("captures", nargs="*", type=Path)
    parser.add_argument("--allow-single", action="store_true")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--name", default="re3")
    parser.add_argument(
        "--independent-capture-count",
        type=int,
        help="explicit read-event count when input filenames include provenance aliases",
    )
    parser.add_argument(
        "--alias-note",
        help="human-readable explanation for alias inputs preserved in the manifest",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test(); return 0
    if not args.captures:
        parser.error("provide capture files or --self-test")
    try:
        captures = validate(args.captures, args.allow_single)
    except ValueError as error:
        raise SystemExit(f"RE3 dump validation FAIL: {error}")
    independent_count = args.independent_capture_count or len(captures)
    if independent_count < 1 or independent_count > len(captures):
        parser.error("--independent-capture-count must be between 1 and the parsed capture count")
    if args.alias_note and args.independent_capture_count is None:
        parser.error("--alias-note requires --independent-capture-count")
    print(
        f"RE3 dump validation PASS: {len(captures)} manifest captures, "
        f"{independent_count} independent; raw SHA256 {sha256(captures[0].raw)}"
    )
    if args.out_dir:
        write_outputs(
            args.out_dir,
            args.name,
            captures,
            args.captures,
            args.independent_capture_count,
            args.alias_note,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
