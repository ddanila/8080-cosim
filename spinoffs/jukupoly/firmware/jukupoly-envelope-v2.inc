; JPS v2 fitted ADSR envelope routines.  Included only in the separately
; qualified -P4=1 player; JPS v1 dispatch continues to call the original
; parser/updater directly.

ENV2_SUSTAIN    equ     6
ENV2_DECAY_MASK equ     7
ENV2_RELEASE_MASK equ   8
ENV2_STAGE      equ     9
ENV2_FLAGS      equ     10
ENV2_VIBRATO_DELTA equ  11

ENV2_OFF        equ     0
ENV2_ATTACK     equ     1
ENV2_DECAY      equ     2
ENV2_HOLD       equ     3
ENV2_RELEASE    equ     4

ENV2_ATTACK_IMMEDIATE equ 1
ENV2_DECAY_IMMEDIATE equ  2
ENV2_RELEASE_IMMEDIATE equ 4
ENV2_KEY_SUSTAIN equ       8

; Run outside the timing-critical player prefix.  The library shell calls this
; after verifying/loading each song, which preserves the frozen hot-loop
; address and bytes in the enhanced -P2=1 -P4=1 build.  Standalone -P3=1 calls
; it from player_start.
envelope_dispatch_init:
        xra     a
        sta     ch1_env2_stage
        sta     ch2_env2_stage
        sta     ch3_env2_stage
        if      @@5
        sta     tremolo_phase
        sta     tremolo_phase+1
        mvi     a,03ah                  ; restore LDA ch1_volume
        sta     prepare_frame
        lxi     h,ch1_volume
        shld    prepare_frame+1
        mvi     a,0fch                  ; capability 01h reserved-bit mask
        sta     env2_reserved_mask+1
        mvi     a,03ah                  ; restore LDA env2_work_flags
        sta     env2_load_work_flags
        lxi     h,env2_work_flags
        shld    env2_load_work_flags+1
        endif
        if      @@6
        xra     a
        sta     vibrato_phase
        sta     vibrato_phase+1
        sta     ch1_vibrato_delta
        sta     ch2_vibrato_delta
        sta     ch3_vibrato_delta
        mvi     a,0fch                  ; restore capability 01h parser mask
        sta     env2_reserved_mask+1
        mvi     a,03ah                  ; restore LDA env2_work_flags
        sta     env2_load_work_flags
        lxi     h,env2_work_flags
        shld    env2_load_work_flags+1
        endif
        lxi     h,parse_tone1
        shld    parse_tone1_call+1
        lxi     h,parse_tone2
        shld    parse_tone2_call+1
        lxi     h,parse_tone3
        shld    parse_tone3_call+1
        lxi     h,update_envelope
        shld    update_envelope1_call+1
        shld    update_envelope2_call+1
        shld    update_envelope3_call+1
        mvi     a,JUKUPOLY_FRAME_SAMPLES
        sta     sample_count+1
        sta     prepare_frame_count+1
        if      @@2
        lda     SONG_LOAD+3
        cpi     2
        rnz
        lda     SONG_LOAD+6
        sta     sample_count+1
        sta     prepare_frame_count+1
        endif
        lxi     h,parse_tone1_v2
        shld    parse_tone1_call+1
        lxi     h,parse_tone2_v2
        shld    parse_tone2_call+1
        lxi     h,parse_tone3_v2
        shld    parse_tone3_call+1
        lxi     h,update_envelope_v2
        shld    update_envelope1_call+1
        shld    update_envelope2_call+1
        shld    update_envelope3_call+1
        if      @@5
        if      @@2
        lda     SONG_LOAD+7
        if      @@6
        ani     2
        jz      env2_no_tremolo_init
        else
        cpi     3
        rnz
        endif
        endif
        mvi     a,0f0h                  ; bits 2-3 are depth under cap 03h
        sta     env2_reserved_mask+1
        mvi     a,0cdh                  ; CALL depth-aware flag loader
        sta     env2_load_work_flags
        lxi     h,env2_load_tremolo_flags
        shld    env2_load_work_flags+1
        mvi     a,0c3h                  ; patch to JMP prepare_frame_tremolo
        sta     prepare_frame
        lxi     h,prepare_frame_tremolo
        shld    prepare_frame+1
