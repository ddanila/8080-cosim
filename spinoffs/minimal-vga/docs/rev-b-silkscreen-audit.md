# VJUGA rev B — five-board silkscreen audit

Status: **PASS / RELEASE CANDIDATE REFRESHED / ORDER HOLD**, 2026-08-28.

This audit covers the printable front and bottom silkscreen of CPU, Memory, I/O,
Backplane, and Video. The typography changes fabrication Gerbers, so the former R5.J2
archive hashes are superseded even though no electrical or mechanical geometry moved.

## Finding and correction

The previous candidate was electrically clean but visually inconsistent:

- all printable labels used KiCad's default stroke font rather than the requested
  GOST family;
- CPU, Memory, and I/O exposed only two board-level labels each, while Video had IC
  references and Backplane had interface text;
- four bottom silks were empty despite connector reversal being a recorded residual
  risk;
- I/O DNP positions and Backplane slot purpose were not explicit on the board.

The corrected style is machine-readable in `kicad/revb/silkscreen-style.json`:

| Property | Frozen value |
|---|---|
| Typeface | `GOST CAD KK`, Book |
| Font file SHA-256 | `14f22140e5ac3d581830b903d62d2fdd24392a480ab1284a3cbd16139d6e8d2d` |
| Ordinary / assembly text | 1.5 mm |
| Board title | 1.8 mm |
| Safety text | 1.5 mm |
| Front card orientation | `PIN 1 >`, pointing toward physical bus pad 1 |
| Bottom card orientation | `< PIN 1`, mirrored and pointing toward pad 1 in the bottom view |

The font is a local generation dependency and is not redistributed here. Generation
uses Fontconfig to require the exact family/style/file hash rather than accepting a
fallback. KiCad converts the text to cached vector outlines in the routed board and
Gerber output, so JLCPCB does not need the font file.

## Content result

| Board | Visible GOST silk text items | Assembly and safety additions |
|---|---:|---|
| CPU | 7 | U1/U2, J_DIAG, consistent title/safety text, two-face pin-1 cue |
| Memory | 9 | U1/U2/U3, J_NOP/J_OBS, consistent title/safety text, two-face pin-1 cue |
| I/O | 14 | all seven U refs; U4/U5/U6 and J_KBD explicitly DNP; baud/select labels and two-face pin-1 cue |
| Backplane | 15 | numbered slots, slot 4 keep-empty and slot 5 Video notices, TTL warning/pinout, title/safety text; U_RST moved to clear bottom silk |
| Video | 29 | all 23 U refs, VGA pin 1, 4-layer/title/safety text, two-face bus pin-1 cue |

The GOST Book face needs 1.5 mm text height to keep its thinnest glyph strokes above
KiCad's fabrication check. The earlier 1.0–1.2 mm trial was rejected because every
TrueType label produced `text_thickness` warnings; 1.5 mm clears them without fake
bold styling.

## Verification

- `check_revb_pcb.py` rejects a missing/mixed font, text below 1.5 mm, inconsistent
  title/safety hierarchy, missing IC/DNP/slot labels, or a wrong-side pin-1 cue.
- `apply_revb_silkscreen.py` imports only reviewed text from a fresh generator output
  into each routed release board. It refuses footprint-placement differences and
  proves a non-silkscreen fingerprint covering footprints/pads, tracks/vias, zones,
  nets, drills, copper layers, and non-silk drawings is unchanged.
- All five routed boards pass KiCad total DRC with zero violations and zero
  unconnected items after the transplant.
- The normal top SVGs and new mirrored `*-bottom.svg` files under `docs/revb-previews/`
  were inspected at original resolution. Titles form one hierarchy, labels are
  readable and consistently slanted, pin-1 arrows point toward the connector on both
  faces, and no text is clipped, crowded against an edge, or covered by solder mask.
- `export_fab.sh` and `revb_tier_suite.sh` now run the five-card silk contract before
  packaging or release regression.
- The refreshed five archives produced 42 separately rendered production layers/
  drills and 10 top/bottom composites. Every silk is nonblank; the montage review
  found no clipping, pad collision, crowding, translation, or wrong-side cue.
- The complete rev-B regression passed after the refresh, including both modular
  decode boots and the real-chip TTL Video `/WAIT` boot against the cosim oracle.

The resulting Gerbers and hashes were regenerated and independently rendered as the
new R5.J2/J3 candidate recorded in `rev-b-five-board-package-manifest.json` and
`rev-b-five-board-preupload-review.md`. The existing `ORDER HOLD` remains in force.
