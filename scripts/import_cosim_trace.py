#!/usr/bin/env python3
"""Adapt a bounded Juku TYPE/address/data bus capture to dac-trace-1."""
import argparse
import hashlib
import json
from pathlib import Path


def convert(source, rom, expected):
    if type(expected) is not int or not 0 < expected <= 1000000:
        raise ValueError("expected event count must be 1..1000000")
    events = []
    for line in source.read_text().splitlines():
        fields = line.split()
        if len(fields) != 3 or fields[0] not in {"MR", "MW", "IR", "IW", "IA"}:
            raise ValueError(f"malformed bus event: {line!r}")
        address, data = int(fields[1], 16), int(fields[2], 16)
        if not 0 <= address <= 65535 or not 0 <= data <= 255:
            raise ValueError("bus address/data out of bounds")
        events.append(dict(epoch=0, kind=fields[0], address=address, data=data,
                           cycle=0, source=0, master=0, space=0, offset=0))
    if len(events) != expected:
        raise ValueError(f"incomplete capture: expected {expected} events, got {len(events)}")
    firmware = rom.read_bytes()
    header = dict(schema="dac-trace-1", machine="juku", enabled=True, complete=True,
                  scope="explicit-event-window", events=expected,
                  profile={"step": "access", "clock_hz": None, "trace": "logical-access"},
                  inputs={"firmware:0": {"size": len(firmware), "sha256": hashlib.sha256(firmware).hexdigest()}})
    return [header, *events]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--events", type=int, required=True)
    args = parser.parse_args()
    try:
        records = convert(args.source, args.rom, args.events)
        with args.output.open("x") as stream:
            for record in records:
                stream.write(json.dumps(record, sort_keys=True) + "\n")
    except (ValueError, OSError) as error:
        parser.exit(2, f"{error}\n")


if __name__ == "__main__":
    main()
