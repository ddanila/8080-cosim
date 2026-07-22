# Jukuravi diagnostic firmware

Status date: 2026-07-23.

Status: **D0 RUNGS 1–5C SIMULATION CHECKPOINT — D27/PPI GUARDED**

All images below are directly burnable Jukuravi images for the D15 2764
socket. Each is exactly 8,192 bytes and maps to CPU `0x0000..0x1FFF`; D16 is
not read by these checkpoints. `diag-d0-alive.bin` isolates rung 1,
`diag-d0-cpu.bin` adds rung 2, `diag-d0-usart-local.bin` isolates the local
D11/8251 test, `diag-d0-serial.bin` adds the external framed handshake,
`diag-d0-ram.bin` adds the mode-0 48 KiB serial RAM survey,
`diag-d0-ram-fallback.bin` adds the beep-only fixed-window fallback,
`diag-d0-romcheck.bin` adds the historical ROM block-1 convention self-test,
`diag-d0-pic.bin` adds the D10/8259 interrupt-mask register test, and
`diag-d0-ppi.bin` adds the safe D27/8255 all-port register test.

SHA256:

```text
dfd4327b2752a143fdbd4c199013e53dfb9dc2b9ea897379f3015b4cda92ec9c  diag-d0-alive.bin
a9ca9d59a2a23891b90eb088e1b6901cc210baca30dc03c46c900048efdb67ec  diag-d0-cpu.bin
c708f78adc9b87ba6dfc926314f3937798814d79f1e66512c9ae8d1db8b03a7f  diag-d0-usart-local.bin
e9bebf4cbcca4556a779eef3fcb42f69706892df28a2cc93fc1f3a5d235eb2e0  diag-d0-serial.bin
50f35da507947232c2e2ab0e7b6ab519f3ce16e8310c4c1f02d544b504149baf  diag-d0-ram.bin
96a9417e4dc3a9270671d76b85500727d8a519c76ff977f15fd48e9f3076c8fc  diag-d0-ram-fallback.bin
d102a6320f9446e103ab34a07b73ddca72907163a9444c061efdccbd47841da5  diag-d0-romcheck.bin
65d84269bcd0d2859e31ca343e3640899c3179b0af6404e184a53a304b1b9496  diag-d0-pic.bin
c75fc47b4966532c67794a317ab23b0e75c32977acb799d3e08a94d53baf2685  diag-d0-ppi.bin
```

## Build and guard

```sh
python3 spinoffs/jukuravi/firmware/build_d0_alive.py --check
python3 spinoffs/jukuravi/firmware/build_d0_cpu.py --check
python3 spinoffs/jukuravi/firmware/build_d0_usart_local.py --check
python3 spinoffs/jukuravi/firmware/build_d0_serial.py --check
python3 spinoffs/jukuravi/firmware/build_d0_ram.py --check
python3 spinoffs/jukuravi/firmware/build_d0_ram_fallback.py --check
python3 spinoffs/jukuravi/firmware/build_d0_romcheck.py --check
python3 spinoffs/jukuravi/firmware/build_d0_pic.py --check
python3 spinoffs/jukuravi/firmware/build_d0_ppi.py --check
sync/jukuravi_d0_check.sh
```

The builders are the sources of truth and deterministically emit the committed
images. The alive-only executed code is 30 bytes. The combined CPU image
contains 382 bytes; the local-USART image contains 509; the serial image
contains 684; the RAM-survey image contains 1,496; the fallback image contains
1,967; the ROM-convention, PIC, and PPI builder spans are each 2,066 bytes. Their
identities are stored at `0x1F00`, and unused space is fail-closed
`HLT` fill.

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

## Rung 4a: serial mode-0 RAM survey

The RAM image changes the banner ROM version to `02` and self-checksum to
`12B6`:

```text
banner:    A5 5A 01 04 01 02 12 B6 97
ack:       A5 5A 81 04 01 02 12 B6 7B
RAM_BEGIN: A5 5A 10 04 01 40 FF 01 51
RAM_BLOCK: A5 5A 11 02 page failure-mask crc
RAM_END:   A5 5A 12 02 40 FF 35
```

After the exact predecessor handshake and short serial-confirmed beep, the ROM
replays the source-guarded Ekta 3.7 D54/D55 initialization so autonomous video
timing supplies the board's available DRAM activity. It remains in reset memory
mode 0 and surveys `0x4000..0xFFFF`; the ROM-covered low 16 KiB stays deferred
until uploaded code can run from proven RAM.

