; Loader-callable wrapper for the shared Juku RAM diagnostic mechanisms.
;
; Run in all-RAM mode at 4000h. Results are written at 4E00h:
;   +0 byte-cell/data-bit mismatch mask
;   +1 address-alias boolean
;   +2 retention data-bit mismatch mask
;   +3 additive checksum of the restored page
; The tested page is restored before return.

        org     04000h

start:
        lxi     h,05000h
        lxi     d,05100h
        call    diag_memory_test
        sta     04e00h

        lxi     h,05000h
        mvi     a,8
        call    diag_memory_address_test
        sta     04e01h

        lxi     h,05000h
        lxi     b,0100h
        call    diag_memory_retention_test
        sta     04e02h

        lxi     h,05000h
        lxi     d,05100h
        call    diag_checksum8
        sta     04e03h
        xra     a
        ret

        include "memory.asm"
        include "memory-address.asm"
        include "memory-retention.asm"
        include "checksum.asm"

        end     start
