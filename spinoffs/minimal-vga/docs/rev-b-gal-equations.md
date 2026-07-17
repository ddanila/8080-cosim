# rev B Memory-card decode GAL22V10 (U3)

Status: **DERIVED FROM THE ORACLE-TESTED BEHAVIORAL DECODE (D1.19) / PROGRAMMING UNVALIDATED**.

These equations are the memory-only decode the rev B Memory card's GAL implements.
They are derived from the behavioral `hdl/revb/revb_mem_card.v` decode (Mode A path),
which boots byte-identical to cosim via `sim/revb_boot_check.sh`. They are not yet a
device programming file: convert to a device format, program, and review before use.

Unlike rev A's U5 (which also did I/O decode), this GAL is **memory-only** — in rev B
each card decodes its own I/O (D1.16).

## Pinout (generated in `kicad/revb/gen_revb_boards.py`)

| Pin | Signal | Dir | Pin | Signal | Dir |
|---|---|---|---|---|---|
| 1 | MREQ_N | in | 13 | (spare in, NC) | in |
| 2 | RD_N | in | 14 | ROM_CE_N | out |
| 3 | WR_N | in | 15 | RAM_CE_N | out |
| 4 | A13 | in | 16 | MEM_RD_N | out |
| 5 | A14 | in | 17 | MEM_WR_N | out |
| 6 | A15 | in | 18–23 | spare outs (NC) | out |
| 7 | MODE0 | in | 12 | GND | pwr |
| 8 | MODE1 | in | 24 | VCC | pwr |
| 9 | A11 | in | | | |
| 10 | A12 | in | | | |
| 11 | (spare in, NC) | in | | | |

A11–A15 (not just A13–A15 as first drafted) are required so RAM_CE stops **below the
0xD800 video window** — the Memory card must be silent there or it fights the Video
card on the data bus. This granularity need was surfaced by TD.2.

## Equations (Mode-A baseline; `mode = {MODE1,MODE0}` from the I/O card, S11)

```text
MEM_CYCLE = /MREQ_N

; The framebuffer window 0xD800..0xFFFF belongs to the Video card. FB_HI is true
; for A >= 0xD800: A[15:13]=111 (0xE000+) OR A[15:11]=11011..11111 (0xD800..0xDFFF).
FB_HI     = (A15 & A14 & A13) # (A15 & A14 & /A13 & A12 & A11)

; ROM select. Mode 0 (boot, where ekta37 stays): ROM = low 16 KiB (/A15 & /A14).
; Modes 1-3 overlay ROM elsewhere; the runnable baseline implements mode 0 and the
; mode bits gate the alternates (kept minimal here, matching the behavioral model's
; mode-0 boot path -- extend when modes 1-3 are exercised on hardware).
ROM_SEL   = MEM_CYCLE & /A15 & /A14 & /MODE0 & /MODE1

/ROM_CE_N = ROM_SEL
/RAM_CE_N = MEM_CYCLE & /ROM_SEL & /FB_HI      ; RAM only below the video window
/MEM_RD_N = MEM_CYCLE & /RD_N
/MEM_WR_N = MEM_CYCLE & /WR_N
```

## Provenance / cross-check

- ROM/RAM overlay + mode source: `hdl/revb/revb_mem_card.v` (`is_rom_intA`,
  `fb_is_ram`, `video_owns_rd`) and `ref/juku-machine-facts.json`
  `memory_overlay_modes`.
- 0xD800 framebuffer boundary: `ref/juku-machine-facts.json` `framebuffer.base_addr`.
- The behavioral model is the oracle (D1.19): any change to these terms must keep
  `sim/revb_boot_check.sh` byte-identical to cosim before the GAL is reprogrammed.
