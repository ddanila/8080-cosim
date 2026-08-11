; Seed control file for roms/ekta31.bin (EktaSoft Serial #0031, RomBios 3.43).
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
b $015D
t $015F
b $0166
t $0168
b $017E
t $0181
b $0197
@ $01D4 label=BOOT_PIT_INIT
b $01D4 Boot PIT programming (docs/ektasoft-rombios-lineage.md)
c $08D7
b $08D8
c $0A7A
b $0AD7
c $0C95
b $0C9C
c $0D83
b $0DAB
c $0DD8
b $0DDD
c $0DF1
b $0DF7
@ $0F0D label=MODE_PIT_ALT
c $0F0D Alternative D54/D55 parameter set (shared runtime code; geometry uninterpreted)
b $0F26
@ $0F39 label=MODE_PIT_STD
c $0F39 Restore boot D54/D55 parameter set
b $0F5A
c $0FA8
b $0FB3
c $1841
b $188B
t $188D
b $1899
c $189D
b $18A6
c $18AB
b $18B0
c $18C7
b $194C
c $1964
b $1976
t $19A8
b $19C3
c $19CB
b $1A52
c $1A5F
b $1AB5
c $1AB8
b $1AED
c $1AF0
b $1AFA
c $1B27
b $1B55
c $1B61
b $1B6B
c $1C02
b $1C07
c $1C5F
b $1C65
c $1C80
b $1C88
c $1C94
b $1CA4
c $1CCF
b $1CFB
c $22AE
b $23C3
c $2476
b $2540
c $2564
b $29A6
c $29B2
b $2AA1
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
