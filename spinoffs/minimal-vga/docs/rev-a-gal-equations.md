# Rev A GAL/PAL Equations

Status: **DECODE SIMULATED / TIMING + PROGRAMMING UNVALIDATED**.

The U5 decode is now backed by test vectors from the verified simulation twin
(both jumper modes boot byte-identical to cosim — see the U5 section). These
equations are still not a released programming file: they must be converted to a
device-specific source format, programmed, independently reviewed, and — for the
U24 timing sequencer below — validated against the selected DRAM timing before
fabrication.

## U5 Address/control Decode GAL22V10 (dual-mode: Phase 3)

The decode GAL is **dual-mode**, selected by the `MODE_B` jumper (J94):

- **Mode A** (`MODE_B=0`, РТ4 socket empty): the GAL decodes ROM/RAM itself from
  A15/A14 — the western-parts bring-up baseline.
- **Mode B** (`MODE_B=1`, real К556РТ4 socketed at U3): the РТ4 decides ROM/RAM
  and the GAL only *conditions* its output (this is where the provisional
  `~D0`/`~D3` polarity correction lives — root `PLAN.md` item 1 — so resolving
  the polarity is a **GAL reprogram, not a board respin**).

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
| 22 | WAIT_N | output |
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
; Mode B: the real К556РТ4 (U3) drives it. DEC_ROM_N is its O1 output. Under the
; PROVISIONAL polarity (the ~D0 correction), ROM is selected when DEC_ROM_N is
; HIGH. THIS is the single reprogrammable term: flip it if the D6 level probe
; (PLAN.md item 1) shows the true polarity is inverted.
ROM_B       = DEC_ROM_N

ROM_SEL     = MEM_CYCLE & ( (/MODE_B & ROM_A) # (MODE_B & ROM_B) )

/ROM_CE_N   = ROM_SEL
/RAM_CE_N   = MEM_CYCLE & /ROM_SEL              ; memory that is not ROM is RAM
/PPI_CS_N   = IO_CYCLE                          ; coarse bring-up I/O select

/MEM_RD_N   = MEM_CYCLE & READ_CYCLE
/MEM_WR_N   = MEM_CYCLE & WRITE_CYCLE
/IO_RD_N    = IO_CYCLE & READ_CYCLE
/IO_WR_N    = IO_CYCLE & WRITE_CYCLE

REV_OUT     = MODE_B & DEC_REV                  ; РТ4 rev observ. / future video path
WAIT_N      = 1                                 ; no wait states in first bring-up
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
- `WAIT_N` is held inactive for first bring-up. If DRAM timing needs wait-state
  insertion, move it into U24 or revise this decode GAL.
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
| 13 | RAS_N | output |
| 14 | CAS_N | output |
| 15 | DRAM_WE_N | output |
| 16 | ADDRMUX_SEL | output |
| 17 | CPU_WAIT_N | output |
| 18 | VIDEO_ACK | output |
| 19 | REFRESH_TICK | output |
| 20 | DRAM_OE_N | output |
| 21 | SPARE0 | output |
| 22 | SPARE1 | output |
| 23 | SPARE2 | output |
| 24 | VCC | power |

Bring-up behavior:

```text
CPU_RAM     = /RAM_CE_N
CPU_READ    = /MEM_RD_N
CPU_WRITE   = /MEM_WR_N
CPU_ACCESS  = CPU_RAM & (CPU_READ # CPU_WRITE)
REFRESH     = /RFSH_OBS_N
VIDEO       = VIDEO_REQ

DRAM_CYCLE  = CPU_ACCESS # REFRESH # VIDEO

/RAS_N      = DRAM_CYCLE
/CAS_N      = DRAM_CYCLE & CLK
/DRAM_WE_N  = CPU_RAM & CPU_WRITE & CLK

ADDRMUX_SEL = CLK
CPU_WAIT_N  = 1
VIDEO_ACK   = VIDEO
REFRESH_TICK = REFRESH
/DRAM_OE_N  = CPU_RAM & CPU_READ

SPARE0 = 1
SPARE1 = 1
SPARE2 = 1
```

Notes:

- This is a programmable bring-up timing contract, not a final proven DRAM
  timing model.
- `RAS_N`, `CAS_N`, and `DRAM_WE_N` must be checked against the selected
  `KM4164B-10` datasheet after the first board is powered.
- The board exposes DRAM/debug headers specifically so these equations can be
  adjusted without changing PCB copper.
