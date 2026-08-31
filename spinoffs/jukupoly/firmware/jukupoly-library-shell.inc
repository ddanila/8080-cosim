; CP/M library shell for the disk-resident JukuPoly player.
;
; This file is included only when jukupoly-player-0100.asm is assembled with
; -P2=1.  The timing-critical player above is shared unchanged with standalone
; COM images; this shell runs only before and after playback.

BDOS            equ     00005h
BDOS_CONIN      equ     1
BDOS_CONOUT     equ     2
BDOS_PRINT      equ     9
BDOS_OPEN       equ     15
BDOS_CLOSE      equ     16
BDOS_READ       equ     20
BDOS_DMA        equ     26
SONG_LIMIT      equ     09800h
TRACK_COUNT     equ     44
PAGE_TRACKS     equ     11

library_start:
        call    library_init_console
        lxi     d,library_banner
        call    library_print
        xra     a
        sta     page_start

library_show_page:
        call    library_list_page

library_menu:
        lxi     d,library_prompt
        call    library_print
        call    library_read_selection
        cpi     0ffh
        jz      library_quit
        ora     a
        jz      library_next_page
        cpi     TRACK_COUNT+1
        jnc     library_bad_selection
        sta     selected_track
        call    library_show_selected
        call    library_make_filename
        call    library_load_song
        ora     a
        jnz     library_menu
        call    player_start
        lda     player_aborted
        ora     a
        jnz     library_report_stopped
        lxi     d,library_finished
        call    library_print
        jmp     library_menu
library_report_stopped:
        lxi     d,library_stopped
        call    library_print
        jmp     library_menu

library_next_page:
        lda     page_start
        adi     PAGE_TRACKS
        cpi     TRACK_COUNT
        jc      library_store_page
        xra     a
library_store_page:
        sta     page_start
        jmp     library_show_page

library_bad_selection:
        lxi     d,library_bad_number
        call    library_print
        jmp     library_menu

library_quit:
        lxi     d,library_goodbye
        call    library_print
        ret

; A=one-based global track number.  Return HL=track record.
library_track_pointer:
        dcr     a
        add     a
        mov     e,a
        mvi     d,0
        lxi     h,track_pointers
        dad     d
        mov     e,m
        inx     h
        mov     d,m
        xchg
        ret

library_list_page:
        lxi     d,library_page_header
        call    library_print
        lda     page_start
        mov     b,a
        mvi     c,PAGE_TRACKS
library_list_loop:
        mov     a,b
        cpi     TRACK_COUNT
        rnc
        inr     a
        push    b
        call    library_print_track_line
        pop     b
        inr     b
        dcr     c
        jnz     library_list_loop
        ret

; A=one-based global track number.
library_print_track_line:
        sta     display_track
        call    library_track_pointer
        shld    display_record
        lda     display_track
        call    library_print_two_digits
        mvi     e,' '
        call    library_putc
        lhld    display_record
        lxi     d,4
        dad     d
        xchg
        call    library_print
        lxi     d,library_duration_sep
        call    library_print
        lhld    display_record
        inx     h
        inx     h
        mov     a,m
        call    library_print_number
        mvi     e,':'
        call    library_putc
        lhld    display_record
        inx     h
        inx     h
        inx     h
        mov     a,m
        call    library_print_two_digits
        jmp     library_newline

library_show_selected:
        lxi     d,library_now_playing
        call    library_print
        lda     selected_track
        call    library_print_track_line
        lda     selected_track
        call    library_track_pointer
        mov     a,m                     ; source game 1 or 2
        dcr     a
        jz      library_source_doom
        lxi     d,library_source_doom2
        jmp     library_print_source
library_source_doom:
        lxi     d,library_source_doom1
library_print_source:
        call    library_print
        lxi     d,library_loading
        jmp     library_print

; Build D1T01.JPS or D2T01.JPS in the CP/M FCB from the selected record.
library_make_filename:
        lxi     h,song_fcb+12
        mvi     b,24
        xra     a
