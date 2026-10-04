# VJUGA Phase 4 — observability, assembly, and bench bring-up plan

Status: **TOOLS AND BOARD-MODEL CHECKS IMPLEMENTED / HARDWARE PENDING**.
The capture reassembler and twin comparison are executable. Physical clock,
analyzer sampling and programmed-GAL behavior still require qualification.
Use [manufacturing readiness](rev-a-manufacturing-readiness.md) for current
routing/package holds before planning fabrication.

The planned physical sequence is to boot Rev A with western parts, then test
the scarce Juku РУ5/РТ4/РЕ3 chips one at a time against the simulation twin.

## 4.0 Implemented observability interfaces

These interfaces are present in the board model (`rev-a-physical.board.json`).

| Item | What | Why |
|---|---|---|
| J96 clock-control jumper | 2-pin: `OSC_OE_N` / `GND` | `R4` pulls `OSC_OE_N` high (oscillator runs). Shorting J96 tri-states U50's output, freeing the `CLK` net so the Arduino UNO rig can drive the CPU clock through J92.10. No cut traces, no socket games. |
| J97 high-address header | 1×10: `A8..A15`, `MEM_WR_N`, `GND` | Provides high address bits for 16-bit write reconstruction; `MEM_WR_N` is the capture clock (see channel map). |
| J98 control-bus header | 1×8: `MREQ_N`, `IORQ_N`, `RD_N`, `WR_N`, `M1_N`, `RFSH_N`, `WAIT_N`, `GND` | Provides the control bus for stepping and control-view captures. |
| NOP-plug provision | none (documentation only) | Free-run test uses an empty U2 socket plus a resistor plug on J91 (8× ~1 kΩ, D0-D7→GND) so every fetch reads `0x00` = NOP. No board change needed — J91 already carries D0-D7 + GND. |

`check_rev_a_physical.py` requires J96/J97/J98 and checks their signal assignments.
The NOP plug is an external fixture, with no added PCB copper.

## 4.1 Planned analyzer channel maps (24 data channels plus capture clock)

These profiles define the required signals for an external analyzer. The
repository does not implement or qualify RP2350 capture firmware or its input
hardware. Before connecting, verify the selected analyzer's 5 V input interface,
channel count, capture-clock support and sampling timing.

**Profile FB (framebuffer readback — the workhorse):**

| Channels | Signals | Source header |
|---|---|---|
| CH0-7 | A0-A7 | J90.1-8 |
| CH8-15 | A8-A15 | J97.1-8 |
| CH16-23 | D0-D7 | J91.1-8 |
| write strobe | `MEM_WR_N` (sampling edge requires qualification) | J97.9 |
| trigger | `RESET_N` rising | J91.10 |

The profile requires 24 data channels plus a dedicated strobe input. Select
the sampling edge or delay after measuring address/data validity relative to
`MEM_WR_N`; the channel map alone does not prove one valid sample per write.
Confirm that the exported stream includes every write in the chosen workload.

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
**Byte identity proves the captured workload at its chosen cutoff.** Rev A
does not need VGA electronics for this comparison. A bounded capture does not
prove completion of the boot banner or the full RAM test.

Implemented replay path:

1. `tools/vjuga_fb_readback/reassemble.py` — reads a capture stream (`ADDR DATA`
   hex per line), replays writes in order into a zero-filled 64 KiB image,
   extracts `0xD800–0xFDA7` (40×241 bytes), and writes the framebuffer binary.
   Unwritten bytes remain zero; a physical capture must establish those bytes
   or include writes to them before comparison with the oracle.
2. Twin-side capture emitter — `hdl/vjuga_juku_top.v` `+capture=<file>` logs
   every framebuffer write in that exact format.
3. `sim/vjuga_readback_check.sh` — boots the twin with `+capture`, reassembles,
   and requires `reassemble(capture) == twin dump == cosim vram.bin`
   (default `WRITES=6000`). Wired into `sim/check.sh`. This validates the replay
   path for twin-generated captures at that cutoff. A physical
   mismatch may also arise from sampling, wiring, omitted writes or initial
   state; verify the capture chain before blaming a chip. Use the same write
   cutoff and initial framebuffer state for capture and oracle; retain the ROM
   identity and cutoff with each result.

## 4.3 Arduino UNO single-step rig — DONE (sketch + reference trace)

For static, human-speed inspection (5 V-native, no level shifting):

- **Clock**: J96 shorted (oscillator tri-stated); UNO drives `CLK` on J92.10.
  Confirm that the fitted CPU and support parts permit the chosen clock
  waveform and pauses. Single stepping does not maintain DRAM retention;
  qualify its refresh/WAIT behavior before using a RAM-dependent trace.
