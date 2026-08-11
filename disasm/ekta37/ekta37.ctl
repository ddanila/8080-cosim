; Seed control file for roms/ekta37.bin (EktaSoft '88 Serial #0037, RomBios 3.43m).
; ROM 0000-17FF executes in place; 1800-3FFF executes relocated at +C000
; (runtime D800-FFFF). Addresses here are ROM file offsets.
; Code regions: recursive descent from reset + monitor vectors + verified
; NetBios entries, with control-flow targets D800-FFFF translated by -C000.

@ $0000 label=RESET
c $0000 Reset entry
b $0003
@ $0017 label=BOOT_MAIN
c $0017
b $002C
c $00CE
b $00D6
t $00E0
b $00FA
t $013A
b $0158
t $015A
b $0161
c $0195
@ $01D4 label=BOOT_PIT_INIT
c $01D4 Exact boot PIT programming (docs/video-pit-timing.md; raster + D57)
b $0325
c $03CA
@ $03E0 label=BLOCK1_CHECKSUM
c $03E0 Block-1 checksum routine (docs/cosim-runtime-reference.md)
b $048C
c $049C
b $04A7
c $0698
b $06A5
c $06BD
b $06DB
c $08D8
b $0933
c $0A7A
b $0AC1
c $0BE5
b $0BF0
c $0D73
b $0D83
c $0D98
b $0DAB
c $0FF4
b $1076
c $11E6
b $123F
c $1841
b $188B
c $189E
b $18A7
c $18AC
b $18B1
c $18C8
b $194D
c $1965
b $1977
t $19A9
b $19C4
c $19CC
b $1A53
c $1A60
b $1AB6
c $1AB9
b $1AEE
c $1AF1
b $1AFB
c $1B28
b $1B56
c $1B62
b $1B6C
c $1C03
b $1C08
c $1C60
b $1C66
c $1C81
b $1C89
c $1C95
b $1CA5
c $1CD0
b $1CFC
c $22AF
b $23C4
t $23C6
b $23EA
c $2477
b $2541
c $2565
b $29A7
c $29B3
b $2AA2
t $2C24
b $2C2E
t $2C2F
b $2C3E
c $2D38
b $2D43
c $2F66
b $2F87
c $308D
b $3118
c $3379
b $3396
@ $34B7 label=NET_CONFIG_CMD
c $34B7 NetBios 'S'/'J' configuration commands (docs/ekta37-netbios-notes.md)
@ $34D6 label=NET_USART_INIT
c $34D6 NetBios 8251 init: baud from D5B2h via D57 ch0, mode 5Eh, cmd 35h
@ $3523 label=NET_MON_ARG_FF
c $3523
@ $352B label=NET_TXEN_WRAP
c $352B NetBios TxEN-gated wrapper around monitor call FF7Ah
@ $3540 label=NET_TX_BYTE
c $3540 NetBios transmit byte
@ $3544 label=NET_RX_BYTE
c $3544 NetBios receive byte + error mask 38h
b $357A
c $35C6
b $35D1
c $3605
b $3612
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
