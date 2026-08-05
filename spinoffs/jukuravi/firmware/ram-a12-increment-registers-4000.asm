; Observe the CPU's architecturally visible 16-bit increment results directly.
;
; Load at 4000h and CALL through loader API v2. No high-address memory access
; is used: each register result is copied to a low-A12 result block. This
; separates an internal D1 increment result from D4/BA12 bus behavior.
;
; Result at 4D00h (24 bytes):
;   00..03 "X12C"; 04=A5 complete; 05..07 reserved
;   08..09 INX BC from 0FFFh (expected 1000h)
;   0A..0B INX DE from 1A00h (expected 1A01h; fault 0A01h)
;   0C..0D INX HL from 5A00h (expected 5A01h; fault 4A01h)
;   0E..0F INX SP from 9A00h (expected 9A01h; fault 8A01h)
;   10..11 DAD D: 1A00h + 0001h (expected 1A01h)
;   12..17 reserved

bits 16
org 04000h

RESULT   equ 04D00h
SAVED_SP equ 04DF0h

start:
    db 021h
    dw RESULT
    db 036h, 'X'
    db 023h, 036h, '1'
    db 023h, 036h, '2'
    db 023h, 036h, 'C'
    db 023h, 036h, 000h

    ; Preserve the caller stack without relying on its exact address.
    db 021h
    dw 0000h
    db 039h                 ; DAD SP
    db 022h
    dw SAVED_SP

    db 001h                 ; LXI B,0FFFh / INX B
    dw 00FFFh
    db 003h
    db 060h, 069h           ; MOV H,B / MOV L,C
    db 022h
    dw RESULT + 008h

    db 011h                 ; LXI D,1A00h / INX D
    dw 01A00h
    db 013h
    db 062h, 06Bh           ; MOV H,D / MOV L,E
    db 022h
    dw RESULT + 00Ah

    db 021h                 ; LXI H,5A00h / INX H
    dw 05A00h
    db 023h
    db 022h
    dw RESULT + 00Ch

    db 031h                 ; LXI SP,9A00h / INX SP
    dw 09A00h
    db 033h
    db 021h
    dw 0000h
    db 039h                 ; DAD SP copies SP into HL
    db 022h
    dw RESULT + 00Eh
    db 02Ah                 ; restore caller SP before any CALL/RET
    dw SAVED_SP
    db 0F9h

    db 021h                 ; DAD control: 1A00h + 0001h
    dw 01A00h
    db 011h
    dw 00001h
    db 019h
    db 022h
    dw RESULT + 010h

    db 03Eh, 0A5h
    db 032h
    dw RESULT + 4
    db 0AFh
    db 0C9h
