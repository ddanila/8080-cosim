# Rev A GAL/PAL Equations

Status: **DECODE + DRAM TIMING SIMULATED / PROGRAMMING UNVALIDATED**.

The U5 decode is now backed by test vectors from the verified simulation twin
(both jumper modes boot byte-identical to cosim — see the U5 section). These
equations are still not a released programming file: they must be converted to a
device-specific source format, programmed, and independently reviewed. The U24
reference below is now simulation-validated against the slower vendored
MK4564-12 timing limits at the selected 4 MHz clock.

## U5 Address/control Decode GAL22V10 (dual-mode: Phase 3)

The decode GAL is **dual-mode**, selected by the `MODE_B` jumper (J94):

- **Mode A** (`MODE_B=0`, РТ4 socket empty): the GAL decodes ROM/RAM itself from
  A15/A14 — the western-parts bring-up baseline.
- **Mode B** (`MODE_B=1`, real К556РТ4 socketed at U3): the РТ4 decides ROM/RAM
  and the GAL conditions its active-low output. Corrected reader-3 packing
  proves D0/pin12 is `ROM_N`, so no polarity ambiguity remains.

Pinout (a real 22V10: 12 inputs on pins 1-11+13, 10 macrocells on 14-23):

| Pin | Signal | Direction |
|---|---|---|
| 1 | MREQ_N | input |
| 2 | IORQ_N | input |
| 3 | RD_N | input |
| 4 | WR_N | input |
| 5 | A13 | input |
| 6 | A14 | input |
| 7 | A15 | input |
| 8 | MODE_B | input (J94 jumper) |
| 9 | DEC_ROM_N | input (U3 РТ4 O1 = rom_n) |
| 10 | DEC_RAM_N | input (U3 РТ4 O2 = ram_n) |
| 11 | DEC_REV | input (U3 РТ4 O3 = rev) |
| 12 | GND | power |
| 13 | DEC_ROE_N | input (U3 РТ4 O4 = roe_n) |
| 14 | ROM_CE_N | output |
| 15 | RAM_CE_N | output |
| 16 | PPI_CS_N | output |
| 17 | MEM_RD_N | output |
| 18 | MEM_WR_N | output |
| 19 | IO_RD_N | output |
| 20 | IO_WR_N | output |
| 21 | REV_OUT | output |
| 22 | DECODE_WAIT_N | output to U24.13 only |
| 23 | SPARE_N | output |
| 24 | VCC | power |

Bring-up equations:

```text
MEM_CYCLE   = /MREQ_N
IO_CYCLE    = /IORQ_N
READ_CYCLE  = /RD_N
WRITE_CYCLE = /WR_N

; ---- ROM/RAM decision, selected by the MODE_B jumper ----
; Mode A: coarse western-parts baseline -- ROM is the low 32 KiB (A15=0 & A14=0).
ROM_A       = /A15 & /A14
; Mode B: the real К556РТ4 (U3) drives it. Corrected reader-3 packing proves
; DEC_ROM_N is physical D0/pin12 and ROM is selected when that signal is LOW.
ROM_B       = /DEC_ROM_N

ROM_SEL     = MEM_CYCLE & ( (/MODE_B & ROM_A) # (MODE_B & ROM_B) )

/ROM_CE_N   = ROM_SEL
/RAM_CE_N   = MEM_CYCLE & /ROM_SEL              ; memory that is not ROM is RAM
/PPI_CS_N   = IO_CYCLE                          ; coarse bring-up I/O select

/MEM_RD_N   = MEM_CYCLE & READ_CYCLE
/MEM_WR_N   = MEM_CYCLE & WRITE_CYCLE
/IO_RD_N    = IO_CYCLE & READ_CYCLE
/IO_WR_N    = IO_CYCLE & WRITE_CYCLE

REV_OUT     = MODE_B & DEC_REV                  ; РТ4 rev observ. / future video path
DECODE_WAIT_N = 1                               ; U24 is the sole CPU WAIT driver
SPARE_N     = 1
```

### Test vectors (derived from the verified twin)

These are generated from the same decode the simulation proves byte-identical to
cosim (`hdl/vjuga_juku_top.v` + the real `.038` РТ4 table via `decode_prom`).
`ROM_CE_N` is active-low (0 = ROM selected). Mode B matches the reference memory
overlay in **every** memory-map mode; Mode A reproduces **mode 0** (the boot
path — `sim/vjuga_boot_check.sh` proves both modes boot identically, and the
ekta37 boot stays in mode 0):

| Cycle (MREQ_N=0) | mode | Mode A `ROM_CE_N` | Mode B `ROM_CE_N` | reference |
|---|---|---|---|---|
| A=0x0000 | 0 | 0 | 0 | 0 (ROM) |
| A=0x3FFF | 0 | 0 | 0 | 0 (ROM) |
| A=0x4000 | 0 | 1 | 1 | 1 (RAM) |
| A=0xD800 | 0 | 1 | 1 | 1 (RAM, framebuffer) |
| A=0x0000 | 1 | 0 (A-only, ≠ref) | 1 | 1 (RAM) |
| A=0xD800 | 1 | 1 (A-only, ≠ref) | 0 | 0 (ROM overlay) |

