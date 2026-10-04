# VJUGA rev B — JLCPCB fabrication profile (R5.J1)

Status: **PASS / PROFILE FROZEN**, recorded 2026-08-28. This profile governs the
five independent bare-PCB archives produced at R5.J2. It does not authorize upload or
ordering; `rev-b-five-board-order-plan.md` remains on **ORDER HOLD**.

The machine-readable source is `kicad/revb/jlcpcb-profile.json`; the release gate is
`kicad/revb/check_revb_jlcpcb.py`. The vendor limits and quote selections below
are the retained 2026-08-28 snapshot. Recheck vendor capabilities and the live
quote before release/upload; the checker does not query the vendor.

## Frozen order selections

| Selection | Value |
|---|---|
| Material / thickness | FR-4 / 1.6 mm |
| Outer copper | 1 oz |
| Mask / silk | Green / white |
| Finish | Lead-free HASL |
| Vias | Tented on the four 2-layer designs; Plugged on 4-layer Video (as recorded in the dated quote) |
| Delivery unit | Five separate designs; no panelization |
| Assembly | Bare PCB only; no PCBA files |
| Impedance | None |
| Confirmation | JLCPCB production-file confirmation enabled |
| CPU, Memory, I/O, Backplane | 2 layers |
| Video | 4 layers, JLC7628 standard 1.6-mm stack; signal/GND/VCC/signal |

## Encoded limits and audited exceptions

- Ordinary design tracks and clearance are 0.20/0.20 mm; the profile records
  vendor minima of 0.10/0.10 mm for ordinary 1 oz work.
- Video tracks may narrow to 0.15 mm only on `VID_G` and `HSYNC_N`. The checker
  restricts their nets and widths, not the number of segments.
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
  slots are at least 1.0 mm wide. The profile floor is 1.0-mm silk text with
  0.15-mm strokes; the separate [GOST contract](rev-b-silkscreen-audit.md) requires
  at least 1.5-mm text and 1.6-mm assembly labels.
- The 2026-08-28 live quote freezes five copies of each independent design, FR4 TG135,
  1.6 mm, 1 oz outer copper, 0.5 oz Video inner copper, flying-probe test, regular
  ±0.2-mm outline tolerance and no vendor mark. Two-layer via covering is Tented;
  the four-layer form disables Tented and therefore Video is Plugged.

Protected barrel `J_PWR` is the sole power input; the four-pin USB-TTL console
is data-only. The optional USB4085 power branch is omitted because its specified
land pattern falls below the profile's two-layer PTH ring minimum. See the
[power model](rev-b-five-card-power.md) for the protected input and receipt tests.

## Gate coverage

The checker loads all five routed KiCad sources and verifies:

- exact outlines, thicknesses, copper-layer counts and enabled production layers;
- presence of a zone on each required Video inner layer with its expected
  GND/VCC net; this check alone does not establish plane continuity;
- track widths, default and explicitly allowed local clearances;
- via drills/diameters/rings, PTH rings and plated/non-plated slots;
- minimum visible silk text/stroke geometry;
- total KiCad DRC violations and unconnected items when the `KICAD_CLI`
  environment variable is set. If it is empty, DRC is silently omitted.

With `--package-root`, it also checks ZIP CRCs, exact card-named membership and
required Gerber/Excellon filenames, rejecting extra source, STEP, assembly and
non-production layers. This is archive structure checking, not a rendered-Gerber
review or a comparison of archive hashes to the released candidate.

`--self-test` proves rejection of a 0.08-mm track, undersized via, undersized VGA
ring, open outline, 0.5-mm silk text, STEP-containing archive, missing inner-layer
archive member and the wrong four-layer via-covering selection.

Run from the repository root. Require both tools to include DRC:

```sh
. spinoffs/minimal-vga/kicad/revb/env.sh
revb_have KICAD_CLI && revb_have KICAD_PYTHON && \
  "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_jlcpcb.py \
    --self-test --package-root fab/minimal-vga/revb/package
```

Omit `--package-root` for board-only checking. The Python checker exits 2 if
`pcbnew` cannot be imported; callers may skip it when CAD tools are missing.

The exporter runs this gate before and after packaging. Exact archive members
and hashes are recorded in the [package manifest](rev-b-five-board-package-manifest.json).
Use [the release gate](rev-b-five-board-order-plan.md#final-release-gate) to check
those identities. The [signed pre-upload review](rev-b-five-board-preupload-review.md)
records the independent render/BOM inspection and dated quote.

Official references captured in the JSON profile:

- [JLCPCB capabilities](https://jlcpcb.com/capabilities/Capabilities)
- [Gerber preparation](https://jlcpcb.com/help/article/gerber-files-preparation)
- [KiCad Gerber/drill export](https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-kicad-6)
- [PCB dimensions](https://jlcpcb.com/help/article/pcb-dimensions)
- [Ordering instructions](https://jlcpcb.com/help/article/instructions-for-ordering)
- [Standard four-layer stack-ups](https://jlcpcb.com/quote/pcbOrderFaq/PCB%20Stackup)
