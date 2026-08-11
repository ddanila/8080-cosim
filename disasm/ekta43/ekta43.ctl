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
@ $185B label=MON_SERVICE
c $185B Monitor service dispatcher (command code in A; R/W use 12h/21h)
b $1892
t $1894
b $18A1
c $18A5
b $18AE
c $18B3
b $18B8
c $18CF
@ $1954 label=CMD_T
b $1954 Monitor T: load system -- prints the boot-source prompt; keys: 'D' -> FF50h, 'T' -> EC2Dh
c $196C
b $197E Monitor command dispatch table: FDSXGMCEKTBRWPA
b $19AC
t $19B0
b $19CD
b $19CE T-command key dispatch: 'D' -> FF50h, 'T' -> EC2Dh
c $19D5
b $1A5C
c $1A69
@ $1ABF label=CMD_D
b $1ABF Monitor D: hex-dump memory range (8 bytes per line)
c $1AC2
@ $1AF7 label=CMD_M
b $1AF7 Monitor M: move/copy memory block
c $1AFA
b $1B04
@ $1B22 label=CMD_E
b $1B22 Monitor E: console echo until Ctrl-C
@ $1B2E label=CMD_C
b $1B2E Monitor C: compare memory blocks, listing differences
c $1B31
@ $1B5F label=CMD_F
b $1B5F Monitor F: fill memory range with a byte
c $1B6B
@ $1B75 label=CMD_X
b $1B75 Monitor X: examine/modify saved registers
@ $1BAD label=CMD_S
b $1BAD Monitor S: substitute/examine memory interactively
@ $1BD3 label=CMD_G
b $1BD3 Monitor G: go/execute (restores saved registers; optional address)
c $1C0C
b $1C11
@ $1C22 label=CMD_R
b $1C22 Monitor R: read block -- parses address range, invokes monitor service 12h
@ $1C2A label=CMD_W
b $1C2A Monitor W: write block -- parses address range, invokes monitor service 21h
@ $1C58 label=CMD_P
b $1C58 Monitor P: select console/output device (mode byte; banner lists Parallel printer)
c $1C69
@ $1C6F label=CMD_A
b $1C6F Monitor A: switches device mode and operates on the 4000h region (plausibly application/cartridge start; unverified)
c $1C8A
@ $1C92 label=CMD_K
b $1C92 Monitor K: search memory range for a byte value
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
@ $3F9B label=CMD_B
c $3F9B Monitor B: vector-region stub in this build (BASIC extension slot; semantics unverified)
b $3FA5
c $3FA7
b $3FB4
c $3FB9
b $3FC2
c $3FC4
i $4000