The "A-only ≠ref" rows are why Mode A is a **bring-up baseline** (mode 0), not a
full memory-map model: reproducing modes 1-3 needs the Port C mode bits, which is
exactly the job the real РТ4 does in Mode B. Regenerate the table with
`sim/vjuga_boot_check.sh` (both modes) plus the РТ4 `.038` dump.

Notes:

- `PPI_SEL` is a bring-up placeholder and should be tightened when the final
  I/O map is frozen.
- U5 does not share a push-pull `WAIT_N` net with U24. Its pin 22 feeds only
  U24.13 as `DECODE_WAIT_N`; U24.18 is the sole CPU/header WAIT driver.
- `DEC_RAM_N` (O2) and `DEC_ROE_N` (O4) are brought into the GAL for cross-check
  and future use; `RAM_CE_N` is derived as the complement of `ROM_SEL` so a
  single stuck РТ4 output does not silently corrupt RAM select.
- The previously reserved data-bus-buffer pins are dropped: Rev A routes the
  direct Z80 data bus, and the freed macrocells now carry the real decode
  outputs plus `REV_OUT`.

## U24 DRAM Timing Sequencer GAL22V10

Pinout:

| Pin | Signal | Direction |
|---|---|---|
| 1 | CLK | input |
| 2 | RESET_N | input |
| 3 | RAM_CE_N | input |
| 4 | MEM_RD_N | input |
| 5 | MEM_WR_N | input |
| 6 | RFSH_OBS_N | input |
| 7 | VIDEO_REQ | input |
| 8 | REFRESH_Q0 | input |
| 9 | REFRESH_Q1 | input |
| 10 | REFRESH_Q2 | input |
| 11 | REFRESH_Q3 | input |
| 12 | GND | power |
| 13 | DECODE_WAIT_N | input from U5.22 |
| 14 | RAS_N | output |
| 15 | CAS_N | output |
| 16 | DRAM_WE_N | output |
| 17 | ADDRMUX_SEL | output |
| 18 | CPU_WAIT_N | sole output to CPU/headers |
| 19 | VIDEO_ACK | output / registered video-client flag |
| 20 | REFRESH_TICK | output / registered refresh-client flag |
| 21 | STATE0 | registered feedback output, no external load |
| 22 | STATE1 | registered feedback output, no external load |
| 23 | STATE2 | registered feedback output, no external load |
| 24 | VCC | power |

Pin 13 is the GAL22V10's twelfth input/OE pin; assigning `RAS_N` there was an
invalid eleven-output contract. Pins 14-23 are the ten real macrocells. The
corrected contract uses seven functional outputs and three registered state
bits. `DRAM_OE_N` was removed because 4164 DOUT enable is controlled by CAS.

The programming reference is `hdl/u24_dram_timing.v`, guarded by
`sim/u24_dram_timing_check.sh`. It uses this cyclic Gray sequence, so every
transition—including `DONE -> IDLE`—changes exactly one feedback macrocell:

```text
IDLE(000) -> ROW(001) -> RAS(011) -> COL(010)
          -> CAS(110) -> HOLD(111) -> PRECHARGE(101) -> DONE(100)
          -> IDLE(000)
```

At the owner-selected 4 MHz CPU clock:

- CPU has priority over refresh, then video. CPU inputs remain stable because
  U24 asserts WAIT from request acceptance through `PRECHARGE` and releases it
  only in `DONE`.
- `ROW` presents the row address; `RAS` asserts RAS; `COL` switches the mux and
  establishes early-write WE; `CAS` and `HOLD` keep CAS active for two clocks;
  `PRECHARGE` raises CAS one clock before RAS; `DONE` releases WAIT.
- Refresh takes the RAS-only path `ROW -> RAS -> PRECHARGE -> DONE`. The
  registered `REFRESH_TICK`/`VIDEO_ACK` outputs retain the selected non-CPU
  client even after its request input changes. A CPU request colliding with
  either client remains waited through that client's `DONE`, then receives its
  own complete row/column cycle before WAIT releases.
- The slower vendored MK4564-12 limits are met conservatively: 500 ns
  RAS-to-CAS delay, 500 ns CAS pulse (minimum 75 ns), 1250 ns RAS pulse
  (minimum 120 ns), 250 ns RAS hold after CAS (minimum 75 ns), and at least
  250 ns early-write setup (minimum 0 ns). The selected 4 MHz `Z0840004PSC`
  therefore has timing margin even against the -12 reference, while a future
  clock change must rerun the guard.

Remaining notes:

- This is a simulated programming contract, not a JEDEC fuse map or a
  programmed-device test. Convert it to device-specific equations, compile it
  against the chosen GAL22V10, and preserve the compiler/fuse checksum.
- The board exposes DRAM/debug headers so programmed-device timing can be
  compared with these waveforms without changing the functional pinout.
