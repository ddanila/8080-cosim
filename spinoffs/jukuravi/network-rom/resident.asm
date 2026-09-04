; Runtime-mapped ABI implementation at D800h..FFFFh.
        include "rom-abi.inc"
        include "network-rom-generated.inc"

MODEPORT        equ     006h
USARTDATA       equ     008h
USARTCTL        equ     009h
PITCOUNT0       equ     018h
PITCTL          equ     01bh
VRAM            equ     0d800h
.ifdef ROM_ABI_HOSTSERVICES
.ifdef ROM_ABI_C12
FEATURES        equ     JROMFCONSOLE+JROMFKEYBOARD+JROMFSERIAL+JROMFNETDISK+JROMFSOUND+JROMFDIAG+JROMFNETCON+JROMFLOCALE+JROMFKEYREMAP+JROMFCONBLOCK+JROMFNETMULTI+JROMFKEYRAW+JROMFCONCONFIG
.else
FEATURES        equ     JROMFCONSOLE+JROMFKEYBOARD+JROMFSERIAL+JROMFNETDISK+JROMFSOUND+JROMFDIAG+JROMFNETCON+JROMFLOCALE+JROMFKEYREMAP+JROMFCONBLOCK+JROMFNETMULTI+JROMFKEYRAW
.endif
.else
.ifdef ROM_ABI_EXTENDED
FEATURES        equ     JROMFCONSOLE+JROMFKEYBOARD+JROMFSERIAL+JROMFNETDISK+JROMFSOUND+JROMFDIAG+JROMFLOCALE+JROMFKEYREMAP+JROMFCONBLOCK+JROMFNETMULTI+JROMFKEYRAW
.else
.ifdef ROM_ABI_LOCALE
FEATURES        equ     JROMFCONSOLE+JROMFKEYBOARD+JROMFSERIAL+JROMFNETDISK+JROMFDIAG+JROMFLOCALE+JROMFKEYREMAP
.else
FEATURES        equ     JROMFCONSOLE+JROMFKEYBOARD+JROMFSERIAL+JROMFNETDISK+JROMFDIAG
.endif
.endif
.endif

SELFSTATUS      equ     JROMSTATEBASE+3
TXBYTE          equ     JROMSTATEBASE+4
SERIALMODE      equ     JROMSTATEBASE+5
ROMKEYSTATEBASE equ     JROMSTATEBASE+6
ROMNETSTATEBASE equ     JROMSTATEBASE+010h
.ifdef ROM_ABI_LOCALE
ROMCONFIG       equ     JROMSTATEBASE+041h
ROMKEYREMAPBASE equ     JROMSTATEBASE+042h
.ifdef ROM_ABI_C12
; The console's mode-specific state ends at D7D9h, per-drive NetDisk state
; occupies D7DAh..D7DFh, and the resident-host block ends at D7FCh.
ROMACTIVECONFIG equ     JROMSTATEBASE+07dh
ROMCONFIGFLAGS  equ     JROMSTATEBASE+07eh
.endif
.endif
.ifdef ROM_ABI_HOSTSERVICES
ROMHOSTSTATEBASE equ    JROMSTATEBASE+060h
.endif

; D800h..DCFFh: resident text policy and immutable 5x7 font.
        org     0d800h
        include "rom-console.asm"
        dc      0dd00h-$,0ffh

; DD00h..DE7Fh: shared matrix scanner and immutable translation tables.
ROMKEYBOARD     equ     1
.ifdef ROM_ABI_LOCALE
RAMKEYREMAP     equ     1
.endif
        include "ram-keyboard.asm"
.ifdef ROM_ABI_LOCALE
        dc      0df00h-$,0ffh
.else
        dc      0de80h-$,0ffh
.endif

; DE80h..E0FFh: common D57/D11 serial service.
.ifdef ROM_ABI_LOCALE
        org     0df00h
.endif
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
.ifdef ROM_ABI_LOCALE
ROMNETDISK_PER_DRIVE equ 1
ROMNETDRIVESTATEBASE equ JROMSTATEBASE+05ah
N3MAXRECORDS   equ     8
.endif
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

.ifdef ROM_ABI_HOSTSERVICES
.ifdef ROM_ABI_C9
        dc      0e800h-$,0ffh
