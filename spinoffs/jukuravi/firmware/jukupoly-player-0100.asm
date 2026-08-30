; JukuPoly compiled-pattern player for CP/M on an Intel 8080 Juku.
;
; Three tone channels remain active while an unpacked 4-bit percussion stream
; is mixed into the same mode-0 PIT impulse.  Track parsing, envelopes, and the
; optional channel-1 slide run once per approximately 20 ms frame; the hot loop
; performs only phase accumulation, one PCM fetch, pulse output, and an 8-bit
; frame-sample countdown.

        org     00100h

PITDATA         equ     019h
PITCTL          equ     01bh

FLAG_TONE1      equ     001h
FLAG_TONE2      equ     002h
FLAG_TONE3      equ     004h
FLAG_SLIDE      equ     008h
FLAG_DRUM       equ     010h
FLAG_END        equ     080h

ENV_ATTACK      equ     0
ENV_DECAY       equ     1

start:
        di
        lxi     h,0
        dad     sp
        shld    saved_sp

        mvi     a,050h                  ; D57 ch1, LSB-only, mode 0
        out     PITCTL
        mvi     a,1                     ; static high = silence
        out     PITDATA

        lxi     b,0
        lxi     d,0
        lxi     sp,0
        xra     a
        sta     env_counter
        sta     row_frames
        sta     drum_frames
        sta     ch1_volume
        sta     ch2_volume
        sta     ch3_volume
        lxi     h,jukupoly_song_rows
        shld    song_pointer
        jmp     frame_tick

; The hot path.  BC, DE, and SP hold tone increments; each LXI H immediate is
; its channel's self-modifying phase accumulator.  Channel volumes are 1..15.
sample_loop:
        xra     a

phase1:
        lxi     h,0
        dad     b
        shld    phase1+1
        jnc     phase2
volume1:
        ori     0

phase2:
        lxi     h,0
        dad     d
        shld    phase2+1
        jnc     phase3
volume2:
        ori     0

phase3:
        lxi     h,0
        dad     sp
        shld    phase3+1
        jnc     drum_mix
volume3:
        ori     0

drum_mix:
        lxi     h,jukupoly_silence      ; self-modifying unpacked PCM pointer
        ora     m                       ; QChan-style OR mix, still 0..15
        inx     h
        shld    drum_mix+1
        ora     a
        jz      no_pulse
        rlc                             ; nibble -> PIT count 10h..f0h
        rlc
        rlc
        rlc
        out     PITDATA                 ; 8..120 us hardware-timed impulse
no_pulse:
sample_count:
        mvi     a,JUKUPOLY_FRAME_SAMPLES
        dcr     a
        sta     sample_count+1
        jnz     sample_loop

; Every frame restores the real CP/M stack, updates slow state, parses a new
; row when needed, then lends SP back to channel 3.
frame_tick:
        mov     h,b
        mov     l,c
        shld    ch1_step
        mov     h,d
        mov     l,e
        shld    ch2_step
        lxi     h,0
        dad     sp
        shld    ch3_step
        lhld    saved_sp
        sphl

        call    advance_drum
        lda     env_counter
        inr     a
        sta     env_counter
        lxi     h,ch1_volume
        call    update_envelope
        lxi     h,ch2_volume
        call    update_envelope
        lxi     h,ch3_volume
        call    update_envelope
        call    update_slide

        lda     row_frames
        ora     a
        jz      parse_row
        dcr     a
        sta     row_frames
        jmp     prepare_frame

parse_row:
        lhld    song_pointer
        mov     c,m                     ; duration in frames
        inx     h
        mov     a,m                     ; variable-packet flags
        inx     h
        sta     row_flags
        ani     FLAG_END
        jnz     finished
        mov     a,c
        dcr     a                       ; current frame is duration frame 1
        sta     row_frames
        shld    song_cursor

        lda     row_flags
        ani     FLAG_TONE1
        jz      parsed_tone1
        call    parse_tone1
