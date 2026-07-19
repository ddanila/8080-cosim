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
REVISION = re.compile(r"^# reader_revision=(\d+)$")
DISABLED = re.compile(r"^# disabled_raw=([0-9A-Fa-f]),stable=(OK|UNSTABLE)$")
REVISION_DATA_MAPS = {
    2: "# data_map=D0:D10,D1:D11,D2:D12,D3:A0; CE14:A1; Nano_D13:NC",
    3: (
        "# data_map=D0:D4,D1:D3,D2:D2,D3:A1; "
        "address_map=A0:D12,A1:D13,A2:A0,A3:D11,A4:D10,A5:D9,A6:D8,A7:D7; "
        "CE13:D5,CE14:D6"
    ),
}
DISABLED_CE13 = re.compile(r"^# disabled_ce13_raw=([0-9A-Fa-f]),stable=(OK|UNSTABLE)$")
DISABLED_CE14 = re.compile(r"^# disabled_ce14_raw=([0-9A-Fa-f]),stable=(OK|UNSTABLE)$")


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
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    headers = sum(line.strip() == "# KR556RT4 dump" for line in lines)
    revisions = [
        int(match.group(1))
        for line in lines
        if (match := REVISION.fullmatch(line.strip()))
    ]
    disabled = [
        (int(match.group(1), 16), match.group(2))
        for line in lines
        if (match := DISABLED.fullmatch(line.strip()))
    ]
    known_map_lines = [line for line in lines if line in REVISION_DATA_MAPS.values()]
    metadata_present = bool(revisions or disabled or known_map_lines)
    if metadata_present:
        if len(revisions) != headers or len(set(revisions)) != 1:
            raise ValueError(
                f"{path}: each dump must declare one consistent reader revision; "
                f"found {revisions!r} for {headers} dump(s)"
            )
        revision = revisions[0]
        if revision not in REVISION_DATA_MAPS:
            raise ValueError(f"{path}: unsupported reader revision {revision}")
        expected_map = REVISION_DATA_MAPS[revision]
        if lines.count(expected_map) != headers:
            raise ValueError(f"{path}: revision-{revision} data_map missing or changed")
        if disabled != [(0x0F, "OK")] * headers:
            raise ValueError(
                f"{path}: each reader dump must report disabled_raw=F,stable=OK; "
                f"found {disabled!r}"
            )
        if revision == 3:
            for label, pattern in (("CE13", DISABLED_CE13), ("CE14", DISABLED_CE14)):
                checks = [
                    (int(match.group(1), 16), match.group(2))
                    for line in lines
                    if (match := pattern.fullmatch(line.strip()))
                ]
                if checks != [(0x0F, "OK")] * headers:
                    raise ValueError(
                        f"{path}: revision-3 {label} release self-test must report "
                        f"stable F for every dump; found {checks!r}"
                    )

    for line_number, text in enumerate(lines, 1):
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


def classify_against(candidate: bytes, baseline: bytes) -> str:
    if len(baseline) != 256:
        raise ValueError(f"comparison raw image must be 256 bytes, got {len(baseline)}")
    invalid = [index for index, value in enumerate(baseline) if value & 0xF0]
    if invalid:
        raise ValueError(
            f"comparison raw image has high-nibble data at address {invalid[0]:02X}"
        )
    if candidate == baseline:
        return "EXACT_MATCH"
    if candidate == bytes(value ^ 0x09 for value in baseline):
        return "EXACT_D0_D3_COMPLEMENT"
    bit_reversed = bytes(
        ((value & 0x01) << 3)
        | ((value & 0x02) << 1)
        | ((value & 0x04) >> 1)
        | ((value & 0x08) >> 3)
        for value in baseline
    )
    if candidate == bit_reversed:
        return "EXACT_BIT_REVERSE"

    differences = [
        index for index, (left, right) in enumerate(zip(baseline, candidate))
        if left != right
    ]
    bit_flips = [
        sum(bool((baseline[index] ^ candidate[index]) & (1 << bit)) for index in differences)
        for bit in range(4)
    ]
    first = differences[0]
    return (
        f"OTHER_DIFFERENCE rows={len(differences)} first={first:02X}:"
        f"{baseline[first]:X}->{candidate[first]:X} "
        f"bit_flips=D0:{bit_flips[0]},D1:{bit_flips[1]},"
        f"D2:{bit_flips[2]},D3:{bit_flips[3]}"
    )


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


