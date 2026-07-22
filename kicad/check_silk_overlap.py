#!/usr/bin/env python3
"""Detect illegible silkscreen NOTES on a built board (needs pcbnew).

A generalization of the VJUGA rev-A placement check, scoped to the defect the
main Juku board actually hit: a free silk NOTE -- a functional-block label such
as "FDC OUTPOST", "SERIAL / TAPE", "X1" -- landing on top of *other silk text*
so both become unreadable. (The original board had "FDC OUTPOST" printed across
the AX4xx wire-pad refdes.) It flags, in millimetres:

  1. a note overlapping a footprint's visible reference/value text, and
  2. a note overlapping another note.

Deliberately NOT flagged, because they are how a dense factory board reads and
would swamp the real signal (a block label sitting over the components it names
is its whole purpose):
  * note-over-component-body (a label belongs inside its block);
  * refdes/value pairs among tightly packed passives;
  * anything involving the factory wire-link (W*) footprints, whose bodies span
    the board, or the dense AX*/X* connector-contact refdes (<=2.54 mm pitch).

Hidden text (e.g. the value on an unpopulated, value-hidden socket) is ignored
since it is not drawn. Exit non-zero on any collision. Run:
  check_silk_overlap.py [board.kicad_pcb]   (default kicad/juku_routed.kicad_pcb)
"""
import re
import sys

import pcbnew

OVERLAP_MM = 0.3            # linear overlap on BOTH axes to count as a collision
# Owners whose silk text is expected to be dense/structural and is not treated
# as a legibility defect: factory wire links and the connector-contact lands.
EXCLUDED_OWNER = re.compile(r'^(W\d+|AX\d+|X\d+)$')


def box(bb):
    return (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
            pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))


def collide(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w > OVERLAP_MM and h > OVERLAP_MM


def text_box(item):
    try:
        return box(item.GetTextBox())
    except Exception:
        return box(item.GetBoundingBox())


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "kicad/juku_routed.kicad_pcb"
    board = pcbnew.LoadBoard(path)

    fp_texts = []        # (label, box) -- visible silk refdes/value, dense owners excluded
    excluded = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if EXCLUDED_OWNER.match(ref):
            excluded += 1
            continue
        for field in (fp.Reference(), fp.Value()):
            if field.IsVisible() and field.GetText().strip() \
               and field.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                fp_texts.append((f'{ref} "{field.GetText()}"', text_box(field)))

    notes = []           # (label, box)
    for d in board.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetText().strip() \
           and d.GetLayer() == pcbnew.F_SilkS:
            notes.append((f'note "{d.GetText()}"', text_box(d)))

    errors = []
    # (1) a note overlapping a footprint's visible refdes/value text
    for nlabel, nbox in notes:
        for flabel, fbox in fp_texts:
            if collide(nbox, fbox):
                errors.append(f"{nlabel} overlaps {flabel}")
    # (2) a note overlapping another note
    for i in range(len(notes)):
        for j in range(i + 1, len(notes)):
            if collide(notes[i][1], notes[j][1]):
                errors.append(f"{notes[i][0]} overlaps {notes[j][0]}")

    if excluded:
        print(f"(excluded {excluded} structural W*/AX*/X* silk owners "
              f"-- wire links and dense connector-contact lands)")
    if errors:
        print(f"Juku silk overlap check: FAIL ({len(set(errors))} collisions)")
        for e in sorted(set(errors)):
            print(f"  {e}")
        raise SystemExit(1)
    print(f"Juku silk overlap check: PASS "
          f"({len(notes)} notes vs {len(fp_texts)} silk texts, no note collisions)")


if __name__ == "__main__":
    main()