.else
        dc      0e500h-$,0ffh
        include "rom-host-services.asm"
        dc      0e800h-$,0ffh
.endif
.else
        dc      0e600h-$,0ffh
.endif

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

.ifdef ABI_HOST_SELFTEST
        ; Focused C9 transport fixture: one mirrored byte exercises the exact
        ; production request/reply path. Tests vary the modeled D11 and PTY
        ; peer, then inspect the ABI 1.4 state at D7F8h..D7FBh.
        call    JCGCONINITADDR
        ora     a
        jnz     self_fail_console
        mvi     a,'L'
        call    JCGCONOUTADDR
        mvi     a,1
        call    JCGSERINITADDR
        ora     a
        jnz     self_fail_serial
        mvi     c,JROMHOSTENABLE
        call    JCGHOSTADDR
        mvi     a,1
        mvi     c,JROMHOSTCONFIG
        call    JCGHOSTADDR
        mvi     a,'X'
        mvi     c,JROMHOSTOUT
        call    JCGHOSTADDR
        mvi     a,'R'
        call    JCGCONOUTADDR
        mvi     a,0a5h
        sta     SELFSTATUS
self_host_done:
        hlt
        jmp     self_host_done
.endif

        call    JCGGETINFOADDR
        mov     a,h
        cpi     0ffh
        jnz     self_fail_info
        mov     a,l
        ora     a
        jnz     self_fail_info
        mov     a,d
.ifdef ROM_ABI_C12
        cpi     01fh
.else
.ifdef ROM_ABI_EXTENDED
        cpi     00fh
.else
.ifdef ROM_ABI_LOCALE
        cpi     1
.else
        ora     a
.endif
.endif
.endif
        jnz     self_fail_info
        mov     a,e
.ifdef ROM_ABI_HOSTSERVICES
        cpi     0ffh
.else
.ifdef ROM_ABI_EXTENDED
        cpi     0bfh
.else
.ifdef ROM_ABI_LOCALE
        cpi     0afh
.else
        cpi     FEATURES
.endif
.endif
.endif
        jnz     self_fail_info

.ifdef ROM_ABI_LOCALE
        call    JCGCONFIGADDR
        mov     d,a
        ani     018h                    ; fixture-selected character bank
.ifdef ABI_LOCALE_ENGLISH
        cpi     000h
.else
.ifdef ABI_LOCALE_RUSSIAN
        cpi     010h
.else
.ifdef ABI_LOCALE_USER
        cpi     018h
.else
        cpi     008h
.endif
.endif
.endif
        jnz     self_fail_info
        mov     a,b
        cpi     4
        jnc     self_fail_info
        mov     a,c
.ifdef ABI_LOCALE_ENGLISH
        cpi     0
.else
.ifdef ABI_LOCALE_RUSSIAN
        cpi     2
.else
.ifdef ABI_LOCALE_USER
        cpi     3
.else
        cpi     1                       ; Estonian/default fixture
.endif
.endif
.endif
        jnz     self_fail_info
.endif

.ifdef ROM_ABI_C12
        ; Install the persistent remap before the runtime-console matrix. The
        ; later translated-key assertion therefore proves that set/default
        ; transitions discard only pending key state, not user remaps.
        lxi     h,self_keyremap
        mvi     a,1
        call    JCGKEYREMAPADDR
        ora     a
        jnz     self_fail_keyboard

        mvi     a,JROMCONCONFIGQUERY
        call    JCGCONCONFIGADDR
        mov     a,d
        ora     a
        jnz     self_fail_info
        mov     a,b
        sta     0d5d2h
        mov     a,c
        sta     0d5d3h
.ifdef ABI_C12_KEEP_OVERRIDE
.ifdef ABI_C12_MODE_0
        mvi     a,0
.else
.ifdef ABI_C12_MODE_1
        mvi     a,1
.else
.ifdef ABI_C12_MODE_2
        mvi     a,2
.else
        mvi     a,3
.endif
.endif
.endif
        sta     0d5d0h
.ifdef ABI_C12_BANK_0
        mvi     a,0
.else
.ifdef ABI_C12_BANK_1
        mvi     a,1
.else
.ifdef ABI_C12_BANK_2
        mvi     a,2
.else
        mvi     a,3
