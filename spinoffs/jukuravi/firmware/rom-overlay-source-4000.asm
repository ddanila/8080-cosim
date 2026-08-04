; Distinguish a wrong consecutive ROM byte from underlying RAM or open bus.
;
; Load at 4000h and invoke through loader API v2 CALL mode.  The loader stack
; at C000h remains RAM in every memory view used here.  This probe writes
; distinct sentinels behind the low ROM and below the high ROM overlay, takes
; eight consecutive LHLD samples through each ROM mapping, then selects the
; all-RAM view and verifies the sentinels both before and after the overlay
; reads.  Each sentinel uses the loader's proven register-indirect repeated
; store pattern.  The probe restores Port C zero and PPI #0's all-input reset
; configuration before returning.
;
; Result at 4100h (56 bytes):
;   00..03  "OVLY"
;   04      sample count (8 pairs per mapping)
;   05      A5h when complete
;   06      Port C pin readback in mode 1 (low nibble must be 1)
;   07      Port C pin readback in mode 3 (low nibble must be 3)
;   08..09  expected D15 bytes at physical 1A00h: 3Eh,1Ah
;   0A..0B  RAM sentinel pair: 66h,C7h
;   0C..0D  pre-test mode-3 RAM pair at 1A00h
;   0E..0F  pre-test mode-3 RAM pair at DA00h
;   10..11  isolated mode-3 RAM bytes at 1A00h/1A01h
;   12..13  isolated mode-3 RAM bytes at DA00h/DA01h
;   14..23  eight mode-0 LHLD 1A00h pairs
;   24..33  eight mode-1 LHLD DA00h pairs (same D15 physical address)
;   34..35  post-test mode-3 consecutive RAM pair at 1A00h
;   36..37  post-test mode-3 consecutive RAM pair at DA00h

bits 16
org 04000h

RESULT       equ 04100h
SAMPLE_COUNT equ 8

start:
    db 021h                 ; LXI H,RESULT
    dw RESULT
    db 036h, 'O'
    db 023h, 036h, 'V'
    db 023h, 036h, 'L'
    db 023h, 036h, 'Y'
    db 023h, 036h, SAMPLE_COUNT
    db 023h, 036h, 000h     ; completion
    db 023h, 036h, 000h     ; mode-1 Port C readback
    db 023h, 036h, 000h     ; mode-3 Port C readback
    db 023h, 036h, 03Eh
    db 023h, 036h, 01Ah
    db 023h, 036h, 066h
    db 023h, 036h, 0C7h

    db 03Eh, 09Ah           ; PA/PB/PC upper input, PC lower output
    db 0D3h, 007h           ; mode 0; mode-set clears PC output latch

    ; Select all-RAM mode before initializing either underlying pair.  This
    ; removes the low-ROM write-behind path from the setup.  Repeat each
    ; register-indirect write eight times, matching the robust loader rather
    ; than relying on one absolute STA.
    db 03Eh, 003h
    db 0D3h, 006h
    db 000h, 000h
    db 03Eh, 066h
    db 011h
    dw 01A00h
    db 0CDh
    dw store8
    db 011h
    dw 0DA00h
    db 0CDh
    dw store8
    db 03Eh, 0C7h
    db 011h
    dw 01A01h
    db 0CDh
    dw store8
    db 011h
    dw 0DA01h
    db 0CDh
    dw store8

    ; Prove the underlying sentinels before either ROM-overlay sample.
    db 03Eh, 003h
    db 0D3h, 006h           ; physical memory mode 3: all RAM
    db 000h, 000h
    db 02Ah
    dw 01A00h
    db 022h
    dw RESULT + 0Ch
    db 02Ah
    dw 0DA00h
    db 022h
    dw RESULT + 0Eh
    db 03Ah                 ; isolated LDA 1A00h
    dw 01A00h
    db 032h
    dw RESULT + 010h
    db 03Ah                 ; isolated LDA 1A01h
    dw 01A01h
    db 032h
    dw RESULT + 011h
    db 03Ah                 ; isolated LDA DA00h
    dw 0DA00h
    db 032h
    dw RESULT + 012h
    db 03Ah                 ; isolated LDA DA01h
    dw 0DA01h
    db 032h
    dw RESULT + 013h
    db 0AFh
    db 0D3h, 006h           ; back to physical mode 0
    db 000h, 000h

    db 011h                 ; LXI D,RESULT+14h
    dw RESULT + 014h
    db 006h, SAMPLE_COUNT
low_loop:
    db 02Ah                 ; LHLD 1A00h, consecutive D15 reads in mode 0
    dw 01A00h
    db 07Dh, 012h, 013h     ; MOV A,L / STAX D / INX D
    db 07Ch, 012h, 013h     ; MOV A,H / STAX D / INX D
    db 005h                 ; DCR B
    db 0C2h                 ; JNZ low_loop
    dw low_loop

    db 03Eh, 001h
    db 0D3h, 006h           ; physical memory mode 1
    db 000h, 000h
    db 0DBh, 006h
    db 032h
    dw RESULT + 6
    db 011h                 ; LXI D,RESULT+24h
    dw RESULT + 024h
    db 006h, SAMPLE_COUNT
high_loop:
    db 02Ah                 ; LHLD DA00h, same D15 address in mode 1
    dw 0DA00h
    db 07Dh, 012h, 013h
    db 07Ch, 012h, 013h
    db 005h
    db 0C2h
    dw high_loop

    db 03Eh, 003h
    db 0D3h, 006h           ; physical memory mode 3: all RAM
    db 000h, 000h
    db 0DBh, 006h
    db 032h
    dw RESULT + 7
    db 02Ah                 ; direct underlying RAM at 1A00h
    dw 01A00h
    db 022h
    dw RESULT + 034h
    db 02Ah                 ; direct underlying RAM at DA00h
    dw 0DA00h
    db 022h
    dw RESULT + 036h

    db 0AFh
    db 0D3h, 006h           ; physical mode 0
    db 03Eh, 09Bh
    db 0D3h, 007h           ; restore PPI #0 reset directions
    db 03Eh, 0A5h
    db 032h
    dw RESULT + 5
    db 0AFh                 ; return A=00h
    db 0C9h

store8:
    db 006h, 008h           ; MVI B,8
store8_loop:
    db 012h                 ; STAX D
    db 005h                 ; DCR B
    db 0C2h                 ; JNZ store8_loop
    dw store8_loop
    db 0C9h
