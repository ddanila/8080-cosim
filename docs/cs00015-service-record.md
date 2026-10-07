# Arvutimuuseum CS00015 service record

Evidence period: August 2026. Current fitted state is summarized below and in
[the machine profile](machines/CS00015.json).

This record identifies the physical Juku that underwent the diagnostic work as
the Arvutimuuseum machine `CS00015`. The identifier is the same physical-source
name already used by the retained PROM captures under `ref/physical-proms/`.
It must not be conflated with Danila Sukharev's separate reference board.

## Observed discrepancies

### D15 firmware

Repeated reads established that three bytes in the fitted D15 EPROM differ
from the adopted official RomBios 3.43m low image, `ref/firmware/JUKUROM0.HEX`
(SHA-256
`d6c4ec7418f05e5761ef450e6ee36fb2579d65d9cbf87dce265eaf1c0d077596`).
This is a machine-specific observation, not a replacement for the repository's
adopted firmware.  The three offsets and byte pairs must be added when the raw
CS00015 D15 captures are retained in the repository; no unretained values are
reconstructed here.

### D55 timer

D55 is the middle of the three КР580ВИ53/8253 PITs and supplies vertical video
timing. Historical T15/T16/T31/T32 failures used an invalid predicate: they
latched newly written Mode-0 counts without establishing the D54/D56 clocks
needed to transfer those counts into D55. T16's extra NOP spacing did not
start the missing clocks. Those results cannot establish a bad D55 or localize
a channel-2 package fault.

The corrected raster/D57 channel-2 test described below validates the
D55.13 output clock path. The broader **D55 counter predicates remain
unverified**; run T34 before considering package substitution. A T34 `08`
would still cover D55, its socket/power, D9 select, local strobes/data, D54
output paths and D56 clocks; controlled substitution is a later package
discriminator, not the next assumed action. Full reasoning and structural
negative controls are in
[`jukuravi-d55-diagnostic-audit.md`](jukuravi-d55-diagnostic-audit.md). The
revised substitution record is
[`../spinoffs/jukuravi/D55-REPLACEMENT.md`](../spinoffs/jukuravi/D55-REPLACEMENT.md).

### Repaired D1 increment fault

The original D1 lost an already-high A12 during 16-bit increment operations;
carry into A12 and DAD still worked. T32 ROM and all-RAM controls reproduced
this across memory regions and reconstructed WAIT classes. A register-only
probe confirmed the fault without high-address memory accesses, separating it
from an external D4/D15/BA12-only explanation.

On 2026-08-06 the unchanged probe returned the faulty words
`1000,0A01,4A01,8A01,1A01` immediately before D1 replacement and the clean
`1000,1A01,5A01,9A01,1A01` immediately afterward. Both sessions used T32
`1B/D62B`, completed normally, and had no serial handshake mismatch. This
confirms the replaced D1 as the cause of the tested fault.

The [T32 physical record](../spinoffs/jukuravi/T32-PHYSICAL.md) retains the
individual ROM/RAM controls, exact images and before/after captures.
Cosim's `JUKU_CPU_A12_INCREMENT_FAULT=1` reproduces the six clean/fault probe
classes. The [increment analysis](cs00015-d1-increment-analysis.md) covers the
independent vm80a Boolean reproduction and its remaining transistor/layout
boundary.

After this substitution test, CS00015 was deliberately left with the donor D6
`.038` from the Danila Sukharev machine fitted; the original CS00015 D6 will
not be reinserted because repeated extraction would add mechanical damage
risk. Original CS00015 D8 `.039` was restored. This records component
provenance only and must not be read as a diagnosis of the original D6.

## Ekta4401 service-ROM qualification

Earlier fitted firmware included T31/T32 and EK37; neither is currently
fitted. The owner-reported EK37 restoration did not include socket
readback, so it does not resolve the original D15 byte discrepancy.

The temporary Ekta4401 pair passed Willem post-write verification on
2026-08-11: D15 CRC32 `5E306759`, D16 CRC32 `3B734DEC`. It booted, accepted
`J` without Enter, attached to API v2 without a transport mismatch, passed
the RAM-preserving PROBE, and reported the 128-row `07A9h` refresh service
enabled.

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

