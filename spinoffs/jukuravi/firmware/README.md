# Jukuravi diagnostic firmware

Status date: 2026-07-22.

Status: **D0 RUNG 1 SIMULATION CHECKPOINT — ALIVE BEEP GUARDED**

`diag-d0-alive.bin` is the first directly burnable Jukuravi image for the D15
2764 socket. It is exactly 8,192 bytes and maps to CPU `0x0000..0x1FFF`; D16 is
not read by this checkpoint.

SHA256:

```text
dfd4327b2752a143fdbd4c199013e53dfb9dc2b9ea897379f3015b4cda92ec9c  diag-d0-alive.bin
```

## Build and guard

```sh
python3 spinoffs/jukuravi/firmware/build_d0_alive.py --check
sync/jukuravi_d0_check.sh
```

`build_d0_alive.py` is the source of truth and deterministically emits the
committed image. The executed code is 30 bytes; unused space is fail-closed
`HLT` fill, with `JUKURAVI-D0-ALIVE-1` identification at offset `0x0100`.

The reset path is deliberately stack-free and RAM-free:

```text
0000  MVI A,76h       ; D57 channel 1, LSB+MSB, binary mode 3
0002  OUT 1Bh
0004  MVI A,D0h       ; divisor 2000 = 07D0h
0006  OUT 19h
0008  MVI A,07h
000A  OUT 19h
000C  LXI B,A2C3h     ; 41,667-iteration register-only delay
000F  DCX B
0010  MOV A,B
0011  ORA C
0012  JNZ 000Fh
0015  MVI A,50h       ; channel 1, LSB-only, binary mode 0
0017  OUT 1Bh
0019  MVI A,01h       ; static high after one PIT input clock = silence
001B  OUT 19h
001D  HLT
```

At the source-proved nominal 2 MHz D57 channel-1 clock, mode 3 divisor 2000 is
a 1 kHz tone. The register loop holds it for 1,000,035 8080 T-states, nominally
0.5000175 seconds at a 2 MHz CPU clock. Those are nominal design values, not a
claim that the unresolved physical oscillator/divider error is already known.
The Nano's planned OUT1 measurement will determine the actual fitted-board
clock from the known divisor.

`tests/jukuravi_d0_alive_test.py` runs the image from reset in cosim and requires
the exact five PIT writes and timing, `HLT` at `0x001D`, unchanged `SP=0`, IFF
clear, mode 0, and no RAM write. The same command runs `sync/beeper_check.sh`,
whose HDL PIT model proves that D57 OUT1 toggles and whose connectivity guard
traces `D57.13/SOUND` through the analog handoff. Cosim does not yet synthesize
the PIT waveform, and neither guard models speaker voltage/current or authorizes
a bench burn. The next firmware rung is the register-only CPU self-test and its
distinct failure beep.