env2_no_tremolo_init:
        endif
        if      @@6
        if      @@2
        lda     SONG_LOAD+7
        ani     4
        jz      env2_no_vibrato_init
        endif
        lxi     h,parse_tone1_v2_pitch
        shld    parse_tone1_call+1
        lxi     h,parse_tone2_v2_pitch
        shld    parse_tone2_call+1
        lxi     h,parse_tone3_v2_pitch
        shld    parse_tone3_call+1
        lxi     h,update_envelope_v2_pitch
        shld    update_envelope1_call+1
        shld    update_envelope2_call+1
        shld    update_envelope3_call+1
        if      @@2
        if      @@5
        lda     SONG_LOAD+7
        ani     2
        jz      env2_pitch_without_tremolo
        mvi     a,0c0h                  ; combined: only bits 6-7 reserved
        sta     env2_pitch_reserved_mask+1
        lxi     h,env2_load_combined_flags
        jmp     env2_store_pitch_loader
env2_pitch_without_tremolo:
        endif
        endif
        mvi     a,0cch                  ; cap 05h: tremolo and reserved bits
        sta     env2_pitch_reserved_mask+1
        lxi     h,env2_load_pitch_flags
env2_store_pitch_loader:
        mvi     a,0cdh                  ; CALL feature-aware flag loader
        sta     env2_load_work_flags
        shld    env2_load_work_flags+1
env2_no_vibrato_init:
        endif
        ret

parse_tone1_v2:
        lxi     h,ch1_volume
        shld    env2_channel_pointer
        lxi     h,phase1+1
        shld    env2_phase_pointer
        jmp     parse_tone_v2

parse_tone2_v2:
        lxi     h,ch2_volume
        shld    env2_channel_pointer
        lxi     h,phase2+1
        shld    env2_phase_pointer
        jmp     parse_tone_v2

parse_tone3_v2:
        lxi     h,ch3_volume
        shld    env2_channel_pointer
        lxi     h,phase3+1
        shld    env2_phase_pointer

parse_tone_v2:
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
        jz      env2_key_off_current
        xchg
        shld    env2_step_word

        ; Store the unmodulated phase step at the existing channel offset 4.
        lhld    env2_channel_pointer
        lxi     d,4
        dad     d
        xchg
        lhld    env2_step_word
        mov     a,l
        stax    d
        inx     d
        mov     a,h
        stax    d

        ; Read the compact peak/sustain and three rate codes.
        lhld    song_cursor
        mov     a,m
        sta     env2_levels
        inx     h
        mov     a,m
        sta     env2_rates
        inx     h
        mov     a,m
        sta     env2_packet_flags
        inx     h
        shld    song_cursor

        ; Reserved packet bits are a bounded runtime guard.  A malformed song
        ; stops instead of desynchronizing the variable row stream.
        lda     env2_packet_flags
env2_reserved_mask:
        ani     0fch
        jnz     env2_invalid_packet

env2_packet_valid:

        ; Peak becomes the current-stage target; sustain is persistent state.
        lda     env2_levels
        rrc
        rrc
        rrc
        rrc
        ani     00fh
        mvi     c,1
        call    env2_store_offset
        lda     env2_levels
        ani     00fh
        mvi     c,ENV2_SUSTAIN
        call    env2_store_offset

        ; Convert rate code 0 to an immediate flag and codes 1..7 to the
        ; existing power-of-two frame masks 0,1,3,...63.
        xra     a
        sta     env2_work_flags
        lda     env2_packet_flags
        ani     2
        rlc
        rlc
        ora     a
        jz      env2_no_key_sustain
        lda     env2_work_flags
        ori     ENV2_KEY_SUSTAIN
        sta     env2_work_flags
env2_no_key_sustain:
        lda     env2_rates
        ani     7
        call    env2_decode_rate
        sta     env2_rate_mask_temp
        jnc     env2_attack_not_immediate
        lda     env2_work_flags
        ori     ENV2_ATTACK_IMMEDIATE
        sta     env2_work_flags
env2_attack_not_immediate:
        lda     env2_rate_mask_temp
        mvi     c,2
        call    env2_store_offset

        lda     env2_rates
        rrc
        rrc
        rrc
        ani     7
        call    env2_decode_rate
        sta     env2_rate_mask_temp
        jnc     env2_decay_not_immediate
        lda     env2_work_flags
        ori     ENV2_DECAY_IMMEDIATE
        sta     env2_work_flags
