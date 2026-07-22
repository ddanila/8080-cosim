# Jukuravi diagnostic firmware

Status date: 2026-07-23.

Status: **D0 RUNGS 1–3B SIMULATION CHECKPOINT — FRAMED EXTERNAL HANDSHAKE GUARDED**

All images below are directly burnable Jukuravi images for the D15 2764
socket. Each is exactly 8,192 bytes and maps to CPU `0x0000..0x1FFF`; D16 is
not read by these checkpoints. `diag-d0-alive.bin` isolates rung 1,
`diag-d0-cpu.bin` adds rung 2, `diag-d0-usart-local.bin` isolates the local
D11/8251 test, and `diag-d0-serial.bin` adds the external framed handshake.

SHA256:

```text
dfd4327b2752a143fdbd4c199013e53dfb9dc2b9ea897379f3015b4cda92ec9c  diag-d0-alive.bin
a9ca9d59a2a23891b90eb088e1b6901cc210baca30dc03c46c900048efdb67ec  diag-d0-cpu.bin
c708f78adc9b87ba6dfc926314f3937798814d79f1e66512c9ae8d1db8b03a7f  diag-d0-usart-local.bin
e9bebf4cbcca4556a779eef3fcb42f69706892df28a2cc93fc1f3a5d235eb2e0  diag-d0-serial.bin
```

## Build and guard

```sh
python3 spinoffs/jukuravi/firmware/build_d0_alive.py --check
python3 spinoffs/jukuravi/firmware/build_d0_cpu.py --check
python3 spinoffs/jukuravi/firmware/build_d0_usart_local.py --check
python3 spinoffs/jukuravi/firmware/build_d0_serial.py --check
sync/jukuravi_d0_check.sh
```

The builders are the sources of truth and deterministically emit the committed
images. The alive-only executed code is 30 bytes. The combined CPU image
contains 382 bytes; the local-USART image contains 509; the serial image
contains 684. Their identities are stored at `0x1F00`, and unused space is
fail-closed `HLT` fill.

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

## Rung 3a: local 8251 transmit-state self-test

The local-USART image first sends the standard recovery sequence (`00 00 00
40`) to D11's control register, then selects asynchronous x16, 8 data bits, no
parity, one stop bit (`4E`) and enables Tx/Rx, DTR, RTS, and error reset (`37`).
It requires idle status `05`, writes a `55` test byte while D57 channel 0 is
stopped and requires holding-full status `00`, then starts that channel in
binary mode 2 with divisor 8. The source-proved nominal 1.23 MHz input divided
by 8 and the USART's x16 mode gives approximately 9600 baud.

