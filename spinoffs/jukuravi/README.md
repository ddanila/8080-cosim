# Jukuravi — Juku diagnostic harness (diag-ROM + Arduino Nano + host tool)

"Jukuravi" = Estonian for "Juku-therapy": the harness that examines and
treats a sick board.

Status date: 2026-07-22.

Status: **PLANNED / ASSESSED — no execution yet.**

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
  `docs/replica-bringup-verification-points.md`.
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
- **Host tool** (Python CLI) drives the protocol and prints verdicts. It talks
  to cosim's pty during development and to the Nano's USB port on the bench —
  same code, same protocol.

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
     path broken.)
  2. **Serial handshake** — before the RAM survey, because the 8251 is
     polled I/O and needs no RAM: init, send banner, await the Nano's ack
     with a register-loop timeout. Distinct beeps for serial-confirmed vs
     serial-dead; if dead, all later results fall back to beep codes.
  3. **RAM survey — find usable windows, don't just fail.** The populated
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
  4. **Everything else:** ROM checksum (the firmware's own block-1
     convention, `docs/cosim-runtime-reference.md`), PPI/PIT/PIC
     register-wiggle tests, framebuffer test pattern (needs RAM).

  The beep vocabulary is a tiny fixed set (alive / serial-ok / serial-dead /
  chip-N-dead / windows-found), documented so a human with no Nano attached
  can triage by ear.
- **Stage D1 — Nano + host software.** Nano firmware (bridge + liveness
  probes) and the Python CLI with human-readable verdicts.
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

## The cosim-first loop

The one gap: **cosim does not model the 8251 at all** (`cosim/trace.c` has
keyboard/PPI/video, no USART). The natural first commit of this spin-off is a
minimal 8251 model — data/status at `0x08/0x09`, TX/RX on a pty or socket.
Then:

- the ROM is developed entirely against cosim and cross-checked on the HDL
  twin (`sync/cosim_check.sh` precedent);
- the host tool is developed against cosim's pty and reused unchanged on the
  bench;
- fault injection is trivial in the emulator (stuck RAM bit, dead PPI, bad
  checksum) — each diagnosis is proven correct before any EPROM is burned.

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

## Non-goals and guardrails

- No hardware is designed or ordered in this spin-off; the only physical
  artifacts are a burned EPROM, a Nano with a level shifter, and cables.
- Work here must not distract from the main replica's P0 closure items in the
  repository-root `PLAN.md` (same rule as VJUGA).
- This targets the owner's real board; nothing here relaxes the replica's
  design-hold rules.

## Entry gate for execution

Before bench connection, at minimum:

1. 8251 model merged in root `cosim/` with a pty/socket transport;
2. diagnostic ROM passes in cosim **and** the HDL twin, including injected
   faults (each fault class produces the intended verdict);
3. host tool round-trips the full protocol against cosim;
4. X3 pinout and levels continuity-confirmed on the real board, and S1
   reset-switch contacts identified for the Nano reset line;
5. upload-to-RAM (D2) demonstrated end-to-end in cosim before it is ever run
   on hardware.
