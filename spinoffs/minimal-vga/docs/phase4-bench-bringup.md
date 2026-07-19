# VJUGA Phase 4 — observability, assembly, and bench bring-up plan

Status: **SOFTWARE + BOARD-MODEL DONE / HARDWARE PENDING**. Everything that can
be built and verified against the simulation twin is implemented (§4.0 board
design-ins, §4.2 readback oracle, §4.3 single-step tracer + reference trace).
The remaining work is the physical ladder (§4.4 b-h). Phase 3 routing now
includes both the decode sockets and §4.0 design-ins and passes KiCad DRC; fab
package regeneration and independent review still gate hardware.

Phase 4 turns the fabricated Rev-A board into the working bench fixture: the
board boots the banner with western parts, then tests the scarce Juku
РУ5/РТ4/РЕ3 chips one at a time, with every observation comparable to the
verified simulation twin.

## 4.0 Design-ins that MUST land before the step (f) copper freeze — DONE

These are board-model (`rev-a-physical.board.json`) changes. Each is cheap in
copper and impossible to retrofit cleanly after fab.

| Item | What | Why |
|---|---|---|
| J96 clock-control jumper | 2-pin: `OSC_OE_N` / `GND` | `R4` pulls `OSC_OE_N` high (oscillator runs). Shorting J96 tri-states U50's output, freeing the `CLK` net so the Arduino UNO rig can drive the CPU clock through J92.10. No cut traces, no socket games. |
| J97 high-address header | 1×10: `A8..A15`, `MEM_WR_N`, `GND` | A8-A15 are currently on **no** header; without them the analyzer cannot reconstruct 16-bit write addresses, and `MEM_WR_N` is the capture clock (see channel map). |
| J98 control-bus header | 1×8: `MREQ_N`, `IORQ_N`, `RD_N`, `WR_N`, `M1_N`, `RFSH_N`, `WAIT_N`, `GND` | The Z80 control bus is currently on **no** header; the single-step rig and the control-view captures both need it. |
| NOP-plug provision | none (documentation only) | Free-run test uses an empty U2 socket plus a resistor plug on J91 (8× ~1 kΩ, D0-D7→GND) so every fetch reads `0x00` = NOP. No board change needed — J91 already carries D0-D7 + GND. |

**Done:** J96/J97/J98 are in `rev-a-physical.board.json`, the schematic is
regenerated, and `check_rev_a_physical.py` now requires these refs and enforces
an observability contract (A8-A15 + `MEM_WR_N` on J97, the control bus on J98,
`OSC_OE_N`/GND on J96). The NOP plug is documentation-only (no copper).

## 4.1 Fixed analyzer channel maps (RP2350, 24 channels, 5 V-tolerant inputs)

Two named capture profiles, so captures are comparable across sessions. The
analyzer's TXU-series level shifters + 5 V input select let it hang directly on
the bus.

**Profile FB (framebuffer readback — the workhorse):**

| Channels | Signals | Source header |
|---|---|---|
| CH0-7 | A0-A7 | J90.1-8 |
| CH8-15 | A8-A15 | J97.1-8 |
| CH16-23 | D0-D7 | J91.1-8 |
| capture clock | `MEM_WR_N` (falling edge = one memory write) | J97.9 |
| trigger | `RESET_N` rising | J91.10 |

24 data channels + a dedicated clock pin is exactly the budget: each
`MEM_WR_N` falling edge latches one `(addr, data)` pair — no sample-rate
guessing, no idle samples.

**Profile CTL (control view — single-step and decode debug):**

| Channels | Signals | Source header |
|---|---|---|
| CH0-7 | A0-A7 | J90.1-8 |
| CH8-15 | D0-D7 | J91.1-8 |
| CH16-21 | `MREQ_N` `IORQ_N` `RD_N` `WR_N` `M1_N` `RFSH_N` | J98.1-6 |
| CH22 | `ROM_CE_N` | U2.20 clip or J95 spare |
| CH23 | `DEC_ROM_N` (D6 РТ4 O1) | J95.1 |
| trigger | `RESET_N` rising | J91.10 |

## 4.2 Framebuffer readback without video hardware (the bench boot oracle) — DONE

The bench twin of `sim/vjuga_boot_check.sh`: capture every memory write during
boot (Profile FB), filter to `0xD800-0xFFFF`, replay the stream into a
9640-byte framebuffer image, and `cmp` against cosim's `vram.bin`.
**Byte-identical banner = boot PASS**, with zero display electronics (VGA stays
deferred).

Deliverables — **implemented and green** against the twin, before any hardware:

1. `tools/vjuga_fb_readback/reassemble.py` — reads a capture stream (`ADDR DATA`
   hex per line), replays writes in order into a 64 KiB image, extracts
   `0xD800 + 40×241`, writes the framebuffer binary.
2. Twin-side capture emitter — `hdl/vjuga_juku_top.v` `+capture=<file>` logs
   every framebuffer write in that exact format.
3. `sim/vjuga_readback_check.sh` — boots the twin with `+capture`, reassembles,
   and requires `reassemble(capture) == twin dump == cosim vram.bin`
   (both PASS at 6000 writes). Wired into `sim/check.sh`. The *tool* is thus
   validated by the same oracle as the *board*, so a later bench mismatch
   indicts the chip under test, not the script.

## 4.3 Arduino UNO single-step rig — DONE (sketch + reference trace)

For static, human-speed inspection (5 V-native, no level shifting):

- **Clock**: J96 shorted (oscillator tri-stated); UNO drives `CLK` on J92.10.
  The Z80 and 82C55 are static-friendly CMOS parts; hold time is unbounded.