## Fast-bootstrap evidence

Historical CS00015 loader comparisons and per-run captures are retained in
[the comparison record](evidence/juku-serial/cs00015-fastboot-20260814.json)
and its linked evidence. Their timing boundary is the first valid bootstrap
request to the first valid A: request, not power-on to prompt. These results
qualify the recorded variants, not later releases.

The supported stock recovery path is JF17; use
[the current fastboot guide](janet-fastboot.md) for artifacts, commands and
reset boundaries.

## Current deployment

CS00015 is the home-lab network-first CP/M Plus and Jukuravi development
reference, fitted with JukuNet C8 / ROM ABI 1.3. Its exact identity and
qualification scope are in [the machine profile](machines/CS00015.json).
See [the deployment ledger](machine-deployment-status.md) for other machines.

## Current CS00015 fault summary

| Location | Finding | Confidence / next discriminator |
| --- | --- | --- |
| D15 diagnostic-era fitted EPROM | Three bytes differed from the adopted official RomBios 3.43m low image | Repeat-read historical observation; retain raw dumps and exact byte diff |
| D55/D57 vertical timing path | Historical T15/T16/T31/T32 D55 bits used an unclocked predicate; corrected Ekta raster plus D57 channel-2 sampling passed 8/8 | D57 channel 2 and D55.13 `/VER RTR` output path are physically validated; this does not independently exercise every D55 counter predicate |
| D1 16-bit increment path | The original D1 lost an already-high A12 during INX; carry and DAD worked | Confirmed and repaired: the fault repeated immediately before replacement and the unchanged probe passed immediately afterward |
| Currently fitted firmware | JukuNet C8 / ABI 1.3 D15/D16 pair | Network boot, disk, diagnostics, keyboard, sound and host recovery passed the [C8 physical qualification](https://github.com/ddanila/cpm-plus-juku/blob/master/docs/cs00015-c8-blind-qualification-20260820.md). The [macOS check](portable-c-host-macos-physical-check.md) adds a focused cold-path qualification. |
| Video-data path | CPU-visible framebuffer writes/readback pass, but pixels are absent with stable sync in 40x24, 53x24 and 80x24 | Board-local fault after framebuffer storage; the same corrected pattern probe produced visible stripes on stock-ROM CS00014. See the [video-path evidence](https://github.com/ddanila/cpm-plus-juku/blob/master/docs/cs00015-video-path-20260821.md). |

Ekta4401 and Ekta4402 were temporary service-ROM baselines, not the currently
fitted firmware. The [remix catalog](../spinoffs/jukuravi/remix/README.md)
identifies their artifacts; the
[Ekta4402 physical record](../spinoffs/jukuravi/sessions/cs00015-ekta4402-j-physical/README.md)
retains its API-v2 PROBE, software-refresh and READ evidence.

The superseded C6 pair remains the rollback baseline. Its combined and
D15/D16 identities are pinned in the
[C6 release manifest](../spinoffs/jukuravi/network-rom/juku-network-rom-abi1.2-c6.json).
The monitorless physical matrix and its display boundary are recorded in
[the C6 qualification record](https://github.com/ddanila/cpm-plus-juku/blob/master/docs/cs00015-c6-blind-qualification-20260818.md).

Later source review found a bounded limitation in the immutable historical C6
`JCGKEYRAW` implementation: the global active-low SHIFT/CTRL returns can make
the scan stop at column zero before an ordinary modified key's column is
visited. This does not affect translated keyboard input or unmodified raw-key
tests. The scanner is corrected on `juku-common` master; the historical C6 hashes
in the linked manifest remain authoritative, and any ROM carrying the fix
must receive a new
candidate name rather than replace the C6 artifacts.

## Serial connector measurement

Owner continuity on 2026-08-01 identifies `X3.7` as signal ground.  The
CS00015 diagnostic cable can therefore use X3.9/SOUT, X3.4/SIN, X3.5/CTS,
and X3.7/GND through an RS-232 level interface.  X3 must not be connected
directly to TTL UART pins.

This document records preservation and repair evidence only.  These findings do not
change the replica's adopted firmware or generic circuit model.