library_clear_fcb:
        mov     m,a
        inx     h
        dcr     b
        jnz     library_clear_fcb
        lda     selected_track
        call    library_track_pointer
        mov     a,m
        adi     '0'
        sta     song_fcb+2
        inx     h
        mov     a,m                     ; local pack track 1..23
        call    library_split_decimal
        mov     a,b
        adi     '0'
        sta     song_fcb+4
        mov     a,c
        adi     '0'
        sta     song_fcb+5
        ret

; Load a JPS file sequentially at 1800h.  A=0 on success, A=1 on failure.
library_load_song:
        lxi     d,song_fcb
        mvi     c,BDOS_OPEN
        call    BDOS
        cpi     0ffh
        jz      library_load_missing
        lxi     h,SONG_LOAD
        shld    load_pointer
library_read_record:
        lhld    load_pointer
        mov     a,h
        cpi     SONG_LIMIT SHR 8
        jnc     library_load_too_large
        xchg
        mvi     c,BDOS_DMA
        call    BDOS
        lxi     d,song_fcb
        mvi     c,BDOS_READ
        call    BDOS
        ora     a
        jnz     library_load_eof
        lhld    load_pointer
        lxi     d,128
        dad     d
        shld    load_pointer
        jmp     library_read_record

library_load_eof:
        lxi     d,song_fcb
        mvi     c,BDOS_CLOSE
        call    BDOS
        call    library_restore_dma
        call    library_verify_song
        rnz
        xra     a
        ret

library_load_missing:
        lxi     d,library_missing
        jmp     library_load_error
library_load_too_large:
        lxi     d,song_fcb
        mvi     c,BDOS_CLOSE
        call    BDOS
        call    library_restore_dma
        lxi     d,library_too_large
library_load_error:
        call    library_print
        mvi     a,1
        ret

library_restore_dma:
        lxi     d,00080h
        mvi     c,BDOS_DMA
        jmp     BDOS

library_verify_song:
        lda     SONG_LOAD
        cpi     'J'
        jnz     library_bad_song
        lda     SONG_LOAD+1
        cpi     'P'
        jnz     library_bad_song
        lda     SONG_LOAD+2
        cpi     'S'
        jnz     library_bad_song
        lda     SONG_LOAD+3
        cpi     1
        jnz     library_bad_song
        lda     SONG_LOAD+7
        ora     a                       ; reserved/flags must be ABI-v1 zero
        jnz     library_bad_song
        lda     SONG_LOAD+6
        cpi     JUKUPOLY_FRAME_SAMPLES
        jnz     library_bad_song
        lhld    SONG_LOAD+4
        mov     a,h
        ora     l
        jz      library_bad_song
        mov     a,h
        cpi     080h                    ; maximum 32767 bytes
        jnc     library_bad_song
        xra     a
        ret
library_bad_song:
        lxi     d,library_invalid
        call    library_print
        mvi     a,1
        ret

; Read one or two decimal digits.  Return 1..44, 0 for next page, FFh for quit,
; or FEh for malformed input.  A bare RETURN selects track 01.
library_read_selection:
        call    library_getc
        cpi     00dh
        jz      library_default_track
        cpi     'L'
        jz      library_list_request
        cpi     'l'
        jz      library_list_request
        cpi     'Q'
        jz      library_quit_request
        cpi     'q'
        jz      library_quit_request
        cpi     '0'
        jc      library_invalid_input
        cpi     '9'+1
        jnc     library_invalid_input
        sui     '0'
        sta     input_value
        call    library_getc
        cpi     00dh
        jz      library_input_done
        cpi     '0'
        jc      library_flush_invalid
        cpi     '9'+1
        jnc     library_flush_invalid
        sui     '0'
        mov     b,a
        lda     input_value
        mov     c,a
        add     a
        add     a
        add     c
        add     a
        add     b
        sta     input_value
        call    library_getc
        cpi     00dh
        jnz     library_flush_invalid
