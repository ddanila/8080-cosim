; Survey high-A12 consecutive reads across all D2 A10:A9 input classes.
;
; Load at 4000h and CALL through loader API v2. Absolute STA writes seed the
; A12-low and A12-high pairs at offsets 000h, 200h, 400h, and 600h. Each record
; returns four isolated bytes followed by four LHLD pairs from the high page.
; A11 remains zero; A10:A9 covers 00,01,10,11.
;
; Result at 4F00h (56 bytes), deliberately in a low-A12 page:
;   00..03 "R12C"; 04=A5 complete; 05=4 pair samples; 06..07 reserved
;   Four 12-byte records at 08h,14h,20h,2Ch:
;     +00..03 isolated lower-even/lower-odd/upper-even/upper-odd
;     +04..0B four high-A12 LHLD pairs

bits 16
org 04000h

RESULT equ 04F00h

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

%macro CLASS 9
    WRITE4 %1, %3
    WRITE4 %1 + 1, %4
    WRITE4 %2, %5
    WRITE4 %2 + 1, %6
    db 03Ah
    dw %1
    db 032h
    dw RESULT + %7
    db 03Ah
    dw %1 + 1
    db 032h
    dw RESULT + %7 + 1
    db 03Ah
    dw %2
    db 032h
    dw RESULT + %7 + 2
    db 03Ah
    dw %2 + 1
    db 032h
    dw RESULT + %7 + 3
    db 011h
    dw RESULT + %8
    db 006h, 004h
%%loop:
    db 02Ah
    dw %2
    db 07Dh, 012h, 013h
    db 07Ch, 012h, 013h
    db 005h
    db 0C2h
    dw %%loop
%endmacro

start:
    db 021h
    dw RESULT
    db 036h, 'R'
    db 023h, 036h, '1'
    db 023h, 036h, '2'
    db 023h, 036h, 'C'
    db 023h, 036h, 000h
    db 023h, 036h, 004h

    db 03Eh, 09Ah
    db 0D3h, 007h
    db 03Eh, 003h
    db 0D3h, 006h
    db 000h, 000h

    CLASS 00000h, 01000h, 010h, 011h, 020h, 021h, 008h, 00Ch, 000h
    CLASS 00200h, 01200h, 030h, 031h, 040h, 041h, 014h, 018h, 000h
    CLASS 00400h, 01400h, 050h, 051h, 060h, 061h, 020h, 024h, 000h
    CLASS 00600h, 01600h, 070h, 071h, 080h, 081h, 02Ch, 030h, 000h

    db 0AFh
    db 0D3h, 006h
    db 03Eh, 09Bh
    db 0D3h, 007h
    db 03Eh, 0A5h
    db 032h
    dw RESULT + 4
    db 0AFh
    db 0C9h
