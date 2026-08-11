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
@ $185B label=MON_SERVICE
c $185B Monitor service dispatcher (command code in A; R/W use 12h/21h)
b $1892
t $1894
b $18A0
c $18A4
b $18AD
c $18B2
b $18B7
c $18CE
@ $1953 label=CMD_T
b $1953 Monitor T: load system -- prints the boot-source prompt; keys: 'D' -> FF50h, 'T' -> EC2Ch
c $196B
b $197D Monitor command dispatch table: FDSXGMCEKTBRWPA
b $19AB
t $19AF
b $19CC
b $19CD T-command key dispatch: 'D' -> FF50h, 'T' -> EC2Ch
c $19D4
b $1A5B
c $1A68
@ $1ABE label=CMD_D
b $1ABE Monitor D: hex-dump memory range (8 bytes per line)
c $1AC1
@ $1AF6 label=CMD_M
b $1AF6 Monitor M: move/copy memory block
c $1AF9
b $1B03
@ $1B21 label=CMD_E
b $1B21 Monitor E: console echo until Ctrl-C
@ $1B2D label=CMD_C
b $1B2D Monitor C: compare memory blocks, listing differences
c $1B30
@ $1B5E label=CMD_F
b $1B5E Monitor F: fill memory range with a byte
c $1B6A
@ $1B74 label=CMD_X
b $1B74 Monitor X: examine/modify saved registers
@ $1BAC label=CMD_S
b $1BAC Monitor S: substitute/examine memory interactively
@ $1BD2 label=CMD_G
b $1BD2 Monitor G: go/execute (restores saved registers; optional address)
c $1C0B
b $1C10
@ $1C21 label=CMD_R
b $1C21 Monitor R: read block -- parses address range, invokes monitor service 12h
@ $1C29 label=CMD_W
b $1C29 Monitor W: write block -- parses address range, invokes monitor service 21h
@ $1C57 label=CMD_P
b $1C57 Monitor P: select console/output device (mode byte; banner lists Parallel printer)
c $1C68
@ $1C6E label=CMD_A
b $1C6E Monitor A: switches device mode and operates on the 4000h region (plausibly application/cartridge start; unverified)
c $1C89
@ $1C91 label=CMD_K
b $1C91 Monitor K: search memory range for a byte value
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
@ $3F9B label=CMD_B
c $3F9B Monitor B: vector-region stub in this build (BASIC extension slot; semantics unverified)
b $3FA5
c $3FA7
b $3FB4
c $3FB9
b $3FC2
c $3FC4
i $4000
