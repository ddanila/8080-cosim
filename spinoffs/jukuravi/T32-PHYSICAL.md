# T32 upper-ROM physical diagnostic on CS00015

> **D55 supersession, 2026-08-09:** T32 inherits T31's unclocked D55
> latch/read predicate. Its D55 bit is not valid D55 fault evidence. The
> upper-ROM, CPU, transport and RAM findings below do not depend on that bit.
> See [`../../docs/jukuravi-d55-diagnostic-audit.md`](../../docs/jukuravi-d55-diagnostic-audit.md).

Date: 2026-08-04  
Board: Arvutimuuseum Juku processor board `CS00015`  
ROM socket: D15, AT28C64B; D16 unpopulated  
Serial: X3 through MAX3232 and CP2102, 2400 baud

## Image and cold boot

- DOS name: `T32HOST.BIN`
- ROM version: `1Bh`
- Self-CRC16: `D62B`
- SHA-256: `61832807cd7e52c02384844649776efa75bb3ef25795a8124d795230ed5b5ce2`

The programmer verified the burn. The first physical boot decoded the exact
`1B/D62B` identity with zero transport mismatches. PIC, PPI, D54, D57, RAM
`4000h-4FFFh`, and RAM `C000h-CFFFh` passed; the historical D55 bit was
reported but is now invalidated as D55 evidence; loader API v2 completed a
non-destructive control probe.

Evidence: `sessions/t32-first-boot/20260804T161841.367511Z.*`.

## Upper-ROM wait-class matrix

T32 retains normal execution below `1000h` and adds upper-D15 programs covering
all `{A11,A10,A9}` combinations. Each program stores its high address byte at
RAM `4100h` and jumps to the proven loader entry at `0A0Ch`. The first class
survey used a verified three-byte RAM jump; each RUN was acknowledged before
the loader disappeared and the continuous failure tone began. The later
focused `1A00h` controls strengthen this with a RAM pre-marker and a one-second
quiet period before reattachment, so a RUN acknowledgment alone is not counted
as execution evidence there.

The first representative of every reconstructed D2 wait class failed:

| Entry | D2 class | Physical result |
| --- | --- | --- |
| `1100h` | CAS-gated | loader lost; continuous failure tone |
| `1200h` | no wait | loader lost; continuous failure tone |
| `1400h` | always wait | loader lost; continuous failure tone |

This rules out the earlier hypothesis that the failure is confined to the
CAS-gated pages. It does not validate the reconstructed D2 pin assignment or
identify a component.

Evidence: the successful cold boots immediately before each probe are under
`sessions/t32-boot-before-{1200,1400}/`; acknowledged jump and failed attach
captures are under `sessions/t32-waitclass-physical/`.

## Exact `1A00h` data-versus-execution result

A fresh boot was followed by a 51-byte probe executing wholly from RAM
`4000h`. It read D15 address `1A00h` sixteen times and returned normally. Every
sample was `3Eh`, exactly the first byte burned at `1A00h`:

```text
41313253 1A00 3E 10 A5 3E3E3E3E3E3E3E3E3E3E3E3E3E3E
```

Evidence:
`sessions/t32-read-1a00-fresh/20260804T170625.113348Z.*`.

The same isolated-read probe later sampled `1A01h` sixteen times. Every sample
was the correct `1Ah`:

```text
41313253 1A01 1A 10 A5 1A1A1A1A1A1A1A1A1A1A1A1A1A1A1A1A
```

Evidence:
`sessions/t32-read-1a01-fresh/20260804T182712.307915Z.*`.

## Consecutive-read localization

A 57-byte RAM-resident probe used `LHLD target`, which makes two immediately
consecutive memory reads while every instruction is fetched from RAM. Sixteen
repetitions at each address were byte-identical:

| Pair requested | Bytes in T32 | Physical result | Interpretation |
| --- | --- | --- | --- |
| `0A00/0A01` | `C3 43` | `C3 43` | lower-half control passes |
| `1A00/1A01` | `3E 1A` | `3E 43` | second byte is `0A01` |
| `1A01/1A02` | `1A 32` | `1A 0E` | second byte is `0A02` |
| `1A02/1A03` | `32 00` | `32 C3` | second byte is `0A03` |
| `1A04/1A05` | `41 C3` | `41 0E` | second byte is `0A05` |

The first upper-D15 read is correct; the immediately following read sees the
same low twelve address bits with A12 low. This is deterministic address
aliasing, not random data corruption, a bad burned byte, or an opcode-versus-
data distinction. The reusable probe is
`firmware/rom-read-pair-4000.asm`; raw sessions are under
`sessions/t32-read-pair-{0a00,1a00,1a01,1a02,1a04}-fresh/`.

