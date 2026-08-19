; Reset-visible skeleton for the network-first Juku ROM.
; Generated layout constants are supplied by build_network_rom.py.
        include "rom-abi.inc"
        include "network-rom-generated.inc"

MODEPORT        equ     006h
PPI0CONTROL     equ     007h
PPI1CONTROL     equ     00fh
PICCOMMAND      equ     000h
PICMASK         equ     001h
USARTCTL        equ     009h
PIT54COUNT0     equ     010h
PIT54COUNT1     equ     011h
PIT54COUNT2     equ     012h
PIT54CONTROL    equ     013h
PIT55COUNT0     equ     014h
PIT55COUNT1     equ     015h
PIT55COUNT2     equ     016h
PIT55CONTROL    equ     017h
PITCOUNT0       equ     018h
PITCOUNT2       equ     01ah
PITCTL          equ     01bh
TRANSITION      equ     JROMRAMBASE
POSTSTATUS      equ     JROMRAMBASE+010h
.ifdef ROM_ABI_LOCALE
BOOTSTAGE       equ     JROMRAMBASE+011h
BOOTRETRIES     equ     JROMRAMBASE+012h
BOOTPROTOCOL    equ     JROMRAMBASE+013h
.endif

        org     0
        jmp     boot_start
        db      'JUKU NETWORK ROM ABI1 AUTOBOOT',0
        org     03fh
rom_checksum_balance:
        db      0                       ; builder makes all 16 KiB sum to zero
        org     040h

boot_start:
        di
        lxi     sp,0d5f0h
        call    hardware_init
        xra     a
        sta     POSTSTATUS
.ifdef ROM_ABI_LOCALE
        sta     BOOTRETRIES
        mvi     a,010h                  ; reset/quick POST active
        sta     BOOTSTAGE
.ifdef ROM_ABI_EXTENDED
        mvi     a,16
.else
        mvi     a,15
.endif
        sta     BOOTPROTOCOL
.endif

        call    diag_cpu_test
        ora     a
        jnz     post_cpu_fail

        lxi     h,0d400h                ; scratch RAM, restored by the test
        lxi     d,0d500h
        call    diag_memory_test
        ora     a
        jnz     post_ram_fail

        lxi     h,0c000h                ; C000h plus A0..A11, below workspace
        mvi     a,12
        call    diag_memory_address_test
        ora     a
        jnz     post_address_fail

        lxi     h,00000h                ; complete ROM in reset view
        lxi     d,04000h
        call    diag_checksum8
        ora     a
        jnz     post_rom_fail

        ; Prove that D57's programmed count can be latched/read and that D11
        ; reaches its idle transmitter-ready state. The automatic V15 core
        ; repeats this initialization before it announces readiness.
        mvi     a,015h                  ; ch0, LSB, mode 2, BCD
        out     PITCTL
        mvi     a,4
        out     PITCOUNT0
        xra     a                       ; latch channel 0
        out     PITCTL
        in      PITCOUNT0
        ora     a                       ; live mode-2 count must be 1..4
        jz      post_io_fail
        cpi     5
        jnc     post_io_fail

        xra     a                       ; canonical 8251 reset sequence
        out     USARTCTL
        out     USARTCTL
        out     USARTCTL
        mvi     a,040h
        out     USARTCTL
        mvi     a,04eh                  ; x16, 8N1
        out     USARTCTL
        mvi     a,035h                  ; RxE, TxE, ER, RTS
        out     USARTCTL
        in      USARTCTL
        ani     005h                    ; TxRDY and TxEMPTY
        cpi     005h
        jnz     post_io_fail

        lxi     d,GATESTORED
        lxi     h,JROMGATEBASE
        lxi     b,JROMGATEBYTES
        call    copy_bytes

        lxi     d,HELPSTORED
        lxi     h,JROMHELPBASE
        lxi     b,JROMHELPERBYTES
        call    copy_bytes

.ifndef ABI_SELFTEST
.ifdef ROM_ABI_EXTENDED
        lxi     d,EMBEDSTORED
        lxi     h,00300h
        lxi     b,JROMEMBEDEXTBYTES
        call    copy_bytes
.endif
        lxi     d,CORESTORED
        lxi     h,00100h
        lxi     b,JROMCOREBYTES
        call    copy_bytes
.endif

        lxi     d,transition_source
        lxi     h,TRANSITION
        lxi     b,transition_end-transition_source
        call    copy_bytes
.ifdef ROM_ABI_LOCALE
        mvi     a,020h                  ; V15 core installed and entering
        sta     BOOTSTAGE
.endif
        jmp     TRANSITION

