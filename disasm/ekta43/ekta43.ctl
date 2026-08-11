; Seed control file for roms/ekta43.bin (EktaSoft '90 Serial #0043, RomBios 2.43m,
; homebrew IBM AT keyboard mod with stale block-1 checksum F2h vs computed 57h).
; Same memory model as ekta37: ROM 0000-17FF executes in place; 1800-3FFF
; executes relocated at +C000 (runtime D800-FFFF). Addresses are ROM offsets.
; Code seeded by recursive descent from reset + monitor vectors + the verified
; PIT mode routines, translating control-flow targets D800-FFFF by -C000.

@ $0000 label=RESET
c $0000 Reset entry
b $0003
@ $0017 label=BOOT_MAIN
c $0017
b $002C
c $00CE
b $00D6
t $00DF
b $00FA
t $00FC
b $0111
t $0113
b $0122
t $0124
b $0134
t $0136
b $0152
t $0154
b $016B
t $016D
b $0181
t $0184
b $019A
c $019D
@ $01DC label=BOOT_PIT_INIT
c $01DC Boot PIT programming: byte-identical raster to #0032/#0037; D57 ch2 as 38.4 kHz square wave (docs/ektasoft-rombios-lineage.md)
b $032B
c $03D0
b $0492
c $04A2
b $04AD
c $0697
b $06A4
c $06B3
b $06D1
c $08CD
b $0929
c $0A70
b $0ACD
c $0BDB
b $0BE6
c $0C8B
b $0C92
c $0D69
b $0DA1
c $0DCE
b $0DD3
c $0DE7
b $0DED
@ $0F03 label=MODE_PIT_ALT
c $0F03 Alternative D54/D55 parameter set (shared across the vendored line; geometry uninterpreted)
b $0F1C
@ $0F2F label=MODE_PIT_STD
c $0F2F Restore boot D54/D55 parameter set
b $0F50
c $0F9E
b $0FA9
c $0FEA
b $106C
c $11DC
b $120F
t $14AF AT keyboard layout table: row-ordered shifted/unshifted char pairs
b $14DD
c $1848
b $1892
t $1894
b $18A1
c $18A5
b $18AE
c $18B3
b $18B8
c $18CF
b $1954
c $196C
b $197E
t $19B0
b $19CD
c $19D5
b $1A5C
c $1A69
b $1ABF
c $1AC2
b $1AF7
c $1AFA
b $1B04
c $1B31
b $1B5F
c $1B6B
b $1B75
c $1C0C
b $1C11
c $1C69
b $1C6F
c $1C8A
b $1C92
c $1C9E
b $1CAE
c $1CD9
b $1D01
c $22AE
b $23C7
c $2479
b $2543
c $2567
b $2984
c $2990
b $2A7F
@ $3F50 label=MON_COLD
c $3F50 Monitor vector table (runtime FF50h; EKDOS30.ASM contract)
@ $3F53 label=MON_FLOPPY
c $3F53
@ $3F56 label=MON_START
c $3F56
@ $3F59 label=MON_RWFLOPPY
c $3F59
b $3F5F
c $3F68
b $3FA5
c $3FA7
b $3FB4
c $3FB9
b $3FC2
c $3FC4
i $4000