## Cross-memory and instruction-class localization

The overlay probe established the same failure in ROM and RAM. Isolated
all-RAM reads returned the deliberately written `66 C7` at `1A00/1A01` and
`DA00/DA01`; consecutive `LHLD` reads returned `66 FF` and `66 55`. Through
the two ROM mappings, the same requests returned `3E 43` and `3E 55`.
Two later repetitions returned stable all-RAM pairs `66 21` and `66 81` and
stable isolated bytes `66 C7`, confirming that instruction fetches between
the isolated reads reset the symptom. Evidence is under
`sessions/t32-rom-overlay-source-*-physical/`.

The first four-region probe cannot be used as a seeded-memory test. Its setup
used `INX D` between the even and odd stores. The physical result is itself
more important: in all four high-A12 regions the even byte reached the target,
while the odd byte reached the A12-low alias. Examples are target/alias
`20 FF / 10 21` at `1A` and `40 FE / 30 41` at `5A`. Multiple instruction
fetches, a CALL, stack writes, and a RET separate `INX D` from the eventual
`STAX D`; this is not an adjacent external bus-cycle effect. The result says
that D1's architecturally visible 16-bit increment lost an already-high A12.
The raw result is retained under `sessions/t32-ram-a12-alias-regions-physical/`
as an INX finding, not as alias-matrix evidence.

Corrected probes initialized every byte with absolute `STA` and produced the
following deterministic results:

| Operation | Lower-A12 control | High-A12 request | Physical result |
| --- | --- | --- | --- |
| `LHLD` in A15:A14 classes `00/01/10/11` | `10 11`, `30 31`, `50 51`, `70 71` | `20 21`, `40 41`, `60 61`, `80 81` | `20 11`, `40 31`, `60 51`, `80 71` |
| `POP H`, SP=`4A00/5A00` | `30 31` | `40 41` | `40 31` |
| `SHLD 9A00`, HL=`BBAA` | lower `50 51` | upper `60 61` | lower `50 BB`, upper `AA 61` |
| `LHLD 0FFF` and `LHLD 2FFF` | — | carry must assert A12 | correct `1F 20` and `2F 40` |

The same high-page alias occurred in all four `{A10,A9}` classes at
`1000`, `1200`, `1400`, and `1600` in all-RAM mode. The first READY-class run
stored its result at high-A12 `5000h` and corrupted its own result pointer; it
is retained as an invalid setup. The corrected low-A12 result at `4F00h` is
the evidence. Sessions and corresponding sources use the
`t32-ram-a12-*-physical` and `firmware/ram-a12-*-4000.asm` names.

### Direct D1 register confirmation

The final RAM-resident probe made no high-address memory access. It copied
architecturally visible register results into low-A12 RAM `4D00h`:

| Operation | Physical result |
| --- | --- |
| `INX B` from `0FFFh` | `1000h` |
| `INX D` from `1A00h` | `0A01h` |
| `INX H` from `5A00h` | `4A01h` |
| `INX SP` from `9A00h` | `8A01h` |
| `DAD D`, `1A00h + 1` | `1A01h` |

The exact T32 `1B/D62B` boot had zero transport mismatches and the loader
returned normally. This confirms that D1's retained register values are wrong;
an external D4/BA12/D15 fault cannot produce them. Evidence:
`sessions/t32-ram-a12-increment-registers-physical/20260805T154851.229201Z.*`.

On 2026-08-06 the same probe was run once more immediately before replacing
D1. It reproduced the exact faulty five-word result
`1000,0A01,4A01,8A01,1A01`. After D1 was replaced, the unchanged 81-byte probe
returned the fully clean result `1000,1A01,5A01,9A01,1A01`. Both runs used the
same T32 `1B/D62B` image, completed normally, and recorded zero transport
mismatches. This before/after substitution closes the diagnosis at D1 rather
than its external address path. Evidence:
`sessions/t32-ram-a12-increment-registers-repeat-physical/20260806T161050.050390Z.*`
and
`sessions/t32-ram-a12-increment-registers-cpu-replacement-physical/20260806T161621.106830Z.*`.

### Exact ROM WAIT-class pairs

Using the same successful boot, sixteen LHLD samples per target returned:

| Target | Reconstructed class | Expected | Physical |
| --- | --- | --- | --- |
| `1000h` | CAS-gated | `00 C0` | `00 0B` |
| `1100h` | CAS-gated | `3E 11` | `3E 17` |
| `1200h` | no wait | `3E 12` | `3E 02` |
| `1400h` | always wait | `3E 14` | `3E E6` |

Every second byte is the exact A12-low ROM byte. No WAIT class rescues the
fault. Evidence is under
`sessions/t32-rom-read-pair-{1000,1100,1200,1400}-physical/`.

## Bounded conclusion

CS00015 loses an already-high A12 in D1's 16-bit increment path. A carry from
bit 11 can assert A12 (`0FFF -> 1000`), but incrementing while A12 is already
one clears it. This single rule explains INX register-pair state, PC/instruction
streams, LHLD, POP, and SHLD reads and writes across every tested address and
all-RAM timing class.

That confirms D1 as the hardware diagnosis. D4, D15, the BA12 conductor, and
READY timing cannot by themselves alter the DE register value retained across
the intervening CALL/RET sequence in the INX probe. The clean result after D1
replacement is the direct physical confirmation. A scope comparison of D1.37
and D4.15 could further characterize the old package, but is not required to
localize the repaired fault.

T31 and T32 were burned in different AT28C64B packages. D6, D8, and D2 donor
substitutions did not change the symptom. Those devices and the EEPROMs are
excluded as unique causes. The historical D55 bit is a separate, now-invalid
predicate result and makes no D55 hardware claim.

### Exact cosim reproduction

`JUKU_CPU_A12_INCREMENT_FAULT=1` now models the fault at the 8080/D1 increment
operation rather than as a page-selective external read trick. It affects PC,
INX, paired reads/writes, and POP while allowing carry into A12. The integration
regression replays clean and faulted versions of the write-map, four-region
LHLD, POP/SHLD, four READY-address classes, and boundary probes. One mechanism
matches every meaningful physical byte, including writes and the successful
`0FFF -> 1000` boundary.

`JUKU_ROM_CONSECUTIVE_A12_LOW=1` remains only for the older ROM-local T31/T32
regressions. It is not the current component model.

The die-derived `hdl/vendor/vm80a.v` model independently reproduces the exact
direct-register words when only its shared incrementer's bit-12
retain-high/no-carry term is removed. The Boolean-level localization and its
remaining transistor/layout boundary are documented in
`../../docs/cs00015-d1-increment-analysis.md`.

### One-at-a-time PROM substitutions

Two programmed selector/decoder PROMs were substituted individually from the
donor processor board. Each donor produced the exact T32 cold boot before the
settled `5A00h -> 1A00h` test:

| Substitution | Other PROM | Cold boot | Marker |
| --- | --- | --- | --- |
| donor D8 `.039` | original D6 | exact `1B/D62B`, zero mismatches | `01h` |
| donor D6 `.038` | original D8 restored | exact `1B/D62B`, zero mismatches | `01h` |

The result is byte-for-byte unchanged from the original pair. The original D6
and D8 packages are therefore excluded as unique causes. This does not exclude
their socket contacts, surrounding conductors, shared pull-ups, or the timing
of the selection topology itself.

Final fitted configuration: CS00015 retains the donor D6 `.038` from the
Danila Sukharev processor board, while its original D8 `.039` is restored. The
original CS00015 D6 is intentionally not reinserted because another extraction
and insertion would add avoidable mechanical risk. Retaining the donor part is
a preservation choice, not evidence that the original D6 was faulty: both
packages produced the same exact boot and `01h` result.

Evidence:

- `sessions/t32-d8swap-boot/` and `sessions/t32-d8swap-5a00/`
- `sessions/t32-d6swap-boot/` and `sessions/t32-d6swap-5a00/`

The decisive confirmation is complete: a known-good D1 substitution changed
the existing probe from the exact fitted fault signature to the exact clean
signature without a ROM or probe change. A D1.37/D4.15 capture or a donor-board
run could characterize the removed package further, but neither is required
for localization and neither is active Jukuravi work. No D4/D30 rework or
diagnostic-ROM re-burn is justified by this repaired fault.

Earlier no-delay marker runs and the full-half read attempted after an abnormal
upper jump were superseded and are intentionally not retained as evidence.

## Post-diagnostic restoration

After these diagnostics, the owner restored CS00015 on 2026-08-08 with **EK37 /
EktaSoft 3.7** (repository profile `ekta37`) in D15/D16. T32 is therefore no
longer fitted; this document remains the evidence record for the completed
diagnostic configuration and D1 repair. The donor-D6/original-D8 configuration
recorded above is unchanged.