Each 256-byte page receives five address-complete write passes and five
address-complete read passes. It fills `00`, performs read-before-write
transitions `00 -> FF -> L -> ~L -> 55`, waits approximately 20 ms using BC
only, then verifies retained `55`. The `L/~L` pair exposes low-address aliasing.
A second register-only probe writes a page-specific sentinel at offset `00`,
perturbs and restores every other page's offset `00`, and verifies the sentinel
after each perturbation, exposing high-address page aliasing without changing
the final `55` fill. Every mismatch is XORed with the expected value and ORed
into D, producing one eight-bit failure mask per page: bit 0 names D84, through
bit 7 naming D91. Healthy and failed pages execute identical traffic—1,664
writes per page, with five full 256-byte read passes plus 191 cross-page reads—
and every page emits exactly one CRC-protected `RAM_BLOCK`. No result is stored
in the RAM under test, no stack instruction is used, interrupts stay disabled,
and mode 0 is never changed.

`spinoffs/jukuravi/protocol.py` validates the complete ordered record set,
groups bad page numbers by DRAM bit/chip, and selects the largest contiguous
all-eight-bits-good page window. A pristine stream yields `0x4000..0x10000`;
the guarded sample fault at `0x7A5C` yields bad page `7A` for bits 3/D87 and
5/D89 and selects the larger good window `0x7B00..0x10000`. Mapping logical
page `90` onto page `50` makes exactly those two pages report `FF` and selects
`0x9100..0x10000`.

`tests/jukuravi_d0_ram_test.py` executes the exact 8 KiB burn image through a
PTY over all 192 pages. It proves every clean mask, exact full-range traffic,
the final `55` pattern, the D54/D55 write sequence, CRC framing, terminal state,
and host window verdict. A second run uses
`JUKU_RAM_FAULT=7A5C:08:20` (address, stuck-low mask, stuck-high mask) and
requires only page `7A` to report `28`. A third run uses
`JUKU_RAM_ALIAS=50:90` and requires exactly pages `50` and `90` to report
`FF`, proving that the advertised window cannot hide a page-address alias.
The full vm80a top executes the same loop body on a one-page time-bounded
fixture through the bit-sliced D84–D91
models: clean RAM reports `00`, while a D87 cell forced low reports `08`.
Both HDL paths perform exactly 1,282 physical writes and 1,280 reads, receive
the ACK through X3/D104/D11, emit all expected frames, retain mode 0, and never
enable interrupts. Its fixture shortens the three register delays and changes
only the survey and alias-probe end-page immediates from `FF` to `40`; the
memory-test and framing opcodes are identical to the burn image.

## Rung 4b: serial-dead fixed-window fallback

The cumulative fallback image advertises ROM version `03`, self-checksum
`9FCC`, and these exact handshake records:

```text
banner: A5 5A 01 04 01 03 9F CC 45
ack:    A5 5A 81 04 01 03 9F CC A9
```

A matching ACK retains the complete rung-4a 192-page framed survey. A missing
or malformed ACK, or a later result-transport timeout, instead selects the
stack-free fallback. It first gives a finite approximately 0.25-second nominal
125 Hz serial-dead marker, replays the D54/D55 timing initialization, and then
wholesale-tests `0x4000..0x4FFF` and `0xC000..0xCFFF`. Each 4 KiB candidate
gets five complete writes and reads using `00`, `FF`, address, inverse-address,
and `55`, followed by the same approximately 20 ms retention verification.
Only two bits in E record whether the fixed candidates passed; no result or
working state is trusted to the RAM being tested.

The audible vocabulary is now executable and unambiguous by cadence:

| Outcome | D57 channel-1 code |
| --- | --- |
| alive | one approximately 0.5 s nominal 1 kHz beep |
| CPU bad | continuous nominal 250 Hz |
| ROM block-1 checksum bad | continuous nominal 2 kHz after the alive beep |
| PIC mask-register bad | continuous nominal 4 kHz after the alive beep |
| D27 PPI register bad | continuous nominal 750 Hz after the alive beep |
| local USART bad | continuous nominal 500 Hz |
| serial confirmed | one approximately 0.125 s nominal 2 kHz beep |
| serial dead before fallback | one approximately 0.25 s nominal 125 Hz marker |
| one or both fixed windows found | three short nominal 2 kHz pulses, then silence |
| no fixed window | 1–8 short nominal 1 kHz pulses naming D84–D91's first bad bit, then continuous nominal 125 Hz |