.endif
.endif
.endif
        sta     0d5d1h
.else
        mov     a,b
        inr     a
        ani     3
        sta     0d5d0h
        mov     a,c
        inr     a
        ani     3
        sta     0d5d1h
.endif

        ; Rejected selectors and values must not partially publish state.
        mvi     b,4
        mvi     c,0
        mvi     a,JROMCONCONFIGSET
        call    JCGCONCONFIGADDR
        jnc     self_fail_console
        cpi     0ffh
        jnz     self_fail_console
        mvi     b,0
        mvi     c,4
        mvi     a,JROMCONCONFIGSET
        call    JCGCONCONFIGADDR
        jnc     self_fail_console
        cpi     0ffh
        jnz     self_fail_console
        mvi     a,3
        call    JCGCONCONFIGADDR
        jnc     self_fail_console
        cpi     0ffh
        jnz     self_fail_console
        mvi     a,JROMCONCONFIGQUERY
        call    JCGCONCONFIGADDR
        mov     a,d
        ora     a
        jnz     self_fail_console
        lda     0d5d2h
        cmp     b
        jnz     self_fail_console
        lda     0d5d3h
        cmp     c
        jnz     self_fail_console

        lda     0d5d1h
        mov     c,a
        lda     0d5d0h
        mov     b,a
        mvi     a,JROMCONCONFIGSET
        call    JCGCONCONFIGADDR
        ora     a
        jnz     self_fail_console
        mvi     a,JROMCONCONFIGQUERY
        call    JCGCONCONFIGADDR
        lda     0d5d0h
        cmp     b
        jnz     self_fail_console
        lda     0d5d1h
        cmp     c
        jnz     self_fail_console
        mov     a,d
        cpi     JROMCONOVERRIDEVIDEO+JROMCONOVERRIDELOCALE
        jnz     self_fail_console
.ifndef ABI_C12_KEEP_OVERRIDE
        mvi     a,JROMCONCONFIGDEFAULT
        call    JCGCONCONFIGADDR
        ora     a
        jnz     self_fail_console
        mvi     a,JROMCONCONFIGQUERY
        call    JCGCONCONFIGADDR
        mov     a,d
        ora     a
        jnz     self_fail_console
.endif
.endif

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
.ifdef ROM_ABI_LOCALE
        mvi     a,0c4h                  ; ISO-8859-1 Estonian A-diaeresis
        call    JCGCONOUTADDR
        cpi     0c4h
        jnz     self_fail_console
.endif
.ifdef ROM_ABI_EXTENDED
        lxi     h,0d5d0h
        mvi     m,'Q'
        inx     h
        mvi     m,'!'
        dcx     h
        lxi     b,2
        call    JCGCONBLOCKADDR
        ora     a
        jnz     self_fail_console
.ifdef ABI_SOUND_SELFTEST
        mvi     a,1                     ; complete shared diagnostic phrase
.else
        xra     a                       ; bounded silence operation
.endif
        call    JCGSOUNDADDR
        ora     a
        jnz     self_fail_sound
.endif

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
.ifdef ROM_ABI_HOSTSERVICES
        ; Prove that selector/register dispatch preserves A into the resident
        ; feature configurator before any serial transaction is attempted.
        mvi     a,07fh
        mvi     c,JROMHOSTCONFIG
        call    JCGHOSTADDR
        lxi     h,ROMHOSTSTATEBASE
        mov     a,m
        cpi     1
        jnz     self_fail_info
        inx     h
        mov     a,m
        cpi     1
        jnz     self_fail_info

        mvi     c,8
self_diag_selector:
        mov     a,c
        push    b
        call    JCGDIAGADDR
        pop     b
        ora     a
        jnz     self_fail_diag
        dcr     c
        jnz     self_diag_selector
.endif
        lxi     h,0d7f0h                ; cleared/invalid request version
.ifdef ROM_ABI_HOSTSERVICES
        mvi     m,0
.endif
        call    JCGNETDISKADDR
        cpi     0ffh
        jnz     self_fail_netdisk
