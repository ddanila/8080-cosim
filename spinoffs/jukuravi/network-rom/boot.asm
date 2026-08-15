; Reset-visible skeleton for the network-first Juku ROM.
; Generated layout constants are supplied by build_network_rom.py.
        include "rom-abi.inc"
        include "network-rom-generated.inc"

MODEPORT        equ     006h
TRANSITION      equ     JROMRAMBASE

        org     0
        jmp     boot_start
        db      'JUKU NETWORK ROM ABI SKELETON',0

boot_start:
        di
        lxi     sp,0d5f0h

        lxi     d,GATESTORED
        lxi     h,JROMGATEBASE
        lxi     b,JROMGATEBYTES
        call    copy_bytes

        lxi     d,HELPSTORED
        lxi     h,JROMHELPBASE
        lxi     b,JROMHELPERBYTES
        call    copy_bytes

        lxi     d,transition_source
        lxi     h,TRANSITION
        lxi     b,transition_end-transition_source
        call    copy_bytes
        jmp     TRANSITION

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
        mvi     a,1
        out     MODEPORT
        jmp     0d800h
transition_end:
        end

