; Direct-ROM entry core for CP/Mish Fastboot V15 / NetDisk v3.
;
; This is the readable, specialized form of CP/Mish's one-record V15 core.
; The ekta4402 `N` command copies its padded 128-byte image to 0100h and jumps
; there, eliminating stock Janet from the path.  Keep it byte-identical to the
; first record of cpmish/juku-fastboot-v15-netdisk-v3.bin.

USARTDATA       equ     008h
USARTCTL        equ     009h
PITCOUNT0       equ     018h
PITCTL          equ     01bh
EXTENSION       equ     0300h
EXTENSION_SIZE  equ     010bh

        org     0100h

        jmp     start
        db      'J','F','1','5'
        db      1,0
        dw      EXTENSION_SIZE

start:
        di
        lxi     sp,03ff0h

        mvi     a,015h          ; D57 ch0 mode 2, LSB, BCD, count 4
        out     PITCTL
        mvi     a,4
        out     PITCOUNT0

        xra     a               ; canonical D11 reset, then x16/8N1
        out     USARTCTL
        out     USARTCTL
        out     USARTCTL
        mvi     a,040h
        out     USARTCTL
        mvi     a,04eh
        out     USARTCTL
        mvi     a,035h
        out     USARTCTL

session:
find_first:
        call    rx
        cpi     0a5h
        jnz     find_first
find_second:
        call    rx
        cpi     03ah
        jz      header_found
        cpi     0a5h            ; overlapping A5 is another first byte
        jz      find_second
        jmp     find_first
header_found:
        mvi     a,0c5h          ; extension-header acknowledgement
        out     USARTDATA

        lxi     h,EXTENSION
        lxi     b,EXTENSION_SIZE
        xra     a
        mov     d,a             ; Fletcher sum2
        mov     e,a             ; Fletcher sum1
receive_extension:
        call    rx
        mov     m,a
        inx     h
        add     e
        aci     0
        mov     e,a
        add     d
        aci     0
        mov     d,a
        dcx     b
        mov     a,b
        ora     c
        jnz     receive_extension
        call    rx
        cmp     e
        jnz     session
        call    rx
        cmp     d
        jnz     session
        jmp     EXTENSION

rx:
        in      USARTCTL
        ani     2
        jz      rx
        in      USARTDATA
        ret

core_end:
        end     start