; Establish the same safe PPI and raster/refresh baseline used by EktaSoft
; before relying on DRAM for a network load. D26 mode 82h makes Port A/output,
; Port B/input and both Port C halves/output; BSR 0Fh leaves PC7 high (floppy
; control in the stock-safe state) while PC2 keeps the motor off and the low
; memory-mode bits remain reset view 0. The timer
; sequence is the observed stock D54/D55/D57 initialization; the compact MODX
; console may apply its six documented overrides after CP/M starts.
hardware_init:
        mvi     a,09bh
        out     PPI1CONTROL
        mvi     a,082h
        out     PPI0CONTROL
        mvi     a,00fh
        out     PPI0CONTROL

        mvi     a,015h
        out     PIT54CONTROL
        mvi     a,053h
        out     PIT54CONTROL
        mvi     a,093h
        out     PIT54CONTROL
        mvi     a,073h
        out     PIT55CONTROL
        mvi     a,093h
        out     PIT55CONTROL
        mvi     a,034h
        out     PIT55CONTROL

        mvi     a,039h
        out     PIT55COUNT0
        mvi     a,001h
        out     PIT55COUNT0
        mvi     a,01fh
        out     PITCTL
        mvi     a,076h
        out     PITCTL
        mvi     a,0b0h
        out     PITCTL
        mvi     a,064h
        out     PIT54COUNT0
        mvi     a,032h
        out     PITCOUNT0
        mvi     a,0ffh
        out     PITCOUNT2
        out     PITCOUNT2
        mvi     a,024h
        out     PIT54COUNT1
        mvi     a,008h
        out     PIT54COUNT2
        mvi     a,072h
        out     PIT55COUNT1
        xra     a
        out     PIT55COUNT1
        mvi     a,025h
        out     PIT55COUNT2

        mvi     a,0d6h                  ; stock MCS-80 CALL-vector ICW1
        out     PICCOMMAND
        mvi     a,0feh
        out     PICMASK                 ; ICW2
        mvi     a,0ffh
        out     PICMASK                 ; mask every source during POST/boot
        ret

post_cpu_fail:
        mvi     a,0c1h
        jmp     post_fail
post_ram_fail:
        mvi     a,0c2h
        jmp     post_fail
post_address_fail:
        mvi     a,0c3h
        jmp     post_fail
post_rom_fail:
        mvi     a,0c4h
        jmp     post_fail
post_io_fail:
        mvi     a,0c5h
post_fail:
        sta     POSTSTATUS
.ifdef ROM_ABI_HOSTSERVICES
; Repeat a fixed three-tone binary-style failure code. Bits 2..0 of C1..C5
; select long/short duration, so the audible series are SSL, SLS, SLL, LSS,
; and LSL respectively. The target remains in reset view with interrupts
; masked; successful boot and an absent network host never enter this path.
post_audio_repeat:
        lda     POSTSTATUS
        ani     00fh
        mov     d,a
        mvi     e,4
post_audio_tone:
        mvi     a,076h                  ; D57 ch1, mode 3
        out     PITCTL
        mvi     a,0eeh                  ; 5102 -> approximately G4
        out     019h
        mvi     a,013h
        out     019h
        mov     a,d
        ana     e
        mvi     h,1                     ; short = one unit
        jz      post_audio_length
        mvi     h,3                     ; long = three units
post_audio_length:
        call    post_audio_units
        mvi     a,050h                  ; silence between tones
        out     PITCTL
        mvi     a,1
        out     019h
        mvi     h,1
        call    post_audio_units
        mov     a,e
        rrc
        mov     e,a
        cpi     080h                    ; after mask 1 rotates to 80h
        jnz     post_audio_tone
        mvi     h,6                     ; long pause between series
        call    post_audio_units
        jmp     post_audio_repeat

post_audio_units:
        lxi     b,10000
post_audio_delay:
        dcx     b
        mov     a,b
        ora     c
        jnz     post_audio_delay
        dcr     h
        jnz     post_audio_units
        ret
.else
post_halt:
        hlt
        jmp     post_halt
.endif

copy_bytes:
        ldax    d
        mov     m,a
        inx     d
        inx     h
        dcx     b
        mov     a,b
        ora     c
        jnz     copy_bytes
        ret

; Executes from ordinary RAM while the overlay changes, then enters the same
; upper ROM byte which is remapped from file offset 1800h to CPU D800h.
transition_source:
        in      MODEPORT
        ani     0fch
        ori     1
        out     MODEPORT
.ifdef ABI_SELFTEST
.ifdef ROM_ABI_HOSTSERVICES
        jmp     0e800h
.else
        jmp     0e600h
.endif
.else
.ifdef ROM_ABI_LOCALE
        ; The copied stub cannot branch to its own link-time ROM addresses.
        ; Continue through a fixed upper-ROM vector after selecting mode 1.
        jmp     JROMBOOTPOLICY
.else
        jmp     00100h
.endif
.endif
transition_end:

        include "cpu.asm"
        include "memory.asm"
        include "memory-address.asm"
        include "checksum.asm"
        end
