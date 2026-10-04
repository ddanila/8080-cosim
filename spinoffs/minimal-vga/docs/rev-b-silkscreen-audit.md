# VJUGA rev B — five-board silkscreen audit

Status: **PASS / CURRENT CANDIDATE REVIEWED / ORDER HOLD**, 2026-08-29.

This audit covers the printable front and bottom silkscreen of CPU, Memory, I/O,
Backplane, and Video. The reviewed package is identified by
[the package manifest](rev-b-five-board-package-manifest.json).

## Style contract

The style is defined in `kicad/revb/silkscreen-style.json`:

| Property | Frozen value |
|---|---|
| Typeface | `GOST CAD KK`, Book |
| Font file SHA-256 | `14f22140e5ac3d581830b903d62d2fdd24392a480ab1284a3cbd16139d6e8d2d` |
| Ordinary interface text | 1.5 mm |
| Ref + value assembly text | 1.6 mm |
| Board title | 1.8 mm |
| Safety text | 1.5 mm |
| Front card orientation | `PIN 1 >`, pointing toward physical bus pad 1 |
| Bottom card orientation | `< PIN 1`, mirrored and pointing toward pad 1 in the bottom view |

The font is included at [`fonts/gost.ttf`](../../../fonts/gost.ttf); install it
locally as described in [the font guide](../../../fonts/README.md). Generation
uses Fontconfig to require the exact family/style/file hash rather than accepting a
fallback. KiCad converts the text to cached vector outlines in the routed board and
Gerber output, so JLCPCB does not need the font file.

## Content result

Every physical footprint has a same-side assembly marking containing both its
reference and fitted value or functional role. This includes resistances,
capacitances, oscillator frequencies, exact logic/device families, connector roles,
wire-link gauge and the seven C10 positions fitted in the first system. The
controlled vocabulary and exact value spellings are in `kicad/revb/assembly-markings.json`.

| Board | Physical ref+value labels | Total visible GOST text items | Examples |
|---|---:|---:|---|
| CPU | 7 | 11 | `U1 Z80`, `U2 2.000MHz`, `C1 100nF`, `J_DIAG DIAG HEADER` |
| Memory | 10 | 14 | `U1 27C256`, `U2 AS6C1008`, `U3 ATF22V10`, all bypass capacitors |
| I/O | 46 | 51 | every fitted IC, capacitor, resistor, connector, jumper, test point and POST indicator; compact functional values distinguish PIT, POST, clock and sound parts |
| Backplane | 41 | 55 | every pull-up/value and protected-power/serial part plus all ten slot connectors and the bottom `U_RST` pinout cue |
| Video | 54 | 60 | all 23 ICs, 23 bypass capacitors, RGB resistors, oscillator, VGA and bulk capacitor |

The actual reference `R_BRQ` is printed `R_BRq`: this is the sole case-only display
override because this installed GOST face's uppercase `Q` contains a sub-0.15-mm
segment even at oversized text. Lowercase `q` preserves an unambiguous reference at
the common 1.6-mm height and clears fabrication DRC; the mapping is machine-checked.

The GOST Book face needs at least 1.5 mm text height to keep its thinnest ordinary
glyph strokes above KiCad's fabrication check. Assembly labels use 1.6 mm for
denser values with a little extra visual weight and margin.

## Verification

The DRC, visual inspection, archive rendering, and regression results below are
the recorded 2026-08-29 review; rerun the applicable checks after changing a board.

- `check_revb_pcb.py` rejects a missing/mixed font, undersized text, inconsistent
  title/safety hierarchy, any missing/duplicated/wrong-side ref+value or declared DNP label,
  missing slot labels, or a wrong-side pin-1 cue. It exits successfully with a
  `SKIP` message if `pcbnew` cannot be imported; that is not a validated board.
- `apply_revb_silkscreen.py` imports only reviewed text from a fresh generator output
  into each routed release board. It refuses footprint-placement differences and
  proves a non-silkscreen fingerprint covering footprints/pads, tracks/vias, zones,
  nets, drills, copper layers, and non-silk drawings is unchanged.
- All five routed boards pass KiCad total DRC with zero violations and zero
  unconnected items after the transplant.
- The normal top SVGs and mirrored `*-bottom.svg` files under `docs/revb-previews/`,
  plus bare-board top/bottom PNG assembly plots, were inspected at original
  resolution. Labels are readable, pin-1 arrows point correctly, and no text is
  clipped, crowded against an edge, crossed by other silk, or covered by solder mask.
- `kicad/revb/export_fab.sh` and `sim/revb_tier_suite.sh` run the five-card silk
  contract when a KiCad Python interpreter is available; otherwise these checks
  are skipped.
- The refreshed five archives produced 42 separately rendered production layers/
  drills and 10 top/bottom composites. Every silk is nonblank; the montage review
  found no clipping, pad collision, crowding, translation, or wrong-side cue.
- The complete rev-B regression passed after the refresh, including both modular
  decode boots and the real-chip TTL Video `/WAIT` boot against the cosim oracle.

The existing **ORDER HOLD** remains in force until the owner explicitly authorizes
the exact hashes in the package manifest for upload.
