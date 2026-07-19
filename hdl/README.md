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
paths also have HDL oracles.

The CPU, memory/ROM paging, populated bit-sliced DRAM bank, PPI/PIT/PIC/USART
behavior, FDC boot subset, serializer, and raster helper are functional models.
They are not generic cycle-accurate replacements for every original IC mode.

## Honest boundaries

- D2's physical inputs, validated `.037` table, and D0/WAIT handoff are modeled.
- D6's validated `.038` table and chip-removed separate pins 11/12 remain the
  structural/LVS truth. Runnable simulation now selects from that physical table
  through `U_DECODE`. The 2026-07-19 revision-3 reread corrected the original
  reader's four-channel bit reversal, so all four outputs now connect directly
  with no simulation-only polarity correction.
  `decode_prom_functional` is retained only by the B37A diagnostic comparison.
- D94's validated physical `.092` table is modeled with open-collector outputs,
  and its first three outputs are wired to the accepted local FDC controls. Its
  enable source, remaining far destinations, and complete D93 strobe branches
  are unknown.
- Seven official FDC-support devices have package pins and power endpoints in
  the board model but no functional signal closure or HDL instances;
  `docs/unmodeled-footprint-inventory.md` owns that boundary.
- The shared К555ИЕ7/74LS193 primitive used by video counters D44-D47 and
  representing FDC-area D106 now has its complete standard digital contract
  guarded. Recovered sheet 3 also closes and LVS-maps its actual board straps,
  RAW READ load, selected recovery clock, grounded clear, Q3 output, and five
  explicit no-connects; only physical waveform quality remains a bench check.
- D103's К555ИЕ10/74LS161 behavior and its source-traced D33 feedback are
  guarded through the actual `0011` preset, proving the modulo-13 path from
  16 MHz to the labeled 1.23 MHz Q3 rail. The upstream OSC-to-XTAL16M physical
  merge remains a continuity boundary.
- D7's physical pin12=`SYNC`, pin13=pin11 feedback strobe is retained in the
  structural/LVS path; runnable zero-delay simulation uses the explicit
  IOWR/IORD activity oracle instead of evaluating the propagation-delay loop.
- Factory wire A:7 separates the D35.10 clock-source landing from the
  D1.22/D48.1/D49.1/E2.3 PHI1 consumer island; W7 is the only modeled closure.
- Factory wire A:8 is a mapped `net_boundary` instance between the separate
  D38.8/A8B and D5.1/A8A PCB islands. It is electrically transparent in the
  runnable model but cannot collapse back into routed PCB copper unnoticed.
- Factory wire A:10 similarly separates D41.13/A10A from the shared
  D50.1/D51.1/A10B select island while remaining zero-delay in simulation.
- Factory wire A:11 separates the global D92.13/A11B MEMR island from
  D7.1/A11A; W11 preserves the physical closure as another mapped boundary.
- Factory wire A:14 separates the D35.12/A14B clock-source island from the
  D1.15/E3.3/A14A PHI2 consumer island; W14 is the only modeled closure.
- Factory wire A:19 similarly separates global MEMW/D5.26/A19A from the
  D7.2/A19B landing, with W19 as the only modeled closure.
- Factory wire A:20 separates D3.10/A20B from the co-located A20A/A23.1/X3.3
  cable island; W20 remains transparent in HDL while preserving that assembly.
- 76 modeled nets still carry source-risk annotations requiring
  physical evidence or an explicit redesign before fabrication release.
- The runnable video path reads DRAM through a simulation-only second port.
  Physical D41/D42/D43 and mux/decode instances exist, but faithful shared-DRAM
  slot timing still needs D41 and adjacent one-shot/mux/counter evidence;
  D94's proved outputs belong to FDC control.
- CPU DRAM transactions are functionally closed: RAS spans row through CAS,
  and the РУ5 model implements early/delayed asynchronous writes without a
  synthetic sampling clock. Exact D36/R57 delays and DOUT turn-off remain
  physical evidence boundaries.
- Several device models implement only the modes exercised by the guarded Juku
  paths.
- Simulation-only CPU sampling, keyboard stimulus, framebuffer access, and
  interrupt helpers are excluded from LVS by an explicit allowlist in
  `sync/lvs.py`.

## Verification

```sh
sync/check.sh       # modeled KiCad/HDL connectivity
sync/boot_check.sh  # C and HDL boot/framebuffer regression
sync/cosim_check.sh # value-level read comparison vs the C emulator (cosim)
sync/ie7_check.sh   # К555ИЕ7/74LS193 device behavior and cascade
sync/ie10_check.sh  # К555ИЕ10/74LS161 behavior and traced D103 /13 loop
```

See `../sync/README.md` for subsystem and deep checks. A green LVS result proves
only mapped connectivity; it does not cover omitted pins or validate device
behavior.