library_input_done:
        lda     input_value
        ret
library_default_track:
        mvi     a,1
        ret
library_list_request:
        xra     a
        ret
library_quit_request:
        mvi     a,0ffh
        ret
library_invalid_input:
        mvi     a,0feh
        ret
library_flush_invalid:
        cpi     00dh
        jz      library_invalid_input
        call    library_getc
        jmp     library_flush_invalid

; A=0..99, return B=tens and C=ones.
library_split_decimal:
        mvi     b,0
library_decimal_loop:
        cpi     10
        jc      library_decimal_done
        sui     10
        inr     b
        jmp     library_decimal_loop
library_decimal_done:
        mov     c,a
        ret

library_print_number:
        call    library_split_decimal
        mov     a,b
        ora     a
        jz      library_print_ones
        push    b
        adi     '0'
        mov     e,a
        call    library_putc
        pop     b
library_print_ones:
        mov     a,c
        adi     '0'
        mov     e,a
        jmp     library_putc

library_print_two_digits:
        call    library_split_decimal
        push    b
        mov     a,b
        adi     '0'
        mov     e,a
        call    library_putc
        pop     b
        mov     a,c
        adi     '0'
        mov     e,a
        jmp     library_putc

library_init_console:
        lhld    00001h                  ; page-zero JMP WBOOT target
        lxi     d,6                     ; BIOS CONIN is WBOOT + 6
        dad     d
        shld    library_bios_conin+1
        lxi     d,3                     ; BIOS CONOUT is CONIN + 3
        dad     d
        shld    library_bios_conout+1
        ret

library_getc:
library_bios_conin:
        call    00000h
        push    psw
        mov     e,a                     ; BIOS CONIN does not echo
        call    library_putc
        pop     psw
        ret
library_putc:
        mov     c,e                     ; BIOS CONOUT character convention
library_bios_conout:
        call    00000h
        ret
library_print:
        xchg                            ; HL = '$'-terminated string
        shld    print_pointer
library_print_loop:
        lhld    print_pointer
        mov     a,m
        cpi     '$'
        rz
        inx     h
        shld    print_pointer           ; BIOS may destroy every register
        mov     e,a
        call    library_putc
        jmp     library_print_loop
library_newline:
        lxi     d,library_crlf
        jmp     library_print

page_start:     db      0
selected_track: db      0
display_track:  db      0
input_value:    db      0
display_record: dw      0
load_pointer:   dw      SONG_LOAD
print_pointer:  dw      0

song_fcb:
        db      2                       ; songs live on the library's B: disk
        db      'D','1','T','0','1',' ',' ',' '
        db      'J','P','S'
        ds      24

library_banner:
        db      13,10,'JukuPoly DOOM library',13,10
        db      '44 tracks - DOOM + DOOM II - 2:13:28',13,10
        db      'Music: Robert Prince. Games: id Software.',13,10
        db      'OPL3 rips: vgmrips.net / NewRisingSun.',13,10
        db      'Three-voice + percussion reductions for Juku.',13,10
        db      'Press physical ESC to stop playback.',13,10,'$'
library_page_header:
        db      13,10,'Catalog page (L shows the next 11 tracks):',13,10,'$'
library_prompt:
        db      13,10,'Track 01-44, L=list, Q=quit [RETURN=01]: $'
library_now_playing:
        db      13,10,'Selected: ',13,10,'$'
library_duration_sep:
        db      ' - ','$'
library_source_doom1:
        db      'Source: DOOM (1993)',13,10,'$'
library_source_doom2:
        db      'Source: DOOM II (1994)',13,10,'$'
library_loading:
        db      'Loading disk song...',13,10,'$'
library_finished:
        db      13,10,'Track finished.',13,10,'$'
library_stopped:
        db      13,10,'Track stopped.',13,10,'$'