One chip-ID pulse means D84/bit 0 and eight mean D91/bit 7. The continuous tail
makes “no window” distinct even if the human misses the count; reset repeats
the complete sequence. A fully dead chip therefore cannot be mistaken for an
address-local usable window.

`tests/jukuravi_d0_ram_fallback_test.py` proves the exact burn image's normal
ACK path still emits and decodes all 192 page records. With no ACK, pristine
RAM produces flags `03` and the three-pulse windows-found code. A single-cell
fault in the first candidate produces flags `02` and the same found verdict,
proving that either window suffices. A final no-ACK run uses
`JUKU_RAM_FAULT=*:08:00` to model D87 globally stuck low; both fixed windows
fail, four chip-ID pulses identify D87, and the ROM reaches continuous 125 Hz.
All paths execute identical 20,480 writes and 20,480 reads per fixed window.
The full vm80a fixture shortens each window to one page and only
compresses register counts; clean and forced-D87 paths each perform 2,560
physical writes and reads through D84–D91, check all banner/timer/cadence
operations, retain mode 0 and IFF clear, and reach their distinct terminal
states.

## Rung 5a: historical ROM block-1 convention

The next cumulative image advertises ROM version `04`, full-image
self-checksum `1198`, and these exact handshake records:

```text
banner: A5 5A 01 04 01 04 11 98 98
ack:    A5 5A 81 04 01 04 11 98 74
```

It also adopts and executes EktaSoft's own early-ROM integrity convention:
byte `0x000A` stores the eight-bit additive sum of bytes
`0x000B..0x07FF`. The exact diagnostic value is `CF`. Reset now executes
`JMP 0010h` over the reserved header. After the alive beep and proven CPU
signature, a stack-free loop reads all 2,037 covered bytes through D15, compares
the computed sum with `0x000A`, and only then begins the local USART test. A
mismatch programs a continuous nominal 2 kHz tone and halts before any USART,
PPI, RAM, or memory-mode write.

This layout is source-compatible rather than merely checksum-equivalent. All
five official repository EktaSoft images use the same bounds and pass with
stored values `7B`, `D3`, `8F`, `EE`, and `1A` for versions 2.4, 3.1, 3.2,
3.5, and 3.7. The diagnostic's banner and ACK tables start exactly at
`0x0800`, outside the additive block, so the historical sum and framed
full-image CRC have no circular dependency. The CRC-16 still covers the stored
`CF`; only its own four payload copies and two derived frame CRC bytes retain
the previously documented zeroing rule.

The runtime verdict intentionally claims only that historical block, not an
independent readback of all 8 KiB. Every diagnostic instruction after the
reset header fits below `0x0800`; later bytes contain protocol/identity data
and fail-closed fill, while the host-visible CRC-16 names the exact complete
burn image.

`tests/jukuravi_d0_romcheck_test.py` proves the exact burn image against the
five official headers, re-runs both the acknowledged 192-page survey and the
no-ACK clean fallback, and flips the fail-closed byte at `0x07FF`. The corrupt
image executes exactly 2,037 checksum-loop iterations, transmits nothing,
writes no RAM, and reaches only the continuous 2 kHz ROM-fail halt. The vm80a
fixture shortens only the alive delay and regenerates its stored block sum;
clean D15 data reaches the first post-check USART recovery write, while the
same `0x07FF` bit flip reaches the ROM-fail tone with zero RAM writes. Both
paths retain mode 0, IFF clear, and the `D0` CPU signature.

## Rung 5b: D10/8259 interrupt-mask register

The cumulative PIC image advertises ROM version `05`, historical block-1 sum
`01`, full-image self-checksum `0FEA`, and these exact records:

```text
banner: A5 5A 01 04 01 05 0F EA 2B
ack:    A5 5A 81 04 01 05 0F EA C7
```

After the CPU and ROM checks, it writes the real EktaSoft MCS-80 initialization
pair `D6` to command port `00` and `FE` to data port `01`. It then writes and
reads back IMR masks `00` and `FF`, so every mask bit is exercised in both
polarities and both PIC register selects participate. Success writes `FF`
again before continuing to D11. Any mismatch also writes `FF` before selecting
a continuous nominal 4 kHz PIC-bad tone and halting. The 8080 IFF remains
clear throughout, so the deliberately brief `00` test mask cannot dispatch an
interrupt even if an external request is already active.

