# Arvutimuuseum CS00015 service record

Status date: 2026-08-14

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
timing. Audible ROM diagnostics produced the following repeatable historical
behavior:

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

**Superseded diagnosis, 2026-08-09.** The exact `.009` drawing and Intel 8253
load timing show that T15, T16, T31 and T32 did not establish the D54/D56
clocks required to transfer their newly written Mode-0 counts into D55 before
latching them. T16's NOP spacing delayed bus accesses but did not start those
clock sources. The codes above remain faithful observations, but they no
longer support “bad or marginal D55” or channel-2 package localization.

CS00015 is now **D55 functional path unverified**. Run T34 first. A T34 `08`
would still cover D55, its socket/power, D9 select, local strobes/data, D54
output paths and D56 clocks; controlled substitution is a later package
discriminator, not the next assumed action. Full reasoning and structural
negative controls are in
[`jukuravi-d55-diagnostic-audit.md`](jukuravi-d55-diagnostic-audit.md). The
revised substitution record is
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

## Post-diagnostic restoration and Ekta4401 service ROM

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

On 2026-08-11 the owner temporarily replaced that normal pair with the
project's Ekta4401 service-ROM pair. Both AT28C64 programming images were
verified in Willem's built-in post-write read: D15 CRC32 `5E306759`, 8,167
changed and 25 unchanged bytes; D16 CRC32 `3B734DEC`, 8,173 changed and 19
unchanged bytes. Both operations verified 8,192/8,192 bytes with zero retries
and ended with VCC/VPP off. The fitted pair booted and accepted `J` without an
Enter key. The host attached to API v2 with no transport mismatch, passed the
RAM-preserving PROBE, and observed the 128-row `07A9h` refresh service enabled.

A first legacy D57 probe retained useful raw data but waited only microseconds
after channel-2 programming. The exact E3 drawing establishes that D57.18
(CLK2) is driven by active-low `/VER RTR` from D55.13, about 49.92 Hz, rather
than the 1.23 MHz D57.9 clock. After arming the exact Ekta raster and waiting
64 T36 refresh sweeps (about 79 ms) per channel-2 sample, all eight repetitions
returned `FD/3D`, `FC/3C`, `FE/3E` for channels 0, 1, and 2. This physically
validates D57 channel 2 and the `/VER RTR` clock path on CS00015. Captures are
retained under
[`../spinoffs/jukuravi/sessions/cs00015-ekta4401-d57-verrtr-control-physical/`](../spinoffs/jukuravi/sessions/cs00015-ekta4401-d57-verrtr-control-physical/).

## CP/Mish dual-network-drive validation

On 2026-08-13 CS00015 independently passed the CP/Mish `NETROM2` interactive
network path. It reached the CP/M prompt, completed `DIR` on the 386 KiB A:
volume, selected B:, completed `DIR` on the native 160-track
`J3KGAME2.JUK` volume, and started `TETRIS.COM` successfully. B: was served
read-only. CS00014 had already passed the same setup, so the native game-drive
path is now physically validated on both available reference boards.

## Fast-bootstrap physical baseline

On 2026-08-14 CS00015 physically validated the stock-ROM-compatible fast
bootstrap. Its fitted service ROM retained the ordinary Janet entry: stock
Janet loaded the 558-byte stage at 9600/8O1, the stage selected D57 channel 0
mode 2/count 4 and D11 19200/8O1, thirteen CRC16-protected 512-byte blocks
installed B400h-CDFFh, and the machine reached the visible CP/M prompt.

Freeze this same-machine comparison before further optimization:

- **Fast stage v2:** 12.999 s from first valid bootstrap request to first valid
  A: request; 42 stock frames; stage 8.00 s; bulk 4.39 s; zero retries; visible
  prompt reached.
- **Fast stage v1:** 17.508 s from first valid bootstrap request to first valid
  A: request; 42 stock frames; stage 7.99 s; bulk 8.90 s; one automatically
  recovered block-0 timeout; visible prompt reached.
- **Original stock 9600:** 73.873 s over the original 6784-byte/53-record
  wrapper; 330 stock frames; visible prompt reached.

Fast stage v2 is 1.35x faster than v1, saving 4.509 s (25.8%), and 5.68x faster
than Original stock 9600, saving 60.874 s (82.4%). The v1 result remains frozen
at 4.22x/56.365 s/76.3%. All three runs used the same system, volume, cable,
host, and CS00015. See `janet-fastboot.md` and
`evidence/juku-serial/cs00015-fastboot-20260814.json`.

On 2026-08-15 CS00015 also passed the exact 5518-byte fast stage v9 artifact
(`7dd745e67ac400c22a229a796e77dd51239df793ec5375bf9ebc6bd8069de924`)
with compact stock execute and the conservative host guards. It reached the
visible CP/M prompt and completed network `DIR`. This run qualified the current
fastest code path functionally but did not retain an exact boot timestamp; the
separate low-latency host-guard policy still needs a physical run.

Later repeated runs replaced that pending timing claim with a sharper result.
Guard tuning alone was intermittent: v9 and bounded-decoder v10 each produced
both clean roughly 5.6-5.7-second boots and multi-second extension/stream
retries. V11 added an extension-header ACK, but two of four runs missed the
first ACK and the host contaminated the exchange by sending the body anyway.
V12 made the header parser overlap-safe and withheld the body until ACK. All
four physical runs then had zero extension retries; the fourth required two
header probes and recovered as designed. Its first three disk requests arrived
at 5.739, 5.740, and 5.739 seconds. The fourth exposed the separate `JZ` stream
handoff race, retried that stream once, and arrived at 8.307 seconds.