- **Bus readback**: four 74HC165 parallel-load shift registers chained into the
  UNO's GPIO-driven serial input: A0-A15 (J90+J97), D0-D7 (J91), and `MREQ_N/IORQ_N/RD_N/WR_N/M1_N/
  RFSH_N/WAIT_N` + `DEC_ROM_N` (J98+J95) = 32 bits per snapshot.
- **Sketch**: `tools/vjuga_single_step/vjuga_single_step.ino` (beside
  `rt4_dumper` — same Arduino conventions). Serial protocol: `s` = one clock,
  `r` = run the compile-time `RUN_STEPS` count (400), `z` = zero the trace counter
  (not reset the CPU). At 115200 baud, each sampled transition into
  `M1_N=MREQ_N=RD_N=0` prints one
  line: `F<n>: addr=<hhhh> data=<hh> m1=<b> mreq=<b> rd=<b>`.
- **Twin reference trace**: `hdl/vjuga_juku_top.v` `+trace=<file>` emits the
  first 256 M1 fetches in the identical line format;
  `tools/vjuga_single_step/gen_reference_trace.sh` produces it on demand
  (default `DECODE_MODE=0`, Mode B; use `DECODE_MODE=1` for Mode A).
  The expected early fetches include `F0: addr=0000 data=c3` = the reset JP and
  `F6: addr=0021 data=00` =
  the patched NOP. Compare only fetch lines from the same reset, ROM and decode
  mode, excluding the sketch's `#` status lines. Divergence points at
  the exact fetch.

## 4.4 Assembly & bring-up ladder

Each step gates the next; every observation has an expected value *before* the
step runs. Western parts throughout until step (g).

| # | Step | PASS signal |
|---|---|---|
| a | Compile, program and independently verify U5 and U24 for the selected GAL devices; verify the selected ROM against its source image and U2 pin contract | Independent GAL/ROM readback identities recorded; ROM socket compatibility confirmed |
| b | Sockets + passives only; power via bench supply on J1 | PWR_OK LED on; rails 5 V ± 5 %; idle draw ≲ 50 mA; no warm parts |
| c | Insert U50 + U51 only | CLK = 4 MHz square on J92.10 (scope); RESET_N clean single rising edge; D4/D5 LEDs behave |
| d | Free-run NOP test: Z80 + GAL in, **U2 empty**, NOP plug on J91, J94 = Mode A | A0-A15 binary-count on the analyzer (Profile FB, clock on RD_N); M1 LED (D6) lit dim; RFSH LED (D7) active |
| e | Mode A baseline boot: + ROM, 8255, 74xx, KM4164 bank | Profile FB capture → `reassemble.py` → byte identity with the matching cosim workload; record cutoff and separately confirm the completed banner for baseline acceptance |
| f | Single-step session: J96 shorted, UNO rig on | first ~200 M1 fetches `diff`-clean against the twin reference trace |
| g | Chip tests — ONE scarce part at a time into the proven baseline, re-run the step (e) readback after each swap | matching capture for the tested boot workload; broader part qualification remains separate |
| h | D6 polarity guard (see 4.6) | `DEC_ROM_N` low during reset fetch and agrees with the corrected twin |

Step (g) order (increasing blast radius, decreasing part count):

1. **К565РУ5 DRAM** — swap KM4164 → РУ5 one socket at a time (or full bank if
   impatient; one-at-a-time localizes a bad part to a socket). Still Mode A.
2. **D8 К155РЕ3** into U4 (still Mode A — the РЕ3 is *observed*, not load-bearing):
   Profile CTL / J95.5-12 must show the `.039` pattern (`0xEF` ROM-low rows,
   `0xDF` ROM-high rows) as the boot walks the ROM.
3. **D6 К556РТ4** into U3, J94 → Mode B — the РТ4 now *drives* the decode.
   Boot-to-banner is the chip test.

Record every insertion in a physical-session record: date, chip serial/marking, socket,
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
`ROM_CE_N` is asserted. Record that agreement as Rev A physical evidence;
any unexpected high level requires checking the capture, mode and PROM/socket/GAL path, not a license to restore
the superseded bit-reversed interpretation.

## 4.7 Exit criteria

- Baseline board completes the banner in Mode A; retain a framebuffer capture
  and matching oracle that cover completion, beyond the bounded default in 4.2.
- At least one РУ5 and one РТ4 have a recorded PASS for the tested boot workload,
  and one РЕ3 has a matching observed output table in Mode A. The РЕ3 does not
  drive the decode in this test; these results do not establish full part qualification.
- The D6 active-low observation agrees with both twins and the GAL source.
- A physical-session record identifies every scarce part tested and its capture.
