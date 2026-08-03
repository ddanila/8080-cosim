; Minimal real-board loader proof for the Intel 8080.
;
; Load and run at 4000h.  Emit three valid Jukuravi heartbeat frames through
; the diagnostic ROM's fixed SERIAL_PUT vector at 0A03h, wait for the final
; byte to drain from the 8251, then halt.

bits 16
org 04000h

%macro serial_put 1
    db 03eh, %1              ; MVI A,byte
    db 0cdh, 003h, 00ah      ; CALL 0A03h (SERIAL_PUT)
%endmacro

; TYPE_HEARTBEAT, version 1, sequence 0; CRC-8/ATM = 6Ah.
serial_put 0a5h
serial_put 05ah
serial_put 030h
serial_put 002h
serial_put 001h
serial_put 000h
serial_put 06ah

; Sequence 1; CRC-8/ATM = 6Dh.
serial_put 0a5h
serial_put 05ah
serial_put 030h
serial_put 002h
serial_put 001h
serial_put 001h
serial_put 06dh

; Sequence 2; CRC-8/ATM = 64h.
serial_put 0a5h
serial_put 05ah
serial_put 030h
serial_put 002h
serial_put 001h
serial_put 002h
serial_put 064h

; Drain well beyond one 2400-baud character before halting.
    db 001h                 ; LXI B,1000h
    dw 01000h
.drain:
    db 00bh                 ; DCX B
    db 078h                 ; MOV A,B
    db 0b1h                 ; ORA C
    db 0c2h                 ; JNZ .drain
    dw .drain
    db 076h                 ; HLT
