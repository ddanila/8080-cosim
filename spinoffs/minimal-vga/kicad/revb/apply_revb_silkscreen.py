#!/usr/bin/env python3
"""Replace only printable silk text on an already-routed rev B board.

Usage: KICAD_PYTHON apply_revb_silkscreen.py CARD ROUTED SOURCE [OUTPUT]

ROUTED is the reviewed electrical baseline. SOURCE is a fresh gen_revb_pcb.py
output carrying the current board-level text and footprint text styling. The script
refuses any footprint-placement mismatch and proves that tracks, vias, zones, pads,
nets, drills, and non-text drawings are untouched before saving OUTPUT (or ROUTED).
"""
import hashlib
import json
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
STYLE = json.load(open(os.path.join(HERE, "silkscreen-style.json")))
SILK = (pcbnew.F_SilkS, pcbnew.B_SilkS)


def visible_silk_texts(container):
    return [item for item in container
            if isinstance(item, pcbnew.PCB_TEXT) and item.IsVisible()
            and item.GetLayer() in SILK]


def vec(v):
    return (v.x, v.y)


def electrical_state(board):
    """Stable in-memory identity for everything this operation must not alter."""
    footprints = []
    for fp in sorted(board.GetFootprints(), key=lambda x: x.GetReference()):
        pads = []
        for pad in sorted(fp.Pads(), key=lambda x: x.GetNumber()):
            pads.append((str(pad.GetNumber()), str(pad.GetNetname()),
                         str(pad.GetLayerSet().FmtHex()),
                         vec(pad.GetPosition()), vec(pad.GetSize()),
                         vec(pad.GetDrillSize()), int(pad.GetAttribute())))
        footprints.append((str(fp.GetReference()), vec(fp.GetPosition()),
                           round(fp.GetOrientationDegrees(), 6), fp.IsFlipped(), pads))
    tracks = []
    for item in board.GetTracks():
        row = [str(item.GetClass()), str(item.GetNetname()), item.GetLayer()]
        if isinstance(item, pcbnew.PCB_VIA):
            row += [item.GetWidth(item.TopLayer()), vec(item.GetPosition()), item.GetDrillValue(),
                    item.TopLayer(), item.BottomLayer()]
        else:
            row += [item.GetWidth(), vec(item.GetStart()), vec(item.GetEnd())]
        tracks.append(tuple(row))
    drawings = []
    for item in board.GetDrawings():
        if isinstance(item, pcbnew.PCB_TEXT) and item.GetLayer() in SILK:
            continue
        box = item.GetBoundingBox()
        drawings.append((str(item.GetClass()), item.GetLayer(), box.GetX(), box.GetY(),
                         box.GetWidth(), box.GetHeight()))
    return {
        "footprints_and_pads": footprints,
        "tracks_and_vias": sorted(tracks),
        "non_silk_drawings": sorted(drawings),
        "zone_count": len(list(board.Zones())),
        "copper_layers": board.GetCopperLayerCount(),
    }


def electrical_fingerprint(state):
    return hashlib.sha256(repr(state).encode()).hexdigest()


def copy_text_style(dst, src):
    dst.SetText(src.GetText())
    dst.SetTextPos(src.GetTextPos())
    dst.SetTextAngle(src.GetTextAngle())
    dst.SetTextSize(src.GetTextSize())
    dst.SetTextThickness(src.GetTextThickness())
    dst.SetLayer(src.GetLayer())
    dst.SetMirrored(src.IsMirrored())
    dst.SetItalic(src.IsItalic())
    dst.SetBold(src.IsBold())
    dst.SetFontProp(src.GetFontName())


def main():
    if len(sys.argv) not in (4, 5):
        raise SystemExit(__doc__)
    card, routed_path, source_path = sys.argv[1:4]
    output_path = sys.argv[4] if len(sys.argv) == 5 else routed_path
    routed = pcbnew.LoadBoard(routed_path)
    source = pcbnew.LoadBoard(source_path)
    before_state = electrical_state(routed)
    before = electrical_fingerprint(before_state)

    rf = {fp.GetReference(): fp for fp in routed.GetFootprints()}
    sf = {fp.GetReference(): fp for fp in source.GetFootprints()}
    if set(rf) != set(sf):
        raise SystemExit(f"{card}: footprint reference sets differ")
    for ref in sorted(rf):
        rp, sp = rf[ref].GetPosition(), sf[ref].GetPosition()
        if (abs(rp.x - sp.x) > pcbnew.FromMM(0.001) or
                abs(rp.y - sp.y) > pcbnew.FromMM(0.001) or
                abs(rf[ref].GetOrientationDegrees() -
                    sf[ref].GetOrientationDegrees()) > 1e-6 or
                rf[ref].IsFlipped() != sf[ref].IsFlipped()):
            raise SystemExit(f"{card}: {ref} placement differs from silk source")

        old = {(t.GetText(), t.GetLayer()): t
               for t in visible_silk_texts(rf[ref].GraphicalItems())}
        new = {(t.GetText(), t.GetLayer()): t
               for t in visible_silk_texts(sf[ref].GraphicalItems())}
        if set(old) != set(new):
            raise SystemExit(f"{card}: {ref} visible footprint-text set differs")
        for key in old:
            copy_text_style(old[key], new[key])

    for item in list(visible_silk_texts(routed.GetDrawings())):
        routed.Delete(item)
    for item in visible_silk_texts(source.GetDrawings()):
        replacement = pcbnew.PCB_TEXT(routed)
        copy_text_style(replacement, item)
        routed.Add(replacement)

    after_state = electrical_state(routed)
    after = electrical_fingerprint(after_state)
    if before != after:
        changed = [key for key in before_state if before_state[key] != after_state[key]]
        raise SystemExit(f"{card}: non-silkscreen fingerprint changed in {changed}: "
                         f"{before} -> {after}")
    pcbnew.SaveBoard(output_path, routed)
    count = len(visible_silk_texts(routed.GetDrawings())) + sum(
        len(visible_silk_texts(fp.GraphicalItems())) for fp in routed.GetFootprints())
    print(f"{card}: applied {count} {STYLE['font_family']} silk labels; "
          f"electrical fingerprint {after} unchanged")


if __name__ == "__main__":
    main()
