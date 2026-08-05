; Compare A12 behavior across LHLD, POP H, and SHLD cycle classes.
;
; Load at 4000h and CALL through loader API v2. All test cells are initialized
; with unrolled absolute STA writes in all-RAM mode. LHLD uses the 8080 WZ
; temporary-address increment, POP H uses SP, and SHLD uses the WZ write path.
; The caller SP is saved and restored around POP tests. PPI #0 and memory mode
; are restored before RET.
;
; Result at 4C00h (32 bytes):
;   00..03 "I12C"; 04=A5 complete; 05..07 reserved
;   08..09 LHLD 0A00 lower control
;   0A..0B LHLD 1A00 upper test
;   0C..0D POP H from SP=4A00 lower control
;   0E..0F POP H from SP=5A00 upper test
;   10..13 isolated 8A00/8A01/9A00/9A01 before SHLD
;   14..17 isolated 8A00/8A01/9A00/9A01 after SHLD 9A00 of BB/AA
;   18..1F reserved

bits 16
org 04000h

RESULT   equ 04C00h
SAVED_SP equ 04CF0h

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

start:
    db 021h
    dw RESULT
    db 036h, 'I'
    db 023h, 036h, '1'
    db 023h, 036h, '2'
    db 023h, 036h, 'C'
    db 023h, 036h, 000h

    db 03Eh, 09Ah
    db 0D3h, 007h
    db 03Eh, 003h
    db 0D3h, 006h
    db 000h, 000h

    ; Save the API caller's SP without relying on undocumented entry depth.
    db 021h
    dw 0000h
    db 039h                 ; DAD SP
    db 022h
    dw SAVED_SP

    WRITE4 00A00h, 010h
    WRITE4 00A01h, 011h
    WRITE4 01A00h, 020h
    WRITE4 01A01h, 021h
    WRITE4 04A00h, 030h
    WRITE4 04A01h, 031h
    WRITE4 05A00h, 040h
    WRITE4 05A01h, 041h
    WRITE4 08A00h, 050h
    WRITE4 08A01h, 051h
    WRITE4 09A00h, 060h
    WRITE4 09A01h, 061h

    db 02Ah                 ; LHLD 0A00 lower control
    dw 00A00h
    db 022h
    dw RESULT + 008h
    db 02Ah                 ; LHLD 1A00 upper test
    dw 01A00h
    db 022h
    dw RESULT + 00Ah

    db 031h                 ; LXI SP,4A00 / POP H
    dw 04A00h
    db 0E1h
    db 022h
    dw RESULT + 00Ch
    db 031h                 ; LXI SP,5A00 / POP H
    dw 05A00h
    db 0E1h
    db 022h
    dw RESULT + 00Eh

    ; Restore caller SP before any further CALL/RET activity.
    db 02Ah
    dw SAVED_SP
    db 0F9h                 ; SPHL

    READ_MAP 08A00h, 09A00h, 010h
    db 021h                 ; LXI H,BBAAh (L=AA, H=BB)
    dw 0BBAAh
    db 022h                 ; SHLD 9A00 upper test
    dw 09A00h
    READ_MAP 08A00h, 09A00h, 014h

    db 0AFh
    db 0D3h, 006h
    db 03Eh, 09Bh
    db 0D3h, 007h
    db 03Eh, 0A5h
    db 032h
    dw RESULT + 4
    db 0AFh
    db 0C9h
