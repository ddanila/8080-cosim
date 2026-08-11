; Seed control file for roms/jmon22.bin (Juku Monitor v2.2, public museum image;
; blocks 3/6/7 fail internal checksums -- see docs/jmon22-reconstruction.md).
; The image is preserved unchanged, including the proven-wrong byte at 1EFCh.
; Blocks 6-7 (3000h-3FFFh) came from unstable physical reads: they are marked
; data and deliberately excluded from code discovery until better captures or
; donors resolve them. Code seeded by recursive descent from reset with
; control-flow targets D000h-FFFFh translated by -C000h.

@ $0000 label=RESET
c $0000 Reset entry
b $0003 Stored per-block checksums, blocks 0-7 (docs/jmon22-reconstruction.md); stored block-3/6/7 values do not match this image's computed sums
@ $000B label=BLOCK_CHECKSUM_VERIFY
c $000B Boot-time block checksum verifier over the 0003h-000Ah table
@ $003E label=WARM_CHECK
c $003E Stack setup and warm/cold discriminator over D7A6h RAM state (interpretation; skips PIT init when warm)
@ $0051 label=BOOT_PIT_INIT
c $0051 Boot PIT programming: same raster family as EktaSoft; D57 ch2 as 38.4 kHz square wave (generation marker)
@ $00A2 label=PPI_INIT
c $00A2 PPI initialization: control 9Bh to port 0Fh, 82h to port 07h
@ $00AA label=RELOCATE_HIGH
c $00AA Copy ROM 3F40h-3FFFh to RAM FF40h-FFFFh (vector table; +C000h)
@ $00C3 label=CHECKSUM_FAIL
c $00C3 Block checksum mismatch handler
@ $00C8 label=COPY_BLOCK
c $00C8 Copy helper: HL=source, DE=destination, B=count
b $00D1
c $0151
b $016A
b $03C8 Shared BASIC body: byte-identical to jmon33 up to the proven corrupt byte
c $17F9
b $1811
b $1EFC PROVEN corrupt byte: image reads 9Ah, evidence-proven DAh (jmon33 + cartridge donors + checksum closure); image retained unrepaired
b $1EFD Shared BASIC body continues
b $3000 BLOCK 6: UNSTABLE SOURCE READS, checksum delta +40h -- bytes untrusted, excluded from code discovery
b $3800 BLOCK 7: UNSTABLE SOURCE READS (50 divergences over seven attempts), checksum delta +A3h -- bytes untrusted, excluded from code discovery
i $4000
