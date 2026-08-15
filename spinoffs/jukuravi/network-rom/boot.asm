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
        lxi     d,CORESTORED
        lxi     h,00100h
        lxi     b,JROMCOREBYTES
        call    copy_bytes
.endif

        lxi     d,transition_source
        lxi     h,TRANSITION
        lxi     b,transition_end-transition_source
        call    copy_bytes
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
post_halt:
        hlt
        jmp     post_halt

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
        jmp     0e600h
.else
        jmp     00100h
.endif
transition_end:

        include "cpu.asm"
        include "memory.asm"
        include "memory-address.asm"
        include "checksum.asm"
        end
