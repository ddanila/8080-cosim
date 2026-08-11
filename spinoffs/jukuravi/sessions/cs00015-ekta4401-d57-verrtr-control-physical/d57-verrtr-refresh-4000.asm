; D57 raw discriminator with a channel-2 wait sized for /VER RTR.
;
; D57 CLK0 is 1.23 MHz, CLK1 is 2 MHz, but CLK2 is the active-low vertical
; retrace output from D55 channel 1 (about 49.92 Hz under the EktaSoft raster).
; The historical 40-iteration settle loop is retained for channels 0/1.  For
; channel 2, 64 complete T36 refresh sweeps follow every count write.  At the
; measured 1.2 ms per sweep this spans roughly 79 ms / four frame-clock edges
; without putting DRAM retention at risk.
;
; Result at 4580h, 56 bytes:
;   00..03 "D57S"; 04=A5 complete; 05=version 2; 06=repetitions;
;   07=channel-2 wait sweeps; then eight {ch0 hi/lo, ch1 hi/lo, ch2 hi/lo}.

bits 16
org 04000h

RESULT       equ 04580h
REFRESH      equ 007A9h
PIT_CONTROL  equ 01Bh
SETTLE       equ 40
SLOW_SWEEPS  equ 64
REPETITIONS  equ 8

%macro SAMPLE_FAST 2
    db 0CDh
    dw REFRESH
    db 03Eh, (020h | (%1 << 6))
    db 0D3h, PIT_CONTROL
    db 03Eh, %2
    db 0D3h, (018h + %1)
    db 006h, SETTLE
%%settle:
    db 005h
    db 0C2h
    dw %%settle
    db 03Eh, (%1 << 6)
    db 0D3h, PIT_CONTROL
    db 0DBh, (018h + %1)
    db 012h
    db 013h
%endmacro

%macro SAMPLE_SLOW_CH2 1
    db 0CDh
    dw REFRESH
    db 03Eh, 0A0h
    db 0D3h, PIT_CONTROL
    db 03Eh, %1
    db 0D3h, 01Ah
    db 006h, SLOW_SWEEPS
%%wait_edges:
    db 0CDh
    dw REFRESH
    db 005h
    db 0C2h
    dw %%wait_edges
    db 03Eh, 080h
    db 0D3h, PIT_CONTROL
    db 0DBh, 01Ah
    db 012h
    db 013h
%endmacro

start:
    db 021h
    dw RESULT
    db 036h, 'D'
    db 023h, 036h, '5'
    db 023h, 036h, '7'
    db 023h, 036h, 'S'
    db 023h, 036h, 000h
    db 023h, 036h, 002h
    db 023h, 036h, REPETITIONS
    db 023h, 036h, SLOW_SWEEPS

    db 011h
    dw RESULT + 8
    db 00Eh, REPETITIONS
sample_repetition:
    SAMPLE_FAST 0, 0FFh
    SAMPLE_FAST 0, 03Fh
    SAMPLE_FAST 1, 0FFh
    SAMPLE_FAST 1, 03Fh
    SAMPLE_SLOW_CH2 0FFh
    SAMPLE_SLOW_CH2 03Fh
    db 00Dh
    db 0C2h
    dw sample_repetition

    ; Restore SOUND to the diagnostic quiescent state.
    db 03Eh, 050h
    db 0D3h, PIT_CONTROL
    db 03Eh, 001h
    db 0D3h, 019h

    ; Restore the exact EktaSoft D57 channel-2 / SYNC_B programming.
    db 03Eh, 0B0h
    db 0D3h, PIT_CONTROL
    db 03Eh, 0FFh
    db 0D3h, 01Ah
    db 0D3h, 01Ah

    db 03Eh, 0A5h
    db 032h
    dw RESULT + 4
    db 0AFh
    db 0C9h
