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

The structural top boots the real ekta37 ROM, matches the C oracle’s
framebuffer, handles keyboard and frame-interrupt paths, reads vendored Juku
disk media through the bounded FDC model, reaches EKDOS `A>`, and reaches disk
BASIC `READY`. The exact ROMBIOS `0xA0/0xA2` write-sector path can also stream
512 bytes to an explicitly writable disk copy and read them back; tracked media
remains read-only by default. Monitor 3.3 reset/cursor and selected command
paths also have HDL oracles. The full-prompt results include recorded deep
runs; current reruns have the
[Verilator compatibility limitation](../sync/README.md#simulator-compatibility).
Use each owning report for its inputs, scope, and reproduction command.

The CPU, memory/ROM paging, populated bit-sliced DRAM bank, PPI/PIT/PIC/USART
behavior, FDC boot subset, serializer, and raster helper are functional models.
They are not generic cycle-accurate replacements for every original IC mode.
The 8253 slice implements binary/BCD count loading, LSB/MSB access formats,
live or latched count reads, first-latch ownership, and the video-used modes;
the Juku-specific HDL clocks remain authoritative for count progression.

## Model boundaries

- D2's physical inputs, validated `.037` table, and D0/WAIT handoff are modeled.
- D6's validated `.038` table and chip-removed separate pins 11/12 remain the
  structural/LVS truth. Runnable simulation now selects from that physical table
  through `U_DECODE`. All four outputs connect directly
  with no simulation-only polarity correction. Capture provenance and the
  corrected channel order are in
  [the physical PROM guide](../ref/physical-proms/README.md).
  `decode_prom_functional` is retained only by the B37A diagnostic comparison.
- D94's validated physical `.092` table is modeled with open-collector outputs,
  and its first three outputs are wired to the accepted local FDC controls.
  D4-D7 are proved no-connects; exact `.009` sheets close D9.7 `CS7` to
  D94.15/D93.3. D0's hidden load beyond its measured pull-up remains open.
- 4 official FDC-support devices have package pins and power endpoints in
  the board model but retain untraced functional pins or explicit boundary
  nets;
  `docs/unmodeled-footprint-inventory.md` owns that boundary.
- The shared К555ИЕ7/74LS193 primitive used by video counters D44-D47 and
  representing FDC-area D106 now has its complete standard digital contract
  guarded. Recovered sheet 3 also closes and LVS-maps its actual board straps,
  RAW READ load, selected recovery clock, grounded clear, Q3 output, and five
  explicit no-connects; only physical waveform quality remains a bench check.
- D96's КМ555ТМ2 section 1 is sheet-closed and LVS-mapped: WREQ_N controls
  /CLR and /PRE, /Q feeds D, D28.8 clocks the toggle, and Q drives D93 RCLK.
  The device model now preserves the datasheet's Q=/Q=high result when WREQ
  asserts both asynchronous controls instead of assigning clear priority;
  restart phase is undefined, while divide-by-two behavior after release is
  guarded. Section 2 is structurally restored from the exact sheet:
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
- 55 modeled nets still carry source-risk annotations requiring
  physical evidence or an explicit redesign before fabrication release.
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
  physical evidence boundaries.
- Simulation-only CPU sampling, keyboard stimulus, framebuffer access, and
  interrupt helpers are excluded from LVS by an explicit allowlist in
  `sync/lvs.py`.

## Verification

```sh
sync/check.sh       # modeled KiCad/HDL connectivity
sync/boot_check.sh  # C and HDL boot/framebuffer regression
sync/cosim_check.sh # typed CPU-bus event comparison vs the C emulator (cosim)
sync/ie7_check.sh   # К555ИЕ7/74LS193 device behavior and cascade
sync/ie10_check.sh  # К555ИЕ10/74LS161 behavior and traced D103 /13 loop
```

See [verification entry points](../sync/README.md) for subsystem and deep checks. A green LVS result proves
only mapped connectivity; it does not cover omitted pins or validate device
behavior.
