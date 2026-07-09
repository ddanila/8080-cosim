# Video slot timing audit

Status: **VIDEO SLOT TIMING AUDITED / D94 PROM DUMP PENDING**

This generated audit tracks the remaining M4/V3 boundary: replacing the
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
| Physical D42/D43 ИР16 serializers are traced in the transcription | PASS | `docs/transcription/dram-video-timing.md` |
| Physical serializer instances exist in `juku_top` | PASS | `hdl/juku_top.v` |
| Physical CPU/video mux and D53 decode instances exist in `juku_top` | PASS | `hdl/juku_top.v` |
| Runnable video still uses the abstract raster/read port | PASS | `hdl/juku_top.v` V2 adjunct |
| The DRAM model still exposes sim-only video read pins | PASS | `hdl/devices.v::dram_64kx1` |
| LVS explicitly treats the sim-only video read pins as non-board pins | PASS | `sync/lvs.py` SIM_ONLY contract |
| Owner photo survey confirms a socketed top-center РЕ3 is dumpable | PASS | `ref/photos/juku-pcb-2/SURVEY.md` |
| Scanned `.113/.117` РЕ3 tables are guarded but not D94 `.092` | PASS | `docs/re3-firmware-inspection.md` |
| No D94 `.092` programming table or dump is present under `ref/firmware` | PASS | `ref/firmware/` has no `.092` artifact |

## Guarded Inputs

- `ref/firmware/re3_dgsh5.106.113.hex`: `05b582e19bed47c70374859de41c7fb4ce648a6f0b895059f9cf963c5496cb13`
- `ref/firmware/re3_dgsh5.106.117.hex`: `3c431fdc0005a865aba209a026a3e75cbc1af9bdf1d5d8fc9953954238205f18`

## Interpretation

- V2 is guarded: raster geometry and byte-to-pixel serialization produce the
  expected 40 x 241 framebuffer stream.
- The physical chips for the serializer and mux/decode path are present in
  the structural model, so this is no longer a vague video-output gap.
- The missing piece is the exact video-read slot schedule, which depends on
  the still-undumped D94 `ДГШ5.106.092` РЕ3 timing PROM plus the adjacent
  АГ3 timing. The repo has guarded `.113/.117` scans, but those are not the
  D94 `.092` content.
- Until that PROM is dumped or a programming-disk table appears, the honest
  model keeps `VA/VQ` and `video_raster` as a sim-only V2 adjunct rather
  than inventing a board-critical DRAM arbitration schedule.
