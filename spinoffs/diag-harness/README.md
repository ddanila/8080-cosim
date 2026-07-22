# Juku diagnostic harness (diag-ROM + Arduino Nano + host tool)

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
- **Host tool** (Python CLI) drives the protocol and prints verdicts. It talks
  to cosim's pty during development and to the Nano's USB port on the bench —
  same code, same protocol.

A Nano is sufficient for every stage except the optional bus-master stage
(~30 GPIO needed for address+data+control — that is Mega 2560 territory).

## Staged plan

- **Stage D0 — diagnostic ROM alone.** Stack-free sign-of-life over serial →
  ROM checksum (the firmware's own block-1 convention,
  `docs/cosim-runtime-reference.md`) → RAM march test streamed byte-by-byte.
  Because the populated bank is bit-per-chip (D84–D91 К565РУ5,
  `docs/hardware-map.md`), a failing bit pattern names the exact chip.
  Then PPI/PIT/PIC register-wiggle tests, framebuffer test pattern (needs
  RAM), beeper codes (`docs/beeper-readiness.md`) as the serial-less fallback.
- **Stage D1 — Nano + host software.** Nano firmware (bridge + liveness
  probes) and the Python CLI with human-readable verdicts.
- **Stage D2 — upload-to-RAM.** Serial loader in the same ROM: receive
  length+payload+checksum into tested-good RAM, jump. This turns the harness
  into a development channel for the real board, not just diagnostics.
- **Stage D3 (optional) — external bus master.** Mega-based probe via
  X1/`−INHIBIT`, or CPU-socket ICE. Only worth it for boards where the CPU
  path itself is dead; the CPU-socket route is genuinely complex (КР580ВК38
  expects the status byte during SYNC; the socket carries +12/−5 V rails).

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
  `docs/owner-measured-facts.md` first, as always.

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
4. X3 pinout and levels continuity-confirmed on the real board;
5. upload-to-RAM (D2) demonstrated end-to-end in cosim before it is ever run
   on hardware.
