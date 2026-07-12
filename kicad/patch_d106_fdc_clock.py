#!/usr/bin/env python3
"""Assign the photo-proven D106.7 -> D93.24 FDC clock net.

The source placements still need a coherent FDC-quadrant reroute, so this
idempotent patch deliberately assigns the two physical endpoints without
inventing copper between the current footprint locations. The resulting
airwire is an honest routing obligation.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "kicad/juku.kicad_pcb"
NET_NAME = "FDC_CLK_1M"
NET_CODE = 359
PAD_UUIDS = {
    "D106.7": "e68aa157-55c0-4938-8575-afd143aa8757",
    "D93.24": "05af8cf4-eaa3-4da2-b73d-9cdd1fbed1b8",
}


def main() -> None:
    text = BOARD.read_text(encoding="utf-8")
    net_line = f'\t(net {NET_CODE} "{NET_NAME}")'
    if net_line not in text:
        marker = '\t(net 358 "D94_EN_BOUNDARY")'
        if marker not in text:
            raise SystemExit("last guarded source net is absent; allocate a fresh net code")
        text = text.replace(marker, marker + "\n" + net_line, 1)
    pad_net = f'\t\t\t(net {NET_CODE} "{NET_NAME}")'
    for endpoint, uuid in PAD_UUIDS.items():
        marker = f'\t\t\t(uuid "{uuid}")'
        if marker not in text:
            raise SystemExit(f"{endpoint} guarded pad UUID absent")
        prefix = text[:text.index(marker)]
        pad_start = prefix.rfind('\n\t\t(pad "')
        if pad_start < 0:
            raise SystemExit(f"{endpoint} pad start absent")
        block = text[pad_start:text.index(marker) + len(marker)]
        if pad_net not in block:
            text = text.replace(marker, pad_net + "\n" + marker, 1)
    BOARD.write_text(text, encoding="utf-8")
    print(f"assigned {NET_NAME} to D106.7 and D93.24 without reserializing {BOARD}")


if __name__ == "__main__":
    main()
