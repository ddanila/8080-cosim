; Play the shared four-bar diagnostic phrase, report completion, and return
; cooperatively to the T31 monitor.
;
; Load at 4000h and invoke through loader API v2 CALL mode. The shared player
; touches only D57 channel 1; T31 restores its channel-0 UART timer on return.
;
; Completion contract:
;   A = 0Ch
;   4100h..4103h = "SMOK"
;   4104h = 00h
;   ordinary RET returns to T31

        org     04000h

start:
        call    smoke_play

        lxi     h,04100h
        mvi     m,'S'
        inx     h
        mvi     m,'M'
        inx     h
        mvi     m,'O'
        inx     h
        mvi     m,'K'
        inx     h
        mvi     m,0
        mvi     a,12
        ret

        include "smoke-player.asm"
        include "smoke-table.asm"

        end     start
