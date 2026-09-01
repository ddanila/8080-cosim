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

        if      @@2
KEYCOLPORT      equ     004h
KEYROWPORT      equ     005h
SONG_LOAD       equ     01800h
SONG_ROWS       equ     SONG_LOAD+10
SONG_SILENCE    equ     SONG_LOAD+12
JUKUPOLY_FRAME_SAMPLES equ 143
        endif

FLAG_TONE1      equ     001h
FLAG_TONE2      equ     002h
FLAG_TONE3      equ     004h
FLAG_SLIDE      equ     008h
FLAG_DRUM       equ     010h
FLAG_FX         equ     020h
FLAG_PATTERN     equ     040h
FLAG_END        equ     080h

ENV_ATTACK      equ     0
ENV_DECAY       equ     1

start:
        if      @@2
        jmp     library_start
        endif
player_start:
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
        if      @@1
        else
        lxi     sp,0
        endif
        xra     a
        sta     env_counter
        sta     row_frames
        sta     drum_frames
        sta     ch1_volume
        sta     ch2_volume
        sta     ch3_volume
        if      @@3
        call    envelope_dispatch_init
        endif
        if      @@2
        sta     player_aborted
        endif
        if      @@1
        sta     ch1_volume_delta
        sta     ch2_volume_delta
        sta     ch3_volume_delta
        lxi     h,0
        shld    ch1_pitch_delta
        shld    ch2_pitch_delta
        shld    ch3_pitch_delta
        shld    ch1_porta_target
        shld    ch2_porta_target
        shld    ch3_porta_target
        shld    ch1_porta_rate
        shld    ch2_porta_rate
        shld    ch3_porta_rate
        endif
        if      @@1
        lxi     h,jukupoly_song_order
        shld    order_pointer
        call    advance_pattern
        lxi     d,0                     ; loader used DE before first frame
        else
        if      @@2
        lhld    SONG_ROWS
        else
        lxi     h,jukupoly_song_rows
        endif
        shld    song_pointer
        endif
        if      @@2
        lhld    SONG_SILENCE
        shld    silence_pointer
        shld    drum_mix+1
        endif
        if      @@1
        lxi     sp,0
        endif
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
        if      @@2
        lxi     h,SONG_LOAD             ; patched from the loaded JPS header
        else
        lxi     h,jukupoly_silence      ; self-modifying unpacked PCM pointer
        endif
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
frame_tick_base_saved:
        lhld    saved_sp
        sphl

        if      @@2
        ; Escape is column 3, encoder input 4 (raw low nibble 06h).  Poll only
        ; this contact at the existing frame boundary: 48 cycles when idle,
        ; no BIOS/N4 transaction, and no change to the audio-sample hot loop.
        mvi     a,3
        out     KEYCOLPORT
        in      KEYROWPORT
        ani     00fh
        cpi     006h
        jz      playback_aborted
        endif

        call    advance_drum
        lda     env_counter
        inr     a
        sta     env_counter
        lxi     h,ch1_volume
update_envelope1_call:
        call    update_envelope
        lxi     h,ch2_volume
update_envelope2_call:
        call    update_envelope
        lxi     h,ch3_volume
update_envelope3_call:
        call    update_envelope
        call    update_slide

        lda     row_frames
        ora     a
        jz      parse_row
        if      @@1
        call    update_mod_effects
        lda     row_frames
        endif
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
        if      @@1
        lda     row_flags
        ani     FLAG_PATTERN
        jnz     parse_pattern_end
        endif
        mov     a,c
        dcr     a                       ; current frame is duration frame 1
        sta     row_frames
        shld    song_cursor

        lda     row_flags
        ani     FLAG_TONE1
        jz      parsed_tone1
parse_tone1_call:
        call    parse_tone1
parsed_tone1:
        lda     row_flags
        ani     FLAG_TONE2
parse_tone2_call:
        cnz     parse_tone2
        lda     row_flags
        ani     FLAG_TONE3
parse_tone3_call:
        cnz     parse_tone3
        lda     row_flags
        ani     FLAG_SLIDE
        cnz     parse_slide
        lda     row_flags
        ani     FLAG_DRUM
        cnz     parse_drum
        if      @@1
        lda     row_flags
        ani     FLAG_FX
        cnz     parse_fx
        endif
        lhld    song_cursor
        shld    song_pointer

        if      @@1
        jmp     prepare_frame
parse_pattern_end:
        call    advance_pattern
        jc      finished
        jmp     parse_row

advance_pattern:
        lhld    order_pointer
        mov     e,m
        inx     h
        mov     d,m
        inx     h
        shld    order_pointer
        mov     a,d
        ora     e
        jz      pattern_order_end
        mov     h,d
        mov     l,e
        shld    song_pointer
        ora     a                       ; clear carry
        ret