.ifdef ROM_ABI_EXTENDED
        lxi     h,0d7efh                ; zero descriptors is invalid
        mvi     m,0
        call    JCGNETMULTIADDR
        cpi     0ffh
        jnz     self_fail_netdisk
        lxi     h,0d580h
        mvi     m,2                     ; two successful bounded descriptors
        inx     h
        mvi     m,1
        inx     h
        mvi     m,JROMNETOPINVALIDATE
        lxi     h,0d58bh                ; second descriptor (+1 count +10)
        mvi     m,1
        inx     h
        mvi     m,JROMNETOPINVALIDATE
        lxi     h,0d580h
        call    JCGNETMULTIADDR
        ora     a
        jnz     self_fail_netdisk
.endif

.ifndef ROM_ABI_C12
        call    JCGKEYINITADDR
        ora     a
        jnz     self_fail_keyboard
.endif
.ifdef ROM_ABI_EXTENDED
        call    JCGKEYRAWADDR
        jc      self_fail_keyboard
.ifdef ROM_ABI_RAW_FIXED
.ifdef ABI_RAW_SHIFT_F8
        cpi     14                      ; Shift-F8 ordinary column
        jnz     self_fail_keyboard
        mov     a,b
        cpi     08eh                    ; SHIFT low + row-5 contact
        jnz     self_fail_keyboard
        jmp     self_keyboard_done
.else
.ifdef ABI_RAW_CTRL_UP
        cpi     10                      ; Ctrl-Up/Home ordinary column
        jnz     self_fail_keyboard
        mov     a,b
        cpi     06ah                    ; CTRL low + row-6 contact + S21
        jnz     self_fail_keyboard
        jmp     self_keyboard_done
.else
        cpi     4                       ; uppercase T's ordinary column
        jnz     self_fail_keyboard
.endif
.endif
.else
        cpi     15
        jnc     self_fail_keyboard
.endif
.ifndef ABI_RAW_SHIFT_F8
.ifndef ABI_RAW_CTRL_UP
        mov     a,b
        ani     0cfh                    ; uppercase T includes SHIFT
        cpi     0cfh
        jz      self_fail_keyboard
.endif
.endif
.endif
.ifdef ROM_ABI_LOCALE
.ifndef ROM_ABI_C12
        lxi     h,self_keyremap
        mvi     a,1
        call    JCGKEYREMAPADDR
        ora     a
        jnz     self_fail_keyboard
.endif
.endif
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
.ifdef ROM_ABI_LOCALE
        cpi     'X'
.else
        cpi     'T'
.endif
        jnz     self_fail_keyboard

self_keyboard_done:
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
.ifdef ROM_ABI_EXTENDED
        jmp     self_store_fail
self_fail_sound:
        mvi     a,0e9h
.endif
self_store_fail:
        sta     SELFSTATUS
        jmp     self_done

fill_guard:
        mov     m,a
        inx     h
        dcr     b
        jnz     fill_guard
        ret

.ifdef ROM_ABI_LOCALE
self_keyremap:
        db      'T','X'
.endif
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
.ifdef ROM_ABI_LOCALE
        call    RKCONFIG
        sta     ROMCONFIG
.ifdef ROM_ABI_C12
        sta     ROMACTIVECONFIG
        xra     a
        sta     ROMCONFIGFLAGS
.endif
.endif
        xra     a
        ret

rom_keyscan_impl:
        call    RKSTAT
        ora     a
        rz
        jmp     RKIN

.ifdef ROM_ABI_EXTENDED
; HL is a low-RAM byte span and BC is its length (1..256). One gate crossing
; commits the complete span while retaining the ordinary console renderer and
; control-character policy as the single behavioral implementation.
rom_conblock_impl:
        mov     a,b
        ora     c
        jz      rom_extended_bad
        mov     a,b
        ora     a
        jz      rom_conblock_bounds
        cpi     1
        jnz     rom_extended_bad
        mov     a,c
        ora     a
        jnz     rom_extended_bad        ; 0100h is the sole B=1 length
rom_conblock_bounds:
        mov     a,h
        cpi     0d8h
        jnc     rom_extended_bad
        push    h
        dad     b
        dcx     h
        mov     a,h
        cpi     0d8h
        pop     h
        jnc     rom_extended_bad
rom_conblock_loop:
        mov     a,m
        call    ROMCONOUT
        inx     h
        dcx     b
        mov     a,b
        ora     c
        jnz     rom_conblock_loop
        xra     a
        ret

