; Play the first twelve notes of the familiar "Smoke on the Water" riff on
; the Juku speaker, then return cooperatively to the T31 monitor.
;
; Load at 4000h and invoke in T28/T31 CALL mode. D57 channel 1 is driven from
; the source-proved nominal 2 MHz clock. Mode 3 divides that clock by each
; table value. The published intro is in 4/4 at quarter-note = 112. Tone and
; rest lengths below are expressed in eighth-note units; one unit is nominally
; 60 / 112 / 2 = 267.857 ms at the 2 MHz CPU clock.
;
; Completion contract:
;   A = 0Ch
;   4100h..4103h = "SMOK"
;   4104h = 00h (notes remaining)
;   ordinary RET returns to T31, which restores the UART and its baud timer.

bits 16
org 04000h

start:
    db 0f3h                 ; DI
    db 021h                 ; LXI H,note_table
    dw note_table
    db 016h, 00ch           ; MVI D,12 notes

note_loop:
    db 03eh, 076h           ; MVI A,76h: D57 ch1, LSB+MSB, mode 3
    db 0d3h, 01bh           ; OUT 1Bh
    db 07eh                 ; MOV A,M: divisor low
    db 0d3h, 019h           ; OUT 19h
    db 023h                 ; INX H
    db 07eh                 ; MOV A,M: divisor high
    db 0d3h, 019h           ; OUT 19h
    db 023h                 ; INX H

    db 05eh                 ; MOV E,M: sounding eighth-note units
    db 023h                 ; INX H
tone_unit:
    db 001h                 ; LXI B,22321: nominal 267.852 ms
    dw 22321
note_delay:
    db 00bh, 078h, 0b1h     ; DCX B / MOV A,B / ORA C
    db 0c2h                 ; JNZ note_delay
    dw note_delay
    db 01dh                 ; DCR E
    db 0c2h                 ; JNZ tone_unit
    dw tone_unit

    db 03eh, 050h           ; MVI A,50h: D57 ch1, LSB-only, mode 0
    db 0d3h, 01bh           ; OUT 1Bh
    db 03eh, 001h           ; MVI A,1: static high = silence
    db 0d3h, 019h           ; OUT 19h

    db 05eh                 ; MOV E,M: silent eighth-note units
    db 023h                 ; INX H
    db 07bh, 0b7h           ; MOV A,E / ORA A
    db 0cah                 ; JZ gap_done (D-flat leads directly into C)
    dw gap_done
gap_unit:
    db 001h                 ; LXI B,22321: nominal 267.852 ms
    dw 22321
gap_delay:
    db 00bh, 078h, 0b1h     ; DCX B / MOV A,B / ORA C
    db 0c2h                 ; JNZ gap_delay
    dw gap_delay
    db 01dh                 ; DCR E
    db 0c2h                 ; JNZ gap_unit
    dw gap_unit

gap_done:
    db 015h                 ; DCR D
    db 07ah                 ; MOV A,D
    db 032h                 ; STA 4104h: audible/simulation progress marker
    dw 04104h
    db 0c2h                 ; JNZ note_loop
    dw note_loop

    db 021h                 ; LXI H,4100h
    dw 04100h
    db 036h, 'S'            ; MVI M,'S'
    db 023h, 036h, 'M'      ; INX H / MVI M,'M'
    db 023h, 036h, 'O'      ; INX H / MVI M,'O'
    db 023h, 036h, 'K'      ; INX H / MVI M,'K'
    db 03eh, 00ch           ; MVI A,12
    db 0c9h                 ; RET to T31

; Divisors use round(2,000,000 / frequency). Each row contains divisor,
; sounding eighth-note units, then silent eighth-note units. The complete
; table is exactly 32 eighth notes = four 4/4 bars.
note_table:
    dw 5102                 ; G4   392.00 Hz
    db 1, 1
    dw 4290                 ; Bb4  466.20 Hz
    db 1, 1
    dw 3822                 ; C5   523.29 Hz
    db 2, 1
    dw 5102                 ; G4   392.00 Hz
    db 1, 1
    dw 4290                 ; Bb4  466.20 Hz
    db 1, 1
    dw 3608                 ; Db5  554.32 Hz
    db 1, 0
    dw 3822                 ; C5   523.29 Hz
    db 2, 2
    dw 5102                 ; G4   392.00 Hz
    db 1, 1
    dw 4290                 ; Bb4  466.20 Hz
    db 1, 1
    dw 3822                 ; C5   523.29 Hz
    db 2, 1
    dw 4290                 ; Bb4  466.20 Hz
    db 1, 1
    dw 5102                 ; G4   392.00 Hz
    db 5, 2