pattern_order_end:
        stc
        ret
        endif

prepare_frame:
        lda     ch1_volume
        sta     volume1+1
        lda     ch2_volume
        sta     volume2+1
        lda     ch3_volume
        sta     volume3+1

prepare_frame_steps:
        lhld    ch1_step
        mov     b,h
        mov     c,l
        lhld    ch2_step
        xchg
        lhld    ch3_step
        sphl
prepare_frame_count:
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
        if      @@1
        jz      tone1_retrigger
        lda     ch1_env_mode
        cpi     3
        rnz
        lda     ch1_target
        sta     ch1_volume
        ret
tone1_retrigger:
        else
        rnz
        endif
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
        if      @@1
        jz      tone2_retrigger
        lda     ch2_env_mode
        cpi     3
        rnz
        lda     ch2_target
        sta     ch2_volume
        ret
tone2_retrigger:
        else
        rnz
        endif
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
        if      @@1
        jz      tone3_retrigger
        lda     ch3_env_mode
        cpi     3
        rnz
        lda     ch3_target
        sta     ch3_volume
        ret
tone3_retrigger:
        else
        rnz
        endif
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
        if      @@2
        lhld    silence_pointer
        else
        lxi     h,jukupoly_silence
        endif
        shld    drum_mix+1
        ret

        if      @@1
; Optional ABI-v2 tracker effects.  The packet begins with four channel masks:
; absolute volume, signed volume delta, signed phase-step delta, and target
; portamento.  Payloads then follow in channel order.  Effect state persists
; until a later packet explicitly replaces it; the MOD importer emits stops at
; every row boundary where an effect ceases.
parse_fx:
        lhld    song_cursor
        mov     a,m
        sta     fx_vset_mask
        inx     h
        mov     a,m
        sta     fx_vslide_mask
        inx     h
        mov     a,m
        sta     fx_pslide_mask
        inx     h
        mov     a,m
        sta     fx_porta_mask
        inx     h
        shld    song_cursor

        lda     fx_vset_mask
        ani     1
        jz      fx_vset2
        call    fx_read_byte
        sta     ch1_volume
fx_vset2:
        lda     fx_vset_mask
        ani     2
        jz      fx_vset3
        call    fx_read_byte
        sta     ch2_volume
fx_vset3:
        lda     fx_vset_mask
        ani     4
        jz      fx_vslide1
        call    fx_read_byte
        sta     ch3_volume

fx_vslide1:
        lda     fx_vslide_mask
        ani     1
        jz      fx_vslide2
        call    fx_read_byte
        sta     ch1_volume_delta
fx_vslide2:
        lda     fx_vslide_mask
        ani     2
        jz      fx_vslide3
        call    fx_read_byte
        sta     ch2_volume_delta
fx_vslide3:
        lda     fx_vslide_mask
        ani     4
        jz      fx_pslide1
        call    fx_read_byte
        sta     ch3_volume_delta

fx_pslide1:
        lda     fx_pslide_mask
        ani     1
        jz      fx_pslide2
        call    fx_read_word
        xchg
        shld    ch1_pitch_delta
        lxi     h,0
        shld    ch1_porta_target
fx_pslide2:
        lda     fx_pslide_mask
        ani     2
        jz      fx_pslide3
        call    fx_read_word
        xchg
        shld    ch2_pitch_delta
        lxi     h,0
        shld    ch2_porta_target
fx_pslide3:
        lda     fx_pslide_mask
        ani     4
        jz      fx_porta1
        call    fx_read_word
        xchg
        shld    ch3_pitch_delta
        lxi     h,0
        shld    ch3_porta_target

fx_porta1:
        lda     fx_porta_mask
        ani     1
        jz      fx_porta2
        call    fx_read_word
        xchg
        shld    ch1_porta_target
        call    fx_read_word
        xchg
        shld    ch1_porta_rate
        lxi     h,0
        shld    ch1_pitch_delta
fx_porta2:
        lda     fx_porta_mask
        ani     2
        jz      fx_porta3
        call    fx_read_word
        xchg
        shld    ch2_porta_target
        call    fx_read_word
        xchg
        shld    ch2_porta_rate
        lxi     h,0
        shld    ch2_pitch_delta
fx_porta3:
        lda     fx_porta_mask
        ani     4
        rz
        call    fx_read_word
        xchg
        shld    ch3_porta_target
        call    fx_read_word
        xchg
        shld    ch3_porta_rate
        lxi     h,0
        shld    ch3_pitch_delta
        ret

