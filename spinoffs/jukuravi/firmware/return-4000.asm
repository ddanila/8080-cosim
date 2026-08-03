; T28 ROM-controlled CALL/RET proof for the Intel 8080.
;
; Load at 4000h. The ROM pushes its continuation and enters here. Write an
; eight-byte result at 4100h, return A=42h, and use an ordinary RET so T28 can
; report the register value, read the result block, and remain in its monitor.

bits 16
org 04000h

    db 021h                 ; LXI H,4100h
    dw 04100h
    db 036h, 054h           ; MVI M,'T'
    db 023h, 036h, 032h     ; INX H / MVI M,'2'
    db 023h, 036h, 038h     ; INX H / MVI M,'8'
    db 023h, 036h, 052h     ; INX H / MVI M,'R'
    db 023h, 036h, 045h     ; INX H / MVI M,'E'
    db 023h, 036h, 054h     ; INX H / MVI M,'T'
    db 023h, 036h, 021h     ; INX H / MVI M,'!'
    db 023h, 036h, 000h     ; INX H / MVI M,0
    db 03eh, 042h           ; MVI A,42h
    db 0c9h                 ; RET to T28's ROM continuation
