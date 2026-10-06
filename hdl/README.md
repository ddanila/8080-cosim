# HDL structural model

`juku_top.v` is the runnable structural model of the Juku processor module and
the HDL side of the LVS comparison. Instances represent board devices; wires
represent modeled board nets. `devices.v` contains the behavioral models used
for simulation.

## Files

- `juku_top.v` — structural top and explicitly named simulation adjuncts.
- `devices.v` — CPU wrapper, memories, decode logic, peripheral behavior, and
  bounded timing/analog substitutes.
- `vendor/vm80a.v` — vendored die-level 8080/КР580ВМ80А-compatible core; see
  `vendor/README.md` and `vendor/license.md`.
- `sim/` — unit, boot, lockstep, video, FDC, and checkpoint testbenches.
- `juku_top.json` — generated Yosys netlist; regenerate with `sync/check.sh`.

## What currently runs

The structural top boots the adopted archive-0037 RomBios 3.43m image
(`roms/ekta37.bin`), matches the C oracle’s
framebuffer, handles keyboard and frame-interrupt paths, reads vendored Juku
disk media through the bounded FDC model, reaches EKDOS `A>`, and reaches disk
BASIC `READY`. The exact ROMBIOS `0xA0/0xA2` write-sector path can also stream
512 bytes to an explicitly writable disk copy and read them back; tracked media
remains read-only by default. Monitor 3.3 reset/cursor and selected command
paths also have HDL oracles. The full-prompt results include recorded deep
runs; current reruns have the
[Verilator compatibility limitation](../sync/README.md#simulator-compatibility).
Use each owning report for its inputs, scope, and reproduction command.

The CPU, memory/ROM paging, populated bit-sliced DRAM bank, PPI/PIT/USART
behavior, FDC boot subset, serializer, and raster helper are functional models.
They are not generic cycle-accurate replacements for every original IC mode.
The 8253 slice implements binary/BCD count loading, LSB/MSB access formats,
live or latched count reads, first-latch ownership, and video modes 1/2.
Mode 3 uses a decrement-by-two path guarded for the even divisors used here.
Modes 0/4/5 share a reload/toggle fallback in [the device model](devices.v);
this does not establish their complete 8253 behavior. Count progression uses
the Juku-specific HDL clocks.
D57 channel 2 uses the active-low D55 OUT1 (`VER RTR`) signal, approximately
49.92 Hz under the stock raster setup. Immediate count-read diagnostics must
allow for that clock; the
[D55 audit](../docs/jukuravi-d55-diagnostic-audit.md#structural-simulation-matrix)
currently stops on an additional D57 failure bit before reaching its T34 cases.

## Model boundaries

- `pic_8259` is a two-register read/write stub. The simulation-only `intr_ctl`
  helper snoops ICW1, ICW2 and the interrupt mask, then services external frame
  ticks as IR5 with a three-byte CALL vector. The mapped USART IR2/IR3 and other
  interrupt inputs do not receive arbitration or vector service in this HDL
  model. Frame-interrupt tests therefore do not qualify a complete 8259.
- D2's modeled inputs, captured `.037` table, open-collector D0 output and
  D30 READY sampling are modeled. Complete WAIT duration still depends on
  surrounding clock/control timing. Five address routes still await exact
  source confirmation; see [D2 constraints](../docs/d2-reconstruction-constraints.md)
  and [the READY bench](../docs/d2-ready-path-check.md).
- D6's validated `.038` table and chip-removed separate pins 11/12 remain the
  structural/LVS truth. Runnable simulation selects from that physical table
  through `U_DECODE`. All four outputs connect directly
  with no simulation-only polarity correction. Capture provenance and the
  corrected channel order are in
  [the physical PROM guide](../ref/physical-proms/README.md).
  `decode_prom_functional` is retained only by the B37A diagnostic comparison.
- D94's validated physical `.092` table is modeled with open-collector outputs,
  with D1 feeding D99, D2 feeding D93 `/RE`, and D3 feeding D93 `/WE`.
  D4-D7 are proved no-connects; exact `.009` sheets close D9.7 `CS7` to
  D94.15/D93.3. D0's hidden load beyond its measured pull-up remains open.
- Some FDC-support devices have package pins and power endpoints in
  the board model but retain untraced functional pins or explicit boundary
  nets;
  [the footprint inventory](../docs/unmodeled-footprint-inventory.md) owns
  that boundary.
- The shared К555ИЕ7/74LS193 primitive used by video counters D44-D47 and
  representing FDC-area D106 has its complete standard digital contract
  guarded. Recovered sheet 3 also closes and LVS-maps its actual board straps,
  RAW READ load, selected recovery clock, grounded clear, Q3 output, and five
  explicit no-connects; only physical waveform quality remains a bench check.
- D96's КМ555ТМ2 section 1 is sheet-closed and LVS-mapped: WREQ_N controls
  /CLR and /PRE, /Q feeds D, D28.8 clocks the toggle, and Q drives D93 RCLK.
  The device model preserves the datasheet's Q=/Q=high result when WREQ
  asserts both asynchronous controls;
  restart phase is undefined, while divide-by-two behavior after release is
  guarded. Section 2 follows the exact sheet:
  wired D28.10/.12 feeds /PRE2 and D2. CLK2 is source-joined to
  D94.2/D99.9/R89.1, with physical continuity pending;
  Q2 feeds D101 A0–A3 in the full sheet-3 overview, with physical continuity
  still pending. /CLR2 joins D99.10 B2 and an unread sheet-1 source, and /Q2
  retains its isolated pin-8 test landing. That half is set-only while /CLR2
  is inactive; the clear-source timing remains unproved.
- D103's К555ИЕ10/74LS161 behavior and its source-traced D33 feedback are
  guarded through the actual `0011` preset, proving the modulo-13 path from
  16 MHz to the labeled 1.23 MHz Q3 rail. The upstream OSC-to-XTAL16M physical
  merge remains a continuity boundary.
- D7's physical pin12=`SYNC`, pin13=pin11 feedback strobe is retained in the
  structural/LVS path; runnable zero-delay simulation uses the explicit
  IOWR/IORD activity oracle instead of evaluating the propagation-delay loop.
- Seven factory wires (W7, W8, W10, W11, W14, W19, W20) use mapped
  boundaries between separate PCB islands and are transparent in runnable
  simulation. Three other wire positions remain modeled as copper
  substitutions. [Factory-wire fidelity](../docs/factory-wire-route-fidelity.md)
  owns the endpoint, routing, and landing-fit checks; HDL transparency does
  not establish physical construction.
- Modeled nets with source-risk annotations require physical evidence or an
  explicit redesign before fabrication release. The
  [main-board ERC and parity report](../docs/main-board-erc-parity.md) owns
  their current census and dispositions.
- The runnable video path reads DRAM through a simulation-only second port.
  Physical D41/D42/D43 and mux/decode instances exist. Their ИР16 falling-edge
  LD/SH/OC behavior and D48-D52 inverting КП14/258 behavior are guarded, but
  faithful shared-DRAM slot timing still needs the remote control sources. The
  D59 5->6 inverter is wired locally: D59.5 reaches the
  E14/video /G link and D59.6 reaches the E13/CPU /G link. Owner continuity
  proves D59.5 is driven by the D40.11 1 MHz slot rail, shared with
  D92.2/.3 and D95.5/.6. The runnable HDL, JSON, schematic, and both routed
  PCB representations preserve that modeled single-driver net; this does not
  imply zero open connections across either board. See
  [the route review](../docs/d40-d59-d92-d95-1mhz-route.md). Yosys/LVS applies its complementary
  enables to D48-D51; runnable simulation keeps CPU MA selected while the
  SIM-ONLY video port remains in use, because the D41/D53 slot schedule is
  still an explicit timing boundary. D94's proved
  outputs belong to FDC control.
- CPU DRAM transactions are functionally closed: RAS spans row through CAS,
  and the РУ5 model implements early/delayed asynchronous writes without a
  synthetic sampling clock. Exact D36/R57 delays and DOUT turn-off remain
  physical evidence boundaries. The DRAM cells are initialized to zero and
  have no charge-decay model; successful runs do not prove physical power-on
  contents, retention, or refresh sufficiency.
- LVS compares only instances selected by `sync/map.json`; unmapped simulation
  adjuncts such as `U_INTR` are outside that comparison. The `SIM_ONLY` pin
  allowlist in `sync/lvs.py` also excludes CPU sampling, keyboard stimulus,
  frame ticks, and the second DRAM port from mapped instances.

## Verification

Run these commands from the repository root. Connectivity checks require
Python 3 and Yosys; KiCad CLI is optional, with a board-JSON fallback when
schematic export is unavailable. Simulation checks require Icarus Verilog
(`iverilog` and `vvp`); boot and cosim checks also require Python 3 and a C
compiler (`CC`, default `cc`).

```sh
sync/check.sh       # modeled KiCad/HDL connectivity
sync/boot_check.sh  # C and HDL boot/framebuffer regression
sync/cosim_check.sh # typed CPU-bus event comparison vs the C emulator (cosim)
sync/ie7_check.sh   # К555ИЕ7/74LS193 device behavior and cascade
sync/ie10_check.sh  # К555ИЕ10/74LS161 behavior and traced D103 /13 loop
```

`sync/check.sh` regenerates the schematic and HDL JSON netlist, plus the KiCad
XML netlist when export succeeds. Boot and cosim checks regenerate the ROM hex
and write framebuffer dumps in the source tree. Counter checks overwrite
their owning reports after passing; `IE7_REPORT` and `IE10_REPORT` select
alternate output paths.

See [verification entry points](../sync/README.md) for subsystem and deep checks. A green LVS result proves
only mapped connectivity; it does not cover omitted pins or validate device
behavior.