fx_read_byte:
        lhld    song_cursor
        mov     a,m
        inx     h
        shld    song_cursor
        ret

; Return the little-endian word in DE.
fx_read_word:
        lhld    song_cursor
        mov     e,m
        inx     h
        mov     d,m
        inx     h
        shld    song_cursor
        ret

update_mod_effects:
        lxi     h,ch1_volume
        lda     ch1_volume_delta
        call    apply_volume_delta
        lxi     h,ch2_volume
        lda     ch2_volume_delta
        call    apply_volume_delta
        lxi     h,ch3_volume
        lda     ch3_volume_delta
        call    apply_volume_delta
        call    update_pitch1
        call    update_pitch2
        call    update_pitch3
        ret

; HL points to a 0..15 current volume and A is a signed per-frame delta.
apply_volume_delta:
        ora     a
        rz
        mov     b,a
        jm      volume_delta_down
        mov     a,m
        add     b
        cpi     010h
        jc      volume_delta_store
        mvi     a,00fh
volume_delta_store:
        mov     m,a
        ret
volume_delta_down:
        mov     a,m
        add     b
        jc      volume_delta_store
        xra     a
        mov     m,a
        ret

update_pitch1:
        lhld    ch1_porta_target
        mov     b,h
        mov     c,l
        lhld    ch1_porta_rate
        shld    pitch_rate_arg
        lhld    ch1_pitch_delta
        xchg
        lhld    ch1_step
        call    apply_pitch_effect
        shld    ch1_step
        ora     a
        rz
        lxi     h,0
        shld    ch1_porta_target
        shld    ch1_porta_rate
        ret
update_pitch2:
        lhld    ch2_porta_target
        mov     b,h
        mov     c,l
        lhld    ch2_porta_rate
        shld    pitch_rate_arg
        lhld    ch2_pitch_delta
        xchg
        lhld    ch2_step
        call    apply_pitch_effect
        shld    ch2_step
        ora     a
        rz
        lxi     h,0
        shld    ch2_porta_target
        shld    ch2_porta_rate
        ret
update_pitch3:
        lhld    ch3_porta_target
        mov     b,h
        mov     c,l
        lhld    ch3_porta_rate
        shld    pitch_rate_arg
        lhld    ch3_pitch_delta
        xchg
        lhld    ch3_step
        call    apply_pitch_effect
        shld    ch3_step
        ora     a
        rz
        lxi     h,0
        shld    ch3_porta_target
        shld    ch3_porta_rate
        ret

; HL=current step, DE=signed free-slide delta, BC=portamento target.  A=1 on
; target arrival so the caller can stop the portamento, otherwise A=0.
apply_pitch_effect:
        mov     a,b
        ora     c
        jnz     pitch_has_target
        dad     d
        xra     a
        ret
pitch_has_target:
        mov     a,h
        cmp     b
        jc      pitch_below_target
        jnz     pitch_above_target
        mov     a,l
        cmp     c
        jc      pitch_below_target
        jz      pitch_reached
pitch_above_target:
        xchg
        lhld    pitch_rate_arg
        xchg
        mov     a,l
        sub     e
        mov     l,a
        mov     a,h
        sbb     d
        mov     h,a
        mov     a,h
        cmp     b
        jc      pitch_reached
        jnz     pitch_not_reached
        mov     a,l
        cmp     c
        jc      pitch_reached
        jmp     pitch_not_reached
pitch_below_target:
        xchg
        lhld    pitch_rate_arg
        xchg
        dad     d
        mov     a,h
        cmp     b
        jc      pitch_not_reached
        jnz     pitch_reached
        mov     a,l
        cmp     c
        jnc     pitch_reached
pitch_not_reached:
        xra     a
        ret
pitch_reached:
        mov     h,b
        mov     l,c
        mvi     a,1
        ret
        endif

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

        if      @@4
        include "jukupoly-envelope-v2.inc"
        endif

        if      @@2
playback_aborted:
        mvi     a,1
        sta     player_aborted
        endif
finished:
        mvi     a,050h
        out     PITCTL
        mvi     a,1
        out     PITDATA
        if      @@2
        lda     player_aborted
        ora     a
        jz      playback_return
playback_wait_escape_release:
        mvi     a,3
        out     KEYCOLPORT
        in      KEYROWPORT
        ani     00fh
        cpi     006h
        jz      playback_wait_escape_release
playback_return:
        endif
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
        if      @@1
order_pointer:
        dw      0
        endif
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
        if      @@2
silence_pointer:
        dw      SONG_LOAD
player_aborted:
        db      0
        endif

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
        if      @@4
ch1_env2_sustain:
        db      0
ch1_env2_decay_mask:
        db      0
ch1_env2_release_mask:
        db      0