- **Bus readback**: four 74HC165 parallel-load shift registers chained into the
  UNO's SPI: A0-A15 (J90+J97), D0-D7 (J91), and `MREQ_N/IORQ_N/RD_N/WR_N/M1_N/
  RFSH_N/WAIT_N` + `DEC_ROM_N` (J98+J95) = 32 bits per snapshot.
- **Sketch**: `tools/vjuga_single_step/vjuga_single_step.ino` (beside
  `rt4_dumper` — same Arduino conventions). Serial protocol: `s` = one clock,
  `r` = run N clocks, `z` = zero counter; each `M1_N` falling edge prints one
  line: `F<n>: addr=<hhhh> data=<hh> m1=<b> mreq=<b> rd=<b>`.
- **Twin reference trace**: `hdl/vjuga_juku_top.v` `+trace=<file>` emits the
  first 256 M1 fetches in the identical line format;
  `tools/vjuga_single_step/gen_reference_trace.sh` produces it on demand
  (verified: `F0: addr=0000 data=c3` = the reset JP, `F6: addr=0021 data=00` =
  the patched NOP). Bench session = `diff` against this. Divergence points at
  the exact fetch.

## 4.4 Assembly & bring-up ladder

Each step gates the next; every observation has an expected value *before* the
step runs. Western parts throughout until step (g).

| # | Step | PASS signal |
|---|---|---|
| a | Program + verify the U5 GAL (vectors from `rev-a-gal-equations.md`) and the 27C256 with `ekta37_z80.bin` (SHA-verified readback) | programmer verify pass; ROM SHA matches `roms/README.md` |
| b | Sockets + passives only; power via bench supply on J1 | PWR_OK LED on; rails 5 V ± 5 %; idle draw ≲ 50 mA; no warm parts |
| c | Insert U50 + U51 only | CLK = 4 MHz square on J92.10 (scope); RESET_N clean single rising edge; D4/D5 LEDs behave |
| d | Free-run NOP test: Z80 + GAL in, **U2 empty**, NOP plug on J91, J94 = Mode A | A0-A15 binary-count on the analyzer (Profile FB, clock on RD_N); M1 LED (D6) lit dim; RFSH LED (D7) active |
| e | Mode A baseline boot: + ROM, 8255, 74xx, KM4164 bank | **Profile FB capture → `reassemble.py` → byte-identical to cosim `vram.bin`** = board baseline PASS |
| f | Single-step session: J96 shorted, UNO rig on | first ~200 M1 fetches `diff`-clean against the twin reference trace |
| g | Chip tests — ONE scarce part at a time into the proven baseline, re-run the step (e) readback after each swap | byte-identical banner per swap = that part's PASS |
| h | D6 polarity guard (see 4.6) | `DEC_ROM_N` low during reset fetch and agrees with the corrected twin |

Step (g) order (increasing blast radius, decreasing part count):

1. **К565РУ5 DRAM** — swap KM4164 → РУ5 one socket at a time (or full bank if
   impatient; one-at-a-time localizes a bad part to a socket). Still Mode A.
2. **D8 К155РЕ3** into U4 (still Mode A — the РЕ3 is *observed*, not load-bearing):
   Profile CTL / J95.5-12 must show the `.039` pattern (`0xEF` ROM-low rows,
   `0xDF` ROM-high rows) as the boot walks the ROM.
3. **D6 К556РТ4** into U3, J94 → Mode B — the РТ4 now *drives* the decode.
   Boot-to-banner is the chip test.

Log every insertion in `docs/bench-log.md`: date, chip serial/marking, socket,
mode, result, capture file. The scarce parts are irreplaceable — cold board for
insertion, orientation double-checked against the chip-map pinout, no hot-swap,
and note the bipolar PROMs pull real current (power budget: ~130 mA each).

## 4.5 What a failure looks like (per chip class)

| Part | Failure signature on the bench |
|---|---|
| РУ5 bit-slice | banner differs from cosim in exactly one bit lane of every wrong byte → the failing socket = the bit index |
| D8 РЕ3 | J95 readback byte wrong at specific `A[15:11]` rows while the boot still passes (Mode A) → dead/shorted output pin or bad row, harmless to the baseline |
| D6 РТ4 | Mode B boot diverges or dies at the first decode boundary the bad output crosses; Profile CTL shows `ROM_CE_N`/`DEC_ROM_N` disagreeing with the twin's decode at a known address |

## 4.6 D6 polarity guard

Corrected reader-3 packing, factory labels, and direct continuity agree that
`DEC_ROM_N` is physical D6 D0/pin12 and is active low. At the reset fetch
(`A=0x0000`, firmware mode 0), J95.1 must therefore read **LOW** while
`ROM_CE_N` is asserted. Record that agreement in `docs/owner-measured-facts.md`;
any high level is a bad PROM/socket/GAL-path result, not a license to restore
the superseded bit-reversed interpretation.

## 4.7 Exit criteria

- Baseline board boots the banner in Mode A, proven by the framebuffer
  readback (4.2) — not by eyeballing.
- At least one РУ5, one РТ4, and one РЕ3 part each have a logged PASS in their
  functional role.
- The D6 active-low observation agrees with both twins and the GAL source.
- `bench-log.md` holds a per-serial record for every scarce part tested.

## Build order

1. **No hardware — DONE**: §4.0 board-model design-ins (J96/J97/J98 + checker
   contract); §4.2 readback tool + twin capture emitter + regression (wired into
   `sim/check.sh`); §4.3 sketch + twin reference-trace generator. All verified
   against the simulation twin.
2. **After fab-package regeneration + review:** fab, then the §4.4 ladder.
   — PENDING.
3. **Bench sessions** (owner): ladder steps b-h, logged in `docs/bench-log.md`.
   — PENDING (needs the fabricated board).
