#!/usr/bin/env python3
"""Reposition top-edge silk on an already-built .kicad_pcb to match the generator.

Two fixes, mirroring gen_kicad_pcb.py so the hand-maintained routed/source boards
stay consistent with a fresh generation:

  * "FDC OUTPOST" block note -> (255,50), the open band between the transceiver
    row and the lower FDC chips. The old (270,18) overprinted the AX4xx wire-pad
    refdes and an R-bank.
  * X1 / X2 connector bodies -> the y~1.5-6.3 band ABOVE their solder pins
    (toward the top edge). The old y=13-21 rect+label sat below the pins, on the
    board interior, reading as if the connector plugs downward into the board.

Coordinate-targeted, idempotent text surgery. Run:
  apply_topedge_silk.py kicad/juku_routed.kicad_pcb [more boards...]
"""
import re
import sys
from pathlib import Path

# gr_text "LABEL" -> new (x, y). The block-note nudges clear a note printed over
# a neighbouring component's refdes/value (caught by check_silk_overlap.py).
TEXT_MOVES = {
    "FDC OUTPOST": (255, 50),
    "X1": (61, 3.9),
    "X2": (145.5, 3.9),
    "EXPANSION BUS": (62, 33),
    "SERIAL / TAPE": (204, 38),
    "VIDEO TIMING": (96, 189),
}
# gr_rect old (start)->(end)  =>  new (start)->(end)
RECT_MOVES = {
    (15.0, 13.0, 107.0, 21.0): (20.0, 1.5, 102.0, 6.3),      # X1 body
    (118.0, 13.0, 171.5, 21.0): (126.0, 1.5, 165.0, 6.3),    # X2 body
}


def num(x):
    return f"{x:g}"


def move_texts(s):
    n = 0

    def repl(m):
        nonlocal n
        label = m.group("label")
        if label not in TEXT_MOVES:
            return m.group(0)
        x, y = TEXT_MOVES[label]
        n += 1
        return f'(gr_text "{label}"\n\t\t(at {num(x)} {num(y)} {m.group("rot")})'

    s = re.sub(
        r'\(gr_text "(?P<label>[^"]*)"\s*\(at (?P<x>[\d.-]+) (?P<y>[\d.-]+) (?P<rot>[\d.-]+)\)',
        repl, s)
    return s, n


def move_rects(s):
    n = 0

    def repl(m):
        nonlocal n
        key = tuple(float(m.group(i)) for i in range(1, 5))
        if key not in RECT_MOVES:
            return m.group(0)
        x0, y0, x1, y1 = RECT_MOVES[key]
        n += 1
        return (f"(gr_rect\n\t\t(start {num(x0)} {num(y0)})\n"
                f"\t\t(end {num(x1)} {num(y1)})")

    s = re.sub(
        r'\(gr_rect\s*\(start ([\d.-]+) ([\d.-]+)\)\s*\(end ([\d.-]+) ([\d.-]+)\)',
        repl, s)
    return s, n


def main():
    for t in sys.argv[1:] or ["kicad/juku_routed.kicad_pcb"]:
        s = Path(t).read_text(encoding="utf-8")
        s, nt = move_texts(s)
        s, nr = move_rects(s)
        Path(t).write_text(s, encoding="utf-8")
        print(f"{t}: moved {nt} silk label(s), {nr} connector body rect(s)")


if __name__ == "__main__":
    main()