; HL points to a count byte (1..8) followed by that many ordinary ten-byte
; NetDisk v1 request blocks. Descriptors may mix reads, synchronous writes,
; invalidations, and mode changes. They execute in order and stop on the first
; nonzero result, so write-through and cache invalidation semantics remain
; identical to the single-request ABI.
rom_netmulti_impl:
        mov     a,m
        ora     a
        jz      rom_extended_bad
        cpi     9
        jnc     rom_extended_bad
        mov     b,a
        inx     h
rom_netmulti_loop:
        push    b
        push    h
        call    rom_netdisk_impl
        pop     h
        pop     b
        ora     a
        rnz
        lxi     d,JROMNETREQBYTES
        dad     d
        dcr     b
        jnz     rom_netmulti_loop
        xra     a
        ret

rom_keyraw_impl:
        jmp     RKRAWSCAN

rom_sound_impl:
        ora     a
        jz      rom_sound_silence
        cpi     1
        jnz     rom_extended_bad
        call    smoke_play
        xra     a
        ret
rom_sound_silence:
        mvi     a,050h                  ; D57 ch1, LSB-only, mode 0
        out     PITCTL
        mvi     a,1                     ; static high = silence
        out     019h
        xra     a
        ret

rom_extended_bad:
        mvi     a,0ffh
        stc
        ret

        include "smoke-player.asm"
        include "smoke-table.asm"
.endif

.ifdef ROM_ABI_HOSTSERVICES
rom_diag_impl:
        ora     a
        jz      rom_diag_marker
        dcr     a
        jz      diag_cpu_test
        dcr     a
        jz      rom_diag_memory
        dcr     a
        jz      rom_diag_address
        dcr     a
        jz      rom_diag_retention
        dcr     a
        jz      rom_diag_checksum
        dcr     a
        jz      diag_pit_d57_test
        dcr     a
        jz      diag_usart_status_test
        dcr     a
        jz      rom_diag_post
        jmp     rom_unavailable
rom_diag_marker:
        mvi     a,0a5h
        ret
rom_diag_memory:
        lxi     h,0d5c0h
        lxi     d,0d5e0h
        jmp     diag_memory_test
rom_diag_address:
        lxi     h,0d5c0h
        mvi     a,5
        jmp     diag_memory_address_test
rom_diag_retention:
        lxi     h,0d5c0h
        lxi     b,04000h
        jmp     diag_memory_retention_test
rom_diag_checksum:
        lxi     h,0d800h
        lxi     d,00000h
        jmp     diag_checksum8
rom_diag_post:
        lda     0d610h
        ret
.else
rom_diag_impl:
        ora     a
        jnz     rom_unavailable
        mvi     a,0a5h
        ret
.endif

rom_getinfo_impl:
        lxi     h,JROMABIBASE
        lxi     d,FEATURES
        ret

.ifdef ROM_ABI_LOCALE
; Return raw S21 in A, video bits 2:1 in B, and locale bits 4:3 in C.
rom_config_impl:
        lda     ROMCONFIG
        mov     d,a
        rrc
        ani     3
        mov     b,a
        mov     a,d
        rrc
        rrc
        rrc
        ani     3
        mov     c,a
        mov     a,d
        ret

.ifdef ROM_ABI_C12
; A selects query (0), set B=video/C=character bank (1), or reset to the
; latched S21 default (2). Validation completes before any state or pixels
; change. Calls are synchronous with interrupts disabled under the ROM ABI,
; so console writers observe either the complete old or complete new state.
rom_conconfig_impl:
        ora     a
        jz      rom_conconfig_query
        dcr     a
        jz      rom_conconfig_set
        dcr     a
        jz      rom_conconfig_default
        jmp     rom_extended_bad
rom_conconfig_set:
        mov     a,b
        cpi     4
        jnc     rom_extended_bad
        mov     a,c
        cpi     4
        jnc     rom_extended_bad
        lda     ROMCONFIG
        ani     0e1h                    ; retain reserved bits and boot bit
        mov     e,a
        mov     a,b
        add     a                       ; video in bits 2:1
        ora     e
        mov     e,a
        mov     a,c
        add     a
        add     a
        add     a                       ; character bank in bits 4:3
        ora     e
        sta     ROMACTIVECONFIG
        call    rom_conconfig_flags
        jmp     rom_conconfig_apply
