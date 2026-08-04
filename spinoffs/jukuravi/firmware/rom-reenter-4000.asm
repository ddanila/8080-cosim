; Control for the T31 upper-ROM instruction-fetch experiment.
;
; Load at 4000h and invoke in loader API v2 JUMP mode. This transfers directly
; from RAM to T31's loader entry without fetching any instruction from the
; upper 1000h..1FFFh half of D15. A physical success here followed by failure
; of rom-exec-106f.bin isolates the fault to the upper-ROM fetch path.

bits 16
org 04000h

    db 0c3h                 ; JMP 0A0Ch
    dw 00a0ch
