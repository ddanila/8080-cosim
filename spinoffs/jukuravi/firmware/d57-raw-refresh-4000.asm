; Return repeated raw D57 readings while keeping T35's DRAM refreshed.
;
; This is the T35-safe form of d57-raw-4000.asm. A complete CALL 07A9h sweep
; precedes every counter sample; the intervening programming, 40-iteration
; settle loop, latch, read, and result store remain below the available time
; budget. The public refresh ABI preserves BC, DE, HL, and SP.

bits 16
org 04000h

RESULT       equ 04580h
REFRESH      equ 007A9h
PIT_CONTROL  equ 01Bh
SETTLE       equ 40
REPETITIONS  equ 8

%macro SAMPLE 2
    db 0CDh
    dw REFRESH
    db 03Eh, (020h | (%1 << 6))
    db 0D3h, PIT_CONTROL
    db 03Eh, %2
    db 0D3h, (018h + %1)
    db 006h, SETTLE
%%settle:
    db 005h
    db 0C2h
    dw %%settle
    db 03Eh, (%1 << 6)
    db 0D3h, PIT_CONTROL
    db 0DBh, (018h + %1)
    db 012h
    db 013h
%endmacro

start:
    db 021h
    dw RESULT
    db 036h, 'D'
    db 023h, 036h, '5'
    db 023h, 036h, '7'
    db 023h, 036h, 'R'
    db 023h, 036h, 000h
    db 023h, 036h, 001h
    db 023h, 036h, REPETITIONS
    db 023h, 036h, 000h

    db 011h
    dw RESULT + 8
    db 00Eh, REPETITIONS
sample_repetition:
    SAMPLE 0, 0FFh
    SAMPLE 0, 03Fh
    SAMPLE 1, 0FFh
    SAMPLE 1, 03Fh
    SAMPLE 2, 0FFh
    SAMPLE 2, 03Fh
    db 00Dh
    db 0C2h
    dw sample_repetition

    ; Restore T31/T34/T35's post-test SOUND/SYNC-B quiescent state. Channel 0
    ; is restored by loader API v2 after this snippet returns.
    db 03Eh, 050h
    db 0D3h, PIT_CONTROL
    db 03Eh, 001h
    db 0D3h, 019h
    db 03Eh, 090h
    db 0D3h, PIT_CONTROL
    db 03Eh, 001h
    db 0D3h, 01Ah
    db 03Eh, 0A5h
    db 032h
    dw RESULT + 4
    db 0AFh
    db 0C9h
