#!/usr/bin/env python3
"""Regression guard against tofu (missing-glyph) silkscreen.

The replica silk is Cyrillic (chip values such as К573РФ5 / КР580ВА86). If the
silk face lacks the glyphs a text item uses, KiCad renders empty boxes -- which
is exactly how the board previews once shipped, with "GOST type B italic"
(fonts/gost-type-b-italic.ttf, no Cyrillic) selected for Cyrillic text.

This check (a generalization of VJUGA's "enforce a known silk font" test) runs
without KiCad/pcbnew so it is cheap and CI-safe. For every text item on a board
it verifies:

  1. the font face is one of the approved silk faces, and
  2. every character the item draws is present in that face's font file.

Fails (exit 1) listing the offending faces / characters, so a future font or
label change that reintroduces tofu is caught before the previews are regen'd.
"""
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Approved silk faces -> the repo font file that backs them. A silk (face ...)
# not listed here is rejected: we only ship these, and only these are proven to
# carry the Cyrillic the replica needs.
APPROVED_FACES = {
    "GOST CAD KK": ROOT / "fonts" / "gost.ttf",
}

# Boards whose silk feeds the previews / fabrication. Overridable via argv.
DEFAULT_TARGETS = [
    ROOT / "kicad" / "juku.kicad_pcb",
    ROOT / "kicad" / "juku_routed.kicad_pcb",
    ROOT / "kicad" / "juku_routed_candidate.kicad_pcb",
]

# Rendered text items. Reference/Value are the footprint's on-board markings;
# gr_text/fp_text are free silk labels. Other properties (Footprint, Datasheet,
# Description) are metadata and never plotted, so they are deliberately excluded.
_STR = r'"((?:[^"\\]|\\.)*)"'
TEXT_RES = [
    re.compile(r'\(property\s+"(?:Reference|Value)"\s+' + _STR),
    re.compile(r'\(gr_text\s+' + _STR),
    re.compile(r'\(fp_text\s+\w+\s+' + _STR),
]
FACE_RE = re.compile(r'\(face\s+"([^"]*)"')


def font_codepoints(path):
    """Return the set of Unicode codepoints the TrueType font maps (cmap
    formats 4 and 12 -- what these GOST fonts use)."""
    data = path.read_bytes()
    (num_tables,) = struct.unpack(">H", data[4:6])
    cmap_off = None
    for i in range(num_tables):
        rec = 12 + i * 16
        if data[rec:rec + 4] == b"cmap":
            cmap_off = struct.unpack(">I", data[rec + 8:rec + 12])[0]
            break
    if cmap_off is None:
        raise ValueError(f"{path}: no cmap table")
    (num_sub,) = struct.unpack(">H", data[cmap_off + 2:cmap_off + 4])
    cps = set()
    for i in range(num_sub):
        so = struct.unpack(">I", data[cmap_off + 4 + i * 8 + 4:cmap_off + 4 + i * 8 + 8])[0]
        sub = cmap_off + so
        (fmt,) = struct.unpack(">H", data[sub:sub + 2])
        if fmt == 4:
            seg_x2 = struct.unpack(">H", data[sub + 6:sub + 8])[0]
            segc = seg_x2 // 2
            ends = struct.unpack(f">{segc}H", data[sub + 14:sub + 14 + seg_x2])
            starts_off = sub + 14 + seg_x2 + 2
            starts = struct.unpack(f">{segc}H", data[starts_off:starts_off + seg_x2])
            delta_off = starts_off + seg_x2
            deltas = struct.unpack(f">{segc}h", data[delta_off:delta_off + seg_x2])
            range_off = delta_off + seg_x2
            ranges = struct.unpack(f">{segc}H", data[range_off:range_off + seg_x2])
            for k in range(segc):
                for c in range(starts[k], ends[k] + 1):
                    if c == 0xFFFF:
                        continue
                    if ranges[k] == 0:
                        g = (c + deltas[k]) & 0xFFFF
                    else:
                        gi = range_off + k * 2 + ranges[k] + (c - starts[k]) * 2
                        g = struct.unpack(">H", data[gi:gi + 2])[0]
                        if g != 0:
                            g = (g + deltas[k]) & 0xFFFF
                    if g != 0:
                        cps.add(c)
        elif fmt == 12:
            (ngroups,) = struct.unpack(">I", data[sub + 12:sub + 16])
            g0 = sub + 16
            for gi in range(ngroups):
                sc, ec, _ = struct.unpack(">III", data[g0 + gi * 12:g0 + gi * 12 + 12])
                cps.update(range(sc, ec + 1))
    return cps


def unescape(s):
    return s.replace('\\"', '"').replace("\\\\", "\\").replace("\\n", "\n")


def check_board(path):
    text = path.read_text(encoding="utf-8")

    faces = set(FACE_RE.findall(text))
    bad_faces = sorted(f for f in faces if f not in APPROVED_FACES)
    if bad_faces:
        return [f"unapproved silk face(s): {', '.join(bad_faces)} "
                f"(approved: {', '.join(sorted(APPROVED_FACES))})"]

    strings = []
    for rx in TEXT_RES:
        strings += [unescape(m) for m in rx.findall(text)]

    # Characters actually drawn (skip whitespace/control -- no glyph needed).
    used = {ch for s in strings for ch in s if ch > " "}

    errors = []
    # Every approved face present must cover every used character. All text on
    # these boards shares one face, so this is exact; if faces ever diverge the
    # over-approximation only makes the guard stricter (fails safe).
    for face in (faces or {next(iter(APPROVED_FACES))}):
        covered = font_codepoints(APPROVED_FACES[face])
        missing = sorted(ch for ch in used if ord(ch) not in covered)
        if missing:
            shown = ", ".join(f"{ch!r} U+{ord(ch):04X}" for ch in missing)
            errors.append(f"face '{face}' is missing {len(missing)} glyph(s) "
                          f"used on silk: {shown}")
    if not errors:
        n_cyr = sum(1 for ch in used if 0x400 <= ord(ch) <= 0x4FF)
        print(f"  {path.name}: OK ({len(strings)} text items, "
              f"{len(used)} distinct glyphs incl. {n_cyr} Cyrillic)")
    return errors


def main():
    targets = [Path(a) for a in sys.argv[1:]] or DEFAULT_TARGETS
    print("Juku silk glyph-coverage check:")
    all_errors = []
    for t in targets:
        if not t.exists():
            all_errors.append(f"{t}: not found")
            continue
        all_errors += [f"{t.name}: {e}" for e in check_board(t)]
    if all_errors:
        print("FAIL:")
        for e in all_errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("PASS")


if __name__ == "__main__":
    main()
