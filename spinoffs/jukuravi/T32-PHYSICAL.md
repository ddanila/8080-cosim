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

On CS00015, upper-D15 ordinary data reads are correct while instruction
execution at the same address is wrong. High-A12 instruction execution from
RAM works, failure spans all three reconstructed D2 wait classes, keeping A12
high before the ROM transition does not cure it, and matching all low 13
address bits changes the wrong result but does not produce the burned marker.

This excludes a static A12-low fault, corrupt ROM contents, a general D1/CPU
PC-A12 failure, and a fault confined to one D2 wait class. The board logic has
no intentional M1-versus-data-read decode, so the remaining distinction must
be dynamic: address/select/READY/data timing around D15 access. No individual
IC is identified yet.

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

Evidence:

- `sessions/t32-d8swap-boot/` and `sessions/t32-d8swap-5a00/`
- `sessions/t32-d6swap-boot/` and `sessions/t32-d6swap-5a00/`

The cheapest next discriminators are:

1. run the same verified T32 chip on the donor processor board;
2. run T32 on CS00015 from a second memory device with different output timing;
3. compare D15 A12, chip select/output enable, READY, and data timing for the
   successful RAM-resident `MOV A,M` read and the failing `5A00h -> 1A00h`
   instruction transition with a scope or logic analyzer;
4. substitute D1 only if cross-board or timing measurements still implicate
   the CPU-facing address cycle rather than D15 selection.

Earlier no-delay marker runs and the full-half read attempted after an abnormal
upper jump were superseded and are intentionally not retained as evidence.
