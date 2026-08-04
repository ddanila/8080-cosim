; Consecutive D15 read-cycle probe for the T32 monitor.
;
; Build with TARGET, EXPECTED0, and EXPECTED1 defined, load at 4000h, and
; invoke through loader API v2 CALL mode.  Each LHLD performs two consecutive
; memory reads from TARGET and TARGET+1 while all instructions execute in RAM.
;
; Result at 4100h:
;   00..03  "PAIR"
;   04..05  target address, big-endian
;   06..07  expected bytes at TARGET and TARGET+1
;   08      sample count (16 pairs)
;   09      A5h when complete
;   0A..29  sixteen observed byte pairs

bits 16
org 04000h

%ifndef TARGET
%define TARGET 01A00h
%endif

%ifndef EXPECTED0
%define EXPECTED0 03Eh
%endif

%ifndef EXPECTED1
%define EXPECTED1 01Ah
%endif

; READ_TARGET may be overridden independently for fast physical follow-ups:
; the first 32-byte loader chunk and its descriptive header then stay fixed,
; while only the second chunk containing the LHLD operand changes.
%ifndef READ_TARGET
%define READ_TARGET TARGET
%endif

RESULT       equ 04100h
SAMPLE_COUNT equ 16

start:
    db 021h                 ; LXI H,RESULT
    dw RESULT
    db 036h, 'P'            ; MVI M,'P'
    db 023h, 036h, 'A'      ; INX H / MVI M,'A'
    db 023h, 036h, 'I'      ; INX H / MVI M,'I'
    db 023h, 036h, 'R'      ; INX H / MVI M,'R'
    db 023h, 036h, (TARGET >> 8) & 0ffh
    db 023h, 036h, TARGET & 0ffh
    db 023h, 036h, EXPECTED0
    db 023h, 036h, EXPECTED1
    db 023h, 036h, SAMPLE_COUNT
    db 023h, 036h, 000h     ; completion marker

    db 011h                 ; LXI D,RESULT+10
    dw RESULT + 10
    db 006h, SAMPLE_COUNT   ; MVI B,SAMPLE_COUNT

sample_loop:
    db 02ah                 ; LHLD READ_TARGET: consecutive reads at target,+1
    dw READ_TARGET
    db 07dh                 ; MOV A,L
    db 012h                 ; STAX D
    db 013h                 ; INX D
    db 07ch                 ; MOV A,H
    db 012h                 ; STAX D
    db 013h                 ; INX D
    db 005h                 ; DCR B
    db 0c2h                 ; JNZ sample_loop
    dw sample_loop

    db 03eh, 0a5h           ; MVI A,A5h
    db 032h                 ; STA RESULT+9
    dw RESULT + 9
    db 0afh                 ; XRA A: return A=00h
    db 0c9h                 ; RET to T32
