; Measure effective 8080 speed while keeping T35's DRAM refreshed.
;
; Upload once at 4000h, then CALL 4000h for a one-iteration baseline and 4006h
; for the long sample. Every iteration calls T35's public refresh primitive,
; then executes the same 24-T-state counter loop used by the T34 timebase.
; The enabled refresh call costs 17 + 2115 T-states including CALL, so the
; 500 additional iterations contribute exactly 500 * 2156 = 1,078,000
; nominal T-states. Subtracting the paired host intervals still cancels the
; fixed loader and wire overhead without allowing the long sample to decay RAM.

bits 16
org 04000h

REFRESH equ 007A9h

baseline:
    db 001h
    dw 1
    db 0C3h
    dw measure

long_sample:
    db 001h
    dw 501
    db 0C3h
    dw measure

measure:
    db 0CDh
    dw REFRESH
    db 00Bh, 078h, 0B1h
    db 0C2h
    dw measure
    db 0AFh
    db 0C9h