Fast stage v13 then applied the same explicit readiness protocol to `JZ`. All
five CS00015 runs booted, and the extension needed no retry, but four first
streams failed CRC and succeeded on the complete retransmission. In every such
run the extension header had also required its second probe; the sole one-probe
run was stream-clean. Thus v13 proved recovery, but not a deterministic first
pass.

Fast stage v14 is the simulator-qualified conservative successor. It keeps
v13's two overlap-safe acknowledged handoffs but removes interrupt-fed overlap:
all 4826 compressed bytes are first received into 4000h and CRC-checked, then
ZX0 expands them to B400h. Clean, partial-header, injected corruption/loss,
3.4 MHz, byte-exact, prompt, and network `DIR` simulations pass. A one-shot
RxRDY interrupt delay of more than two character times makes v13 overrun and
retry once in cosim, while v14 stays retry-free under the same disturbance.
Its 5229-byte artifact is only 11 bytes larger than proven v7 and should cost
roughly 0.3 s against a clean v13 while avoiding the observed 2.6 s retry.
Three immediate physical CS00015 runs then reached their first disk request at
6.115, 6.100, and 6.069 seconds. All had zero extension and stream retries;
the first two needed two extension-header probes and recovered without body
contamination. The 46 ms total spread and clean first-pass streams physically
qualify v14 as the repeatable production baseline. Speed optimization is frozen
at this version; later variants require a functional, observability, or
reproduced reliability reason. Exact per-run evidence and rationale are in
`janet-fastboot.md` and `evidence/juku-serial/`.

## Current deployment

Following the Arvutimuuseum demonstration, CS00015 is in the home lab. On
2026-08-18 the Ekta4402 pair was replaced by the exact JukuNet C6 / ROM ABI
1.2 D15/D16 pair. This is the current network-first CP/M Plus and Jukuravi
development reference machine. CS00014 is in the museum's main exhibition
with its stock ROM, and CS00000 is the other home-lab diagnostic candidate; see
`machine-deployment-status.md` for the cross-machine ledger.

## Current CS00015 fault summary

| Location | Finding | Confidence / next discriminator |
| --- | --- | --- |
| D15 diagnostic-era fitted EPROM | Three bytes differed from the adopted official EktaSoft 3.7 low image | Repeat-read historical observation; retain raw dumps and exact byte diff |
| D55/D57 vertical timing path | Historical T15/T16/T31/T32 D55 bits used an unclocked predicate; corrected Ekta raster plus D57 channel-2 sampling passed 8/8 | D57 channel 2 and D55.13 `/VER RTR` output path are physically validated; this does not independently exercise every D55 counter predicate |
| D1 16-bit increment path | The original D1 lost an already-high A12 during INX; carry and DAD worked | Confirmed and repaired: the fault repeated immediately before replacement and the unchanged probe passed immediately afterward |
| Currently fitted firmware | JukuNet C6 / ABI 1.2 D15/D16 pair | Repeated automatic 19,200-baud V16 boot, NetDisk-v3/N4, diagnostics, keyboard, sound, write/warm-boot/soak, and two live reconnects passed blind qualification on 2026-08-18; display observation remains pending |

The preceding Ekta4402 image is SHA-256
`20ff871307b65523428b6ce21e8153842b54c070cd897826154735af6cea6378`;
its low/high halves are respectively
`ee87c5b199b409c97909f0eb2b7cfd24cbee2537569bbcdec378631ec8fc85d5`
and `e76587d94189ce8d1cf33ee95cb50f68f5d62280a9dd675ded006eb32232e6e7`.
The retained Jukuravi evidence is under
`spinoffs/jukuravi/sessions/cs00015-ekta4402-j-physical/`. The first capture
received no bytes because its host timeout expired before `J` was entered; it
is timing chronology, not a board failure. Two immediate no-reset attaches
then completed with zero mismatch. Both proved API-v2 PROBE and 128-row
software refresh; the second also read 32 bytes at `4000h` without modifying
RAM. Ekta4401 and Ekta4402 remain frozen preceding physical baselines, not the
currently fitted firmware.

The fitted C6 ROM SHA-256 is
`0487d5150f9b662a193b3f031aadd90002ee232477d355d3877a757a247c2f09`;
its D15-low and D16-high halves are respectively
`8cf403663ed860f7e5ab56f382e42bddf6e8951e478e89313074c03ab31f2750`
and `3a60561d0e5f8a8d8e9a1f1c355e503db5daeadec174b45380de732690c9bdf1`.
Both AT28C64 writes passed their single built-in 8,192-byte verify with zero
retries or late completions. The complete monitorless physical matrix and its
remaining display boundary are recorded in
[`../cpm-plus-juku/docs/cs00015-c6-blind-qualification-20260818.md`](../cpm-plus-juku/docs/cs00015-c6-blind-qualification-20260818.md).

## Serial connector measurement

Owner continuity on 2026-08-01 identifies `X3.7` as signal ground.  The
CS00015 diagnostic cable can therefore use X3.9/SOUT, X3.4/SIN, X3.5/CTS,
and X3.7/GND through an RS-232 level interface.  X3 must not be connected
directly to TTL UART pins.

This document records preservation and repair evidence only.  Neither finding
changes the replica's adopted firmware or generic circuit model.
