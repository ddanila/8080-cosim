# T32 upper-ROM physical diagnostic on CS00015

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
`4000h-4FFFh`, and RAM `C000h-CFFFh` passed; the independently known D55 fault
was reported; loader API v2 completed a non-destructive control probe.

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

## Cross-ROM/RAM A12 localization

The first shared-path probe wrote `11 22` at RAM `4A00h` and `AA BB` at RAM
`5A00h`. Sixteen `LHLD 5A00h` pairs all returned `AA BB`. That proves D1,
D4, and BA12 can carry two consecutive high-A12 RAM reads in this address
class; it does not prove that every address/timing class passes.

Evidence: `sessions/t32-a12-path-boot/` and
`sessions/t32-a12-path-physical/`.

A later RAM-resident probe configured PPI #0 PC3..PC0 as outputs, exercised
normal mode 0, high-ROM mode 1, and all-RAM mode 3, and restored the reset
all-input configuration before returning. Port C readbacks `B1h` and `B3h`
prove that modes 1 and 3 were physically selected. It first wrote `66 C7` to
the underlying RAM pairs at `1A00h` and `DA00h`, then compared isolated and
consecutive reads:

| Mapping/read | Physical result | Repetitions |
| --- | --- | ---: |
| all-RAM isolated `1A00h`, then isolated `1A01h` | `66 C7` | one complete check |
| all-RAM consecutive `LHLD 1A00h` | `66 FF` | before and after overlay reads |
| mode-0 D15 consecutive `LHLD 1A00h` | `3E 43` | 8 |
| all-RAM isolated `DA00h`, then isolated `DA01h` | `66 C7` | one complete check |
| all-RAM consecutive `LHLD DA00h` | `66 55` | before and after overlay reads |
| mode-1 D15 consecutive `LHLD DA00h` | `3E 55` | 8 |

The sentinel writes therefore succeeded. A RAM instruction fetch between the
two target reads makes both bytes correct; only the second uninterrupted read
is corrupt. This excludes D15, its socket, and D15 pin 2 as the unique fault
site. It also explains why the high-overlay second byte need not be another
ROM byte: if physical BA12 falls, logical `DA01h` becomes `CA01h`, below the
mode-1 ROM window, and the RAM path supplies the byte.

The existing values at the proposed aliases were not deliberately seeded in
that run, so `1A01h -> 0A01h` and `DA01h -> CA01h` remain a unified, exact
hypothesis rather than the final alias proof. The next probe,
`firmware/ram-a12-alias-regions-4000.asm`, writes distinct target and alias
bytes in all four A15:A14 classes before sampling them. Its clean and
page-selective fault results are guarded in cosim. Evidence for the physical
cross-memory result is
`sessions/t32-rom-overlay-source-isolated-physical/20260804T202216.721145Z.*`.

Instruction execution at the same address did not produce the required `1Ah`
marker:

| RAM trampoline | Control | Marker after `JMP 1A00h` |
| --- | --- | --- |
| `4000h` | pre-marker `D5h` written | `D5h` |
| `5000h` | standalone CALL returns `A=50h` | `D5h` |
| `5A00h` | standalone CALL returns `A=5Ah` | `01h`, repeatably |

The `5A00h` source has the same low 13 address bits as `1A00h`; only the memory
region changes. Both repeated runs wrote `01h`, not random values. The upper
program therefore behaves deterministically but incorrectly for that source
geometry. The lower two sources return to the loader without executing the
upper marker store.

Positive evidence:

- `sessions/t32-pc-a12-physical/`: distinct CALL/RET programs at RAM `4000h`
  and `5000h`; CALL `5000h` returns `A=50h` and marker `50h`.
- `sessions/t32-pc-5a00-control/`: CALL `5A00h` returns `A=5Ah`.
- `sessions/t32-waitclass-settled/`: `4000h -> 1A00h`, marker `D5h`.
- `sessions/t32-waitclass-settled-from-5000/`: `5000h -> 1A00h`, marker `D5h`.
- `sessions/t32-waitclass-settled-from-5a00/` and `-repeat/`: marker `01h` in
  both runs.

## Bounded conclusion