The tighter version-5 header jumps directly to `000B`; all executable bytes,
including the PIC recovery path, still end below `0800`, and the framed tables
still begin exactly at `0800`. `tests/jukuravi_d0_pic_test.py` proves the exact
burn image's acknowledged 192-page survey and no-ACK clean fallback, then uses
`JUKU_PIC_FAULT=STUCK_LOW:STUCK_HIGH` to force both mismatch polarities. Both
fault cases transmit nothing, touch no RAM or memory-mode bit, retain the `D0`
CPU signature, and finish with the active mask restored to `FF`. The vm80a
fixture shortens only the alive delay and regenerates its block sum; clean and
forced-low D10 readback paths prove the exact command/data traffic, terminal
mask, and distinct 4 kHz path through `juku_top`.

This is intentionally an IMR and register-decode test, not a claim about the
whole 8259. It does not enable CPU interrupts or exercise IRR/ISR selection,
priority resolution, external IR inputs, INTR, the three INTA cycles, or the
MCS-80 `CALL` vector. Those behaviors already have separate boot/frame-interrupt
guards and remain a physical bring-up boundary for this ROM-only checkpoint.

## Rung 5c: D27/8255 all-port register test

The cumulative PPI image advertises ROM version `06`, historical block-1 sum
`23`, full-image self-checksum `1C68`, and these exact records:

```text
banner: A5 5A 01 04 01 06 1C 68 79
ack:    A5 5A 81 04 01 06 1C 68 95
```

This rung requires the X2 auxiliary connector to be disconnected. After the
CPU, ROM, and PIC checks, it writes D27 control `80` (mode 0, all ports output)
and writes/reads `00` then `FF` on ports A, B, and C at `0C..0E`. Every data
bit and all four D27 register selects therefore participate. Both success and
failure finish by writing control `9B` (mode 0, all ports input), then writing
zero to A/B/C to clear the hidden output latches while the pins remain inputs.
A mismatch stops before D11 or RAM and selects the continuous nominal 750 Hz
PPI-bad tone. The D10 mask remains `FF` and the CPU IFF remains clear; this is
also important because D27 PB7 shares the D10 IR1 path.

The version-6 profile fits this test below `0800` by sharing one complete RAM
march body between the two beep-fallback windows. The burn image still performs
the same five writes, five reads, retention interval, per-window verdicts, and
final `55` contents as rung 4b. Builder metadata now names all six loop counts,
five page rewinds, and the first-window end sentinel together, preventing a
shortened HDL fixture from changing the shared loop's control flow.

`tests/jukuravi_d0_ppi_test.py` proves the exact image's acknowledged 192-page
survey, clean/second-only/dead-chip fallback results, complementary D27 stuck
polarities, exact port traffic, and safe terminal state. Cosim accepts only
`JUKU_PPI_FAULT=PORT:STUCK_LOW:STUCK_HIGH` for D27 data ports `0C..0E`.
The vm80a fixtures separately prove the early clean and forced Port-C-low
branches, then replay the shared fallback through both physical candidate
windows for clean and forced-D87 outcomes with exact traffic and cadence.

This is a D27 register/latch/decode check, not an electrical test of X2 or its
external loads, handshake modes, drive strength, or contention behavior. Keep
X2 disconnected for this image; connector and cable tests require a controlled
harness after the register-only checkpoint.

Broader row/column-shaped fault generators and the user-facing session CLI
remain later host-tool work; rung 4's required serial and beep-only RAM paths
are now both represented by exact burn images.

The same command runs `sync/beeper_check.sh`, whose HDL PIT model proves that
D57 OUT1 toggles and whose connectivity guard traces `D57.13/SOUND` through the
analog handoff. Cosim does not yet synthesize the PIT waveform, and neither
guard models speaker voltage/current or authorizes a bench burn. The next D0
firmware rung is the remaining PIT register-wiggle test. Its prerequisite is
now explicit and regression-guarded: both twins implement the 8253
counter-latch command and the programmed LSB/MSB read sequence, while
`JUKU_PIT_FAULT=PORT:STUCK_LOW:STUCK_HIGH` is restricted to the nine D54/D55/D57
counter ports. Cosim intentionally leaves live count progression to HDL because
the board uses distinct 1 MHz, 2 MHz, 1.23 MHz, and cascaded clocks. The ROM
must therefore use a phase-tolerant count predicate rather than compare an
exact free-running 16-bit value.
