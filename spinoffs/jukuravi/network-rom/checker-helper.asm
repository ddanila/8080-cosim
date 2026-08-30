; C11 low-RAM deterministic POST checkerboard helper.
; Copyright (c) 2026 Danila Sukharev
; BSD-2-Clause; see ../../../third_party/juku-common/LICENSE-BSD-2-Clause.
;
; Mode 3 hides the reset ROM, so boot.asm copies this bounded helper to D400h
; after POST and calls it from RAM.  The stock boot raster is 320x241 pixels:
; forty bytes per scanline and 241 scanlines.

MODEPORT        equ     006h
VRAM            equ     0d800h

        org     0d400h

checker_entry:
        in      MODEPORT
        ani     0fch
        ori     3
        out     MODEPORT
        lxi     h,VRAM
        mvi     d,241
        mvi     e,0ffh
        mvi     c,8
checker_row:
        mvi     b,40
        mov     a,e
checker_byte:
        mov     m,a
        cma
        inx     h
        dcr     b
        jnz     checker_byte
        dcr     c
        jnz     checker_next
        mov     a,e
        cma
        mov     e,a
        mvi     c,8
checker_next:
        dcr     d
        jnz     checker_row
        in      MODEPORT
        ani     0fch
        out     MODEPORT
        ret

checker_end:
        end
