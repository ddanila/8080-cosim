; Runtime-mapped ABI implementation at D800h..FFFFh.
        include "rom-abi.inc"
        include "network-rom-generated.inc"

MODEPORT        equ     006h
USARTDATA       equ     008h
USARTCTL        equ     009h
PITCOUNT0       equ     018h
PITCTL          equ     01bh
VRAM            equ     0d800h
FEATURES        equ     JROMFCONSOLE+JROMFKEYBOARD+JROMFSERIAL+JROMFNETDISK+JROMFDIAG

SELFSTATUS      equ     JROMSTATEBASE+3
TXBYTE          equ     JROMSTATEBASE+4
SERIALMODE      equ     JROMSTATEBASE+5
ROMKEYSTATEBASE equ     JROMSTATEBASE+6
ROMNETSTATEBASE equ     JROMSTATEBASE+010h

; D800h..DCFFh: resident text policy and immutable 5x7 font.
        org     0d800h
        include "rom-console.asm"
        dc      0dd00h-$,0ffh

; DD00h..DE7Fh: shared matrix scanner and immutable translation tables.
ROMKEYBOARD     equ     1
        include "ram-keyboard.asm"
        dc      0de80h-$,0ffh

; DE80h..E0FFh: common D57/D11 serial service.
rom_serinit_impl:
        sta     SERIALMODE
        push    psw
        mvi     a,015h
        out     PITCTL
        mvi     a,4
        out     PITCOUNT0
        xra     a
        out     USARTCTL
        out     USARTCTL
        out     USARTCTL
        mvi     a,040h
        out     USARTCTL
        pop     psw
        ora     a
        mvi     a,04eh
        jz      rom_serinit_mode
        mvi     a,05eh
rom_serinit_mode:
        out     USARTCTL
        mvi     a,035h
        out     USARTCTL
        in      USARTDATA
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
        ora     a
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
        ora     a
        ret
rom_serial_end:

        dc      0e100h-$,0ffh

; E100h..E3FFh: versioned NetDisk-v3 read-ahead/write-through service.
ROMNETDISK      equ     1
        include "netdisk-v3.asm"

rom_netdisk_impl:
        mov     a,m
        cpi     1                       ; request version
        jnz     rom_netdisk_bad
        inx     h
        mov     a,m                     ; operation: read/invalidate/mode/write
        inx     h
        ora     a
        jz      rom_netdisk_read
        dcr     a
        jz      N3INV
        dcr     a
        jz      rom_netdisk_mode
        dcr     a
        jz      rom_netdisk_write
        jmp     rom_netdisk_bad
rom_netdisk_mode:
        mov     a,m
        jmp     N3ENA
rom_netdisk_read:
        mvi     b,0
        jmp     rom_netdisk_rw
rom_netdisk_write:
        mvi     b,1
rom_netdisk_rw:
        mov     a,m
        sta     SEKDSK
        inx     h
        mov     a,m
        sta     SEKTRK
        inx     h
        mov     a,m
        sta     SEKTRK+1
        inx     h
        mov     a,m
        sta     SEKSEC
        inx     h
        mov     a,m
        sta     MEMADR
        inx     h
        mov     a,m
        sta     MEMADR+1
        inx     h
        mov     a,m
        sta     N3CACHE
        inx     h
        mov     a,m
        sta     N3CACHE+1
        mov     a,b
        ora     a
        jnz     N3WRITE
        jmp     N3READ
rom_netdisk_bad:
        mvi     a,0ffh
        stc
        ret
rom_netdisk_end:

        dc      0e600h-$,0ffh

; E600h onward: initialization, diagnostics, and retained ABI self-test.
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

        call    JCGCONINITADDR
        ora     a
        jnz     self_fail_console
        lxi     b,01234h
        lxi     d,05678h
        lxi     h,09abch
        mvi     a,'Z'
        call    JCGCONOUTADDR
        cpi     'Z'
        jnz     self_fail_registers
        mvi     a,05ah
        sta     VRAM+100                ; mode-1 overlay write must be rejected
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

; Test-only variants exercise complete cursor periods using the public
; console-status vector. They are assembled only into transient ABI fixtures;
; the committed production image is byte-identical.
.ifdef ABI_CURSOR_HIDDEN
        call    self_cursor_phase
        lda     RCCURVISIBLE
        ora     a
        jnz     self_fail_console
