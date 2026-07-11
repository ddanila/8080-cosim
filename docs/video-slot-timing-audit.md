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
| Physical D42/D43 ИР16 serializers are identified in the board model | PASS | `kicad/juku.board.json` D42/D43 identities |
| Physical serializer instances exist in `juku_top` | PASS | `hdl/juku_top.v` |
| Physical CPU/video mux and D53 decode instances exist in `juku_top` | PASS | `hdl/juku_top.v` |
| Video counter address nets VA0-VA15 are present in the board JSON | PASS | `kicad/juku.board.json` VA0-VA15 from D44-D47 into the mux stage |
| D53 bank/RAS ladder outputs are present in the board JSON | PASS | `kicad/juku.board.json` D53_Y0_R49..D53_Y3_R52 |
| D42/D43 serializer control/serial nets are present in the board JSON | PASS | `kicad/juku.board.json` LOAD_VID / D43_DS / D42_Q |
| D41 latch-chain output boundary is guarded | PASS | `docs/d41-timing-boundary.md` |
| Runnable video still uses the abstract raster/read port | PASS | `hdl/juku_top.v` runnable adjunct |
| The DRAM model still exposes sim-only video read pins | PASS | `hdl/devices.v::dram_64kx1` |
| LVS explicitly treats the sim-only video read pins as non-board pins | PASS | `sync/lvs.py` SIM_ONLY contract |
| Owner photo survey confirms a socketed top-center РЕ3 is dumpable | PASS | `ref/photos/juku-pcb-2/SURVEY.md` |
| Scanned `.113/.117` РЕ3 tables are guarded but not D94 `.092` | PASS | `docs/re3-firmware-inspection.md` |
| No D94 `.092` programming table or dump is present under `ref/firmware` | PASS | `ref/firmware/` has no `.092` artifact |
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
- D41's output-side role is now narrowed: QA/QB are modeled, while
  serial input, QC/QD outputs, parallel inputs, load, gate, and clock remain a timing-bus
  source-read/continuity boundary.
- The missing piece is the exact video-read slot schedule around D41, D52,
  D53, D56, and the adjacent one-shot/counter timing. D94 is not used as
  video-timing evidence: its only proved outputs terminate at FDC D93.
- Until those physical slot-control paths are traced, the honest
  model keeps `VA/VQ` and `video_raster` as a sim-only runnable adjunct rather
  than inventing a board-critical DRAM arbitration schedule.
