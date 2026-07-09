# BASIC low-stub inspection

Status: **LOW STUB PATCHED / BODY MATCHES**

This generated report interprets the 14-byte `0x0100..0x01FF`
cartridge-vs-RAM mismatch pinned by `docs/basic-launch-probe.md`.
The `0x0200..0x1FFF` BASIC body is byte-identical after Monitor 3.3
loads the cartridge; the unresolved boundary is this low entry/workspace
area and the monitor launch vector, not the cartridge window or bulk copy.

## Inputs

| Item | Value |
| --- | --- |
| `roms/jbasic11.bin` SHA1 | `27e40395e8b49e2f9febf2b23773fbfe251befcf` |
| legacy `BAS0-3.HEX` SHA1 | `3d96ba589aa21d44412efb099a144fbe23a2f52f` |
| images identical | `NO` |
| first `0x0200` bytes identical | `YES` |
| low mismatches | `14` |
| body mismatches from `0x0200` | `0` |

## Mismatch Bytes

| Address | Cartridge | Loaded RAM |
| --- | ---: | ---: |
| `0x0101` | `0x00` | `0xFE` |
| `0x0102` | `0xD7` | `0xFF` |
| `0x0111` | `0xFF` | `0xFE` |
| `0x0112` | `0xB3` | `0xFF` |
| `0x0121` | `0xFF` | `0xFE` |
| `0x0122` | `0xB3` | `0xFF` |
| `0x0129` | `0x99` | `0x00` |
| `0x012A` | `0x1C` | `0x22` |
| `0x0133` | `0xCD` | `0xCC` |
| `0x0134` | `0xB3` | `0xFF` |
| `0x013F` | `0x1F` | `0x00` |
| `0x0140` | `0x02` | `0x00` |
| `0x0141` | `0x84` | `0x56` |
| `0x0142` | `0x87` | `0x6F` |

## Grouped Interpretation

| Range | Interpretation |
| --- | --- |
| `0101..0102` | `LXI SP` operand changes `0xD700` -> `0xFFFE` |
| `0111..0112` | low control bytes change `0xB3FF` -> `0xFFFE` |
| `0121..0122` | low control bytes change `0xB3FF` -> `0xFFFE` |
| `0129..012A` | workspace/vector word changes `0x1C99` -> `0x2200` |
| `0133..0134` | workspace/control word changes `0xB3CD` -> `0xFFCC` |
| `013F..0142` | four-byte low workspace/control block changes before the shared body at `0x0151` |

The only unambiguous executable entry change is the stack pointer at
`0x0100`: the loaded image starts with `LXI SP,0xFFFE` instead of the
cartridge's `LXI SP,0xD700`. The remaining changes sit in the BASIC
low control/workspace region. A linear disassembly is useful for
orientation, but should not be treated as proof that every byte below
`0x0151` is executable code.

## Linear Disassembly: Cartridge

```text
0100: 31 00 D7  LXI  SP,$D700
0103: C3 C7 1C  JMP  $1CC7
0106: 00        NOP
0107: 32 32 37  STA  $3732
010A: 30        DB   $30
010B: 00        NOP
010C: 00        NOP
010D: 00        NOP
010E: 00        NOP
010F: 01 00 FF  LXI  B,$FF00
0112: B3        ORA  E
0113: 15        DCR  D
0114: 01 06 00  LXI  B,$0006
0117: 6B        MOV  L,E
0118: 02        STAX B
0119: 01 00 89  LXI  B,$8900
011C: 17        RAL
011D: 00        NOP
011E: 00        NOP
011F: 00        NOP
0120: 00        NOP
0121: FF        RST  7
0122: B3        ORA  E
0123: D5        PUSH D
0124: 01 00 00  LXI  B,$0000
0127: 00        NOP
0128: 00        NOP
0129: 99        SBB  C
012A: 1C        INR  E
012B: D5        PUSH D
012C: 01 FF FF  LXI  B,$FFFF
012F: 6E        MOV  L,M
0130: 0A        LDAX B
0131: 00        NOP
0132: 00        NOP
0133: CD B3 01  CALL $01B3
0136: 22 03 22  SHLD $2203
0139: 03        INX  B
013A: 22 03 22  SHLD $2203
013D: 00        NOP
013E: 22 1F 02  SHLD $021F
0141: 84        ADD  H
0142: 87        ADD  A
0143: C2 20 32  JNZ  $3220
0146: 35        DCR  M
0147: 36 00     MVI  M,$00
0149: 30        DB   $30
014A: 30        DB   $30
014B: 30        DB   $30
014C: 00        NOP
014D: 00        NOP
014E: 00        NOP
014F: 00        NOP
0150: 00        NOP
```

## Linear Disassembly: Loaded RAM Shape

```text
0100: 31 FE FF  LXI  SP,$FFFE
0103: C3 C7 1C  JMP  $1CC7
0106: 00        NOP
0107: 32 32 37  STA  $3732
010A: 30        DB   $30
010B: 00        NOP
010C: 00        NOP
010D: 00        NOP
010E: 00        NOP
010F: 01 00 FE  LXI  B,$FE00
0112: FF        RST  7
0113: 15        DCR  D
0114: 01 06 00  LXI  B,$0006
0117: 6B        MOV  L,E
0118: 02        STAX B
0119: 01 00 89  LXI  B,$8900
011C: 17        RAL
011D: 00        NOP
011E: 00        NOP
011F: 00        NOP
0120: 00        NOP
0121: FE FF     CPI  $FF
0123: D5        PUSH D
0124: 01 00 00  LXI  B,$0000
0127: 00        NOP
0128: 00        NOP
0129: 00        NOP
012A: 22 D5 01  SHLD $01D5
012D: FF        RST  7
012E: FF        RST  7
012F: 6E        MOV  L,M
0130: 0A        LDAX B
0131: 00        NOP
0132: 00        NOP
0133: CC FF 01  CZ   $01FF
0136: 22 03 22  SHLD $2203
0139: 03        INX  B
013A: 22 03 22  SHLD $2203
013D: 00        NOP
013E: 22 00 00  SHLD $0000
0141: 56        MOV  D,M
0142: 6F        MOV  L,A
0143: C2 20 32  JNZ  $3220
0146: 35        DCR  M
0147: 36 00     MVI  M,$00
0149: 30        DB   $30
014A: 30        DB   $30
014B: 30        DB   $30
014C: 00        NOP
014D: 00        NOP
014E: 00        NOP
014F: 00        NOP
0150: 00        NOP
```

## Boundary

- The loaded low stub is not random corruption: changes are sparse,
  repeat for both public BASIC media shapes, and leave the body exact.
- The next cartridge-BASIC step is to identify what monitor routine patches
  or synthesizes these low bytes, then confirm the intended launch PC/mode.
- Disk-side EKDOS `JBASIC.COM` is already proven separately to visible
  `READY`; this report only narrows the unresolved Monitor 3.3 cartridge
  path.
