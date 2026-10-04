; Standalone packed-PCM player for CP/M on an Intel 8080 Juku.
;
; The Juku D57 channel-1 mode-0 output is used as a pulse-width DAC.  Each
; source byte carries two unsigned 4-bit samples, high nibble first.  The hot
; loop takes 422 CPU cycles per pair in the current 8080 model, yielding an
; average 8,056.872 samples/s at the assumed 1.70 MHz effective CPU clock.

        org     00100h

PITDATA         equ     019h
PITCTL          equ     01bh

start:
        di
        mvi     a,050h                  ; D57 ch1, LSB-only, mode 0
        out     PITCTL
        mvi     a,1                     ; terminal count -> static-high silence
        out     PITDATA

        lxi     h,jukupoly_pcm_data
        lxi     b,jukupoly_pcm_end-jukupoly_pcm_data

; First and second delay blocks take 157 and 172 cycles.  Together with the
; remaining instructions, one packed byte takes exactly 422 cycles. JNZ takes
; ten cycles on both paths. Sample writes alternate 197/225 cycles apart.
sample_pair:
        mov     a,m
        ani     0f0h
        out     PITDATA
        mvi     d,10
delay_high:
        dcr     d
        jnz     delay_high
        mov     a,m
        rlc
        rlc
        rlc
        rlc
        ani     0f0h
        out     PITDATA
        mvi     d,11
delay_low:
        dcr     d
        jnz     delay_low
        inx     h
        dcx     b
        mov     a,b
        ora     c
        jnz     sample_pair

        mvi     a,050h
        out     PITCTL
        mvi     a,1
        out     PITDATA
        ei
        ret

        include "jukupoly-pcm-generated.inc"

        end     start