library_bad_number:
        db      13,10,'Please enter a track from 01 through 44.',13,10,'$'
library_missing:
        db      13,10,'Song file is missing from this disk.',13,10,'$'
library_too_large:
        db      13,10,'Song exceeds the Juku CP/M memory limit.',13,10,'$'
library_invalid:
        db      13,10,'Invalid or incompatible JPS song file.',13,10,'$'
library_goodbye:
        db      13,10,'JukuPoly stopped.',13,10,'$'
library_crlf:
        db      13,10,'$'

track_pointers:
        dw track01,track02,track03,track04,track05,track06,track07,track08
        dw track09,track10,track11,track12,track13,track14,track15,track16
        dw track17,track18,track19,track20,track21,track22,track23,track24
        dw track25,track26,track27,track28,track29,track30,track31,track32
        dw track33,track34,track35,track36,track37,track38,track39,track40
        dw track41,track42,track43,track44

; game, local track, minutes, seconds, title
track01: db 1,1,0,7,'Title Screen','$'
track02: db 1,2,1,37,'At Doom',27h,'s Gate','$'
track03: db 1,3,2,38,'The Imp',27h,'s Song','$'
track04: db 1,4,4,32,'Dark Halls','$'
track05: db 1,5,2,53,'Kitchen Ace (and Taking Names)','$'
track06: db 1,6,2,53,'Suspense','$'
track07: db 1,7,1,26,'On the Hunt','$'
track08: db 1,8,2,31,'Demons on the Prey','$'
track09: db 1,9,2,33,'Sign of Evil','$'
track10: db 1,10,2,21,'Hiding the Secrets','$'
track11: db 1,11,2,35,'I Sawed the Demons','$'
track12: db 1,12,2,36,'The Demons from Adrian',27h,'s Pen','$'
track13: db 1,13,4,13,'They',27h,'re Going to Get You','$'
track14: db 1,14,2,58,'Sinister','$'
track15: db 1,15,1,46,'Waltz of the Demons','$'
track16: db 1,16,2,58,'Nobody Told Me About id','$'
track17: db 1,17,1,37,'Untitled','$'
track18: db 1,18,1,59,'Donna to the Rescue','$'
track19: db 1,19,2,2,'Deep into the Code','$'
track20: db 1,20,1,36,'Facing the Spider','$'
track21: db 1,21,3,23,'Intermission from Doom','$'
track22: db 1,22,3,12,'The End of Doom','$'
track23: db 1,23,1,2,'Sweet Little Dead Bunny','$'
track24: db 2,1,0,11,'Title Music','$'
track25: db 2,2,3,51,'Running From Evil','$'
track26: db 2,3,2,53,'Intermission Music','$'
track27: db 2,4,4,53,'The Healer Stalks','$'
track28: db 2,5,3,50,'Countdown to Death','$'
track29: db 2,6,2,35,'Between Levels','$'
track30: db 2,7,4,20,'DOOM','$'
track31: db 2,8,6,59,'In the Dark','$'
track32: db 2,9,4,20,'Shawn',27h,'s Got the Shotgun','$'
track33: db 2,10,5,1,'The Dave D. Taylor Blues','$'
track34: db 2,11,4,40,'Into Sandy',27h,'s City','$'
track35: db 2,12,4,24,'The Demon',27h,'s Dead','$'
track36: db 2,13,5,7,'Waiting for Romero to Play','$'
track37: db 2,14,4,40,'Message for the Archvile','$'
track38: db 2,15,1,39,'Bye Bye American Pie','$'
track39: db 2,16,1,55,'Adrian',27h,'s Asleep','$'
track40: db 2,17,4,46,'Getting Too Tense','$'
track41: db 2,18,4,40,'Opening to Hell','$'
track42: db 2,19,1,11,'Evil Incarnate','$'
track43: db 2,20,1,18,'The Ultimate Challenge','$'
track44: db 2,21,4,48,'Endgame Music','$'
