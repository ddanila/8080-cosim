; Minimal, non-destructive D15 data-read probe for the T31 monitor.
;
; Build with TARGET and EXPECTED defined, load at 4000h, and invoke through
; loader API v2 CALL mode. The snippet reads one ROM address 16 times while
; executing entirely from RAM, stores the observations at 4100h, and returns.
;
; Result at 4100h:
;   00..03  "A12S"
;   04..05  target address, big-endian
;   06      expected byte
;   07      sample count (16)
;   08      A5h when complete
;   09..18  observed bytes

bits 16
org 04000h

%ifndef TARGET
%define TARGET 00017h
%endif

%ifndef EXPECTED
%define EXPECTED 001h
%endif

RESULT       equ 04100h
SAMPLE_COUNT equ 16

start:
    db 021h                 ; LXI H,RESULT
    dw RESULT
    db 036h, 'A'            ; MVI M,'A'
    db 023h, 036h, '1'      ; INX H / MVI M,'1'
    db 023h, 036h, '2'      ; INX H / MVI M,'2'
    db 023h, 036h, 'S'      ; INX H / MVI M,'S'
    db 023h, 036h, (TARGET >> 8) & 0ffh
    db 023h, 036h, TARGET & 0ffh
    db 023h, 036h, EXPECTED
    db 023h, 036h, SAMPLE_COUNT
    db 023h, 036h, 000h     ; completion marker

    db 021h                 ; LXI H,TARGET
    dw TARGET
    db 011h                 ; LXI D,RESULT+9
    dw RESULT + 9
    db 006h, SAMPLE_COUNT   ; MVI B,SAMPLE_COUNT

sample_loop:
    db 07eh                 ; MOV A,M: read D15
    db 012h                 ; STAX D
    db 013h                 ; INX D
    db 005h                 ; DCR B
    db 0c2h                 ; JNZ sample_loop
    dw sample_loop

    db 03eh, 0a5h           ; MVI A,A5h
    db 032h                 ; STA RESULT+8
    dw RESULT + 8
    db 0afh                 ; XRA A: return A=00h
    db 0c9h                 ; RET to T31
