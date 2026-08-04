; Prove or reject transient A12-low aliasing across all A15:A14 classes.
;
; Load at 4000h and invoke through loader API v2 CALL mode.  In all-RAM mode,
; each high-A12 target xA00h/xA01h and its A12-low alias (x-1)A00h/(x-1)A01h
; receive distinct bytes.  Isolated target reads, consecutive alias controls,
; and four consecutive target pairs are returned for the four A15:A14 classes.
; The probe restores mode 0 and PPI #0's reset directions before returning.
;
; Result at 4400h (60 bytes):
;   00..03  "A12M"
;   04      target pairs per class (4)
;   05      A5h when complete
;   06..07  reserved
;   Four 13-byte records at 08h,15h,22h,2Fh:
;     +0    high-A12 target high byte (1Ah,5Ah,9Ah,DAh)
;     +1..2 isolated target bytes
;     +3..4 consecutive A12-low alias control pair
;     +5..C four consecutive target pairs
;
; Programmed pairs:
;   0A=10/11, 1A=20/21; 4A=30/31, 5A=40/41
;   8A=50/51, 9A=60/61; CA=70/71, DA=80/81

bits 16
org 04000h

RESULT       equ 04400h
SAMPLE_COUNT equ 4

%macro INIT_PAIR 3
    db 011h
    dw %1
    db 03Eh, %2
    db 0CDh
    dw store8
    db 013h
    db 03Eh, %3
    db 0CDh
    dw store8
%endmacro

%macro SAMPLE_CLASS 4
    db 03Eh, %3             ; target high-byte identity
    db 032h
    dw RESULT + %4
    db 03Ah                 ; isolated target even
    dw %2
    db 032h
    dw RESULT + %4 + 1
    db 03Ah                 ; isolated target odd
    dw %2 + 1
    db 032h
    dw RESULT + %4 + 2
    db 02Ah                 ; consecutive lower-alias control
    dw %1
    db 022h
    dw RESULT + %4 + 3
    db 011h
    dw RESULT + %4 + 5
    db 006h, SAMPLE_COUNT
%%target_loop:
    db 02Ah                 ; consecutive high-A12 target pair
    dw %2
    db 07Dh, 012h, 013h
    db 07Ch, 012h, 013h
    db 005h
    db 0C2h
    dw %%target_loop
%endmacro

start:
    db 021h
    dw RESULT
    db 036h, 'A'
    db 023h, 036h, '1'
    db 023h, 036h, '2'
    db 023h, 036h, 'M'
    db 023h, 036h, SAMPLE_COUNT
    db 023h, 036h, 000h
    db 023h, 036h, 000h
    db 023h, 036h, 000h

    db 03Eh, 09Ah           ; PC lower output
    db 0D3h, 007h
    db 03Eh, 003h           ; all-RAM mode
    db 0D3h, 006h
    db 000h, 000h

    INIT_PAIR 00A00h, 010h, 011h
    INIT_PAIR 01A00h, 020h, 021h
    INIT_PAIR 04A00h, 030h, 031h
    INIT_PAIR 05A00h, 040h, 041h
    INIT_PAIR 08A00h, 050h, 051h
    INIT_PAIR 09A00h, 060h, 061h
    INIT_PAIR 0CA00h, 070h, 071h
    INIT_PAIR 0DA00h, 080h, 081h

    SAMPLE_CLASS 00A00h, 01A00h, 01Ah, 008h
    SAMPLE_CLASS 04A00h, 05A00h, 05Ah, 015h
    SAMPLE_CLASS 08A00h, 09A00h, 09Ah, 022h
    SAMPLE_CLASS 0CA00h, 0DA00h, 0DAh, 02Fh

    db 0AFh
    db 0D3h, 006h
    db 03Eh, 09Bh
    db 0D3h, 007h
    db 03Eh, 0A5h
    db 032h
    dw RESULT + 5
    db 0AFh
    db 0C9h

store8:
    db 006h, 008h
store8_loop:
    db 012h
    db 005h
    db 0C2h
    dw store8_loop
    db 0C9h
