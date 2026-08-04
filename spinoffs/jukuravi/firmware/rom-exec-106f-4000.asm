; Direct T31 upper-half instruction-fetch probe.
;
; Load at 4000h and invoke in loader API v2 JUMP mode. This RAM trampoline
; transfers control to T31 address 106Fh, whose exact bytes are C3 0C 0A
; (JMP 0A0Ch). Address 0A0Ch is T31's loader entry, so successful upper-ROM
; instruction fetch restarts the resident loader without a hardware RESET.

bits 16
org 04000h

    db 0c3h                 ; JMP 106Fh
    dw 0106fh