rom_conconfig_default:
        lda     ROMCONFIG
        sta     ROMACTIVECONFIG
        xra     a
        sta     ROMCONFIGFLAGS
rom_conconfig_apply:
        call    ROMCONINIT              ; hide/reset cursor, timing, full clear
        ; Keep the persistent JCGKEYREMAP table. RKINIT would also clear its
        ; count, so reset only debounce and pending translated-key state.
        xra     a
        sta     ROMKEYSTATEBASE
        sta     ROMKEYSTATEBASE+1
        sta     ROMKEYSTATEBASE+2
        xra     a                       ; explicit ABI success result
        ret
rom_conconfig_flags:
        lda     ROMACTIVECONFIG
        mov     e,a
        lda     ROMCONFIG
        xra     e
        mov     e,a
        mvi     d,0
        ani     006h
        jz      rom_conconfig_locale_flag
        mvi     d,JROMCONOVERRIDEVIDEO
rom_conconfig_locale_flag:
        mov     a,e
        ani     018h
        jz      rom_conconfig_store_flags
        mov     a,d
        ori     JROMCONOVERRIDELOCALE
        mov     d,a
rom_conconfig_store_flags:
        mov     a,d
        sta     ROMCONFIGFLAGS
        ret
rom_conconfig_query:
        lda     ROMACTIVECONFIG
        mov     e,a
        rrc
        ani     3
        mov     b,a
        mov     a,e
        rrc
        rrc
        rrc
        ani     3
        mov     c,a
        lda     ROMCONFIGFLAGS
        mov     d,a
        lda     ROMCONFIG
        ora     a                       ; success and carry clear
        ret
.endif

rom_keyremap_impl:
        call    RKSETREMAP
        xra     a
        ret

; Reset handoff for the network-only image. C9 makes network boot
; unconditional and reserves S21 bit 0. C5--C8 retain the concealed local-N
; recovery gate byte-for-byte.
rom_boot_policy_impl:
        call    JCGINITADDR
        ora     a
        jnz     rom_boot_policy_halt
.ifdef ROM_ABI_C9
        jmp     rom_boot_policy_network
.else
        call    JCGCONFIGADDR
        ani     1
        jnz     rom_boot_policy_network
        call    JCGKEYINITADDR
rom_boot_policy_wait_n:
        call    JCGKEYSCANADDR
        cpi     'N'
        jz      rom_boot_policy_network
        cpi     'n'
        jnz     rom_boot_policy_wait_n
.endif
rom_boot_policy_network:
        jmp     00100h
rom_boot_policy_halt:
        hlt
        jmp     rom_boot_policy_halt
.endif

rom_unavailable:
        mvi     a,0ffh
        stc
        ret

.ifdef ROM_ABI_HOSTSERVICES
.ifdef ROM_ABI_C12
build_identity:
        db      'JukuNet C12 ROM ABI 1.5 runtime console 2026-09-04',0
.else
.ifdef ROM_ABI_C11
build_identity:
        db      'JukuNet C11 ROM ABI 1.4 deterministic POST raster 2026-08-29',0
.else
.ifdef ROM_ABI_C10
build_identity:
        db      'JukuNet C10 ROM ABI 1.4 physical POF release 2026-08-27',0
.else
.ifdef ROM_ABI_C9
build_identity:
        db      'JukuNet C9 ROM ABI 1.4 bounded resident host 2026-08-26',0
.else
build_identity:
        db      'JukuNet C8 ROM ABI 1.3 resident host services 2026-08-20',0
.endif
.endif
.endif
.endif
.else
.ifdef ROM_ABI_EXTENDED
build_identity:
        db      'Juku network ROM ABI 1.2 complete services 2026-08-17',0
.else
.ifdef ROM_ABI_LOCALE
build_identity:
        db      'Juku network ROM ABI 1.1 locale candidate 2026-08-17',0
.else
build_identity:
        db      'Juku network ROM ABI 1.0 automatic boot 2026-08-16',0
.endif
.endif
.endif

