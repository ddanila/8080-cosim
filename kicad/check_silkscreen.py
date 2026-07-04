#!/usr/bin/env python3
import re
import sys

import pcbnew


SILK_FONT_FACE = "GOST type B italic"
BOARD_SILK_NOTES = (
    "8080 HEART",
    "BOOT ROM FIELD",
    "DRAM MEMORY FIELD",
    "VIDEO TIMING",
    "CLOCK MILL",
    "FDC OUTPOST",
    "SERIAL / TAPE",
    "KEYBOARD SCANNER",
    "POWER EDGE",
    "EXPANSION BUS",
)
REF_RE = re.compile(r"^(D|C|R|VD)\d+$")


def fail(message):
    raise SystemExit(f"Juku silkscreen check: FAIL: {message}")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "kicad/juku.kicad_pcb"
    board = pcbnew.LoadBoard(path)
    text = open(path, encoding="utf-8").read()

    missing_refs = []
    missing_values = []
    checked_refs = 0
    checked_chips = 0
    for fp in board.Footprints():
        ref = fp.GetReference()
        if REF_RE.match(ref):
            checked_refs += 1
            if not fp.Reference().IsVisible():
                missing_refs.append(ref)
        if ref.startswith("D"):
            checked_chips += 1
            if not fp.Value().IsVisible() or not fp.Value().GetText().strip():
                missing_values.append(ref)

    if missing_refs:
        fail(f"hidden component refdes: {', '.join(sorted(missing_refs))}")
    if missing_values:
        fail(f"hidden/missing chip value markings: {', '.join(sorted(missing_values))}")

    for note in BOARD_SILK_NOTES:
        if f'(gr_text "{note}"' not in text:
            fail(f"missing subsystem silk note: {note}")
    if f'(face "{SILK_FONT_FACE}")' not in text:
        fail(f"missing GOST silk font face: {SILK_FONT_FACE}")

    print(
        "Juku silkscreen check: PASS "
        f"({checked_refs} component refdes, {checked_chips} chip markings, "
        f"{len(BOARD_SILK_NOTES)} subsystem notes)"
    )


if __name__ == "__main__":
    main()
