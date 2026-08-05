; Survey A12 behavior of consecutive LHLD reads in all A15:A14 classes.
;
; Load at 4000h and CALL through loader API v2. In all-RAM mode, each low/high
; A12 page pair is initialized by unrolled absolute STA instructions. This
; avoids the faulty repeated-STAX setup identified by ram-a12-write-map. Each
; record returns four isolated bytes, four lower-page LHLD pairs, and four
; upper-page LHLD pairs. PPI #0 and memory mode are restored before RET.
;
; Result at 4800h (88 bytes):
;   00..03 "L12C"; 04=A5 complete; 05=4 pair samples; 06..07 reserved
;   Four 20-byte records at 08h,1Ch,30h,44h:
;     +00..03 isolated lower-even/lower-odd/upper-even/upper-odd
;     +04..0B four lower-page LHLD pairs
;     +0C..13 four upper-page LHLD pairs
;
; Programmed pairs:
;   0A=10/11, 1A=20/21; 4A=30/31, 5A=40/41
;   8A=50/51, 9A=60/61; CA=70/71, DA=80/81

bits 16
org 04000h

RESULT equ 04800h

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

%macro READ_MAP 3
    db 03Ah
    dw %1
    db 032h
    dw RESULT + %3
    db 03Ah
    dw %1 + 1
    db 032h
    dw RESULT + %3 + 1
    db 03Ah
    dw %2
    db 032h
    dw RESULT + %3 + 2
    db 03Ah
    dw %2 + 1
    db 032h
    dw RESULT + %3 + 3
%endmacro

%macro PAIRS4 3
    db 011h
    dw RESULT + %3
    db 006h, 004h
%%loop:
    db 02Ah
    dw %1
    db 07Dh, 012h, 013h
    db 07Ch, 012h, 013h
    db 005h
    db 0C2h
    dw %%loop
%endmacro

%macro CLASS 9
    WRITE4 %1, %3
    WRITE4 %1 + 1, %4
    WRITE4 %2, %5
    WRITE4 %2 + 1, %6
    READ_MAP %1, %2, %7
    PAIRS4 %1, %2, %8
    PAIRS4 %2, %1, %9
%endmacro

start:
    db 021h
    dw RESULT
    db 036h, 'L'
    db 023h, 036h, '1'
    db 023h, 036h, '2'
    db 023h, 036h, 'C'
    db 023h, 036h, 000h
    db 023h, 036h, 004h
    db 023h, 036h, 000h
    db 023h, 036h, 000h

    db 03Eh, 09Ah
    db 0D3h, 007h
    db 03Eh, 003h
    db 0D3h, 006h
    db 000h, 000h

    CLASS 00A00h, 01A00h, 010h, 011h, 020h, 021h, 008h, 00Ch, 014h
    CLASS 04A00h, 05A00h, 030h, 031h, 040h, 041h, 01Ch, 020h, 028h
    CLASS 08A00h, 09A00h, 050h, 051h, 060h, 061h, 030h, 034h, 03Ch
    CLASS 0CA00h, 0DA00h, 070h, 071h, 080h, 081h, 044h, 048h, 050h

    db 0AFh
    db 0D3h, 006h
    db 03Eh, 09Bh
    db 0D3h, 007h
    db 03Eh, 0A5h
    db 032h
    dw RESULT + 4
    db 0AFh
    db 0C9h
