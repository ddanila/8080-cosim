; Minimal mode-3 framebuffer helper used to prove the ROM/RAM crossing.
; This skeleton is replaced by the packed console paint/clear/scroll helper.
        include "rom-abi.inc"

MODEPORT        equ     006h
VRAM            equ     0d800h
HELPCHAR        equ     JROMSTATEBASE+0
HELPMODE        equ     JROMSTATEBASE+1
HELPREADBACK    equ     JROMSTATEBASE+2

        org     JROMHELPBASE

JROMHELPENTRY:
        push    psw
        push    b
        push    d
        push    h
        sta     HELPCHAR
        in      MODEPORT
        ani     0fch
        ori     1
        sta     HELPMODE
        ani     0fch
        ori     3
        out     MODEPORT
        lda     HELPCHAR
        sta     VRAM
        lda     VRAM
        sta     HELPREADBACK
        lda     HELPMODE
        out     MODEPORT
        pop     h
        pop     d
        pop     b
        pop     psw
        ret

JROMHELPEND:
        end

