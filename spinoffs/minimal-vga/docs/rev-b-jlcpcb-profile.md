# VJUGA rev B — JLCPCB fabrication profile (R5.J1)

Status: **PASS / PROFILE FROZEN** on 2026-08-28. This profile governs the five
independent bare-PCB archives produced at R5.J2. It does not authorize upload or
ordering; `rev-b-five-board-order-plan.md` remains on **ORDER HOLD**.

The machine-readable source is `kicad/revb/jlcpcb-profile.json`; the release gate is
`kicad/revb/check_revb_jlcpcb.py`. Recheck the live quote and vendor capabilities at
R5.J3 because fab options can change.

## Frozen order selections

| Selection | Value |
|---|---|
| Material / thickness | FR-4 / 1.6 mm |
| Outer copper | 1 oz |
| Mask / silk | Green / white |
| Finish | Lead-free HASL |
| Vias | Tented on the four 2-layer designs; Plugged on 4-layer Video (the live standard 4-layer form disables Tented) |
| Delivery unit | Five separate designs; no panelization |
| Assembly | Bare PCB only; no PCBA files |
| Impedance | None |
| Confirmation | JLCPCB production-file confirmation enabled |
| CPU, Memory, I/O, Backplane | 2 layers |
| Video | 4 layers, JLC7628 standard 1.6-mm stack; signal/GND/VCC/signal |

## Encoded limits and audited exceptions

- Ordinary design tracks and clearance remain 0.20/0.20 mm although JLCPCB lists
  0.10/0.10 mm for ordinary 1 oz work.
- Seven Video neck segments may be 0.15 mm only on `VID_G` and `HSYNC_N`.
- Vias are at least 0.60/0.30 mm diameter/drill. Their 0.15-mm ring equals the
  published multilayer absolute and therefore remains subject to production-file
  confirmation.
- Ordinary PTH rings target at least 0.25 mm on 2-layer boards and 0.20 mm on the
  4-layer board. Exact Video VGA signal pads use the published 4-layer absolute of
  0.15 mm.
- The DS1813's exact inline TO-92 pitch is 1.27 mm. Its pads are enlarged to a
  0.18-mm ring with 0.15-mm local clearance, equal to JLCPCB's 2-layer absolute;
  changing to a wide footprint would require bending the ordered part's leads.
- Plated slots are at least 0.50 mm wide and at least twice as long as wide; non-plated
  slots are at least 1.0 mm wide. Silk text is at least 1.0 mm high with 0.15-mm strokes.
- The 2026-08-28 live quote freezes five copies of each independent design, FR4 TG135,
  1.6 mm, 1 oz outer copper, 0.5 oz Video inner copper, flying-probe test, regular
  ±0.2-mm outline tolerance and no vendor mark. Two-layer via covering is Tented;
  the four-layer form disables Tented and therefore Video is Plugged.

The optional GCT USB4085 power connector failed this audit. Its specified 0.40-mm
holes and 0.70-mm lands at 0.85-mm pitch yield only a 0.15-mm PTH annular ring, below
JLCPCB's published 0.18-mm 2-layer absolute. Enlarging the lands enough would violate
the pitch/clearance geometry, and shrinking the drill would contradict the connector
drawing. Production Rev B therefore omits `J_USBC`, `R_CC1`, `R_CC2`, `F_VBUS` and
`D_USB`; protected barrel `J_PWR` is the sole power input. The four-pin USB-TTL
console remains data-only.

## Gate coverage

The checker loads all five routed KiCad sources and verifies:

- exact outlines, thicknesses, copper-layer counts and enabled production layers;
- Video's dedicated inner GND/VCC planes;
- track widths, default and explicitly allowed local clearances;
- via drills/diameters/rings, PTH rings and plated/non-plated slots;
- minimum visible silk text/stroke geometry;
- total KiCad DRC when `KICAD_CLI` is available;
- exact card-named ZIP membership, required Gerber/Excellon names and absence of
  source, STEP, assembly, paste, courtyard and user layers.

`--self-test` proves rejection of a 0.08-mm track, undersized via, undersized VGA
ring, open outline, 0.5-mm silk text, STEP-containing archive and missing inner plane.
The fresh USB-free backplane regenerates and routes total DRC 0/0 on attempt 1.

Run the board-only profile gate with:

```sh
. spinoffs/minimal-vga/kicad/revb/env.sh
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_jlcpcb.py --self-test
```

R5.J2 passes `--package-root` as well, so the same checker validates the generated
upload archives rather than trusting their filenames by inspection. Exact archive
members and hashes are frozen in `docs/rev-b-five-board-package-manifest.json`.

Official references captured in the JSON profile:

- [JLCPCB capabilities](https://jlcpcb.com/capabilities/Capabilities)
- [Gerber preparation](https://jlcpcb.com/help/article/gerber-files-preparation)
- [KiCad Gerber/drill export](https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-kicad-6)
- [PCB dimensions](https://jlcpcb.com/help/article/pcb-dimensions)
- [Ordering instructions](https://jlcpcb.com/help/article/instructions-for-ordering)
- [Standard four-layer stack-ups](https://jlcpcb.com/quote/pcbOrderFaq/PCB%20Stackup)
- [GCT USB4085 product drawing](https://gct.co/connector/usb4085)