parsed_tone1:
        lda     row_flags
        ani     FLAG_TONE2
        cnz     parse_tone2
        lda     row_flags
        ani     FLAG_TONE3
        cnz     parse_tone3
        lda     row_flags
        ani     FLAG_SLIDE
        cnz     parse_slide
        lda     row_flags
        ani     FLAG_DRUM
        cnz     parse_drum
        lhld    song_cursor
        shld    song_pointer

prepare_frame:
        lda     ch1_volume
        sta     volume1+1
        lda     ch2_volume
        sta     volume2+1
        lda     ch3_volume
        sta     volume3+1

        lhld    ch1_step
        mov     b,h
        mov     c,l
        lhld    ch2_step
        xchg
        lhld    ch3_step
        sphl
        mvi     a,JUKUPOLY_FRAME_SAMPLES
        sta     sample_count+1
        jmp     sample_loop

; Tone packet: 15-bit step + legato bit, followed (unless step=0) by envelope
; mask and mode/target nibble.  Non-legato notes reset phase and envelope.
parse_tone1:
        lhld    song_cursor
        mov     e,m
        inx     h
        mov     d,m
        inx     h
        shld    song_cursor
        mov     a,d
        ani     080h
        sta     parse_legato
        mov     a,d
        ani     07fh
        mov     d,a
        ora     e
        jz      tone1_rest
        mov     h,d
        mov     l,e
        shld    ch1_step
        lhld    song_cursor
        mov     e,m
        inx     h
        mov     d,m
        inx     h
        shld    song_cursor
        mov     a,e
        sta     ch1_env_mask
        mov     a,d
        ani     00fh
        sta     ch1_target
        mov     a,d
        rrc
        rrc
        rrc
        rrc
        ani     003h
        sta     ch1_env_mode
        lda     parse_legato
        ora     a
        rnz
        lxi     h,0
        shld    phase1+1
        lda     ch1_env_mode
        ora     a
        jz      tone1_attack
        lda     ch1_target
        sta     ch1_volume
        ret
tone1_attack:
        xra     a
        sta     ch1_volume
        ret
tone1_rest:
        lxi     h,0
        shld    ch1_step
        shld    phase1+1
        xra     a
        sta     ch1_volume
        ret

parse_tone2:
        lhld    song_cursor
        mov     e,m
        inx     h
        mov     d,m
        inx     h
        shld    song_cursor
        mov     a,d
        ani     080h
        sta     parse_legato
        mov     a,d
        ani     07fh
        mov     d,a
        ora     e
        jz      tone2_rest
        mov     h,d
        mov     l,e
        shld    ch2_step
        lhld    song_cursor
        mov     e,m
        inx     h
        mov     d,m
        inx     h
        shld    song_cursor
        mov     a,e
        sta     ch2_env_mask
        mov     a,d
        ani     00fh
        sta     ch2_target
        mov     a,d
        rrc
        rrc
        rrc
        rrc
        ani     003h
        sta     ch2_env_mode
        lda     parse_legato
        ora     a
        rnz
        lxi     h,0
        shld    phase2+1
        lda     ch2_env_mode
        ora     a
        jz      tone2_attack
        lda     ch2_target
        sta     ch2_volume
        ret
tone2_attack:
        xra     a
        sta     ch2_volume
        ret
tone2_rest:
        lxi     h,0
        shld    ch2_step
        shld    phase2+1
        xra     a
        sta     ch2_volume
        ret

parse_tone3:
        lhld    song_cursor
        mov     e,m
        inx     h
        mov     d,m
        inx     h
        shld    song_cursor
        mov     a,d
        ani     080h
        sta     parse_legato
        mov     a,d
        ani     07fh
        mov     d,a
        ora     e
        jz      tone3_rest
        mov     h,d
        mov     l,e
        shld    ch3_step
        lhld    song_cursor
        mov     e,m
        inx     h
        mov     d,m
        inx     h
        shld    song_cursor
        mov     a,e
        sta     ch3_env_mask
        mov     a,d
        ani     00fh
        sta     ch3_target
        mov     a,d
        rrc
        rrc
        rrc
        rrc
        ani     003h
        sta     ch3_env_mode
        lda     parse_legato
        ora     a
        rnz
        lxi     h,0
        shld    phase3+1
        lda     ch3_env_mode
        ora     a
        jz      tone3_attack
        lda     ch3_target
        sta     ch3_volume
        ret