.ifdef ROM_ABI_HOSTSERVICES
        ; C12 uses some of the former pre-diagnostic slack. Older variants
        ; still align diagnostics at EC00h; C12 continues immediately and is
        ; bounded together with diagnostics by the hard F000h assertion.
        .if     $ < 0ec00h
        dc      0ec00h-$,0ffh
        .endif
DIAG_PIT_CONTROL equ   PITCTL
DIAG_PIT_COUNT0 equ    PITCOUNT0
DIAG_USART_CONTROL equ USARTCTL
        include "cpu.asm"
        include "memory.asm"
        include "memory-address.asm"
        include "memory-retention.asm"
        include "checksum.asm"
        include "pit-d57.asm"
        include "usart-status.asm"
        .if     $ > 0f000h
        .error  "Resident core and diagnostics exceed D800h..EFFFh"
        .endif
        dc      0f000h-$,0ffh
.endif

.ifdef ROM_ABI_LOCALE
; F000h..F7FFh holds ABI 1.1 console extensions and locale banks. S21 bits
; 2:1 select the same four proven geometries as the shared RAM console.
        org     0f000h
RCSETVIDEO:
.ifdef ROM_ABI_C12
        lda     ROMACTIVECONFIG
.else
        lda     ROMCONFIG
.endif
        rrc
        ani     3
        sta     RCVIDMODE
        ora     a
        jz      RCMODE40
        dcr     a
        jz      RCMODE53
        dcr     a
        jz      RCMODE64
RCMODE80:
        mvi     a,80
        sta     RCCOLS
        mvi     a,24
        sta     RCTEXTROWS
        mvi     a,5
        sta     RCCELLWIDTH
        mvi     a,8
        sta     RCCELLHEIGHT
        mvi     a,0f8h
        sta     RCCELLMASK
        mvi     a,49
        sta     RCVIDSTEP
        lxi     h,400
        shld    RCROWBYTES
        lxi     h,0d990h
        shld    RCSCROLLSOURCE
        lxi     h,350
        shld    RCCURSORLINE
        lxi     h,9200
        shld    RCSCROLLBYTES
        mvi     a,073h
        out     017h
        mvi     a,014h
        out     011h
        mvi     a,003h
        out     012h
        mvi     a,01ah
        out     015h
        mvi     a,001h
        out     015h
        mvi     a,045h
        out     016h
        ret
RCMODE40:
        mvi     a,40
        sta     RCCOLS
        mvi     a,8
        sta     RCCELLWIDTH
        mvi     a,0ffh
        sta     RCCELLMASK
        jmp     RCMODESTOCK
RCMODE53:
        mvi     a,53
        sta     RCCOLS
        mvi     a,6
        sta     RCCELLWIDTH
        mvi     a,0fch
        sta     RCCELLMASK
RCMODESTOCK:
        mvi     a,24
        sta     RCTEXTROWS
        mvi     a,10
        sta     RCCELLHEIGHT
        mvi     a,39
        sta     RCVIDSTEP
        lxi     h,400
        shld    RCROWBYTES
        lxi     h,0d990h
        shld    RCSCROLLSOURCE
        lxi     h,360
        shld    RCCURSORLINE
        lxi     h,9200
        shld    RCSCROLLBYTES
        mvi     a,024h
        out     011h
        mvi     a,008h
        out     012h
        mvi     a,072h
        out     015h
        xra     a
        out     015h
        mvi     a,025h
        out     016h
        ret
RCMODE64:
        mvi     a,64
        sta     RCCOLS
        mvi     a,20
        sta     RCTEXTROWS
        mvi     a,6
        sta     RCCELLWIDTH
        mvi     a,10
        sta     RCCELLHEIGHT
        mvi     a,0fch
        sta     RCCELLMASK
        mvi     a,47
        sta     RCVIDSTEP
        lxi     h,480
        shld    RCROWBYTES
        lxi     h,0d9e0h
        shld    RCSCROLLSOURCE
        lxi     h,432
        shld    RCCURSORLINE
        lxi     h,9120
        shld    RCSCROLLBYTES
        mvi     a,016h
        out     011h
        mvi     a,004h
        out     012h
        mvi     a,012h
        out     015h
        mvi     a,001h
        out     015h
        mvi     a,045h
        out     016h
        ret

; Sparse lookups return DE at seven text rows or eight edge-connected
; pseudographic rows and A=row count.
RCFONTLOOKUP:
        mov     e,a
