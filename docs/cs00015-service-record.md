# Arvutimuuseum CS00015 service record

Status date: 2026-08-01

This record identifies the physical Juku under current diagnostic work as the
Arvutimuuseum machine `CS00015`.  The identifier is the same physical-source
name already used by the retained PROM captures under `ref/physical-proms/`.
It must not be conflated with Danila Sukharev's separate reference board.

## Observed discrepancies

### D15 firmware

Repeated reads established that three bytes in the fitted D15 EPROM differ
from the adopted official EktaSoft 3.7 low image, `ref/firmware/JUKUROM0.HEX`
(SHA-256
`d6c4ec7418f05e5761ef450e6ee36fb2579d65d9cbf87dce265eaf1c0d077596`).
This is a machine-specific observation, not a replacement for the repository's
adopted firmware.  The three offsets and byte pairs must be added when the raw
CS00015 D15 captures are retained in the repository; no unretained values are
reconstructed here.

### D55 timer

D55 is the middle of the three КР580ВИ53/8253 PITs and supplies vertical video
timing.  Audible ROM diagnostics produced the following repeatable evidence:

- T15 (`diag-d0-pit-debug-slow.bin`, SHA-256
  `34c110f209e7ccfffb3a261bea25b3b2e9d361eaaad57bcde638d744e8eed72a`)
  always passed all four D54 checkpoints, then stopped variably at D55
  checkpoints 5, 7, or 8.  These correspond to D55 channel 0 high, channel 2
  high, and channel 0 low readback respectively.
- T16 (`diag-d0-d55-stress.bin`, SHA-256
  `703514bd36ea3fb1c695b91259040571d601880f475f4562698c851ffbdfd0ce`)
  repeated each D55 predicate 32 times with eight 8080 NOPs of recovery after
  each control write, count write, and latch command.  Across repeated resets
  it consistently emitted failure code 3: channel 0 and channel 1 completed,
  while D55 channel 2 high-value readback failed before the channel 0 low test.

The bounded diagnosis is a bad or marginal D55, strongly localized to its
channel-2 behavior under recovery-spaced access.  It is not yet proof that the
IC die alone is defective: replacement or substitution is required to
distinguish the package from its local socket, solder joints, supply bypass,
and board-level channel-2 connections.

## Current CS00015 fault summary

| Location | Finding | Confidence / next discriminator |
| --- | --- | --- |
| D15 | Three bytes differ from the adopted official EktaSoft 3.7 low image | Repeat-read observation; retain raw dumps and exact byte diff |
| D55 | КР580ВИ53/8253 PIT fails consistently in channel-2 stress testing | Strong functional localization; replace/substitute D55 and rerun T15/T16 |

## Serial connector measurement

Owner continuity on 2026-08-01 identifies `X3.7` as signal ground.  The
CS00015 diagnostic cable can therefore use X3.9/SOUT, X3.4/SIN, X3.5/CTS,
and X3.7/GND through an RS-232 level interface.  X3 must not be connected
directly to TTL UART pins.

This document records preservation and repair evidence only.  Neither finding
changes the replica's adopted firmware or generic circuit model.
