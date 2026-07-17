#!/usr/bin/env python3
"""Detect silk/placement collisions on the generated Rev-A board.

Runs under the KiCad Python (needs pcbnew). Loads a generated .kicad_pcb and
flags, in millimetres:

  1. component bodies (silk + pads) that overlap each other;
  2. a silk text label (a part's reference/value, or a standalone label such as
     the board title/block names) sitting on top of a *different* component;
  3. two silk text labels overlapping each other (e.g. a block title landing on
     a nearby part's designator);
  4. a component that straddles a functional-block outline boundary (half in a
     labelled block it does not belong to -- e.g. the CPU poking into POWER).

This is the automatic version of eyeballing the silk preview. Exit non-zero if
any collision is found.
"""
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_rev_a_pcb as gen  # for SILK_BLOCK_OUTLINES / SILK_BLOCK_LABELS

# Minimum linear overlap (mm) on BOTH axes to count as a real collision, so a
# footprint merely touching a neighbour's edge does not raise noise.
OVERLAP_MM = 0.3


def box(bbox):
    return (
        pcbnew.ToMM(bbox.GetLeft()), pcbnew.ToMM(bbox.GetTop()),
        pcbnew.ToMM(bbox.GetRight()), pcbnew.ToMM(bbox.GetBottom()),
    )


def overlap(a, b):
    """Linear overlap (w, h) in mm of two (l, t, r, b) boxes; <=0 means apart."""
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w, h


def collide(a, b):
    w, h = overlap(a, b)
    return w > OVERLAP_MM and h > OVERLAP_MM


def text_box(item):
    try:
        return box(item.GetTextBox())
    except Exception:
        return box(item.GetBoundingBox())


def contains(outer, inner, margin=0.3):
    return (inner[0] >= outer[0] - margin and inner[1] >= outer[1] - margin
            and inner[2] <= outer[2] + margin and inner[3] <= outer[3] + margin)


# Standalone silk texts that are intentionally placed on a component (connector
# pin labels), so overlap with that component is expected, not a collision.
INTENDED_PIN_LABELS = (
    {t for t, *_ in gen.POWER_INPUT_PIN_LABELS}
    | gen.CONNECTOR_PIN_LABEL_TEXTS
    | {"FUSE"}
)

# Board-edge connectors are meant to sit at the board/block boundary (e.g. the
# USB-C power receptacle overhangs the edge), so their block-straddle is expected.
EDGE_CONNECTORS = {"J3"}


def main():
    pcb = sys.argv[1] if len(sys.argv) > 1 else "/tmp/rev-a.kicad_pcb"
    board = pcbnew.LoadBoard(pcb)

    bodies = {}          # ref -> body box (silk + pads, no text)
    texts = []           # (label, box, owner_ref_or_None)
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        bodies[ref] = box(fp.GetBoundingBox(False, False))
        for field in (fp.Reference(), fp.Value()):
            if field.IsVisible() and field.GetText().strip():
                texts.append((f"{ref} “{field.GetText()}”", text_box(field), ref))

    for d in board.GetDrawings():
        if not (isinstance(d, pcbnew.PCB_TEXT) and d.GetText().strip()):
            continue
        if d.GetLayer() != pcbnew.F_SilkS:      # ignore back-side / non-front silk
            continue
        if d.GetText() in INTENDED_PIN_LABELS:  # connector pin labels sit on the part by design
            continue
        texts.append((f"silk “{d.GetText()}”", text_box(d), None))

    errors = []

    refs = sorted(bodies)
    for i in range(len(refs)):
        for j in range(i + 1, len(refs)):
            if collide(bodies[refs[i]], bodies[refs[j]]):
                w, h = overlap(bodies[refs[i]], bodies[refs[j]])
                errors.append(f"body overlap: {refs[i]} & {refs[j]} ({w:.1f}x{h:.1f} mm)")

    for label, tbox, owner in texts:
        for ref, bbox in bodies.items():
            if ref == owner:
                continue
            if not collide(tbox, bbox):
                continue
            # A *standalone* silk label fully inside a body is an intended in-part
            # label (connector pin names, etc.). But a footprint's own ref/value
            # field landing inside a DIFFERENT component is a real, unreadable
            # clash -- e.g. a tightly-packed resistor's designator printed on top
            # of its neighbour -- so containment is not a free pass for owned text.
            if owner is None and contains(bbox, tbox):
                continue
            errors.append(f"label {label} overlaps component {ref}")

    # Silk text vs silk text (sign collisions), skipping a part's own ref+value.
    for i in range(len(texts)):
        la, ba, oa = texts[i]
        for j in range(i + 1, len(texts)):
            lb, bb, ob = texts[j]
            if oa is not None and oa == ob:
                continue
            if collide(ba, bb):
                errors.append(f"silk-text overlap: {la} & {lb}")

    # Straddle: a component body OR a silk label that crosses a block outline
    # (partly in, partly out) sits on the border line. Fully-inside / fully-out
    # is fine. This catches a refdes printed on top of a block frame (e.g. a
    # DIP's side-printed designator landing on the block's left edge).
    # Only component bodies are checked for straddle: block titles now sit ON the
    # frame's top border by design, and part designators near a frame are handled
    # by the label-vs-component / text-vs-text checks above.
    straddle_items = [(ref, bbox) for ref, bbox in bodies.items()
                      if ref not in EDGE_CONNECTORS]
    # Block outlines are computed from the placed parts (the module-level
    # SILK_BLOCK_OUTLINES is empty until build time), matching how the generator
    # and check_rev_a_pcb.py derive them.
    block_outlines = gen.compute_block_outlines(
        {fp.GetReference(): fp for fp in board.GetFootprints()}
    )
    for name, (l, t, r, b) in block_outlines.items():
        rect = (l, t, r, b)
        for who, bbox in straddle_items:
            w, h = overlap(bbox, rect)
            if w > OVERLAP_MM and h > OVERLAP_MM:
                inside = bbox[0] >= l - 0.2 and bbox[1] >= t - 0.2 and bbox[2] <= r + 0.2 and bbox[3] <= b + 0.2
                if not inside:
                    errors.append(f"{who} straddles block '{gen.SILK_BLOCK_LABELS[name]}' boundary")

    if errors:
        print(f"Rev A placement check: FAIL ({len(errors)} collisions)")
        for e in sorted(set(errors)):
            print(f"  {e}")
        return 1
    print(f"Rev A placement check: PASS ({len(bodies)} components, no silk collisions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
