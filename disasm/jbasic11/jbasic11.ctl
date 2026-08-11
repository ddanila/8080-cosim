; Seed control file for roms/jbasic11.bin (Juku BASIC 1.1 cartridge, 8 KiB).
; Addresses are cartridge FILE OFFSETS. The runtime mapping is an explicitly
; open boundary (PLAN.md cartridge BASIC loading): the apparent JMP at offset 0
; targets data under an org-0 reading, so this seed deliberately marks no code.
; The BASIC body identity to the Monitor images is content-level and
; mapping-independent; it served as a donor in the jmon22 block-3 proof.

b $0000 Cartridge header (file offsets; the physical runtime mapping is an open boundary -- PLAN.md cartridge BASIC loading -- so no byte here is asserted as code)
b $0100 Shared BASIC body: monitor offset = cartridge offset + 2C8h, byte-identical to jmon33 and to jmon22 except its proven 1EFCh byte (docs/jmon22-reconstruction.md)
t $0482
b $0492
t $0495
b $04A2
t $04AF ENSV TA Kub.I / AT EKB credit string
b $04C3
i $2000