.endif
.ifdef ABI_CURSOR_VISIBLE
        call    self_cursor_phase
        lda     RCCURVISIBLE
        ora     a
        jnz     self_fail_console
        call    self_cursor_phase
        lda     RCCURVISIBLE
        cpi     1
        jnz     self_fail_console
.endif

        mvi     a,0
        call    JCGDIAGADDR
        cpi     0a5h
        jnz     self_fail_diag
        lxi     h,0d7f0h                ; cleared/invalid request version
        call    JCGNETDISKADDR
        cpi     0ffh
        jnz     self_fail_netdisk

        call    JCGKEYINITADDR
        ora     a
        jnz     self_fail_keyboard
        lxi     b,0ffffh
self_wait_keyboard:
        call    JCGKEYSCANADDR
        ora     a
        jnz     self_got_keyboard
        dcx     b
        mov     a,b
        ora     c
        jnz     self_wait_keyboard
        jmp     self_fail_keyboard
self_got_keyboard:
        cpi     'T'
        jnz     self_fail_keyboard

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
        cpi     0c3h
        jnz     self_fail_serial

.ifdef ABI_NETDISK_SELFTEST
        ; Switch to runtime 8O1 and issue one public read request. The HDL host
        ; returns a checked single-record fill, proving the exact resident
        ; transaction code through the structural D57/D11/D104 path.
        mvi     a,1
        call    JCGSERINITADDR
        ora     a
        jnz     self_fail_serial
        lxi     h,0d7f0h
        mvi     m,1                     ; request version
        inx     h
        mvi     m,JROMNETOPMODE
        inx     h
        mvi     m,3                     ; enable NetDisk v3
        lxi     h,0d7f0h
        call    JCGNETDISKADDR
        ora     a
        jnz     self_fail_netdisk

        lxi     h,0d7f0h
        mvi     m,1
        inx     h
        mvi     m,JROMNETOPREAD
        inx     h
        mvi     m,0                     ; drive A
        inx     h
        mvi     m,2                     ; track 2
        inx     h
        mvi     m,0
        inx     h
        mvi     m,1                     ; sector 1
        inx     h
        mvi     m,0                     ; DMA 0300h
        inx     h
        mvi     m,3
        inx     h
        mvi     m,0                     ; cache 0400h
        inx     h
        mvi     m,4
        lxi     h,0d7f0h
        call    JCGNETDISKADDR
        ora     a
        jnz     self_fail_netdisk
        lda     0300h
        cpi     05ah
        jnz     self_fail_netdisk
.endif

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
        jmp     self_store_fail
self_fail_keyboard:
        mvi     a,0e6h
        jmp     self_store_fail
self_fail_console:
        mvi     a,0e7h
        jmp     self_store_fail
self_fail_netdisk:
        mvi     a,0e8h
self_store_fail:
        sta     SELFSTATUS
        jmp     self_done

fill_guard:
        mov     m,a
        inx     h
        dcr     b
        jnz     fill_guard
        ret

.ifdef ABI_CURSOR_HIDDEN
self_cursor_phase:
        lxi     d,CURSORPERIOD
self_cursor_tick:
        call    JCGCONSTATADDR
        dcx     d
        mov     a,d
        ora     e
        jnz     self_cursor_tick
        ret
.endif
.ifdef ABI_CURSOR_VISIBLE
self_cursor_phase:
        lxi     d,CURSORPERIOD
self_cursor_tick:
        call    JCGCONSTATADDR
        dcx     d
        mov     a,d
        ora     e
        jnz     self_cursor_tick
        ret
.endif

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

rom_keyscan_impl:
        call    RKSTAT
        ora     a
        rz
        jmp     RKIN

rom_diag_impl:
        ora     a
        jnz     rom_unavailable
        mvi     a,0a5h
        ret

rom_getinfo_impl:
        lxi     h,JROMABIBASE
        lxi     d,FEATURES
        ret

rom_unavailable:
        mvi     a,0ffh
        stc
        ret

build_identity:
        db      'Juku network ROM ABI 1.0 automatic boot 2026-08-16',0

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
        jmp     ROMCONINIT
        jmp     ROMCONSTAT
        jmp     ROMCONIN
        jmp     ROMCONOUT
        jmp     rom_serinit_impl
        jmp     rom_serrx_impl
        jmp     rom_sertx_impl
        jmp     rom_netdisk_impl
        jmp     RKINIT
        jmp     rom_keyscan_impl
        jmp     rom_unavailable
        jmp     rom_diag_impl
        jmp     rom_getinfo_impl

        dc      10000h-$,0ffh
        end     resident_entry
