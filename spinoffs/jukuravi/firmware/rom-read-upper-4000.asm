; Focused, non-destructive T31 upper-ROM data-read probe.
;
; Load at 4000h and invoke through loader API v2 CALL mode. The snippet runs
; entirely from RAM and reads the four upper-half bytes that distinguish the
; physical 1000h boundary and the direct 106Fh instruction-fetch experiment.
;
; Result at 4200h (84 bytes):
;   00..03  "U12D"
;   04      record count (4)
;   05      samples per record (16)
;   06      A5h when complete
;   07      active record (1..4), zero after completion
;   Each 19-byte record contains target high, target low, expected, then
;   sixteen observed bytes.

bits 16
org 04000h

RESULT       equ 04200h
SAMPLE_COUNT equ 16

%macro store_immediate 1
    db 036h, %1             ; MVI M,value
    db 023h                 ; INX H
%endmacro

%macro write_record 3
    db 021h                 ; LXI H,record
    dw %3
    store_immediate (%1 >> 8) & 0ffh
    store_immediate %1 & 0ffh
    store_immediate %2
%endmacro

%macro sample_address 4
    db 03eh, %4             ; MVI A,active record
    db 032h                 ; STA RESULT+7
    dw RESULT + 7
    db 021h                 ; LXI H,target
    dw %1
    db 011h                 ; LXI D,result samples
    dw %3 + 3
    db 006h, SAMPLE_COUNT   ; MVI B,SAMPLE_COUNT
%%loop:
    db 07eh                 ; MOV A,M: read D15
    db 012h                 ; STAX D
    db 013h                 ; INX D
    db 005h                 ; DCR B
    db 0c2h                 ; JNZ loop
    dw %%loop
%endmacro

start:
    db 021h                 ; LXI H,RESULT
    dw RESULT
    store_immediate 'U'
    store_immediate '1'
    store_immediate '2'
    store_immediate 'D'
    store_immediate 4
    store_immediate SAMPLE_COUNT
    store_immediate 0       ; completion marker
    store_immediate 0       ; active record

    ; Record metadata. Samples are filled by the RAM-resident loops below.
    write_record 0100ch, 0b1h, RESULT + 8
    write_record 0106fh, 0c3h, RESULT + 27
    write_record 01070h, 00ch, RESULT + 46
    write_record 01071h, 00ah, RESULT + 65

    sample_address 0100ch, 0b1h, RESULT + 8, 1
    sample_address 0106fh, 0c3h, RESULT + 27, 2
    sample_address 01070h, 00ch, RESULT + 46, 3
    sample_address 01071h, 00ah, RESULT + 65, 4

    db 03eh, 0a5h           ; MVI A,A5h
    db 032h                 ; STA RESULT+6
    dw RESULT + 6
    db 0afh                 ; XRA A
    db 032h                 ; STA RESULT+7: no active record
    dw RESULT + 7
    db 0c9h                 ; RET to T31
