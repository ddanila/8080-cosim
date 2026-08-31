; Three-voice pin-pulse demonstration for Juku, as a CP/M transient.
;
; Timeline:
;   0..2 s  A3             (220.00 Hz)
;   2..4 s  A3 + C#4       (277.18 Hz)
;   4..9 s  A3 + C#4 + E4  (329.63 Hz)
;
; The hot loop uses 16-bit phase accumulators stored in the immediate operands
; of LXI H.  BC, DE, and SP hold the three phase increments.  D57 channel 1 is
; configured as an LSB-only mode-0 one-shot: each OUT 19h starts one low pulse.
; The voice mask in A adds a small mix-dependent component to a 96 us drive
; bias, producing 100..124 us pulses.  The PIT returns SOUND high without a
; second CPU write.  This remains far gentler than the ROM tune's 50% square
; wave but is substantially louder than the original 4..28 us experiment.
;
; Phase increments are calibrated for the approximately 10.9 kHz hot-loop rate
; expected from CS00000/CS00024's measured ~1.70 MHz effective RAM execution.
; The first voice counts its own overflows, so the staged entrances remain near
; 2/4/9 seconds even when READY timing changes the sample rate slightly.

        org     00100h

PITDATA         equ     019h
PITCTL          equ     01bh

STEP_A3         equ     1303            ; approximately 220.0 Hz
STEP_CS4        equ     1648            ; approximately 277.2 Hz
STEP_E4         equ     1972            ; approximately 329.6 Hz

VOL_A3          equ     020h            ; 16 us at the 2 MHz PIT clock
VOL_CS4         equ     010h            ;  8 us
VOL_E4          equ     008h            ;  4 us
DRIVE_BIAS       equ     0c0h            ; add 96 us to every audible impulse

TWO_SECONDS     equ     440             ; counted A3 periods
FIVE_SECONDS    equ     1100

start:
        di
        lxi     h,0
        dad     sp
        shld    saved_sp

        mvi     a,050h                  ; D57 ch1, LSB-only, mode 0
        out     PITCTL
        mvi     a,1                     ; settle at static high / silence
        out     PITDATA

        lxi     b,STEP_A3
        lxi     d,0                     ; voice 2 enters at two seconds
        lxi     sp,0                    ; voice 3 enters at four seconds
        lxi     h,TWO_SECONDS
        shld    periods_left
        xra     a
        sta     stage

sample_loop:
        xra     a                       ; combined pulse width, also sets Z

phase_a3:
        lxi     h,0                     ; self-modifying phase accumulator
        dad     b
        shld    phase_a3+1
        jnc     phase_cs4

        ; Count time only on A3 overflows, rather than burdening every sample.
        lhld    periods_left
        dcx     h
        shld    periods_left
        mov     a,h
        ora     l
        jz      advance_stage
        mvi     a,VOL_A3

phase_cs4:
        lxi     h,0
        dad     d
        shld    phase_cs4+1
        jnc     phase_e4
        ori     VOL_CS4

phase_e4:
        lxi     h,0
        dad     sp
        shld    phase_e4+1
        jnc     emit
        ori     VOL_E4

emit:
        jz      sample_loop             ; no accumulator overflow this sample
        ori     DRIVE_BIAS               ; 100..124 us physical speaker pulse
        out     PITDATA                 ; hardware-timed pin pulse
        jmp     sample_loop

advance_stage:
        lda     stage
        inr     a
        sta     stage
        cpi     1
        jz      enable_cs4
        cpi     2
        jz      enable_e4
        jmp     finished

enable_cs4:
        lxi     d,STEP_CS4
        lxi     h,TWO_SECONDS
        shld    periods_left
        xra     a
        ori     VOL_A3                  ; retain the boundary A3 pulse
        jmp     phase_cs4

enable_e4:
        lxi     sp,STEP_E4
        lxi     h,FIVE_SECONDS
        shld    periods_left
        xra     a
        ori     VOL_A3
        jmp     phase_cs4

finished:
        mvi     a,050h
        out     PITCTL
        mvi     a,1
        out     PITDATA                 ; leave channel 1 silent

        lhld    saved_sp
        sphl
        ei
        ret

saved_sp:
        dw      0
periods_left:
        dw      0
stage:
        db      0

        end     start