.ifdef ROM_ABI_C12
        lda     ROMACTIVECONFIG
.else
        lda     ROMCONFIG
.endif
        rrc
        rrc
        rrc
        ani     3
        cpi     1
        jz      RCFONTEST
        cpi     2
        jz      RCFONTRUS
        jmp     RCFONTPSEUDOTRY
RCFONTEST:
        lxi     h,RAMFONTESTONIANCODES
        mvi     b,8
        call    RCFONTFIND
        jc      RCFONTPSEUDOTRY
        lxi     h,RAMFONTESTONIAN
        jmp     RCFONTPTR7
RCFONTRUS:
        lxi     h,RAMFONTCP866CODES
        mvi     b,66
        call    RCFONTFIND
        jc      RCFONTPSEUDOTRY
        lxi     h,RAMFONTCP866
        jmp     RCFONTPTR7
RCFONTPSEUDOTRY:
        lxi     h,RAMFONTPSEUDOCODES
        mvi     b,17
        call    RCFONTFIND
        rc
        lxi     h,RAMFONTPSEUDO
        xchg
        mov     l,c
        mvi     h,0
        dad     h
        dad     h
        dad     h
        dad     d
        xchg
        mvi     a,8
        ora     a
        ret
RCFONTPTR7:
        xchg
        mov     l,c
        mvi     h,0
        mov     c,l
        mvi     b,0
        dad     h
        dad     h
        dad     b
        dad     b
        dad     b
        dad     d
        xchg
        mvi     a,7
        ora     a
        ret
; E=encoded byte, HL=code table, B=count; C=index on success.
RCFONTFIND:
        mvi     c,0
RCFONTFIND1:
        mov     a,e
        cmp     m
        jz      RCFONTFOUND
        inx     h
        inr     c
        dcr     b
        jnz     RCFONTFIND1
        stc
        ret
RCFONTFOUND:
        ora     a
        ret

CREEP_PSEUDO_ONLY equ  1
        include "creep-console-font.asm"
        include "locale-console-fonts.asm"
        .if     $ > 0f800h
        .error  "Locale console exceeds F000h..F7FFh"
        .endif
        dc      0f800h-$,0ffh
.endif

.ifdef ROM_ABI_C9
; C8's resident host nearly fills E500h..E7FFh. C9 keeps that immutable
; envelope unused and places the successor implementation in the otherwise
; empty ROM tail, without adding a direct vector or expanding the RAM gate.
        org     0f800h
        include "rom-host-services.asm"
        .if     $ > JROMABIBASE
        .error  "Resident host exceeds F800h..FEFFh"
        .endif
        dc      JROMABIBASE-$,0ffh
.else

        dc      JROMABIBASE-$,0ffh
.endif

        db      'J','U','K','U','A','B','I',0
        db      JROMABIMAJOR,JROMABIMINOR
        dw      JROMABISIZE
        dw      FEATURES
        dw      build_identity
        dw      JROMRAMEND-JROMRAMBASE
        dw      JROMHELPERBYTES
.ifdef ROM_ABI_HOSTSERVICES
        dc      JROMMANIFESTEND-1-$,0ffh
resident_checksum_balance:
        db      0
.else
        dc      JROMMANIFESTEND-$,0ffh
.endif

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
.ifdef ROM_ABI_EXTENDED
        jmp     rom_sound_impl
.else
        jmp     rom_unavailable
.endif
        jmp     rom_diag_impl
        jmp     rom_getinfo_impl
.ifdef ROM_ABI_LOCALE
        jmp     rom_config_impl
        jmp     rom_keyremap_impl
        jmp     rom_boot_policy_impl
.endif
.ifdef ROM_ABI_EXTENDED
        jmp     rom_conblock_impl
        jmp     rom_netmulti_impl
        jmp     rom_keyraw_impl
.endif
.ifdef ROM_ABI_HOSTSERVICES
        jmp     rom_host_impl
.endif
.ifdef ROM_ABI_C12
        jmp     rom_conconfig_impl
.endif

        .if     $ > 10000h
        .error  "ROM ABI manifest and vectors exceed FF00h..FFFFh"
        .endif
        dc      10000h-$,0ffh
        end     resident_entry
