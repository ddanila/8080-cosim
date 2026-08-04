# Arvutimuuseum CS00015 service record

Status date: 2026-08-04

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

The later cross-memory probe changes the localization materially. In all-RAM
mode, isolated reads return the deliberately written `66 C7` at both
`1A00/1A01` and `DA00/DA01`, while consecutive `LHLD` reads return `66 FF` and
`66 55`. Through the ROM mappings, the same classes return `3E 43` and
`3E 55`. A separate `4A00/5A00` RAM pair passes sixteen times. The fault is
therefore a region-dependent second-cycle failure on the shared address/timing
path, not a D15/socket-pin-2 fault. Clearing physical BA12 before memory decode
unifies the observations: `1A01 -> 0A01`, while `DA01 -> CA01` also leaves the
mode-1 high-ROM overlay. The final deliberately seeded alias proof is prepared
for the next successful loader boot. Owner tracing around D15 pin 2 found its
local PCB conductor intact, consistent with moving the diagnosis away from a
D15-local open trace.

Cosim now reproduces the complete host-visible signature. Clearing ROM A12
after the first uninterrupted D15 read loses the loader at `1100h`, `1200h`,
and `1400h`, while the lower-alias byte stream from `1A00h` accidentally jumps
to loader entry `0A0Ch` without changing the RAM premarker. The separate
`5A00h` CALL evidence (returned `A=5A` but marker remained `00`) proves its
uploaded stream was also not executed normally. Replacing its first fetched
`3Eh` with `00h` explains both CALL marker `00` and JUMP marker `01`, because
loader API v2 enters those modes with `A=00/01` respectively. These models are
guarded fault reproductions, not yet pin-voltage measurements. The newer
`JUKU_CONSECUTIVE_A12_LOW_PAGES=1,D` injection applies A12 loss before ROM/RAM
decoding and passes the clean/faulted pure-RAM alias matrix.
Exact image, controls, raw logs, and next
discriminators are in
[`../spinoffs/jukuravi/T32-PHYSICAL.md`](../spinoffs/jukuravi/T32-PHYSICAL.md).

After this substitution test, CS00015 was deliberately left with the donor D6
`.038` from the Danila Sukharev machine fitted; the original CS00015 D6 will
not be reinserted because repeated extraction would add mechanical damage
risk. Original CS00015 D8 `.039` was restored. This records component
provenance only and must not be read as a diagnosis of the original D6.

## Current CS00015 fault summary

| Location | Finding | Confidence / next discriminator |
| --- | --- | --- |
| D15 | Three bytes differ from the adopted official EktaSoft 3.7 low image | Repeat-read observation; retain raw dumps and exact byte diff |
| D55 | КР580ВИ53/8253 PIT fails consistently in channel-2 stress testing | Strong functional localization; replace/substitute D55 and rerun T15/T16 |
| Shared A12/timing path | Isolated ROM/RAM reads pass; consecutive `1Axx` and `DAxx` reads fail, while `5Axx` passes | Run seeded `0A/1A`, `4A/5A`, `8A/9A`, `CA/DA` alias matrix; compare D1.37, D4.15, and READY |
| `5A00h` execution | First fetched byte behaves as `00h`; explains CALL/JUMP markers `00/01` | Treat as a separate RAM execution-cycle symptom until the four-class matrix closes it |

## Serial connector measurement

Owner continuity on 2026-08-01 identifies `X3.7` as signal ground.  The
CS00015 diagnostic cable can therefore use X3.9/SOUT, X3.4/SIN, X3.5/CTS,
and X3.7/GND through an RS-232 level interface.  X3 must not be connected
directly to TTL UART pins.

This document records preservation and repair evidence only.  Neither finding
changes the replica's adopted firmware or generic circuit model.
