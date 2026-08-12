; Loader-callable wrapper for the shared Juku RAM cell diagnostic.
;
; Run in all-RAM mode at 4000h. The result byte at 4E00h is zero on success
; and contains accumulated mismatch bits on failure. The tested page is
; restored before return.

        org     04000h

start:
        lxi     h,05000h
        lxi     d,05100h
        call    diag_memory_test
        sta     04e00h
        xra     a
        ret

        include "memory.asm"

        end     start
