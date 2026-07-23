# Jukuravi — Juku diagnostic harness (diag-ROM + Arduino Nano + host tool)

"Jukuravi" = Estonian for "Juku-therapy": the harness that examines and
treats a sick board.

Status date: 2026-07-23.

Status: **EXECUTION STARTED — D1 HOST, BRIDGE, STARTUP RESET GUARDED; PROBES NEXT.**

A diagnostics spin-off for the **real production board** (the owner's
`ДГШ5.109.009` processor module #2), not the replica: a custom diagnostic ROM
that runs with **zero working RAM**, an Arduino Nano acting as the smart
console, and host software that turns the output into verdicts ("RAM bit 3
fails → replace D87", or "everything passes"). In the advanced stage the same
ROM uploads programs into tested-good RAM and runs them.

Everything is developed and validated **in cosim first** (plus the HDL twin),
then connected to the real board. This document records the feasibility
assessment and the staged plan; it is not a build log.

## Why this is feasible on the .009 board

Three properties of the real board make it friendly (all root-doc facts,
cited per the commons contract in `docs/spinoff-commons.md`):

1. **The BIOS ROMs are socketed.** D15–D22 are 2764-class devices in sockets
   (`docs/official-009-ic-census.md`, `docs/eprom-programming-images.md`).
   After reset the board maps ROM at `0x0000` (mode 0 of the 4-mode overlay,
   `docs/hardware-map.md`), so a diagnostic ROM in the D15 socket runs first,
   before anything touches RAM.
2. **There is already a UART on the board.** The 8251 USART (D11, ports
   `0x08–0x0B`) goes out to bracket connector X3 through К170АП2/УП2
   (1488/1489-class RS-232 line drivers), `docs/serial-handoff.md`. Polled
   8251 I/O needs no RAM and no interrupts — it is the talk-back channel.
3. **X1 exposes the whole buffered bus.** The 96-pin edge connector carries
   buffered active-low data/address plus `−MRDC/−AMWTC/−IOM/−INHIBIT`
   (`ref/schematics/system-bus-connector-map.md`) — the hook for the optional
   external-bus-master stage.

**Constraint that shapes the ROM:** until RAM is proven there is no stack —
no `CALL`/`RET`/`PUSH`; registers and `JMP` only.

**Dead idea, recorded so it is not re-proposed:** the classic
"bit-bang through the tape jack" channel does not exist here — the `.009`
FDC revision dropped the cassette circuit entirely; only a masked legacy
`TAPE RUN INT` label survives (`docs/replica-bringup-verification-points.md`,
`docs/serial-handoff.md`).

## Role split

- **Diagnostic ROM** does the heavy lifting: all tests run on the 8080 itself,
  streaming results out through the 8251.
- **Arduino Nano** is the smart console, not a ROM emulator or bus driver:
  USB↔serial bridge (through a MAX3232-class shifter — X3 is ±12 V RS-232,
  a 5 V Nano must not touch it directly) plus a few GPIO liveness probes for
  the failure class where the ROM never speaks: reset released? derived clock
  toggling? `−MRDC` pulsing? Candidate probe nets are already cataloged in
  `docs/replica-bringup-verification-points.md`. **Implemented firmware
  checkpoint:** the classic-Nano sketch keeps D0/D1 for 115200 USB, bridges D8/
  D9 at nominal 9600 through the level shifter, and asserts CTS with D10. Its
  shared core is binary-transparency tested and the exact sketch AVR-compiles;
  see `nano/README.md`. D4 now drives the isolated startup-reset input; probe
  pins and all board-side contacts remain measurement-gated.
- **Nano-driven hardware reset (required for unattended runs).** The 8080
  has no NMI, so no firmware watchdog can reclaim a hung uploaded test that
  runs with interrupts masked — a hardware reset is the only reliable
  recovery. Implementation: a Nano GPIO drives an optocoupler or
  open-collector transistor **across the S1 reset-switch contacts**
  (electrically "pressing the switch"; never push-pull-drive the reset-RC
  node — VD1 sits in that corner, and the measured chain reaches D1.12
  active-high RESET, `docs/owner-measured-facts.md`). Reset also returns
  the PPI memory mode to 0, so the ROM regains control at 0x0000 and
  re-announces over serial: upload → run → heartbeat timeout → reset pulse →
  banner → host retries, fully unattended. The Nano can also hold reset
  during hookup and pulse it before each session for deterministic runs.
  **Implemented firmware checkpoint:** each Nano sketch start asserts D4 only
  into an optocoupler LED for 250 ms, releases it, and keeps the bridge quiet
  for 50 ms recovery. Boundary and `millis()`-rollover tests guard the portable
  sequencer, and the actual AVR sketch compiles. The board-side isolated
  contact remains forbidden until the SPDT S1 reset pair is measured;
  automatic retry and reset-hold control are not yet implemented. **Implemented
  host checkpoint:** before a real `--port` session, `host.py` explicitly
  releases DTR for 50 ms and reasserts it, restarting the Nano and therefore
  this startup pulse on standard classic-Nano hardware. The JSON log records
  the request and successful DTR ioctl separately from any unobserved physical
  reset.
- **Host tool** (Python CLI) drives the protocol and prints verdicts. It talks
  to cosim's pty during development and to the Nano's USB port on the bench —
  same code, same protocol. Every session is logged verbatim (raw stream +
  decoded verdicts, timestamped), matching the repo's provenance culture: a
  verdict like "D87 bad rows 0x80–0xFF" is a citable artifact from a named
  session, not a memory. **Implemented simulation checkpoint:** `host.py`
  validates the banner identity, sends the exact framed ACK, decodes all 192
  page records, prints per-chip and largest-good-window verdicts, and writes
  timestamped RX, TX, and JSON logs. Its inherited-fd transport round-trips
  against cosim; `--port` uses the same session engine plus the guarded DTR
  restart for the Nano USB device.

A Nano is sufficient for every stage except the optional bus-master stage
(~30 GPIO needed for address+data+control — that is Mega 2560 territory).

## Staged plan

- **Stage D0 — diagnostic ROM alone.** A strict boot ladder in which every
  rung is stack-free (registers + JMP only) and no rung assumes anything the
  previous rungs have not proven:
  1. **Alive-beep** (~0.5 s) as the very first act: PIT #2/D57 channel 1
     drives the speaker (`docs/beeper-readiness.md`), programmable with OUT
     instructions and a register delay loop — zero RAM. One beep proves
     CPU + ROM fetch + bus + PIT + the analog path. (No beep at all is
     disambiguated by the Nano's `−MRDC` liveness probe: CPU dead vs beeper
     path broken.) **The beep doubles as a measurement:** the Nano
     timestamps OUT1 edges through its probe, and known divisor × measured
     frequency yields the PIT's actual input clock — empirically closing
     the CPU-Φ/baud-clock open unknown on the very first boot.
     **Implemented simulation checkpoint:** the exact 8 KiB D15 image, build
     contract, disassembly, hash, and cosim/HDL guard are in
     `firmware/README.md`. It programs a nominal 1 kHz tone for 0.5000175 s,
     silences D57, and halts without changing SP or writing RAM. This is not
     yet a bench-burn authorization.
  2. **CPU self-test** — "executes" is not "computes correctly": a failing
     КР580 can run code yet get flags, rotates, or DAA wrong, silently
     poisoning every later verdict. A register-only instruction smoke test
     (ALU ops, rotates, flag behavior, DAA) accumulates a signature in
     registers and compares against the known-good constant; a distinct
     beep code on mismatch. Zero RAM.
     **Implemented simulation checkpoint:** the combined 8 KiB D15 image
     preserves the rung-1 alive sequence, checks 17 ALU/flag/rotate/DAA
     results through a rolling `D0` signature, and halts on success. Any
     branch or signature mismatch selects a continuous nominal 250 Hz
     CPU-bad tone. Cosim and the vm80a-based full HDL top prove both the
     success path and an injected bad-signature path, with no stack
     instructions and no RAM writes; exact image/hash details are in
     `firmware/README.md`.
  3. **Serial handshake** — before the RAM survey, because the 8251 is
     polled I/O and needs no RAM. First a **local 8251 self-test** (after
     init, do TxRDY/TxEMPTY status transitions behave across a written
     byte?) so "serial dead" splits into *8251 dead* vs *8251 fine,
     path/cable/Nano side dead* — different beeps, different bench
     actions. Then the link proper: a train of `0x55` bytes (alternating
     bits — a bit-width ruler) so the Nano auto-bauds and locks regardless
     of the unresolved baud-clock divisor, then the banner (carrying ROM
     version + self-checksum so the host knows exactly what it is talking
     to), then await the Nano's ack with a register-loop timeout. Distinct
     beeps for serial-confirmed vs serial-dead; if dead, all later results
     fall back to beep codes.
     **Local-test simulation checkpoint implemented:** the third exact 8 KiB
     image recovers and initializes D11, verifies the independent idle,
     holding-full, frame-active, and fully-empty transmit states around a `55`
     byte, and uses bounded register-only timeouts. A stuck transmitter selects
     a continuous nominal 500 Hz USART-bad tone. Cosim and the full vm80a HDL
     top prove success, injected stuck-TX, and predecessor CPU-bad paths with
     exact I/O and no RAM writes. This separates a working D11/baud-clock core
     from the still-untested outbound line-driver and ack path. Because the
     8251A cannot start without active-low CTS and the receiver is inactive for
     an open input, the Nano/level-shifter must assert X3 CTS before reset; a
     missing/non-asserting harness takes the bounded USART-stage failure path.
     The HDL fixture drives that connector input plus the already-documented
     unresolved upstream 16 MHz rail boundary; D104 and the modeled
     D103/D57/D11 clock chain remain in circuit.
     **External-link simulation checkpoint implemented:** the fourth exact
     8 KiB image extends the first `55` into a 16-byte training run, emits a
     self-delimiting `A5 5A` banner carrying protocol version, ROM version, and
     full-image CRC-16, and accepts only the matching CRC-8-protected ACK under
     bounded register-only waits. A valid ACK gives a short nominal 2 kHz
     serial-confirmed beep; malformed or missing ACK gives a continuous
     nominal 125 Hz serial-dead tone. Cosim proves valid, malformed, complete
     timeout, local-transmitter-fault, and CPU-fault paths through a PTY. The
     full vm80a top additionally shifts valid and corrupt ACKs from X3 `SIN`
     through D104 into D11 and proves the timeout path, with zero RAM writes.
     Exact wire bytes, checksum exclusions, hashes, and guard details are in
     `firmware/README.md`; this remains a simulation checkpoint, not bench-burn
     authorization.
  4. **RAM survey — find usable windows, don't just fail.** The populated
     bank is bit-sliced: D84–D91 (К565РУ5, 64K×1) each hold ONE BIT of
     every byte across the whole 64 KiB (`docs/hardware-map.md`) — no chip
     owns an address block. Therefore: a fully dead chip leaves NO usable
     window anywhere, but the failing bit position names the exact chip to
     replace (N beeps = D84+N, or named over serial). Partial failures
     (bad cells/rows/columns — the common case; internally 256×256 per
     chip) corrupt only the addresses sharing the bad row/column, so a
     usable window can exist — and **the window analysis lives on the
     host, not in the ROM**: with no proven RAM there is nowhere on-device
     to store a health map. The ROM marches the map in 256-byte blocks and
     emits one byte per block (OR-mask of failing bit positions,
     register-accumulated) — constant 256-bytes-per-pass traffic whether
     RAM is pristine or a chip is dead. The host reconstructs per-chip
     health and failure geometry, picks the largest all-eight-bits-good
     window, and simply parameterizes the D2 loader with addresses inside
     it (including the uploaded code's stack pointer) — the ROM never
     needs window logic at all. First upload into a fresh window can be a
     better RAM tester running from RAM. Beep-only fallback (serial dead)
     does no window-finding: it wholesale-tests a couple of fixed candidate
     windows and beeps found/not-found — without serial nothing can be
     uploaded anyway. (The empty D60–D83 sockets are the 16K×1-era banks,
     not a software-selectable alternative bank.)
     **Coverage limit:** in mode 0 the ROM overlay hides 0x0000–0x3FFF, so
     the D0 survey covers 0x4000–0xFFFF only (ample for a landing zone);
     the low 16 KiB is tested later by *uploaded* code that runs from RAM
     and can switch to mode 3 freely — the ROM never mode-switches itself
     out from under its own program counter.
     **Refresh caveat (open unknown):** DRAM strobes flow through the
     video/timing chain and refresh scheduling is an open boundary
     (`docs/memory-timing-boundary.md`) — if refresh requires programmed
     PITs, RAM decays silently during ROM-only loops. The diag ROM
     replicates the BIOS timer init early, and the survey includes a
     retention pass (write, wait, re-read), not just a march.
     **Serial-survey simulation checkpoint implemented:** the fifth exact
     8 KiB image stays in mode 0 and surveys every page from `40` through `FF`
     with `00`, `FF`, low-address, inverse-address, and `55` patterns, including
     an approximately 20 ms retention interval and a cross-page alias probe.
     Each page executes identical traffic and emits a framed page/failure-mask
     record. The shared host decoder
     groups bad pages by D84–D91 data bit and chooses the largest contiguous
     all-bits-good window. Full-range cosim proves pristine RAM and a combined
     stuck-low/stuck-high cell fault plus a two-page address alias; the vm80a top proves the identical loop
     body against clean and forced-D87 physical DRAM cells. Exact bytes,
     checksum, traffic counts, and bounded HDL-fixture scope are documented in
     `firmware/README.md`.
     **Beep-fallback simulation checkpoint implemented:** the sixth exact 8 KiB
     image retains the acknowledged full survey. Without an ACK it gives a
     finite serial-dead marker, tests fixed 4 KiB windows at `4000` and `C000`,
     and emits either three windows-found pulses or 1–8 D84–D91 chip-ID pulses
     followed by continuous no-window tone. Exact-image cosim and the bit-sliced
     vm80a DRAM path prove clean and globally dead-D87 outcomes without stack,
     interrupts, or a memory-mode switch. The complete cadence table and
     fixture scope are in `firmware/README.md`.
  5. **Everything else:** ROM checksum (the firmware's own block-1
     convention, `docs/cosim-runtime-reference.md`), PPI/PIT/PIC
     register-wiggle tests, framebuffer test pattern (needs RAM).
     **ROM-convention simulation checkpoint implemented:** the seventh exact
     8 KiB image reserves EktaSoft's `000A` header byte, stores the additive
     sum of `000B..07FF`, and recomputes all 2,037 bytes after the CPU test but
     before touching D11. Exact-image cosim retains both acknowledged-survey
     and no-ACK fallback paths; a covered-byte flip produces only a continuous
     nominal 2 kHz ROM-bad tone with no serial or RAM activity. The vm80a twin
     proves the same clean/corrupt branch through D15. At that checkpoint,
     peripheral register wiggles and the later RAM-backed framebuffer pattern
     remained next.
     **PIC-register simulation checkpoint implemented:** the eighth exact
     8 KiB image performs the BIOS's `D6/FE` MCS-80 initialization, writes and
     reads D10's interrupt mask as `00` then `FF`, and restores `FF` on success
     or failure while CPU interrupts remain disabled. Exact-image cosim proves
     both stuck-bit polarities plus the cumulative serial/RAM paths; vm80a
     proves clean and forced-low D10 readback through the physical port decode.
     A mismatch gives a continuous nominal 4 kHz PIC-bad tone before USART or
     RAM activity. This bounded test does not claim the priority/INTR/INTA
     engine.
     **PPI-register simulation checkpoint implemented:** the ninth exact 8 KiB
     image drives D27 ports A/B/C through `00` and `FF` in mode-0 output, reads
     every value back, and restores all ports to input with cleared output
     latches on success or failure. Exact-image cosim proves both stuck-bit
     polarities and all cumulative serial/RAM paths; vm80a proves the clean and
     forced-low Port-C branches plus the shared two-window fallback loop. The
     X2 auxiliary connector must be disconnected: this is a register/latch and
     decode test, not a connector-load test. A mismatch gives a continuous
     nominal 750 Hz PPI-bad tone before USART or RAM activity.
     **PIT-register simulation checkpoint implemented:** the tenth exact 8 KiB
     image checks all nine D54/D55/D57 counters with latched, phase-tolerant
     DB7-high and DB7-low predicates, then recovers D57 before continuing or
     selecting a continuous nominal 1.5 kHz PIT-bad tone. A 251-byte extension
     after the framed tables has its own stack-free additive guard; corruption
     reaches the earlier ROM-bad halt before PIT, USART, or RAM activity.
     Exact-image cosim proves every counter/control select, both stuck-bit
     polarities, and cumulative ACK/no-ACK paths. vm80a proves clean, forced
     D55 failure, corrupt-extension, and both shared fallback outcomes through
     the three physical PITs.
     **Framebuffer-pattern simulation checkpoint implemented:** the eleventh
     exact 8 KiB image draws only after the acknowledged full RAM survey and a
     final `55` verification of the 9,640 visible bytes at `D800..FDA7`. It
     writes and reads back an address-XOR field, while a bad precondition or
     readback selects a continuous nominal 3 kHz tone. Both executable
     extensions are independently additive-guarded. Exact-image cosim proves
     the complete 40×241 pattern, D84 fault suppression, corrupt extensions,
     and the no-ACK predecessor. vm80a proves a bounded eight-row draw,
     readback, abstract pixel stream, fault halt, and both physical fallback
     outcomes. This closes the planned D0 firmware ladder in simulation. The
     Stage D1 host CLI and Nano bridge are guarded below; reset and probes are
     next after their measurement gates close.

  The beep vocabulary is a tiny fixed set (alive / cpu-bad / rom-bad /
  pic-bad / ppi-bad / pit-bad / framebuffer-ram-bad / usart-bad / serial-ok /
  serial-dead / chip-N-dead / windows-found), documented so a human with no
  Nano attached can triage by ear.

  **ROM discipline:** interrupts stay disabled for the diag ROM's whole
  life (the 8080 resets with them off; never `EI` — the PIC IMR is now tested,
  but its vector engine is not, and a spurious RST vectors into nothing). The
  entire diag ROM fits D15's 8 KiB with zero dependence on D16's contents: one
  socket swapped, one variable changed.

  **Protocol discipline:** the serial protocol is framed records
  (type/length/payload/CRC), not free text, from day one — self-delimiting
  so the host can re-attach mid-stream after a reset pulse and resume
  decoding at the next frame boundary. Cheap now, painful to retrofit.

  **Optional fallback channels** (not gating, recorded so they aren't
  re-invented): if the 8251 path is broken, the ROM can bit-bang slow
  telemetry on the beeper — serial-dead need not mean data-dead; the
  input direction has a mirror fallback via the keyboard lines (PPI Port
  A/B, reachable at X9): the Nano can drive matrix lines to send slow
  commands with the 8251 fully dead, and — simpler — the ROM samples the
  keyboard at boot so a human holding a key selects a test mode with no
  host attached at all; and once RAM + video prove good, verdicts can be
  mirrored to the framebuffer, letting the Juku diagnose itself to its
  own monitor with no Nano attached.

  **Analog beeper tap (optional Nano channel):** the speaker unit
  (ДГШ5.884.001) solders to two posts — the easiest attachment point on
  the whole board, no IC clips — and VD4 already clamps the coil kickback
  (`docs/beeper-readiness.md`); a series resistor makes it ADC-safe. What
  it buys: (a) completes fault isolation — activity at PIT OUT1 but
  silence at the posts pinpoints the analog stage (VT1/VD4/R48/speaker),
  silence at both pinpoints the PIT; (b) the Nano *hears* the beep codes
  (~10 kHz ADC sampling suffices for cadence and coarse pitch), so the
  beep vocabulary is machine-decoded even with serial down; (c) it is the
  natural front-end for the bit-banged telemetry fallback. For the rung-1
  clock measurement the digital OUT1 clip remains the precision option;
  the speaker tap gives a serviceable estimate with zero IC clips. The
  Nano ADC is ~10-bit/~10 kHz — cadence and envelope, not an oscilloscope.
  A spare ADC channel is worth pointing at the +5 V rail: logging it
  alongside test results catches the "RAM fails only when the rail sags
  under load" class that pure logic testing misattributes to chips
  (negative rails would need dividers — optional extras).
- **Stage D1 — Nano + host software.** Nano firmware (bridge + liveness
  probes) and the Python CLI with human-readable verdicts.
  **Host-session simulation checkpoint implemented:** the dependency-free CLI
  accepts the final D0 banner only after protocol/optional ROM identity checks,
  transmits its matching nine-byte ACK, validates the ordered full survey, and
  names D84–D91 failures plus the largest all-bits-good window. Clean RAM and a
  `7A5C:08:20` D87+D89 injection are exercised through the actual CLI process
  and exact version-8 ROM. Both sessions retain timestamped raw RX/TX and JSON
  evidence.
  **Nano-bridge checkpoint implemented:** D0/D1 hardware serial remains the
  115200 host side; D8/D9 `SoftwareSerial` is the nominal-9600 Juku side; and
  D10 asserts CTS through the MAX3232's second driver with an external
  boot-state pull-down. The bounded pump is checked with every byte value and
  the exact ACK in both directions, while `arduino-cli` compiles the actual
  ATmega328P sketch. Overflow latches D13 without changing the evidence stream.
  **Startup-reset checkpoint implemented:** D4 drives only an optocoupler LED,
  using a boot-state pull-down; the wrap-safe 250 ms assertion and 50 ms quiet
  recovery are boundary-tested before the bridge can run. The S1 contact side,
  automatic retry/reset-hold, and liveness probes remain gated or future work.
  **Host-controlled session-reset checkpoint implemented:** real `--port`
  sessions perform a release/wait/assert DTR sequence before reading, flush
  stale bytes, and log requested/completed state. Mocked modem-control ordering
  and failure are guarded; `--no-nano-reset` opts out and `--fd` remains raw.
- **Stage D2 — upload-to-RAM (the payoff stage).** Serial loader in the same
  ROM: on a host command ("load at address, N bytes, payload, checksum") the
  ROM writes the received bytes into tested-good onboard RAM, verifies, and
  jumps on a "run" command. Pure firmware + serial — no bus hardware
  involved. This removes the diag-ROM's own limitations: every new test
  (FDC, video, keyboard, timing) is a file the host sends, with no EPROM
  re-burn per iteration. Design notes: two-phase discipline (stack-free
  until the RAM march passes, ordinary stack code after); the ROM exposes a
  fixed-address jump-table API (serial in/out, print, return-to-loader) so
  uploaded tests get reporting for free; in mode 0 the region
  0x4000–0xD7FF is a clean landing zone with no bank switching needed —
  specifically, the all-eight-bits-good window the D0 RAM survey adopted.
- **Stage D3 (optional, likely never needed) — external bus master.**
  Mega-based probe via X1/`−INHIBIT`, or CPU-socket ICE. This is NOT the
  memory-upload path (that is D2, done in firmware); it exists solely for
  boards so dead the CPU cannot execute ROM code at all. The CPU-socket
  route is genuinely complex (КР580ВК38 expects the status byte during
  SYNC; the socket carries +12/−5 V rails).

## Host session CLI

The bench-facing command is:

```sh
python3 spinoffs/jukuravi/host.py \
  --port /dev/ttyUSB0 \
  --expect-rom-version 08 \
  --expect-crc16 8D59 \
  --log-dir sessions
```

The host-facing USB link defaults to 115200 baud. The Nano firmware in
`nano/jukuravi_bridge/` bridges that to the diagnostic ROM's nominal 9600-baud
8N1 link through a MAX3232-class level shifter. This is still not a bench-ready
claim: X3 continuity/levels and the SPDT S1 reset contact pair must be measured.
The firmware pulses the isolated reset input on each Nano start, but it must
remain disconnected from S1 until that measurement closes. By default, a real
`--port` session explicitly toggles DTR to restart the classic Nano before
waiting for the banner; use `--no-nano-reset` only when the adapter lacks or
must not use the DTR auto-reset circuit. `--fd` is the inherited PTY-master
transport used by the cosim regression and never receives modem-control
operations. A successful session creates one
timestamp-matched `.rx.bin`, `.tx.bin`, and `.json` set. The JSON contains the
validated image identity, every decoded frame, page masks, D84–D91 bad-page
lists, the selected largest good window, and whether DTR reset was requested
and its complete release/wait/assert/flush sequence succeeded.

## The cosim-first loop

The first infrastructure gap is closed in root `cosim/trace.c`: opt-in
`JUKU_USART_PTY` attaches either a host-created PTY or an automatically created
one, and models the D11 data/status mirrors at `0x08..0x0B`, the 8251
mode/command sequence, RxRDY, and the TxRDY/TxEMPTY transmit states. The
transmit side separates its CPU holding register from the shift register, so
the planned local test can distinguish status `00`
(holding full), `01` (holding empty but frame active), and `05` (transmitter
empty). `tests/cosim_usart_pty_test.py`, run by `sync/juk_disk_check.sh`,
executes a stack-free synthetic 8080 ROM through a real PTY: it sends `55 A5`,
receives `3C`, echoes it, and can finish only after observing the ready-state
transitions; the HDL unit guard proves the same intermediate status around its
8N1 shifter. The model is deliberately limited to the async slice needed by the
harness; sync/parity and physical baud timing remain outside this step.

The alive, CPU, ROM-convention, PIC, PPI, PIT, serial, mode-0 RAM-survey, and
framebuffer-pattern diagnostic-ROM rungs now run under cosim and the
vm80a-based HDL twin,
including injected ROM, PIC, PPI, PIT, USART, protocol, and bit-sliced RAM
failure paths, while the D57 beeper path has its own waveform/connectivity
guard. The 8253 register model and the cumulative diagnostic now compose:
focused model tests cover latch/read formats, BCD conversion, and pending-latch
ownership, while the ROM guard covers all physical counter selects with
phase-tolerant live-count predicates. The planned D0 ladder, Stage D1 host
session CLI, Nano serial bridge, and isolated startup-reset sequencer are
guarded, as is the host's DTR-commanded session restart. Automatic reset retry/
hold and liveness probes are next, after their physical measurement gates
close.
Then:

- the ROM is developed entirely against cosim and cross-checked on the HDL
  twin (`sync/cosim_check.sh` precedent);
- the host tool is developed against cosim's pty and reused unchanged on the
  bench;
- fault injection is scriptable rather than manual. Cosim now accepts
  `JUKU_USART_FAULT=tx_stuck`,
  `JUKU_PIC_FAULT=STUCK_LOW:STUCK_HIGH`,
  `JUKU_PPI_FAULT=PORT:STUCK_LOW:STUCK_HIGH`,
  `JUKU_PIT_FAULT=PORT:STUCK_LOW:STUCK_HIGH`,
  `JUKU_RAM_FAULT=ADDR:STUCK_LOW:STUCK_HIGH` (or `*` for every address), and
  `JUKU_RAM_ALIAS=PAGE_A:PAGE_B`; the D0 matrix asserts their exact protocol
  masks and host window verdicts. The cosim PIT slice deliberately preserves
  register/load/latch semantics without inventing a common clock for the three
  differently clocked and cascaded chips; live progression is cross-checked in
  HDL. Row/column-shaped RAM faults remain a later addition.

Per the commons contract, the 8251 model lands in root `cosim/`, not here —
this spin-off consumes it, and any bench finding it produces flows back to
root first.

## Open unknowns (measurement tasks, not blockers)

- Exact CPU Φ divisor from the 16 MHz master, and the PIT #2 input that
  clocks the 8251 baud (`docs/master-oscillator-boundary.md`,
  `docs/video-pit-timing.md`). Mitigation: conservative baud + auto-baud on
  the Nano side.
- X3 pinout must be continuity-confirmed before plugging anything in — check
  `docs/owner-measured-facts.md` first, as always. (The connector identity is
  already photo-closed: РГ1Н-1-4 12-contact panel socket, cable mate
  РШ2Н-1-23/-24 — see the owner-measured-facts bracket-connectors row.)
- S1 reset-switch contact arrangement: which contact pair closes to assert
  reset, and the node polarity — needed before wiring the Nano's reset opto
  across it.
- Whether DRAM refresh runs before the BIOS programs the PITs (refresh
  scheduling is an open root boundary, `docs/memory-timing-boundary.md`).
  Determines how early the diag ROM must replicate the timer init; resolve
  in cosim/HDL before trusting any bench RAM verdict. The rung-1 beep
  clock measurement also feeds back here (it pins the PIT input clock).

## Non-goals and guardrails

- No hardware is designed or ordered in this spin-off; the only physical
  artifacts are a burned EPROM, a Nano with a level shifter, and cables.
- Work here must not distract from the main replica's P0 closure items in the
  repository-root `PLAN.md` (same rule as VJUGA).
- This targets the owner's real board; nothing here relaxes the replica's
  design-hold rules.

## Entry gate for execution

Before bench connection, at minimum:

1. **DONE:** 8251 model merged in root `cosim/` with guarded PTY transport;
2. diagnostic ROM passes in cosim **and** the HDL twin, including injected
   faults (each fault class produces the intended verdict);
3. **DONE:** host tool round-trips the full protocol against cosim with clean
   and injected RAM failure, human-readable verdicts, and timestamped logs;
4. X3 pinout and levels continuity-confirmed on the real board, and S1
   reset-switch contacts identified for the Nano reset line;
5. upload-to-RAM (D2) demonstrated end-to-end in cosim before it is ever run
   on hardware.
