# BASIC low-stub inspection

Status: **LOW STUB PATCHED / BODY MATCHES**

This generated report interprets the 14-byte `0x0100..0x01FF`
cartridge-vs-RAM mismatch pinned by `docs/basic-launch-probe.md`.
The `0x0200..0x1FFF` BASIC body is byte-identical after Monitor 3.3
loads the cartridge; the unresolved boundary is the post-`0x0100`
handoff through this low entry/workspace area, not the cartridge
window or bulk copy.

## Inputs

| Item | Value |
| --- | --- |
| `roms/jbasic11.bin` SHA1 | `27e40395e8b49e2f9febf2b23773fbfe251befcf` |
| `roms/jmon33.bin` SHA1 | `76407d99bf83035ef526d980c9468cb04972608c` |
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

## Monitor 3.3 Handoff

In memory modes 1 and 2, Monitor 3.3's high-ROM window maps CPU
addresses `0xD800..0xFFFF` to `roms/jmon33.bin` offsets
`0x1800..0x3FFF`; equivalently, disassemble the ROM with file byte
0 mapped at CPU address `0xC000` for high-window snippets.

The source-aware launch probe now shows the first cartridge reads from
high ROM at `0xEF4D` / `0xFF09`, followed by reads from RAM-resident
copy code at `0xD763`. The eventual execution in `0x4000..0xBFFF`
happens in mode 1 from RAM, not in mode 2 from the cartridge overlay,
and the sampled opcodes there are `0x00`.

Header check around the first sampled high-ROM cartridge read:

```text
EF4A: 2A 03 40  LHLD $4003
EF4D: EB        XCHG
EF4E: CD E5 D7  CALL $D7E5
EF51: 7A        MOV  A,D
EF52: FE DC     CPI  $DC
EF54: C0        RNZ
EF55: 7B        MOV  A,E
EF56: FE BA     CPI  $BA
EF58: C0        RNZ
EF59: C3 01 FF  JMP  $FF01
```

Launch/copy setup around the second sampled high-ROM cartridge read:

```text
FF01: 3E 02     MVI  A,$02
FF03: CD E7 D7  CALL $D7E7
FF06: 2A 05 40  LHLD $4005
FF09: EB        XCHG
FF0A: CD E5 D7  CALL $D7E5
FF0D: EB        XCHG
FF0E: 11 00 01  LXI  D,$0100
FF11: 01 00 40  LXI  B,$4000
FF14: 3E 12     MVI  A,$12
FF16: CD 43 EE  CALL $EE43
FF19: C3 00 01  JMP  $0100
```

Shared high-ROM copy trampoline reached with `A=0x12`, `BC=0x4000`,
and `DE=0x0100` from the launch setup:

```text
EE43: 32 59 D7  STA  $D759
EE46: E5        PUSH H
EE47: D5        PUSH D
EE48: 21 30 D6  LXI  H,$D630
EE4B: E5        PUSH H
EE4C: 50        MOV  D,B
EE4D: 59        MOV  E,C
EE4E: 21 5E EE  LXI  H,$EE5E
EE51: 3A 59 D7  LDA  $D759
EE54: E5        PUSH H
EE55: 21 5E D7  LXI  H,$D75E
EE58: E5        PUSH H
EE59: E6 03     ANI  $03
EE5B: C3 E7 D7  JMP  $D7E7
EE5E: E1        POP  H
EE5F: EB        XCHG
EE60: E3        XTHL
EE61: E5        PUSH H
EE62: 11 30 D6  LXI  D,$D630
EE65: 21 72 EE  LXI  H,$EE72
EE68: 3A 59 D7  LDA  $D759
EE6B: 07        RLC
EE6C: 07        RLC
EE6D: 07        RLC
EE6E: 07        RLC
EE6F: C3 54 EE  JMP  $EE54
EE72: E1        POP  H
EE73: C1        POP  B
EE74: E3        XTHL
EE75: 11 80 FF  LXI  D,$FF80
EE78: 19        DAD  D
EE79: D1        POP  D
EE7A: 7C        MOV  A,H
EE7B: FE FF     CPI  $FF
EE7D: CA E5 D7  JZ   $D7E5
EE80: B5        ORA  L
EE81: C2 46 EE  JNZ  $EE46
EE84: C3 E5 D7  JMP  $D7E5
```

This proves that the monitor deliberately validates the cartridge header,
copies from the `0x4000` cartridge window into low RAM starting at
`0x0100`, then jumps to `0x0100`. The still-wrong later execution from
zero-filled RAM at `0x4000` is therefore after this intentional handoff.

## Runtime Cartridge Bootstrap

The initial Monitor copy places cartridge offset `0x0000` at runtime
RAM address `0x0100`, so the first runtime bootstrap snippets below
disassemble `roms/jbasic11.bin` with file byte 0 mapped at CPU
address `0x0100`.

Initial entry stub:

```text
0100: C3 07 01  JMP  $0107
0103: BA        CMP  D
0104: DC 00 20  CC   $2000
0107: C3 00 20  JMP  $2000
010A: FF        RST  7
010B: FF        RST  7
010C: FF        RST  7
010D: FF        RST  7
010E: FF        RST  7
010F: FF        RST  7
```

Relocation loop reached by that stub:

```text
2000: 21 00 02  LXI  H,$0200
2003: 11 00 01  LXI  D,$0100
2006: 01 00 20  LXI  B,$2000
2009: 7E        MOV  A,M
200A: 12        STAX D
200B: 23        INX  H
200C: 13        INX  D
200D: 0B        DCX  B
200E: 78        MOV  A,B
200F: B1        ORA  C
2010: C2 09 20  JNZ  $2009
2013: C3 00 01  JMP  $0100
```

The source-aware launch probe now records this runtime path as
`0x0100 -> 0x0107 -> 0x2000`. The `0x2000` loop copies runtime
`0x0200..0x21FF` down to `0x0100..0x20FF`, then jumps back to
`0x0100`; that is why the final loaded RAM shape compares cartridge
offset `0x0100` against runtime `0x0100`. The same probe records the
first later entry into the failing BASIC window as
`0x3FFF -> 0x4000`, `src=ram`, `op=0x00`, `mode=1/1`: a linear
fall-through into zero-filled RAM, not a cartridge-overlay jump.

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
