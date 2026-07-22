# D40/D59/D92/D95 1 MHz route review

Status date: 2026-07-22.

Status: **OWNER-CONTINUITY CLOSED / SOURCE-MODEL CORRECTION REQUIRED**

This note records the long timing trace measured on the target `.009` board
and reconciles it with both recovered electrical-schematic revisions. It
supersedes the earlier interpretation that left D59.5 without a dynamic source
and placed D92.2/.3 on the separately drawn `PHI2TTL` conductor.

## Measured route

The owner reports powered-off continuity along the following chain:

```text
D40.11 (КР531ИЕ17 Q3, 1 MHz)
  -> D59.5 (КР531ЛН1 input)
  -> D92.2 (К555ЛЕ4 input)
  -> D95.5 + D95.6 (К555КП12 inputs D01/D00)
```

The same session confirms the complementary address-mux enable endpoints:

```text
D59.5 -> D51.15 /G       D59.6 -> D48.15 /G
```

The factory drawings already extend those local branches to D50.15 and
D49.15 through E14 and E13 respectively. On sheet 2, D92.2 and D92.3 are
visibly tied together; the new continuity closes their previously ambiguous
long source onto D40.11.

## Drawing cross-check

- Exact-revision `.009` sheet 2 detail
  `ref/photos/dgsh5-109-009-e3/PXL_20260718_101908284.jpg` labels D40 Q3/pin
  11 as `1MHz (3)`. The adjacent Q2/pin12 branch belongs to the separately
  drawn 2 MHz/D35 phase-shaping path.
- Exact-revision `.009` sheet 2 detail
  `ref/photos/dgsh5-109-009-e3/PXL_20260718_101911242.jpg` draws D59 section
  5->6 between the E14 video and E13 CPU mux-enable islands.
- Exact-revision `.009` sheet 2 detail
  `ref/photos/dgsh5-109-009-e3/PXL_20260718_101921033.MP.jpg` visibly ties
  D92 pins 2 and 3 before their conductor enters the long timing bundle.
- Exact-revision `.009` sheet 3 detail
  `ref/photos/dgsh5-109-009-e3/PXL_20260718_101637906.jpg` labels the arriving
  rail `1MHz (2)` and explicitly draws the external short between D95.5 and
  D95.6.
- The higher-resolution `.006` sheet 2 in
  `ref/schematics/juku_es101_processor_module.pdf` shows the same D40 divider,
  D59 mux-enable inverter, and D92 timing-gate topology.

D95 pins 5 and 6 are independent КП12 data inputs; they are not joined inside
the IC. Their short is intentional board copper, as the sheet-3 junction shows.

## Functional interpretation

D40.11 supplies the 1 MHz memory-slot clock. D59.5 applies that phase directly
to the active-low D50/D51 video-mux enables; D59.6 supplies the complement to
the active-low D48/D49 CPU-mux enables. The two mux banks therefore alternate
ownership of the shared DRAM address bus. D92.2/.3 use the same slot phase when
qualifying RAM reads and writes. D95 duplicates that 1 MHz source on two mux
input codes, just as its pins 3/4 duplicate the 2 MHz source.

This is a coherent single-driver net: D40.11 is the output, while D59.5,
D92.2/.3, and D95.5/.6 are inputs.

## Required model correction

The current source model still represents this physical conductor as three
separate nets:

- `LATCH_B`: D40.11, D37.2, D54.9/.15/.18, and D95.5/.6;
- `VID_MUX_G`: D59.5, E14.1/.3, and D50.15/D51.15;
- `PHI2TTL`: currently includes D92.2/.3.

The next atomic connectivity update must merge the first two groups, move
D92.2/.3 onto that 1 MHz net, and re-audit the D35 2 MHz/`PHI2TTL` source-side
pin attribution. HDL must then drive D59.5 from D40 Q3 instead of its temporary
TTL-high fallback. Source, schematic, routed boards, reports, LVS, DRC, and the
zero-open fabrication manifests must be regenerated together; this finding
therefore reopens that part of the P0 connectivity/routing gate until the
atomic update lands.

## D96 exclusion

The earlier tentative D96.6 endpoint is **not adopted**. Exact `.009` sheet 3
draws D96.6 `/Q1` only as local feedback to D96.2. D96.6 and D40.11 are both
active outputs, so joining them would be an electrical conflict. Recheck
D96.6 with actual resistance in both probe polarities, preferably at empty
socket pads; do not infer a copper connection from the continuity beeper.