On CS00015, isolated reads are correct, but the second uninterrupted read in
at least the `1Axx` and `DAxx` classes behaves consistently with physical A12
low. The same symptom occurs in ROM and all-RAM modes, while the `4Axx/5Axx`
RAM control passes. The fault is therefore address/timing-class dependent,
not D15-local. This excludes corrupt ROM contents, a static A12 fault, a
general data-bit fault, D15/socket pin 2 as the unique cause, and a fault
confined to one reconstructed D2 class.

The shared electrical path is `D1.37/A12 -> D4.5`, then
`D4.15/BA12` to D15.2, D16.2, the RAM/address-decode consumers, and the rest of
the buffered bus. D6 and D8 package substitutions did not change the result.
The remaining component-level alternatives are:

1. D1 emits A12 incorrectly during the affected second cycle, or D4's A12
   channel fails to preserve it dynamically;
2. the D2/D30/R29 READY and memory-cycle timing path ends the affected cycle
   while the CPU/buffered address is no longer valid; donor D2 produced the
   same symptom, so the original D2 package is not the unique cause;
3. a shared BA12 conductor/load or surrounding timing input is marginal in
   only some high-address classes.

The owner confirms that T31 and T32 were burned into two different physical
AT28C64B packages. Both show correct isolated upper-D15 data with broken
upper-D15 execution on CS00015. The exact consecutive-pair alias was measured
only with T32, but the same second-cycle failure in all-RAM mode excludes
either EEPROM package as the common explanation.

The [Microchip AT28C64B specification](https://ww1.microchip.com/downloads/en/DeviceDoc/doc0270.pdf)
defines an ordinary asynchronous SRAM-like read:
with `/CE` and `/OE` low and `/WE` high, output is selected solely by the
address pins. It does not define an A12-low second-read mode. The measured
behavior is therefore a device/path fault, not expected EEPROM operation.

### Exact cosim reproduction

`JUKU_CONSECUTIVE_A12_LOW_PAGES=1,D` applies the current cross-memory working
model before overlay decoding: from the second uninterrupted read within a
listed logical 4 KiB page, physical A12 is cleared. The pure-RAM alias matrix
passes both clean and faulted simulation, including `1A01h -> 0A01h` and
`DA01h -> CA01h`. The page list is explicit because physical `5Axx`
consecutive RAM reads pass and `9Axx` is pending a fresh hardware run.

The older `JUKU_ROM_CONSECUTIVE_A12_LOW=1` switch remains as a historical
ROM-local regression. It reproduces these earlier physical outcomes:

- `1100h`, `1200h`, and `1400h` lose the loader;
- the consecutive-pair bytes above alias to their exact lower-half values;
- entry at `1A00h` reads the physical stream
  `3E 43 0E C3 FE 0E C3 0C 0A`, which executes `MVI A,43`, `MVI C,C3`,
  `CPI 0E`, and `JMP 0A0C`; it returns to the loader without executing
  `STA 4100`, preserving the RAM premarker `D5` from sources `4000h` and
  `5000h`.

The apparently special `5A00h -> 1A00h` marker `01` is independently explained
by the earlier `5A00h` CALL control. Its exact eight-byte program
`3E 5A 32 00 41 3E 5A C9` returned `A=5A` but left marker `00`, proving that
the uploaded bytes were not executed normally. If its first `3E` fetch is
`00`, CALL mode enters with `A=00` and stores `00`, while JUMP mode enters with
`A=01` and stores `01`; both then continue at byte 1 and reach their intended
transfer. `JUKU_EXEC_BYTE_FAULT=5A00:00` combined with the D15 burst fault
reproduces the complete physical `01` result. This is a behavioral
localization, not proof that RAM physically contains `00` at `5A00h`.

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

The cheapest next discriminators are:

1. on the next successful T32 loader boot, run
   `firmware/ram-a12-alias-regions-4000.asm`; it distinguishes target bytes
   from deliberately seeded A12-low aliases in the `1A`, `5A`, `9A`, and `DA`
   classes;
2. compare D1.37 and D4.15/BA12 with READY at the affected second read using a
   scope or logic analyzer: disagreement localizes D4, while matching early
   A12 loss moves upstream to D1/READY timing;
3. run the same verified T32 chip on the donor processor board;
4. substitute D1 only if cross-board or timing measurements still implicate
   the CPU-facing cycle.

Earlier no-delay marker runs and the full-half read attempted after an abnormal
upper jump were superseded and are intentionally not retained as evidence.
