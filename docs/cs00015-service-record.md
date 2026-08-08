# Arvutimuuseum CS00015 service record

Status date: 2026-08-08

This record identifies the physical Juku that underwent the diagnostic work as
the Arvutimuuseum machine `CS00015`. The identifier is the same physical-source
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
The controlled before/substitute/after procedure and blank evidence record are
[`../spinoffs/jukuravi/D55-REPLACEMENT.md`](../spinoffs/jukuravi/D55-REPLACEMENT.md).

### D15 upper-ROM execution timing

T32 (`1B/D62B`) broadened the earlier T31 upper-ROM experiment across all
three reconstructed D2 wait classes. RAM-resident isolated reads sample both
`1A00h=3Eh` and `1A01h=1Ah` correctly sixteen times. Consecutive `LHLD` reads
localize the actual failure: the first upper-D15 byte is correct and the second
uses the exact A12-low alias. Repeated examples include `1A00: 3E 43` where
`43` is `0A01`, `1A02: 32 C3` where `C3` is `0A03`, and `1A04: 41 0E` where
`0E` is `0A05`; lower control `0A00: C3 43` passes.

This is not a static A12 fault, corrupt ROM data, general data-bit fault, or
failure isolated to one D2 wait class. T31 and T32 used two different physical
AT28C64B packages; both show correct isolated upper data and broken upper
execution on CS00015. One-at-a-time substitutions of donor D8 `.039` and donor
D6 `.038` preserve the result, excluding the original D6 and D8 packages as
unique causes.

The corrected all-RAM matrix changes the localization materially. Absolute
STA initialization shows the same second-byte A12-low alias in all four
A15:A14 regions, all four A10:A9 classes, LHLD, POP, and SHLD writes. Boundary
reads `0FFF -> 1000` and `2FFF -> 3000` pass, proving that carry can assert A12.

The earlier four-region setup used `INX D` to advance from each even to odd
address. On the physical CPU that increment changed every high-A12 pointer to
its low-A12 alias: the even byte reached `1A00/5A00/9A00/DA00`, while the odd
byte reached `0A01/4A01/8A01/CA01`. The eventual STAX is separated from INX by
CALL, stack, and instruction cycles. This architecturally visible register-pair
error cannot be caused solely by D4, D15, or a transient external BA12 load.
It localizes the common fault to D1's 16-bit increment path: carry into A12
works, but an already-high A12 is not retained.

A direct register-only probe then confirmed the diagnosis without any
high-address memory access. It returned `1000,0A01,4A01,8A01,1A01` for INX BC
from `0FFF`, INX DE/HL/SP from `1A00/5A00/9A00`, and DAD `1A00+1`. Thus carry
and DAD work while INX loses retained A12. Exact ROM LHLD pairs in CAS-gated,
no-wait, and always-wait classes all returned their A12-low second bytes 16/16.

Immediately before D1 replacement on 2026-08-06, a repeat of the unchanged
probe reproduced the same five faulty words. Immediately after replacement it
returned `1000,1A01,5A01,9A01,1A01`, the complete expected result. Both sessions
completed cleanly against T32 `1B/D62B` with the same probe hash and no serial
handshake mismatch. The retained before/after sessions therefore confirm that
the diagnosed behavior belonged to the replaced D1 rather than D4, D15, BA12,
READY timing, or the test transport.

Cosim now injects that single CPU behavior with
`JUKU_CPU_A12_INCREMENT_FAULT=1`. The model covers PC, INX, LHLD/SHLD, POP,
and boundary behavior and reproduces the meaningful bytes from six physical
probe classes in both clean and faulted regression runs.

The die-derived vm80a HDL core also reproduces the exact direct result when
only the shared incrementer's bit-12 retain-high/no-carry Boolean term is
removed. See `cs00015-d1-increment-analysis.md` for the bounded internal
diagnosis and the transistor/layout caveat.
Exact image, controls, raw logs, and completed replacement evidence are in
[`../spinoffs/jukuravi/T32-PHYSICAL.md`](../spinoffs/jukuravi/T32-PHYSICAL.md).

After this substitution test, CS00015 was deliberately left with the donor D6
`.038` from the Danila Sukharev machine fitted; the original CS00015 D6 will
not be reinserted because repeated extraction would add mechanical damage
risk. Original CS00015 D8 `.039` was restored. This records component
provenance only and must not be read as a diagnosis of the original D6.

## Post-diagnostic restoration

On 2026-08-08, after the diagnostic work was completed, the owner restored
CS00015 to its normal firmware configuration with **EK37 / EktaSoft 3.7**
(repository firmware profile `ekta37`) in the D15/D16 positions. The T31/T32
diagnostic firmware is no longer the fitted machine configuration; its images,
hashes, and physical results remain retained as diagnostic evidence.

This update records the fitted firmware identity reported by the owner. It
does not assert a new socket readback or byte-for-byte comparison, so the
earlier machine-specific D15 read discrepancy remains part of the service
history. The repaired-D1 finding, donor-D6/original-D8 provenance, and open D55
discriminator are unchanged.

## Current CS00015 fault summary

| Location | Finding | Confidence / next discriminator |
| --- | --- | --- |
| D15 diagnostic-era fitted EPROM | Three bytes differed from the adopted official EktaSoft 3.7 low image | Repeat-read historical observation; retain raw dumps and exact byte diff |
| D55 | КР580ВИ53/8253 PIT fails consistently in channel-2 stress testing | Strong functional localization; replace/substitute D55 and rerun T15/T16 |
| D1 16-bit increment path | The original D1 lost an already-high A12 during INX; carry and DAD worked | Confirmed and repaired: the fault repeated immediately before replacement and the unchanged probe passed immediately afterward |

## Serial connector measurement

Owner continuity on 2026-08-01 identifies `X3.7` as signal ground.  The
CS00015 diagnostic cable can therefore use X3.9/SOUT, X3.4/SIN, X3.5/CTS,
and X3.7/GND through an RS-232 level interface.  X3 must not be connected
directly to TTL UART pins.

This document records preservation and repair evidence only.  Neither finding
changes the replica's adopted firmware or generic circuit model.