tone3_attack:
        xra     a
        sta     ch3_volume
        ret
tone3_rest:
        lxi     h,0
        shld    ch3_step
        shld    phase3+1
        xra     a
        sta     ch3_volume
        ret

parse_slide:
        lhld    song_cursor
        mov     e,m
        inx     h
        mov     d,m
        inx     h
        shld    song_cursor
        mov     h,d
        mov     l,e
        shld    slide_delta
        ret

; A percussion packet points to a compiled descriptor: PCM pointer, then frame
; count.  A new hit may replace a still-playing tail.
parse_drum:
        lhld    song_cursor
        mov     e,m
        inx     h
        mov     d,m
        inx     h
        shld    song_cursor
        xchg
        mov     e,m
        inx     h
        mov     d,m
        inx     h
        mov     a,m
        sta     drum_frames
        mov     h,d
        mov     l,e
        shld    drum_mix+1
        ret

advance_drum:
        lda     drum_frames
        ora     a
        jz      drum_silence
        dcr     a
        sta     drum_frames
        rnz
drum_silence:
        lxi     h,jukupoly_silence
        shld    drum_mix+1
        ret

update_slide:
        lhld    ch1_step
        mov     a,h
        ora     l
        rz
        xchg
        lhld    slide_delta
        dad     d
        shld    ch1_step
        ret

; HL addresses {current,target,mask,mode}.  Speed masks are 1,3,...255, so an
; envelope step occurs whenever env_counter AND mask is zero.
update_envelope:
        push    h
        inx     h
        inx     h
        lda     env_counter
        ana     m
        pop     h
        rnz
        mov     a,m
        inx     h
        mov     b,m                     ; target
        inx     h
        inx     h
        mov     c,m                     ; mode
        dcx     h
        dcx     h
        dcx     h
        mov     a,c
        ora     a
        jz      envelope_attack
        dcr     a
        jz      envelope_decay
        ret                             ; hold
envelope_attack:
        mov     a,m
        cmp     b
        rnc
        inr     m
        ret
envelope_decay:
        mov     a,m
        ora     a
        rz
        dcr     m
        ret

finished:
        mvi     a,050h
        out     PITCTL
        mvi     a,1
        out     PITDATA
        lhld    saved_sp
        sphl
        ei
        ret

saved_sp:
        dw      0
song_pointer:
        dw      0
song_cursor:
        dw      0
row_frames:
        db      0
row_flags:
        db      0
env_counter:
        db      0
parse_legato:
        db      0
drum_frames:
        db      0
slide_delta:
        dw      0

; Channel layout is deliberately {volume,target,mask,mode,step word}; the first
; four bytes are consumed by update_envelope.
ch1_volume:
        db      0
ch1_target:
        db      0
ch1_env_mask:
        db      1
ch1_env_mode:
        db      2
ch1_step:
        dw      0
ch2_volume:
        db      0
ch2_target:
        db      0
ch2_env_mask:
        db      1
ch2_env_mode:
        db      2
ch2_step:
        dw      0
ch3_volume:
        db      0
ch3_target:
        db      0
ch3_env_mask:
        db      1
ch3_env_mode:
        db      2
ch3_step:
        dw      0

; The test locates this table by its magic rather than depending on a listing.
test_manifest:
        db      'J','P','O','L',1
        dw      sample_loop
        dw      frame_tick
        dw      phase1+1
        dw      phase2+1
        dw      phase3+1
        dw      drum_mix+1
        dw      drum_frames
        dw      ch1_volume
        dw      ch2_volume
        dw      ch3_volume
        dw      slide_delta
        dw      row_frames
        dw      jukupoly_song_rows

        include "jukupoly-song-generated.inc"

        end     start
