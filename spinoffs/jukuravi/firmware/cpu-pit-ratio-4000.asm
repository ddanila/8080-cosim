; Measure the effective CPU/PIT clock ratio without external instruments.
;
; Load at 4000h and CALL through loader API v2. D57 channel 1 is programmed as
; a 16-bit mode-0 down counter twice. The difference between the two latched
; remaining counts covers exactly 1,500 additional iterations of the
; DCX B / MOV A,B / ORA C / JNZ loop, or 36,000 8080 T-states. Fixed setup,
; programming and latch overhead cancels. The probe restores the speaker
; channel to T31/T34's quiet mode before RET.
;
; Result at 4500h (16 bytes, little-endian words):
;   00..03 "CPIT"; 04=A5 complete; 05=version 1
;   06..07 additional CPU T-states (36000)
;   08..09 remaining count after 500 iterations
;   0A..0B remaining count after 2000 iterations
;   0C..0F reserved

bits 16
org 04000h

RESULT       equ 04500h
PIT_CH1      equ 019h
PIT_CONTROL  equ 01Bh
SHORT_LOOPS  equ 500
LONG_LOOPS   equ 2000
DELTA_T      equ (LONG_LOOPS - SHORT_LOOPS) * 24

start:
    db 021h
    dw RESULT
    db 036h, 'C'
    db 023h, 036h, 'P'
    db 023h, 036h, 'I'
    db 023h, 036h, 'T'
    db 023h, 036h, 000h
    db 023h, 036h, 001h
    db 023h, 036h, DELTA_T & 0FFh
    db 023h, 036h, DELTA_T >> 8

    ; Channel 1, LSB+MSB, binary mode 0, count FFFFh.
    db 03Eh, 070h
    db 0D3h, PIT_CONTROL
    db 03Eh, 0FFh
    db 0D3h, PIT_CH1
    db 0D3h, PIT_CH1
    db 001h
    dw SHORT_LOOPS
short_loop:
    db 00Bh, 078h, 0B1h
    db 0C2h
    dw short_loop
    db 03Eh, 040h           ; latch channel 1
    db 0D3h, PIT_CONTROL
    db 0DBh, PIT_CH1
    db 032h
    dw RESULT + 8
    db 0DBh, PIT_CH1
    db 032h
    dw RESULT + 9

    db 03Eh, 070h
    db 0D3h, PIT_CONTROL
    db 03Eh, 0FFh
    db 0D3h, PIT_CH1
    db 0D3h, PIT_CH1
    db 001h
    dw LONG_LOOPS
long_loop:
    db 00Bh, 078h, 0B1h
    db 0C2h
    dw long_loop
    db 03Eh, 040h
    db 0D3h, PIT_CONTROL
    db 0DBh, PIT_CH1
    db 032h
    dw RESULT + 10
    db 0DBh, PIT_CH1
    db 032h
    dw RESULT + 11

    ; Quiet channel 1 exactly as T31/T34 do before entering the loader.
    db 03Eh, 050h
    db 0D3h, PIT_CONTROL
    db 03Eh, 001h
    db 0D3h, PIT_CH1
    db 03Eh, 0A5h
    db 032h
    dw RESULT + 4
    db 0AFh
    db 0C9h