Two BC-only `FFFF` timeouts bound the wait for `TxRDY` and `TxEMPTY`. The first
must end at status `01`, proving the holding byte entered an active shifter;
the second must end at `05`, proving the frame completed. A complete failed
wait is 3,342,295 CPU T-states, nominally 1.6711475 seconds at 2 MHz. Any
initial, intermediate, final, or timeout mismatch selects a continuous
nominal 500 Hz USART-bad tone (D57 channel 1 divisor 4000), distinct from the
short 1 kHz alive tone and continuous 250 Hz CPU-bad tone. Success halts after
the `55` byte reaches the transport. The [Intel 8251A datasheet](https://community.intel.com/cipcp26785/attachments/cipcp26785/programmable-devices/89914/1/P8251A.pdf)
requires active-low CTS before shifting, while the [TI MC1489 datasheet](https://www.ti.com/lit/ds/symlink/mc1489a.pdf)
specifies a high output for an open receiver input. The Nano/level-shifter harness
must therefore drive X3 CTS active before reset. This checkpoint needs no
received byte or ack: it proves the D11 host interface and D57/D11 clocked
transmit states under a known asserted CTS, but does not prove the outbound
line driver or an end-to-end serial link. An unplugged or non-asserting harness
correctly reaches the same bounded USART-stage failure code rather than hanging.

`tests/jukuravi_d0_usart_local_test.py` runs the exact burn image through a real
PTY (representing an attached harness with CTS asserted), checks status `05 ->
00 -> 01 -> 05`, and receives exactly `55`. It then
uses the cosim `JUKU_USART_FAULT=tx_stuck` injection to exhaust the complete
timeout and select the 500 Hz path, and separately corrupts the predecessor
CPU signature comparison to prove it still selects 250 Hz before any USART
access. The full vm80a `juku_top` executes the same three outcomes; its fault
fixture shortens only the timeout count and its common fixture shortens only
the half-second alive delay. Because the physical merge feeding `xtal16m_w`
remains a documented continuity boundary, that upstream rail alone is driven
by the testbench and X3 CTS is explicitly asserted; D104, D103 /13, D57 channel
0 mode 2/divisor 8, and the D11 TxC/RxC path remain integrated. The guard
also proves that deliberately inactive X3 CTS takes the bounded 500 Hz path,
then observes at least ten resulting baud edges, exact I/O, IFF clear, and zero
RAM writes. All paths remain free of CALL, RET, PUSH, POP, and memory-writing
instructions.

## Rung 3b: external framed handshake

The serial image preserves all predecessor tests, counts their first `55` as
the first byte of a 16-byte training run, and then emits this self-delimiting
record:

```text
A5 5A | type | length | payload | CRC-8/ATM
banner: A5 5A 01 04 01 01 60 7A 4F
ack:    A5 5A 81 04 01 01 60 7A A3
```

The banner payload is protocol version `01`, ROM version `01`, and big-endian
ROM self-checksum `607A`. CRC-8/ATM uses polynomial `07`, initial value `00`,
no reflection, and xor-out `00`, over type through payload. The shared
`spinoffs/jukuravi/protocol.py` decoder discards noise or a corrupt candidate
and resumes at the next `A5 5A`, so a host that attaches after reset can regain
record alignment without session state.

The self-checksum is CRC-16/CCITT-FALSE (polynomial `1021`, initial `FFFF`, no
reflection, xor-out `0000`) across the entire 8,192-byte burn image. Its four
stored checksum-byte copies and the two frame-CRC bytes derived from them are
treated as zero during that calculation, explicitly avoiding direct and
indirect fixed-point definitions. All other bytes—including executable code,
identity, framing fields, and `HLT` fill—are covered. The ACK repeats the exact
banner payload under type `81`; firmware compares all nine bytes.

Every transmit wait, the final `TxEMPTY` wait, and every expected ACK byte use
a fresh BC-only `FFFF` bound. A valid ACK selects a short nominal 2 kHz,
approximately 0.125-second serial-confirmed beep and silence. Timeout or any
wrong ACK byte selects a continuous nominal 125 Hz serial-dead tone, distinct
from the continuous 500 Hz local-USART and 250 Hz CPU fault tones. The image
reads immutable protocol tables from ROM through HL but never writes memory,
uses the reset `SP` for nothing, and never enables interrupts.

`tests/jukuravi_d0_serial_test.py` connects the exact image to a PTY, decodes
the banner with the shared stream parser, sends its ACK, and checks the short
confirmation path. It separately proves a corrupt ACK CRC, the complete ACK
timeout, a stuck local transmitter, and the predecessor CPU fault, including
exact output, terminal tones, unchanged `SP=0`, and zero RAM writes. The full
vm80a `juku_top` fixture sends valid and corrupt ACK bits through X3 `SIN` and
D104 into D11 and also proves timeout; it checks all 25 transmitted bytes,
all nine received bytes where applicable, the physical baud chain, exact
terminal path, IFF clear, and zero memory writes. Generated HDL fixtures
shorten only the initial/confirmed tone delays and the timeout-case ACK count.

The same command runs `sync/beeper_check.sh`, whose HDL PIT model proves that
D57 OUT1 toggles and whose connectivity guard traces `D57.13/SOUND` through the
analog handoff. Cosim does not yet synthesize the PIT waveform, and neither
guard models speaker voltage/current or authorizes a bench burn. The next
firmware rung is the stack-free mode-0 RAM survey and framed result stream.
