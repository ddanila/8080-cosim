; Test whether a second consecutive cycle can assert A12 across a page boundary.
;
; In all-RAM mode, LHLD 0FFFh should read 0FFFh then 1000h, and LHLD 2FFFh
; should read 2FFFh then 3000h. Distinct bytes at the A12-low alternatives
; 0000h and 2000h expose a second cycle that cannot assert A12.
;
; Result at 4E00h (16 bytes):
;   00..03 "B12C"; 04=A5 complete
;   08..09 LHLD 0FFFh (expected 1F/20; A12-low failure 1F/10)
;   0A..0B LHLD 2FFFh (expected 2F/40; A12-low failure 2F/30)

bits 16
org 04000h

RESULT equ 04E00h

%macro WRITE4 2
    db 03Eh, %2
    db 032h
    dw %1
    db 032h
    dw %1
    db 032h
    dw %1
    db 032h
    dw %1
%endmacro

start:
    db 021h
    dw RESULT
    db 036h, 'B'
    db 023h, 036h, '1'
    db 023h, 036h, '2'
    db 023h, 036h, 'C'
    db 023h, 036h, 000h

    db 03Eh, 09Ah
    db 0D3h, 007h
    db 03Eh, 003h
    db 0D3h, 006h
    db 000h, 000h

    WRITE4 00000h, 010h
    WRITE4 00FFFh, 01Fh
    WRITE4 01000h, 020h
    WRITE4 02000h, 030h
    WRITE4 02FFFh, 02Fh
    WRITE4 03000h, 040h

    db 02Ah
    dw 00FFFh
    db 022h
    dw RESULT + 8
    db 02Ah
    dw 02FFFh
    db 022h
    dw RESULT + 0Ah

    db 0AFh
    db 0D3h, 006h
    db 03Eh, 09Bh
    db 0D3h, 007h
    db 03Eh, 0A5h
    db 032h
    dw RESULT + 4
    db 0AFh
    db 0C9h
