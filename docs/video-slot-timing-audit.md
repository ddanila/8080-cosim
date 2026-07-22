# Video slot timing audit

Status: **VIDEO SLOT TIMING AUDITED / PHYSICAL SLOT SCHEDULE PENDING**

This generated audit tracks the remaining faithful-video boundary: replacing the
runnable sim-only framebuffer read path with the faithful КП14/ИД7/АГ3/РЕ3
shared-DRAM video slot schedule.

## Command

```sh
python3 scripts/report_video_slot_timing_audit.py
```

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Runnable raster geometry is guarded | PASS | `docs/video-timing-reference.md` / `sync/video_timing_check.sh` |
| Runnable byte-to-pixel readout is guarded | PASS | `docs/video-readout-readiness.md` / `sync/video_readout_check.sh` |
| ROM-programmed autonomous raster timing is guarded | PASS | `docs/video-pit-timing.md`: D54/D55/D56/D34_SYNC timing |
| Physical D42/D43 ИР16 serializers are identified in the board model | PASS | `kicad/juku.board.json` D42/D43 identities |
| D41/D42/D43 ИР16 primitive semantics are datasheet-guarded | PASS | `docs/ir16-readiness.md`: LD/SH, clock edge, and OC behavior |
| Physical serializer instances exist in `juku_top` | PASS | `hdl/juku_top.v` |
| Physical CPU/video mux and D53 decode instances exist in `juku_top` | PASS | `hdl/juku_top.v` |
| D48-D52 КП14 inversion and three-state behavior are datasheet-guarded | PASS | `docs/kp14-readiness.md`: SN74LS/S258 truth table |
| D59 complementary CPU/video mux-enable inverter is source-traced | PASS | sheet-2 D59.5->E14/video /G; inverted D59.6->E13/CPU /G |
| Video counter address nets VA0-VA15 are present in the board JSON | PASS | `kicad/juku.board.json` VA0-VA15 from D44-D47 into the mux stage |
| D53 bank/RAS ladder outputs are present in the board JSON | PASS | `kicad/juku.board.json` D53_Y0_R49..D53_Y3_R52 |
| PIT video/baud timing endpoints are source-complete | PASS | sheet-2 D54 HOR RTR, D55 VERT SYNC, and D57 CLK0/GATE0 labels |
| D42/D43 serializer control/serial nets are present in the board JSON | PASS | `kicad/juku.board.json` LOAD_VID / D43_DS / D42_Q |
| D41 package timing connectivity is source-closed | PASS | `docs/d41-timing-boundary.md` |
| Runnable video still uses the abstract raster/read port | PASS | `hdl/juku_top.v` runnable adjunct |
| The DRAM model still exposes sim-only video read pins | PASS | `hdl/devices.v::dram_64kx1` |
| LVS explicitly treats the sim-only video read pins as non-board pins | PASS | `sync/lvs.py` SIM_ONLY contract |
| Owner photo survey confirms a socketed top-center РЕ3 is dumpable | PASS | `ref/photos/juku-pcb-2/SURVEY.md` |
| Scanned `.113/.117` РЕ3 tables are guarded but not D94 `.092` | PASS | `docs/re3-firmware-inspection.md` |
| Owner-scan firmware directory has no mislabeled D94 `.092` table | PASS | `ref/firmware/` has no `.092` artifact |
| D94 FDC-control role is separated from video timing | PASS | `docs/d94-reconstruction-constraints.md`; only proved outputs terminate at D93 |

## Guarded Inputs

- `ref/firmware/re3_dgsh5.106.113.hex`: `05b582e19bed47c70374859de41c7fb4ce648a6f0b895059f9cf963c5496cb13`
- `ref/firmware/re3_dgsh5.106.117.hex`: `3c431fdc0005a865aba209a026a3e75cbc1af9bdf1d5d8fc9953954238205f18`
- `docs/d94-reconstruction-constraints.md`: generated D94 `.092` FDC
  control/address/firmware boundary; D94 is not used as video-timing evidence.
- `docs/d41-timing-boundary.md`: generated D41 output-side net
  guard plus explicit input/control timing-bus boundary.

## Interpretation

- The runnable path is guarded: raster geometry and byte-to-pixel serialization produce the
  expected 40 x 241 framebuffer stream.
- The physical chips for the serializer and mux/decode path are present in
  the structural model, so this is no longer a vague video-output gap.
- The shared ИР16 primitive is now datasheet-exact: falling-edge clock,
  high LD/SH for parallel load, low LD/SH for right shift, and active-high
  output control. This reclassifies `SHIFT_G` as D42/D43 OC rather than
  a clock gate; its remote source remains open.
- D48-D52 now preserve the physical КП14/258 output inversion and
  three-state disable behavior; the DRAM model normalizes that inversion
  only at its internal logical address index.
- Full-resolution sheet review restores the previously missed D59 5->6
  inverter: D59.5 reaches E14/video /G and D59.6 reaches E13/CPU /G.
  Owner continuity now closes D59.5 onto the D40.11 1 MHz slot rail shared
  with D92.2/.3 and D95.5/.6. The runnable TTL-high fallback remains only
  until the JSON, HDL, and PCB net merge is applied atomically; see
  `docs/d40-d59-d92-d95-1mhz-route.md`.
- D41's role is now narrowed: QA/QB, its fixed data/enable straps, and
  intentional QC/QD no-connects are modeled; only the remote LD/CK
  timing-bundle sources remain continuity boundaries.
- The ROM-programmed D54/D55/D56/D34_SYNC raster timing is now executable
  and independently agrees with the 320x241 reference geometry.
- The missing piece is the exact video-read slot schedule around D41, D50,
  D51, D52, and D53, plus the D34 signal input. D94 is not used as
  video-timing evidence: its only proved outputs terminate at FDC D93.
- Until those physical slot-control paths are traced, the honest
  model keeps `VA/VQ` and `video_raster` as a sim-only runnable adjunct rather
  than inventing a board-critical DRAM arbitration schedule.