ch1_env2_stage:
        db      0
ch1_env2_flags:
        db      0
        if      @@6
ch1_vibrato_delta:
        db      0
        endif
        endif
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
        if      @@4
ch2_env2_sustain:
        db      0
ch2_env2_decay_mask:
        db      0
ch2_env2_release_mask:
        db      0
ch2_env2_stage:
        db      0
ch2_env2_flags:
        db      0
        if      @@6
ch2_vibrato_delta:
        db      0
        endif
        endif
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
        if      @@4
ch3_env2_sustain:
        db      0
ch3_env2_decay_mask:
        db      0
ch3_env2_release_mask:
        db      0
ch3_env2_stage:
        db      0
ch3_env2_flags:
        db      0
        if      @@6
ch3_vibrato_delta:
        db      0
        endif
        endif

        if      @@5
; Shared M4 phase; per-channel table-page offsets live in ENV2_FLAGS bits 4-5.
tremolo_phase:
        dw      0
        endif

        if      @@6
; Shared M5 phase.  The parser-only checkpoint records it but does not yet
; advance or apply it; runtime qualification is a separate guarded slice.
vibrato_phase:
        dw      0
        endif

        if      @@1
fx_vset_mask:
        db      0
fx_vslide_mask:
        db      0
fx_pslide_mask:
        db      0
fx_porta_mask:
        db      0
ch1_volume_delta:
        db      0
ch2_volume_delta:
        db      0
ch3_volume_delta:
        db      0
ch1_pitch_delta:
        dw      0
ch2_pitch_delta:
        dw      0
ch3_pitch_delta:
        dw      0
ch1_porta_target:
        dw      0
ch2_porta_target:
        dw      0
ch3_porta_target:
        dw      0
ch1_porta_rate:
        dw      0
ch2_porta_rate:
        dw      0
ch3_porta_rate:
        dw      0
pitch_rate_arg:
        dw      0
        endif

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
        if      @@2
        dw      SONG_LOAD
        else
        dw      jukupoly_song_rows
        endif
        if      @@1
        dw      ch1_volume_delta
        dw      ch2_volume_delta
        dw      ch3_volume_delta
        dw      ch1_pitch_delta
        dw      ch2_pitch_delta
        dw      ch3_pitch_delta
        dw      ch1_porta_target
        dw      ch2_porta_target
        dw      ch3_porta_target
        endif
        if      @@4
        dw      ch1_target
        dw      ch1_env_mask
        dw      ch1_step
        dw      ch1_env2_sustain
        dw      ch1_env2_decay_mask
        dw      ch1_env2_release_mask
        dw      ch1_env2_stage
        dw      ch1_env2_flags
        dw      ch2_step
        dw      ch2_env2_stage
        dw      ch3_step
        dw      ch3_env2_stage
        endif

        if      @@5
tremolo_test_manifest:
        db      'J','T','R','E',1
        dw      sample_loop
        dw      frame_tick
        dw      volume1+1
        dw      volume2+1
        dw      volume3+1
        dw      ch1_volume
        dw      ch2_volume
        dw      ch3_volume
        dw      ch1_env2_flags
        dw      ch2_env2_flags
        dw      ch3_env2_flags
        dw      tremolo_phase
        dw      prepare_frame
        endif

        if      @@6
vibrato_parser_test_manifest:
        db      'J','V','P','R',1
        dw      ch1_step
        dw      ch2_step
        dw      ch3_step
        dw      ch1_env2_flags
        dw      ch2_env2_flags
        dw      ch3_env2_flags
        dw      ch1_vibrato_delta
        dw      ch2_vibrato_delta
        dw      ch3_vibrato_delta
        dw      vibrato_phase
        dw      sample_loop
        dw      frame_tick
        dw      env2_invalid_packet
        dw      song_pointer
        dw      song_cursor
        if      @@2
        dw      library_bad_song
        dw      verified_cursor
        dw      verified_tone_flags
        dw      verified_tone_step
        dw      verified_song_end
        endif

        if      @@7
vibrato_runtime_test_manifest:
        db      'J','V','I','B',1
        dw      ch1_step
        dw      ch2_step
        dw      ch3_step
        dw      ch1_env2_flags
        dw      ch2_env2_flags
        dw      ch3_env2_flags
        dw      ch1_vibrato_delta
        dw      ch2_vibrato_delta
        dw      ch3_vibrato_delta
        dw      vibrato_phase
        dw      sample_loop
        dw      frame_tick
        dw      prepare_frame
        endif
        endif

        if      @@2
        include "jukupoly-library-shell.inc"
        else
        include "jukupoly-song-generated.inc"
        endif

        end     start
