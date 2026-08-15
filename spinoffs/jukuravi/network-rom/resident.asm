; Runtime-mapped ABI skeleton at D800h..FFFFh.
        include "rom-abi.inc"
        include "network-rom-generated.inc"

MODEPORT        equ     006h
USARTDATA       equ     008h
USARTCTL        equ     009h
PITCOUNT0       equ     018h
PITCTL          equ     01bh
VRAM            equ     0d800h
FEATURES        equ     JROMFSERIAL+JROMFDIAG

SELFSTATUS      equ     JROMSTATEBASE+3
TXBYTE          equ     JROMSTATEBASE+4

        org     0d800h

resident_entry:
        lxi     sp,0d5f0h
        lxi     h,0d5c0h
        mvi     b,16
        mvi     a,0a6h
        call    fill_guard
        lxi     h,0d5f0h
        mvi     b,16
        call    fill_guard
        call    JCGINITADDR
        ora     a
        jnz     self_fail_gate

        call    JCGGETINFOADDR
        mov     a,h
        cpi     0ffh
        jnz     self_fail_info
        mov     a,l
        ora     a
        jnz     self_fail_info
        mov     a,d
        ora     a
        jnz     self_fail_info
        mov     a,e
        cpi     FEATURES
        jnz     self_fail_info

        lxi     b,01234h
        lxi     d,05678h
        lxi     h,09abch
        mvi     a,05ah
        call    JCGCONOUTADDR            ; rejected overlay write + RAM helper
        cpi     05ah
        jnz     self_fail_registers
        mov     a,b
        cpi     012h
        jnz     self_fail_registers
        mov     a,c
        cpi     034h
        jnz     self_fail_registers
        mov     a,d
        cpi     056h
        jnz     self_fail_registers
        mov     a,e
        cpi     078h
        jnz     self_fail_registers
        mov     a,h
        cpi     09ah
        jnz     self_fail_registers
        mov     a,l
        cpi     0bch
        jnz     self_fail_registers
        mvi     a,0
        call    JCGDIAGADDR
        cpi     0a5h
        jnz     self_fail_diag

        mvi     a,0
        call    JCGSERINITADDR
        ora     a
        jnz     self_fail_serial
        mvi     a,'A'
        lxi     b,0ffffh
        call    JCGSERTXADDR
        jc      self_fail_serial
        mvi     a,'B'
        lxi     b,0ffffh
        call    JCGSERTXADDR
        jc      self_fail_serial
        mvi     a,'I'
        lxi     b,0ffffh
        call    JCGSERTXADDR
        jc      self_fail_serial
        mvi     a,'1'
        lxi     b,0ffffh
        call    JCGSERTXADDR
        jc      self_fail_serial
        lxi     b,0ffffh
        call    JCGSERRXADDR
        jc      self_fail_serial
        cpi     0c3h                    ; host byte queued during ABI calls
        jnz     self_fail_serial

        mvi     a,0a5h
        sta     SELFSTATUS
self_done:
        hlt
        jmp     self_done

self_fail_gate:
        mvi     a,0e1h
        jmp     self_store_fail
self_fail_info:
        mvi     a,0e2h
        jmp     self_store_fail
self_fail_diag:
        mvi     a,0e3h
        jmp     self_store_fail
self_fail_serial:
        mvi     a,0e4h
        jmp     self_store_fail
self_fail_registers:
        mvi     a,0e5h
self_store_fail:
        sta     SELFSTATUS
        jmp     self_done

fill_guard:
        mov     m,a
        inx     h
        dcr     b
        jnz     fill_guard
        ret

rom_init_impl:
        lxi     h,JROMSTATEBASE
        lxi     b,080h
rom_init_clear:
        mvi     m,0
        inx     h
        dcx     b
        mov     a,b
        ora     c
        jnz     rom_init_clear
        xra     a
        ret

rom_conout_impl:
        sta     VRAM+1                  ; overlay write must be rejected
        call    JROMHELPBASE            ; hidden-RAM read/write proof
        ret

rom_serinit_impl:
        push    psw
        mvi     a,015h                  ; D57 ch0 mode 2, LSB, BCD
        out     PITCTL
        mvi     a,4                     ; 16 MHz/13/4/16 = 19230.8 baud
        out     PITCOUNT0
        xra     a
        out     USARTCTL
        out     USARTCTL
        out     USARTCTL
        mvi     a,040h
        out     USARTCTL
        pop     psw
        ora     a
        mvi     a,04eh                  ; x16, 8N1
        jz      rom_serinit_mode
        mvi     a,05eh                  ; x16, 8O1
rom_serinit_mode:
        out     USARTCTL
        mvi     a,035h
        out     USARTCTL
        xra     a
        ret

rom_serrx_impl:
        in      USARTCTL
        ani     2
        jnz     rom_serrx_ready
        dcx     b
        mov     a,b
        ora     c
        jnz     rom_serrx_impl
        stc
        ret
rom_serrx_ready:
        in      USARTDATA
        ora     a                       ; clear carry, retain data
        ret

rom_sertx_impl:
        sta     TXBYTE
rom_sertx_wait:
        in      USARTCTL
        ani     1
        jnz     rom_sertx_ready
        dcx     b
        mov     a,b
        ora     c
        jnz     rom_sertx_wait
        stc
        ret
rom_sertx_ready:
        lda     TXBYTE
        out     USARTDATA
        ora     a                       ; clear carry
        ret

rom_diag_impl:
        ora     a
        jnz     rom_unavailable
        mvi     a,0a5h                  ; ABI skeleton diagnostic signature
        ret

rom_getinfo_impl:
        lxi     h,JROMABIBASE
        lxi     d,FEATURES
        ret

rom_no_key:
        xra     a
        ret
rom_unavailable:
        mvi     a,0ffh
        stc
        ret

build_identity:
        db      'Juku network ROM ABI 1.0 skeleton 2026-08-16',0

        dc      JROMABIBASE-$,0ffh

        db      'J','U','K','U','A','B','I',0
        db      JROMABIMAJOR,JROMABIMINOR
        dw      JROMABISIZE
        dw      FEATURES
        dw      build_identity
        dw      JROMRAMEND-JROMRAMBASE
        dw      JROMHELPERBYTES
        dc      JROMMANIFESTEND-$,0ffh

        jmp     rom_init_impl
        jmp     rom_unavailable          ; console init
        jmp     rom_no_key               ; console status
        jmp     rom_unavailable          ; console input
        jmp     rom_conout_impl
        jmp     rom_serinit_impl
        jmp     rom_serrx_impl
        jmp     rom_sertx_impl
        jmp     rom_unavailable          ; NetDisk follows in migration step
        jmp     rom_unavailable          ; keyboard init
        jmp     rom_no_key               ; keyboard scan
        jmp     rom_unavailable          ; sound
        jmp     rom_diag_impl
        jmp     rom_getinfo_impl

        dc      10000h-$,0ffh
        end     resident_entry
