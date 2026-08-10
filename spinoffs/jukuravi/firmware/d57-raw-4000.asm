; Return repeated raw D57 counter readings, isolated by channel and polarity.
;
; Load at 4000h and CALL through loader API v2. Every channel receives an
; MSB-only mode-0 count of FF00h and then 3F00h. A fixed 40-iteration CPU delay
; lets the independently clocked counter advance before its MSB is latched and
; read. Eight repetitions expose intermittent DB7/path failures. Channel 0 is
; the serial baud generator; loader API v2 restores D57 and the 8251 after RET
; before it emits RETURN. This snippet restores channels 1 and 2 to quiet mode.
;
; Result at 4580h (56 bytes):
;   00..03 "D57R"; 04=A5 complete; 05=version 1; 06=repetitions; 07=reserved
;   Eight six-byte records at 08h:
;     ch0-high, ch0-low, ch1-high, ch1-low, ch2-high, ch2-low
; A valid high sample has DB7=1; a valid low sample has DB7=0.

bits 16
org 04000h

RESULT       equ 04580h
PIT_CONTROL  equ 01Bh
SETTLE       equ 40
REPETITIONS  equ 8

%macro SAMPLE 2
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
    db 012h                 ; STAX D into low-A12 result window
    db 013h                 ; INX D cannot cross or retain a high A12 here
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

    ; Preserve T31/T34's post-test SOUND/SYNC-B quiescent state. Channel 0 is
    ; restored by loader API v2 after this snippet returns.
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
