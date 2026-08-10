; Measure effective 8080 speed against the host's monotonic clock.
;
; Upload once at 4000h, then CALL 4000h for a one-iteration baseline and 4006h
; for the long sample.  Both entry paths have identical LXI/JMP overhead.  The
; long call executes exactly 50,000 additional iterations of the
; DCX B / MOV A,B / ORA C / JNZ loop, or 1,200,000 additional 8080 T-states.
; Subtracting the loader's recorded RUN-ack-to-RETURN intervals cancels its
; fixed recovery and wire overhead.  This probe performs no I/O and is safe
; when D57 or another peripheral has already reported a fault.

bits 16
org 04000h

baseline:
    db 001h
    dw 1
    db 0C3h
    dw measure

long_sample:
    db 001h
    dw 50001
    db 0C3h
    dw measure

measure:
    db 00Bh, 078h, 0B1h
    db 0C2h
    dw measure
    db 0AFh
    db 0C9h
