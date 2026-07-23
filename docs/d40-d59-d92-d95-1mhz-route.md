# D40/D59/D92/D95 1 MHz route review

Status date: 2026-07-23.

Status: **OWNER-CONTINUITY CLOSED / MODEL AND ZERO-OPEN ROUTE GUARDED**

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

## Implemented model correction

The canonical JSON now represents the physical conductor as one `LATCH_B`
net containing:

- D40.11, D37.2, D54.9/.15/.18, and D95.5/.6;
- D59.5, E14.1/.3, and D50.15/D51.15;
- tied D92.2/.3.

`PHI2TTL` is now limited to D35.13, D39.1, D53.4, and its sheet-1 continuation
D30.3. The HDL drives the D59 input and both D92 timing inputs from D40 Q3
instead of the former fixed-high/D35 phase assumptions. The generated
schematic round-trips at 117 mapped instances and 308 matched nets.
The structural Yosys/LVS view applies D59's complementary outputs to D48-D51.
Runnable simulation retains a CPU-only MA-bus scaffold while video uses its
SIM-ONLY second DRAM port; it does not apply an unproved D41/D53 slot schedule
to the behavioral RAS/CAS model.

The PCB migration removes the two obsolete PHI2TTL branches into D92, retains
the explicit D92.2/.3 bottom-copper tie, and merges all former video-enable
copper into `LATCH_B`. The initial correction exposed three real opens. The
two short gaps were repaired directly; the long LATCH_B transaction displaced
29 removable items across nine nets. Restoring the affected routes left one
RAIL_H channel at D78/D79 with no conservative path across all tested 0.125 mm
and 0.10 mm grid offsets. The equivalent source-proved RAIL_H component was
closed instead from D76.1 to D84.1, and four electrically redundant abandoned
stubs were removed under
`ref/routing/d40-1mhz-dangling-prune.json`.

The promoted and candidate boards are byte-identical at this checkpoint:
322 footprints, 2,436 pads, 30,904 copper items, zero connectivity opens,
zero electrical DRC blockers, and zero dangling tracks or vias. The exact
endpoint and direct-tie invariant is executable in
`kicad/check_d40_1mhz_route.py`; the guarded one-shot migration is retained as
`kicad/apply_d40_1mhz_route.py`.

## D96 exclusion

The earlier tentative D96.6 endpoint is **not adopted**. Exact `.009` sheet 3
draws D96.6 `/Q1` only as local feedback to D96.2. D96.6 and D40.11 are both
active outputs, so joining them would be an electrical conflict. Recheck
D96.6 with actual resistance in both probe polarities, preferably at empty
socket pads; do not infer a copper connection from the continuity beeper.
