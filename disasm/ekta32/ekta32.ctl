; Seed control file for roms/ekta32.bin (EktaSoft Serial #0032, RomBios 2.43).
; Same memory model as ekta37: ROM 0000-17FF executes in place; 1800-3FFF
; executes relocated at +C000 (runtime D800-FFFF). Addresses are ROM offsets.
; Code seeded by recursive descent from reset + monitor vectors, translating
; control-flow targets D800-FFFF by -C000.

@ $0000 label=RESET
c $0000 Reset entry
b $0003
@ $0017 label=BOOT_MAIN
c $0017
b $0021
t $00DF
b $00FA
t $00FC
b $0111
t $0113
b $012B
t $012D
b $013D
t $013F
b $015B
t $015D
b $0174
t $0176
b $018C
t $018F
b $01A5
@ $01E2 label=BOOT_PIT_INIT
b $01E2 Boot PIT programming (docs/ektasoft-rombios-lineage.md)
c $08D0
b $08D1
c $0A73
b $0AD0
c $0C8E
b $0C95
c $0D7C
b $0DA4
c $0DD1
b $0DD6
c $0DEA
b $0DF0
@ $0F06 label=MODE_PIT_ALT
c $0F06 Alternative D54/D55 parameter set (shared runtime code; geometry uninterpreted)
b $0F1F
@ $0F32 label=MODE_PIT_STD
c $0F32 Restore boot D54/D55 parameter set
b $0F53
c $0FA1
b $0FAC
c $1848
b $1892
t $1894
b $18A0
c $18A4
b $18AD
c $18B2
b $18B7
c $18CE
b $1953
c $196B
b $197D
t $19AF
b $19CC
c $19D4
b $1A5B
c $1A68
b $1ABE
c $1AC1
b $1AF6
c $1AF9
b $1B03
c $1B30
b $1B5E
c $1B6A
b $1B74
c $1C0B
b $1C10
c $1C68
b $1C6E
c $1C89
b $1C91
c $1C9D
b $1CAD
c $1CD8
b $1D04
c $22B1
b $23C6
c $2478
b $2542
c $2566
b $2983
c $298F
b $2A7E
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
