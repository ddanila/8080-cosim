; Loader-callable wrapper for the shared Juku 8080 CPU diagnostic.
;
; Run in all-RAM mode at 4000h. The result byte at 4E00h is zero on success
; or a structured CPU failure mask. The caller's SP is restored before return.

        org     04000h

start:
        call    diag_cpu_test
        sta     04e00h
        xra     a
        ret

        include "cpu.asm"

        end     start
