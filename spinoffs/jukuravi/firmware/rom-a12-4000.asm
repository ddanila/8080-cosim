; Non-destructive D15 A12/read-path diagnostic for the T31 monitor.
;
; Load at 4000h and invoke through loader API v2 CALL mode. The snippet runs
; entirely from RAM, computes CRC-16/CCITT-FALSE over both 4 KiB halves of D15,
; then samples 16 lower/upper address pairs eight times. It does not write ROM
; or change the memory map.
;
; Result at 4200h:
;   00..03  "A12R"
;   04      format version 1
;   05      sample passes (8)
;   06..07  CRC16 of 0000h..0FFFh, big-endian (T31 expects 8B80h)
;   08..09  CRC16 of 1000h..1FFFh, big-endian (T31 expects D581h)
;   0A      samples per pass (32: lower then upper for each pair)
;   0B      A5h when complete
;   0C      passes remaining (zero when complete)
;   0D..0F  reserved zero
;   10..10F eight consecutive 32-byte sample vectors
;
; If A12 is stuck low, the upper-half CRC will equal 8B80h and each upper
; sample will equal its paired lower sample. Correct, stable reads instead
; produce the two expected CRCs and identical sample vectors on all passes.

bits 16
org 04000h

RESULT      equ 04200h
SAMPLES     equ RESULT + 010h
PASSES      equ 8
PAIR_COUNT  equ 16

start:
    db 021h                 ; LXI H,RESULT
    dw RESULT
    db 036h, 'A'            ; MVI M,'A'
    db 023h, 036h, '1'      ; INX H / MVI M,'1'
    db 023h, 036h, '2'      ; INX H / MVI M,'2'
    db 023h, 036h, 'R'      ; INX H / MVI M,'R'
    db 023h, 036h, 001h     ; version
    db 023h, 036h, PASSES
    db 023h, 036h, 000h     ; lower CRC high
    db 023h, 036h, 000h     ; lower CRC low
    db 023h, 036h, 000h     ; upper CRC high
    db 023h, 036h, 000h     ; upper CRC low
    db 023h, 036h, PAIR_COUNT * 2
    db 023h, 036h, 000h     ; completion marker
    db 023h, 036h, PASSES   ; passes remaining
    db 023h, 036h, 000h
    db 023h, 036h, 000h
    db 023h, 036h, 000h

    db 021h                 ; LXI H,0000h
    dw 00000h
    db 00eh, 010h           ; MVI C,10h: stop when H reaches 10h
    db 0cdh                 ; CALL crc_range
    dw crc_range
    db 07ah, 032h           ; MOV A,D / STA RESULT+6
    dw RESULT + 6
    db 07bh, 032h           ; MOV A,E / STA RESULT+7
    dw RESULT + 7

    db 021h                 ; LXI H,1000h
    dw 01000h
    db 00eh, 020h           ; MVI C,20h: stop when H reaches 20h
    db 0cdh                 ; CALL crc_range
    dw crc_range
    db 07ah, 032h           ; MOV A,D / STA RESULT+8
    dw RESULT + 8
    db 07bh, 032h           ; MOV A,E / STA RESULT+9
    dw RESULT + 9

    db 011h                 ; LXI D,SAMPLES
    dw SAMPLES

sample_pass:
    db 021h                 ; LXI H,address_table
    dw address_table

sample_next:
    db 04eh                 ; MOV C,M: address low
    db 023h                 ; INX H
    db 046h                 ; MOV B,M: address high
    db 023h                 ; INX H
    db 078h, 0feh, 0ffh     ; MOV A,B / CPI FFh: table terminator
    db 0cah                 ; JZ sample_pass_done
    dw sample_pass_done
    db 0e5h                 ; PUSH H: preserve table pointer
    db 060h, 069h           ; MOV H,B / MOV L,C
    db 07eh                 ; MOV A,M: read D15
    db 012h                 ; STAX D: save sample
    db 013h                 ; INX D
    db 0e1h                 ; POP H
    db 0c3h                 ; JMP sample_next
    dw sample_next

sample_pass_done:
    db 03ah                 ; LDA RESULT+0Ch
    dw RESULT + 00ch
    db 03dh                 ; DCR A
    db 032h                 ; STA RESULT+0Ch
    dw RESULT + 00ch
    db 0c2h                 ; JNZ sample_pass
    dw sample_pass

    db 03eh, 0a5h           ; MVI A,A5h
    db 032h                 ; STA RESULT+0Bh
    dw RESULT + 00bh
    db 0afh                 ; XRA A: return A=00h
    db 0c9h                 ; RET to T31

; Input: HL=start, C=end high byte. Output: DE=CRC16/CCITT-FALSE.
crc_range:
    db 011h                 ; LXI D,FFFFh
    dw 0ffffh

crc_byte:
    db 07eh                 ; MOV A,M
    db 0aah                 ; XRA D: byte enters the CRC high byte
    db 057h                 ; MOV D,A
    db 006h, 008h           ; MVI B,8

crc_bit:
    db 07bh, 0b7h, 017h     ; MOV A,E / ORA A / RAL
    db 05fh                 ; MOV E,A
    db 07ah, 017h, 057h     ; MOV A,D / RAL / MOV D,A
    db 0d2h                 ; JNC crc_no_xor
    dw crc_no_xor
    db 07bh, 0eeh, 021h     ; MOV A,E / XRI 21h
    db 05fh                 ; MOV E,A
    db 07ah, 0eeh, 010h     ; MOV A,D / XRI 10h
    db 057h                 ; MOV D,A

crc_no_xor:
    db 005h                 ; DCR B
    db 0c2h                 ; JNZ crc_bit
    dw crc_bit
    db 023h                 ; INX H
    db 07ch, 0b9h           ; MOV A,H / CMP C
    db 0c2h                 ; JNZ crc_byte
    dw crc_byte
    db 0c9h                 ; RET

; Lower address followed by its A12-high counterpart. Every pair differs in
; the exact T31 image; two pairs differ in all eight data bits.
address_table:
    dw 00000h, 01000h
    dw 00003h, 01003h
    dw 00017h, 01017h
    dw 00018h, 01018h
    dw 00029h, 01029h
    dw 0004eh, 0104eh
    dw 00062h, 01062h
    dw 00072h, 01072h
    dw 00100h, 01100h
    dw 00209h, 01209h
    dw 0040ah, 0140ah
    dw 00800h, 01800h
    dw 0098bh, 0198bh
    dw 00ff0h, 01ff0h
    dw 00ff2h, 01ff2h
    dw 00fffh, 01fffh
    dw 0ffffh