env2_decay_not_immediate:
        lda     env2_rate_mask_temp
        mvi     c,ENV2_DECAY_MASK
        call    env2_store_offset

        lda     env2_rates
        rlc
        rlc
        ani     3
        mov     b,a
        lda     env2_packet_flags
        ani     1
        rlc
        rlc
        ora     b
        call    env2_decode_rate
        sta     env2_rate_mask_temp
        jnc     env2_release_not_immediate
        lda     env2_work_flags
        ori     ENV2_RELEASE_IMMEDIATE
        sta     env2_work_flags
env2_release_not_immediate:
        lda     env2_rate_mask_temp
        mvi     c,ENV2_RELEASE_MASK
        call    env2_store_offset
env2_load_work_flags:
        lda     env2_work_flags
        mvi     c,ENV2_FLAGS
        call    env2_store_offset

        lhld    env2_channel_pointer
        lda     parse_legato
        ora     a
        jnz     env2_refresh_legato
        xra     a
        mov     m,a                     ; retrigger from silence
        push    h
        lxi     d,ENV2_STAGE
        dad     d
        mvi     m,ENV2_ATTACK
        pop     h
        lhld    env2_phase_pointer
        mvi     m,0
        inx     h
        mvi     m,0
        lhld    env2_channel_pointer
        push    h
        lxi     d,ENV2_FLAGS
        dad     d
        mov     a,m
        pop     h
        ani     ENV2_ATTACK_IMMEDIATE
        rz
        inx     h                       ; target peak
        mov     a,m
        dcx     h
        mov     m,a
        jmp     env2_enter_decay

env2_refresh_legato:
        push    h
        lxi     d,ENV2_STAGE
        dad     d
        mov     a,m
        pop     h
        cpi     ENV2_DECAY
        jz      env2_set_decay_fields
        cpi     ENV2_HOLD
        jz      env2_set_sustain_target
        cpi     ENV2_RELEASE
        jz      env2_set_release_fields
        ret                             ; off or attack already has new fields

env2_key_off_current:
        lhld    env2_channel_pointer
        jmp     env2_enter_release

        if      @@6
; Capability-bit-2 parser.  It deliberately has a separate entry path, so
; capability 01h/03h songs retain the already-qualified parser instruction
; stream.  The envelope body after validation remains shared.
parse_tone1_v2_pitch:
        lxi     h,ch1_volume
        shld    env2_channel_pointer
        lxi     h,phase1+1
        shld    env2_phase_pointer
        jmp     parse_tone_v2_pitch

parse_tone2_v2_pitch:
        lxi     h,ch2_volume
        shld    env2_channel_pointer
        lxi     h,phase2+1
        shld    env2_phase_pointer
        jmp     parse_tone_v2_pitch

parse_tone3_v2_pitch:
        lxi     h,ch3_volume
        shld    env2_channel_pointer
        lxi     h,phase3+1
        shld    env2_phase_pointer

parse_tone_v2_pitch:
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
        jz      env2_key_off_current_pitch
        xchg
        shld    env2_step_word

        lhld    env2_channel_pointer
        lxi     d,4
        dad     d
        xchg
        lhld    env2_step_word
        mov     a,l
        stax    d
        inx     d
        mov     a,h
        stax    d

        lhld    song_cursor
        mov     a,m
        sta     env2_levels
        inx     h
        mov     a,m
        sta     env2_rates
        inx     h
        mov     a,m
        sta     env2_packet_flags
        inx     h
        shld    song_cursor

        lda     env2_packet_flags
env2_pitch_reserved_mask:
        ani     0cch
        jnz     env2_invalid_packet
        lda     env2_packet_flags
        ani     030h
        cpi     030h                    ; mode 3 is always invalid
        jz      env2_invalid_packet
        ora     a
        jz      env2_pitch_disabled
        lhld    song_cursor
        mov     a,m                    ; serialized peak delta minus one
        inx     h
        shld    song_cursor
        mvi     c,ENV2_VIBRATO_DELTA
        call    env2_store_offset
        jmp     env2_packet_valid
env2_pitch_disabled:
        xra     a
        mvi     c,ENV2_VIBRATO_DELTA
        call    env2_store_offset
        jmp     env2_packet_valid

env2_key_off_current_pitch:
        lhld    env2_channel_pointer
        call    env2_enter_release
        jmp     env2_clear_finished_pitch
        endif

env2_invalid_packet:
        if      @@2
        jmp     playback_aborted
        else
        jmp     finished
        endif

; A=rate code.  Return A=frame mask and carry set only for immediate code 0.
env2_decode_rate:
        ora     a
        jnz     env2_rate_from_table
        stc
        ret