def write_outputs(
    directory: Path,
    name: str,
    captures: list[Capture],
    inputs: list[Path],
    independent_capture_count: int | None,
    alias_note: str | None,
    comparison: dict[str, str] | None,
) -> None:
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
        "schema_version": 2,
        "device": "KR556RT4 256x4",
        "name": name,
        "capture_count": len(captures),
        "independent_capture_count": independent_capture_count or len(captures),
        "raw_pin_level_sha256": sha256(raw),
        "active_low_asserted_sha256": sha256(asserted),
        "packing": "256 bytes in address order; low nibble significant; high nibble zero",
        "comparison_rule": "raw pin-level table is authoritative; asserted table is bitwise low-nibble complement",
        "inputs": [{"path": str(path), "sha256": sha256(path.read_bytes())} for path in inputs],
        "captures": [capture.source for capture in captures],
    }
    if alias_note:
        report["alias_note"] = alias_note
    if comparison:
        report["comparison"] = comparison
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {raw_path}, {asserted_path}, {hex_path}, {report_path}")


def self_test() -> None:
    def capture(
        mutate: tuple[int, int] | None = None,
        unstable: int | None = None,
        reader_revision: int | None = None,
    ) -> str:
        lines = []
        if reader_revision is not None:
            lines.extend([
                f"# reader_revision={reader_revision}",
                REVISION_DATA_MAPS[reader_revision],
                "# disabled_raw=F,stable=OK",
            ])
            if reader_revision == 3:
                lines.extend([
                    "# disabled_ce14_raw=F,stable=OK",
                    "# disabled_ce13_raw=F,stable=OK",
                ])
        lines.extend(["# KR556RT4 dump", "# addr,raw_pins,logical_active_low,stable"])
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
        first.write_text(capture(reader_revision=2))
        second.write_text(capture(reader_revision=2))
        captures = validate([first, second], False)
        assert len(captures) == 2

        first.write_text(capture(reader_revision=3))
        second.write_text(capture(reader_revision=3))
        captures = validate([first, second], False)
        assert len(captures) == 2

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

        revision_lines = capture(reader_revision=2).replace(
            "# disabled_raw=F,stable=OK", "# disabled_raw=E,stable=OK"
        )
        first.write_text(revision_lines)
        try:
            parse(first)
            raise AssertionError("bad revision-2 disabled state was accepted")
        except ValueError as error:
            assert "disabled_raw=F" in str(error)

        baseline = bytes(value & 0x0F for value in range(256))
        assert classify_against(baseline, baseline) == "EXACT_MATCH"
        assert (
            classify_against(bytes(value ^ 0x09 for value in baseline), baseline)
            == "EXACT_D0_D3_COMPLEMENT"
        )
        asymmetric = bytes((value ^ (value >> 1)) & 0x0F for value in range(256))
        reversed_asymmetric = bytes(
            ((value & 0x01) << 3)
            | ((value & 0x02) << 1)
            | ((value & 0x04) >> 1)
            | ((value & 0x08) >> 3)
            for value in asymmetric
        )
        assert classify_against(reversed_asymmetric, asymmetric) == "EXACT_BIT_REVERSE"
        other = bytearray(baseline)
        other[0x42] ^= 0x02
        assert classify_against(bytes(other), baseline).startswith(
            "OTHER_DIFFERENCE rows=1 first=42:2->0 bit_flips=D0:0,D1:1,D2:0,D3:0"
        )
    print("RT4 dump validator self-test: PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("captures", nargs="*", type=Path)
    parser.add_argument("--allow-single", action="store_true")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--name", default="rt4")
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
    parser.add_argument(
        "--compare-raw",
        type=Path,
        help="classify the validated capture against a 256-byte low-nibble raw image",
    )
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
    independent_count = args.independent_capture_count or len(captures)
    if independent_count < 1 or independent_count > len(captures):
        parser.error("--independent-capture-count must be between 1 and the parsed capture count")
    if args.alias_note and args.independent_capture_count is None:
        parser.error("--alias-note requires --independent-capture-count")
    print(
        f"RT4 dump validation PASS: {len(captures)} manifest captures, "
        f"{independent_count} independent; raw SHA256 {sha256(raw)}"
    )
    comparison = None
    if args.compare_raw:
        try:
            comparison_raw = args.compare_raw.read_bytes()
            classification = classify_against(raw, comparison_raw)
        except (OSError, ValueError) as error:
            raise SystemExit(f"RT4 dump comparison FAIL: {error}")
        print(f"RT4 raw comparison: {classification}")
        comparison = {
            "path": str(args.compare_raw),
            "sha256": sha256(comparison_raw),
            "classification": classification,
        }
    if args.out_dir:
        write_outputs(
            args.out_dir,
            args.name,
            captures,
            args.captures,
            args.independent_capture_count,
            args.alias_note,
            comparison,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
