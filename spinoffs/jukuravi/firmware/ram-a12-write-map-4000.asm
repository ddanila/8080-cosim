; Map isolated writes and consecutive reads across two A12 page pairs.
;
; Load at 4000h and CALL through loader API v2. In all-RAM mode, the 0A/1A
; group is written lower-first and the CA/DA group upper-first. Each group
; records all four isolated bytes before writes, after the first page write,
; after the second page write, then four LHLD pairs from each page. Reversing
; write order distinguishes an address alias from a last-writer/output latch.
;
; Result at 4600h (64 bytes):
;   00..03 "W12M"; 04=A5 complete; 05=4 pair samples; 06..07 reserved
;   08..23  0A/1A: baseline4, after-lower4, after-upper4
;   14..1B  four LHLD 0A00 pairs
;   1C..23  four LHLD 1A00 pairs
;   24..2F  CA/DA: baseline4, after-upper4, after-lower4
;   30..37  four LHLD CA00 pairs
;   38..3F  four LHLD DA00 pairs
; Four-byte isolated maps are ordered lower-even, lower-odd, upper-even,
; upper-odd.

bits 16
org 04000h

RESULT equ 04600h

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

%macro PAIRS4 2
    db 011h
    dw RESULT + %2
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

start:
    db 021h
    dw RESULT
    db 036h, 'W'
    db 023h, 036h, '1'
    db 023h, 036h, '2'
    db 023h, 036h, 'M'
    db 023h, 036h, 000h
    db 023h, 036h, 004h
    db 023h, 036h, 000h
    db 023h, 036h, 000h

    db 03Eh, 09Ah
    db 0D3h, 007h
    db 03Eh, 003h
    db 0D3h, 006h           ; all RAM
    db 000h, 000h

    ; Group 0A/1A: lower page first, upper page second.
    READ_MAP 00A00h, 01A00h, 008h
    WRITE4 00A00h, 010h
    WRITE4 00A01h, 011h
    READ_MAP 00A00h, 01A00h, 00Ch
    WRITE4 01A00h, 020h
    WRITE4 01A01h, 021h
    READ_MAP 00A00h, 01A00h, 010h
    PAIRS4 00A00h, 014h
    PAIRS4 01A00h, 01Ch

    ; Group CA/DA: upper page first, lower page second.
    READ_MAP 0CA00h, 0DA00h, 024h
    WRITE4 0DA00h, 080h
    WRITE4 0DA01h, 081h
    READ_MAP 0CA00h, 0DA00h, 028h
    WRITE4 0CA00h, 070h
    WRITE4 0CA01h, 071h
    READ_MAP 0CA00h, 0DA00h, 02Ch
    PAIRS4 0CA00h, 030h
    PAIRS4 0DA00h, 038h

    db 0AFh
    db 0D3h, 006h
    db 03Eh, 09Bh
    db 0D3h, 007h
    db 03Eh, 0A5h
    db 032h
    dw RESULT + 4
    db 0AFh
    db 0C9h
