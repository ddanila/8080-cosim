# Video slot timing audit

Status: **VIDEO SLOT TIMING AUDITED / PHYSICAL SLOT SCHEDULE PENDING**

This generated audit tracks the remaining faithful-video boundary: replacing the
runnable sim-only framebuffer read path with the physical shared-DRAM
video slot schedule through the КП14 muxes, D53 decoder and D41 timing chain.

## Command

Run from the repository root with Python 3. The generator reads the
board JSON, HDL/LVS source, and referenced reports; no simulator is
required. It overwrites this report with PASS/FAIL results and exits
with status 1 if any audit check fails.

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
| Video counter address nets VA0-VA15 are present in the board JSON | PASS | `kicad/juku.board.json` VA0-VA15 counter endpoints on D44-D47 |
| D53 bank/RAS ladder outputs are present in the board JSON | PASS | `kicad/juku.board.json` D53_Y0_R49..D53_Y3_R52 |
| Selected PIT video/baud timing endpoints are present in the board JSON | PASS | exact .009 E3 D54 HOR RTR, D55 VERT SYNC, D57 CLK0/GATE0, and D57 CLK2=/VER RTR labels |
| D42/D43 serializer control/serial nets are present in the board JSON | PASS | `kicad/juku.board.json` LOAD_VID / D43_DS / D42_Q |
| D41 package timing connectivity is source-closed | PASS | `docs/d41-timing-boundary.md` |
| Runnable video still uses the abstract raster/read port | PASS | `hdl/juku_top.v` runnable adjunct |
| The DRAM model still exposes sim-only video read pins | PASS | `hdl/devices.v::dram_64kx1` |
| LVS explicitly treats the sim-only video read pins as non-board pins | PASS | `sync/lvs.py` SIM_ONLY contract |
| Owner photo survey separates socketed РЕ3 from an assumed video role | PASS | `ref/photos/juku-pcb-2/SURVEY.md` |
| Scanned `.113/.117` РЕ3 tables are guarded but not D94 `.092` | PASS | `docs/re3-firmware-inspection.md` |
| Owner-scan firmware directory has no mislabeled D94 `.092` table | PASS | `ref/firmware/` has no `.092` artifact |
| D94 FDC-control role is separated from video timing | PASS | `docs/d94-reconstruction-constraints.md`; outputs serve D93 and its FDC support logic |

## Recorded inputs

- `ref/firmware/re3_dgsh5.106.113.hex`: `05b582e19bed47c70374859de41c7fb4ce648a6f0b895059f9cf963c5496cb13`
- `ref/firmware/re3_dgsh5.106.117.hex`: `3c431fdc0005a865aba209a026a3e75cbc1af9bdf1d5d8fc9953954238205f18`
- [D41 boundary](d41-timing-boundary.md): complete package connectivity
  disposition and the remaining remote rail-17 source boundary.

## Interpretation

- This audit checks board endpoints, HDL text and recorded-report markers.
  The two firmware hashes above are computed for reporting, not compared
  against pinned identities by this generator.
  It does not execute the raster, serializer or mux tests; use the commands
  cited in the table to refresh their runtime evidence.
- The runnable video adjunct reads 40 bytes per line for 241 lines from
  a second, simulation-only DRAM port. Physical serializer and mux
  instances coexist with that adjunct in `juku_top`.
- The ИР16 model uses falling-edge clocks, high LD/SH for parallel load,
  low LD/SH for shift, and active-high output control. `SHIFT_G` drives
  D42/D43 OC; its sheet-traced D35.6/R38.1 connection has no owner-board
  continuity measurement.
- D48-D52 preserve КП14 inversion and three-state disable behavior; the
  DRAM model normalizes the inversion at its internal address index.
- D59.5 reaches the video /G rail and D59.6 the CPU /G rail. The measured
  D40.11 1 MHz branch is documented in the
  [clock-route report](d40-d59-d92-d95-1mhz-route.md). Yosys/LVS uses
  the complementary enables; runnable simulation keeps CPU MA selected.
- D41 package connectivity is source-closed. Its remote rail-17 origin
  remains a timing-chain boundary. The exact shared-DRAM slot schedule
  around D41/D50-D53 and the D34 signal input remain unresolved.