env2_rate_from_table:
        dcr     a
        push    d
        mov     e,a
        mvi     d,0
        lxi     h,env2_rate_masks
        dad     d
        mov     a,m
        pop     d
        ora     a                       ; clear carry
        ret
env2_rate_masks:
        db      0,1,3,7,15,31,63

; Store A at current enhanced channel base + C.  Preserve all caller registers.
env2_store_offset:
        push    b
        push    d
        push    h
        mov     e,c
        mvi     d,0
        lhld    env2_channel_pointer
        dad     d
        mov     m,a
        pop     h
        pop     d
        pop     b
        ret

; HL addresses the existing channel volume byte.
update_envelope_v2:
        push    h
        inx     h
        inx     h                       ; current stage rate mask
        lda     env_counter
        ana     m
        pop     h
        rnz
        push    h
        lxi     d,ENV2_STAGE
        dad     d
        mov     a,m
        pop     h
        cpi     ENV2_ATTACK
        jz      env2_update_attack
        cpi     ENV2_DECAY
        jz      env2_update_decay
        cpi     ENV2_RELEASE
        jz      env2_update_release
        ret                             ; off or keyed sustain

        if      @@6
; Capability 01h/03h keeps update_envelope_v2 byte- and cycle-identical.
; Pitch songs use this wrapper so stale mode/delta state is cleared as soon as
; a release (including an immediate key-off) has zeroed the immutable base.
update_envelope_v2_pitch:
        call    update_envelope_v2
env2_clear_finished_pitch:
        push    h
        lxi     d,4
        dad     d
        mov     a,m
        inx     h
        ora     m
        pop     h
        rnz
        push    h
        lxi     d,ENV2_FLAGS
        dad     d
        mvi     m,0
        inx     h
        mvi     m,0
        pop     h
        ret
        endif

env2_update_attack:
        mov     a,m
        inx     h
        cmp     m
        dcx     h
        jnc     env2_enter_decay
        inr     m
        mov     a,m
        inx     h
        cmp     m
        dcx     h
        rc
        jmp     env2_enter_decay

env2_update_decay:
        mov     a,m
        inx     h
        cmp     m
        dcx     h
        jc      env2_after_decay
        jz      env2_after_decay
        dcr     m
        mov     a,m
        inx     h
        cmp     m
        dcx     h
        jz      env2_after_decay
        ret

env2_update_release:
        mov     a,m
        ora     a
        jz      env2_finish
        dcr     m
        jz      env2_finish
        ret

; Transition helpers all receive HL=channel volume.
env2_enter_decay:
        push    h
        lxi     d,ENV2_STAGE
        dad     d
        mvi     m,ENV2_DECAY
        pop     h
env2_set_decay_fields:
        push    h
        lxi     d,ENV2_SUSTAIN
        dad     d
        mov     a,m
        pop     h
        inx     h
        mov     m,a                     ; target=sustain
        dcx     h
        push    h
        lxi     d,ENV2_DECAY_MASK
        dad     d
        mov     a,m
        pop     h
        inx     h
        inx     h
        mov     m,a                     ; current mask=decay mask
        dcx     h
        dcx     h
        push    h
        lxi     d,ENV2_FLAGS
        dad     d
        mov     a,m
        pop     h
        ani     ENV2_DECAY_IMMEDIATE
        rz
        push    h
        lxi     d,ENV2_SUSTAIN
        dad     d
        mov     a,m
        pop     h
        mov     m,a
        jmp     env2_after_decay

env2_after_decay:
        push    h
        lxi     d,ENV2_FLAGS
        dad     d
        mov     a,m
        pop     h
        ani     ENV2_KEY_SUSTAIN
        jz      env2_enter_release
        push    h
        lxi     d,ENV2_STAGE
        dad     d
        mvi     m,ENV2_HOLD
        pop     h
env2_set_sustain_target:
        push    h
        lxi     d,ENV2_SUSTAIN
        dad     d
        mov     a,m
        pop     h
        inx     h
        mov     m,a
        dcx     h
        ret

env2_enter_release:
        push    h
        lxi     d,ENV2_STAGE
        dad     d
        mvi     m,ENV2_RELEASE
        pop     h
env2_set_release_fields:
        xra     a
        inx     h
        mov     m,a                     ; target=zero
        dcx     h
        push    h
        lxi     d,ENV2_RELEASE_MASK
        dad     d
        mov     a,m
        pop     h
        inx     h
        inx     h
        mov     m,a                     ; current mask=release mask
        dcx     h
        dcx     h
        push    h
        lxi     d,ENV2_FLAGS
        dad     d
        mov     a,m
        pop     h
        ani     ENV2_RELEASE_IMMEDIATE
        rz

