; Seed control file for roms/jmon33.bin (Juku Monitor v3.3, MAME default BIOS,
; interrupt-driven; all eight block checksums pass). Same Monitor memory model
; as jmon22: short in-place boot, then high code dispatched via the vector
; region copied to FF40h+ (+C000h). Addresses are ROM file offsets. This image
; is the healthy structural reference for the jmon22 block-6/7 repair project
; (docs/jmon22-reconstruction.md). Code seeded by recursive descent from reset
; and the 3F40h-3FFFh vector slots, targets D000h-FFFFh translated by -C000h.

@ $0000 label=RESET
c $0000 Reset entry
b $0003 Stored per-block checksums, blocks 0-7 (verified: all eight pass the jmon22-convention additive sums)
@ $000B label=BOOT_MAIN
c $000B Boot: stack, warm/cold discriminator, then init
@ $0026 label=BOOT_PIT_INIT
c $0026 Boot PIT programming: same raster family; D55 ch0 as BCD 312; D57 ch2 as mode-0 one-shot (newer-generation marker)
b $009B
c $0100
b $012D
c $0151
b $01B8
c $01BB
b $01C3
c $01E8
b $01E9
c $03F6
b $0429
c $043E
b $044A
c $0687
b $0688
c $068B
b $0698
c $06A1
b $06C4
c $06CC
b $06DE
c $06E3
b $06F0
c $0734
t $074A
c $075A
t $075D
c $076A
t $0777 ENSV TA Kub.I / AT EKB credit string
c $078B
b $07D5
c $07ED
b $08FD
c $0918
b $0972
c $0978
b $0983
c $09B4
b $0A7A
c $0A97
b $0AB5
c $0AC7
b $0AFC
c $0B08
b $0B4D
c $0B59
b $0B9F
c $0BA1
b $0BAC
c $0BE7
b $0C17
c $0C1E
b $0C40
c $0CD5
b $0CD8
c $0CE5
b $0D5F
c $0D67
b $0DAD
c $0E02
b $0E06
c $0E13
b $0E15
c $0E74
b $0E8B
c $0E94
b $0EA0
c $0EA2
b $0ED0
c $0F40
b $0F4A
c $0F4C
b $0F51
c $0F56
b $0F71
c $0F93
b $0FAC
c $0FB5
b $0FF8
c $1014
b $101B
c $1056
b $1074
c $1078
b $1086
c $109D
b $10A1
c $10B9
t $10BB
c $10C6
b $10CA
c $10D5
b $10D9
c $10EA
b $1101
c $1103
b $113C
c $1155
b $115C
c $1169
b $1193
c $11C5
b $11D0
c $11E5
b $1214
c $122D
b $124E
c $124F
b $1253
c $126B
b $126C
c $12BA
b $12DC
c $12F1
b $1336
c $1345
b $1357
c $135E
b $13CB
c $13ED
b $13F3
c $1414
b $144C
c $147E
b $14D9
c $14DC
b $1507
c $1532
b $1574
c $157C
b $1582
c $1599
b $15B9
c $15C8
b $160C
c $1617
b $1626
c $163D
b $1644
c $165D
b $1687
c $169E
b $16E0
c $173F
b $1750
c $1760
b $177D
c $1787
b $178C
c $178D
b $179C
c $17AE
b $17DC
c $17E5
b $1811
c $182D
b $183F
c $1853
b $185E
c $1860
b $1872
c $187A
b $188D
c $189D
b $18DF
c $190E
b $1937
c $19AF
b $1A28
c $1B69
b $1B7F
@ $2000 label=CMD_T
b $2000 Monitor T: load system -- enters the Bootstrap v3.3 block
t $20A5 Bootstrap v3.3 banner: FDC 1791 on main board
b $20CA
t $20CD
b $20F1
t $20F3
b $2110
t $2112
b $2138
t $213B
b $2155
@ $2E29 label=CMD_B
b $2E29 Monitor B handler (command letter shared with the EktaSoft monitor; semantics not independently decoded here)
c $2E2F
b $2E5E
c $2E87
b $2EB1
c $2F08
t $2F35 Block-checksum failure UI: reports the failing EPROM number
b $2F3F
t $2F5D
c $2F6D
b $2F91
c $2FB5
b $3236
c $3296
b $3400
c $3404
b $3464
c $3493
b $368B
c $36C8
b $36D5
c $37A8
b $3847
c $3BAC
b $3BB5
c $3BBA
b $3BBF
t $3BC5 MONITOR 3.3 version banner
b $3BD0
c $3BD1
b $3C55 Monitor command dispatch table: FDSXGMCEKTBRWPA (same command set as the EktaSoft monitor)
c $3C83
b $3D0A
c $3D17
@ $3D6D label=CMD_D
b $3D6D Monitor D handler (command letter shared with the EktaSoft monitor; semantics not independently decoded here)
c $3D70
@ $3DA5 label=CMD_M
b $3DA5 Monitor M handler (command letter shared with the EktaSoft monitor; semantics not independently decoded here)
c $3DA8
b $3DB2
@ $3DD0 label=CMD_E
b $3DD0 Monitor E handler (command letter shared with the EktaSoft monitor; semantics not independently decoded here)
@ $3DDC label=CMD_C
b $3DDC Monitor C handler (command letter shared with the EktaSoft monitor; semantics not independently decoded here)
c $3DDF
@ $3E0D label=CMD_F
b $3E0D Monitor F handler (command letter shared with the EktaSoft monitor; semantics not independently decoded here)
c $3E19
@ $3E23 label=CMD_X
b $3E23 Monitor X handler (command letter shared with the EktaSoft monitor; semantics not independently decoded here)
@ $3E5B label=CMD_S
b $3E5B Monitor S handler (command letter shared with the EktaSoft monitor; semantics not independently decoded here)
@ $3E81 label=CMD_G
b $3E81 Monitor G handler (command letter shared with the EktaSoft monitor; semantics not independently decoded here)
c $3EBA
b $3EBF
@ $3ED0 label=CMD_R
b $3ED0 Monitor R handler (command letter shared with the EktaSoft monitor; semantics not independently decoded here)
@ $3ED8 label=CMD_W
b $3ED8 Monitor W handler (command letter shared with the EktaSoft monitor; semantics not independently decoded here)
@ $3EEB label=CMD_P
b $3EEB Monitor P handler (command letter shared with the EktaSoft monitor; semantics not independently decoded here)
c $3EFB
@ $3F01 label=CMD_A
b $3F01 Monitor A handler (command letter shared with the EktaSoft monitor; semantics not independently decoded here)
c $3F1C
@ $3F24 label=CMD_K
b $3F24 Monitor K handler (command letter shared with the EktaSoft monitor; semantics not independently decoded here)
c $3F30
c $3F40 High vector region, copied to FF40h-FFFFh at boot (+C000h); healthy reference for jmon22 block-7 repair
b $3F6B
c $3F6E
b $3FA4
c $3FA7
b $3FAD
c $3FB0
b $3FB3
c $3FB9
b $3FC2
c $3FC4
i $4000
