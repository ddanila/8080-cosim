# Rev A GAL/PAL Equations

Status: **DRAFT / UNVALIDATED**.

These equations document the pinout and intended bring-up behavior routed by
the current experimental board. They are not a released programming file and
must be simulated, reviewed, converted to a device-specific source format, and
validated against the selected DRAM timing before fabrication.

## U5 Address/control Decode GAL22V10

Pinout:

| Pin | Signal | Direction |
|---|---|---|
| 1 | CLK | input |
| 2 | RESET_N | input |
| 3 | MREQ_N | input |
| 4 | IORQ_N | input |
| 5 | RD_N | input |
| 6 | WR_N | input |
| 7 | M1_N | input |
| 8 | RFSH_N | input |
| 9 | A13 | input |
| 10 | A14 | input |
| 11 | A15 | input |
| 12 | GND | power |
| 13 | ROM_CE_N | output |
| 14 | RAM_CE_N | output |
| 15 | PPI_CS_N | output |
| 16 | MEM_RD_N | output |
| 17 | MEM_WR_N | output |
| 18 | IO_RD_N | output |
| 19 | IO_WR_N | output |
| 20 | RESERVED_BUS_OE_N | output / Rev A NC |
| 21 | RESERVED_BUS_DIR | output / Rev A NC |
| 22 | WAIT_N | output |
| 23 | SPARE_N | output |
| 24 | VCC | power |

Bring-up equations:

```text
MEM_CYCLE   = /MREQ_N
IO_CYCLE    = /IORQ_N
READ_CYCLE  = /RD_N
WRITE_CYCLE = /WR_N

ROM_SEL     = MEM_CYCLE & /A15
RAM_SEL     = MEM_CYCLE & A15
PPI_SEL     = IO_CYCLE & /A7 & /A6 & /A5 & /A4

/ROM_CE_N   = ROM_SEL
/RAM_CE_N   = RAM_SEL
/PPI_CS_N   = PPI_SEL

/MEM_RD_N   = MEM_CYCLE & READ_CYCLE
/MEM_WR_N   = MEM_CYCLE & WRITE_CYCLE
/IO_RD_N    = IO_CYCLE & READ_CYCLE
/IO_WR_N    = IO_CYCLE & WRITE_CYCLE

RESERVED_BUS_DIR  = 1
RESERVED_BUS_OE_N = 1
WAIT_N      = 1
SPARE_N     = 1
```

Notes:

- The ROM/RAM split is coarse by design: lower 32 KiB ROM, upper 32 KiB RAM.
- `PPI_SEL` is a bring-up placeholder and should be tightened when the final
  I/O map is frozen.
- `WAIT_N` is held inactive for first bring-up. If DRAM timing needs wait-state
  insertion, move it into U24 or revise this decode GAL.
- Pins 20 and 21 are reserved for a possible future data-bus buffer. The Rev A
  board routes the direct Z80 data bus, so these GAL outputs are explicitly
  no-connect in the physical schematic and should be programmed inactive.

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