env2_finish:
        xra     a
        mov     m,a                     ; volume zero
        push    h
        lxi     d,4
        dad     d
        mov     m,a                     ; phase step zero
        inx     h
        mov     m,a
        inx     h
        inx     h
        inx     h
        inx     h
        mov     m,a                     ; stage off at offset 9
        pop     h
        ret

        if      @@5
; Used only when env2_load_work_flags has been patched from LDA to CALL.
; Return A=low internal envelope flags plus the 16-byte tremolo-table offset.
env2_load_tremolo_flags:
        lda     env2_packet_flags
        ani     00ch
        rlc
        rlc
        mov     b,a
        lda     env2_work_flags
        ora     b
        ret
        endif

        if      @@6
; Capability 05h: mode bits have already been validated by the pitch parser.
; The serialized shallow/deep distinction is resolved into peak_step_delta on
; the host, so target state needs only one enable bit plus the encoded delta.
env2_load_pitch_flags:
        lda     env2_packet_flags
        ani     030h
        jz      env2_pitch_flags_off
        mvi     b,040h
        jmp     env2_merge_feature_flags
env2_pitch_flags_off:
        mvi     b,0
env2_merge_feature_flags:
        lda     env2_work_flags
        ora     b
        ret

        if      @@5
env2_load_combined_flags:
        lda     env2_packet_flags
        ani     00ch
        rlc
        rlc
        mov     b,a
        lda     env2_packet_flags
        ani     030h
        jz      env2_merge_feature_flags
        mov     a,b
        ori     040h
        mov     b,a
        jmp     env2_merge_feature_flags
        endif
        endif

        if      @@5
; M4 amplitude-only tremolo.  This is reached only after prepare_frame's
; original three-byte LDA has been patched to a JMP for capability 03h.
; chN_volume remains the envelope's unmodulated state; only the ORI immediates
; for the next sample batch receive the clamped attenuation.
prepare_frame_tremolo:
        lhld    tremolo_phase
        mov     a,h
        rrc
        rrc
        rrc
        rrc
        ani     00fh
        mov     c,a                     ; shared table index for this frame
        lxi     d,012f2h
        dad     d
        shld    tremolo_phase

        lda     ch1_env2_flags
        ani     030h
        jz      tremolo_copy1
        ora     c
        mov     e,a
        mvi     d,0
        lxi     h,tremolo_tables
        dad     d
        lda     ch1_volume
        sub     m
        jnc     tremolo_store1
        xra     a
tremolo_store1:
        sta     volume1+1
        jmp     tremolo_channel2
tremolo_copy1:
        lda     ch1_volume
        sta     volume1+1

tremolo_channel2:
        lda     ch2_env2_flags
        ani     030h
        jz      tremolo_copy2
        ora     c
        mov     e,a
        mvi     d,0
        lxi     h,tremolo_tables
        dad     d
        lda     ch2_volume
        sub     m
        jnc     tremolo_store2
        xra     a
tremolo_store2:
        sta     volume2+1
        jmp     tremolo_channel3
tremolo_copy2:
        lda     ch2_volume
        sta     volume2+1

tremolo_channel3:
        lda     ch3_env2_flags
        ani     030h
        jz      tremolo_copy3
        ora     c
        mov     e,a
        mvi     d,0
        lxi     h,tremolo_tables
        dad     d
        lda     ch3_volume
        sub     m
        jnc     tremolo_store3
        xra     a
tremolo_store3:
        sta     volume3+1
        jmp     prepare_frame_steps
tremolo_copy3:
        lda     ch3_volume
        sta     volume3+1
        jmp     prepare_frame_steps

; Exact opl_tremolo.TABLES rows for depths 0, 1, 2, and 3.
tremolo_tables:
        db      0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
        db      0,0,0,0,1,1,1,1,1,1,1,1,0,0,0,0
        db      0,0,1,1,1,1,2,2,2,2,1,1,1,1,0,0
        db      0,0,1,1,2,2,3,3,3,3,2,2,1,1,0,0
        endif

env2_channel_pointer:
        dw      0
env2_phase_pointer:
        dw      0
env2_step_word:
        dw      0
env2_levels:
        db      0
env2_rates:
        db      0
env2_packet_flags:
        db      0
env2_work_flags:
        db      0
env2_rate_mask_temp:
        db      0
