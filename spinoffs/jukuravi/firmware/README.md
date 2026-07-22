# Jukuravi diagnostic firmware

Status date: 2026-07-22.

Status: **D0 RUNGS 1–2 SIMULATION CHECKPOINT — ALIVE BEEP AND CPU SELF-TEST GUARDED**

Both images below are directly burnable Jukuravi images for the D15 2764
socket. Each is exactly 8,192 bytes and maps to CPU `0x0000..0x1FFF`; D16 is
not read by either checkpoint. `diag-d0-alive.bin` isolates rung 1, while
`diag-d0-cpu.bin` includes that same alive sequence followed by rung 2.

SHA256:

```text
dfd4327b2752a143fdbd4c199013e53dfb9dc2b9ea897379f3015b4cda92ec9c  diag-d0-alive.bin
a9ca9d59a2a23891b90eb088e1b6901cc210baca30dc03c46c900048efdb67ec  diag-d0-cpu.bin
```

## Build and guard

```sh
python3 spinoffs/jukuravi/firmware/build_d0_alive.py --check
python3 spinoffs/jukuravi/firmware/build_d0_cpu.py --check
sync/jukuravi_d0_check.sh
```

The two builders are the sources of truth and deterministically emit the
committed images. The alive-only executed code is 30 bytes. The combined CPU
image contains 382 bytes of code and a `JUKURAVI-D0-CPU-1` identity at
`0x1F00`. Unused space is fail-closed `HLT` fill.

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

`tests/jukuravi_d0_alive_test.py` runs the alive image from reset in cosim and requires
the exact five PIT writes and timing, `HLT` at `0x001D`, unchanged `SP=0`, IFF
clear, mode 0, and no RAM write.

## Rung 2: register-only CPU self-test

The combined image folds 17 independently listed results into an 8-bit rolling
signature seeded with `A5`; the expected terminal value is `D0`. It exercises
ADD/ADC, SUB/SBB, AND/XOR/OR, preserving-A CMP, all four rotates, carry-preserving
INR/DCR, and both non-carry and carry-producing DAA cases. Conditional branches
check the expected sign, zero, carry, and parity state along the way, including
that rotates preserve Z/S/P, so a final signature match cannot hide a wrong flag
that would corrupt later diagnostics.

On success the CPU halts with the signature in A and E. Any intermediate flag
failure or the final signature mismatch branches to a continuous, lower
CPU-bad tone: D57 channel 1 mode 3 with divisor 8000, nominally 250 Hz from the
source-proved 2 MHz input. The whole path contains no CALL, RET, PUSH, POP, or
memory-writing instruction and executes with interrupts disabled.

`tests/jukuravi_d0_cpu_test.py` proves the burn image's success path and then
flips only its expected-signature byte to force the CPU-bad path. Both runs
require exact PIT writes, the terminal signature, IFF clear, mode 0, unchanged
cosim `SP=0`, and zero RAM writes. `hdl/sim/jukuravi_d0_cpu_tb.v` independently
executes both paths through the vm80a-based `juku_top`, checks the architectural
signature and I/O sequence, and observes no memory write. Its generated fixture
shortens only the rung-1 register delay from 41,667 iterations to one so the HDL
test remains bounded; every CPU-test and terminal-path byte is identical to the
burn image. The physical core's reset SP is undefined, so the HDL contract is
the instruction/memory-write guarantee rather than a particular SP value.

The same command runs `sync/beeper_check.sh`, whose HDL PIT model proves that
D57 OUT1 toggles and whose connectivity guard traces `D57.13/SOUND` through the
analog handoff. Cosim does not yet synthesize the PIT waveform, and neither
guard models speaker voltage/current or authorizes a bench burn. The next
firmware rung is the local 8251 self-test and serial handshake.
