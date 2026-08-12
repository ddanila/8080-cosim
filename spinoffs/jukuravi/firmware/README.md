# Jukuravi diagnostic firmware

## Shared mnemonic diagnostic

`shared-memory-4000.asm` is a loader-callable wrapper around the pinned
`juku-common/diag/memory.asm` source. Unlike the older NASM probes, its 8080
instructions are written as assembler mnemonics. It tests and restores
`5000h..50FFh`, writes the accumulated mismatch mask to `4E00h`, and returns.

Initialize the shared source and build with zmac in Intel 8080 mode:

```sh
git submodule update --init --recursive
python3 spinoffs/jukuravi/firmware/build_shared_memory.py
python3 spinoffs/jukuravi/firmware/build_shared_memory.py --check
cc -O2 -Wall -Wextra -o /tmp/jukuravi-shared-memory-test \
  tests/jukuravi_shared_memory_test.c cosim/i8080.c
/tmp/jukuravi-shared-memory-test \
  spinoffs/jukuravi/firmware/shared-memory-4000.bin
```

Set `ZMAC` to the zmac executable when it is not installed in `PATH`.

Status date: 2026-08-11.

Status: **T36 COMPLETE PHYSICAL RAM EVIDENCE + HISTORICAL D0/D2 LADDER**

All images below are directly burnable Jukuravi images for the D15 2764
socket. Each is exactly 8,192 bytes and maps to CPU `0x0000..0x1FFF`; D16 is
not read by these checkpoints. `diag-d0-alive.bin` isolates rung 1,
`diag-d0-cpu.bin` adds rung 2, `diag-d0-usart-local.bin` isolates the local
D11/8251 test, `diag-d0-serial.bin` adds the external framed handshake,
`diag-d0-ram.bin` adds the mode-0 48 KiB serial RAM survey,
`diag-d0-ram-fallback.bin` adds the beep-only fixed-window fallback,
`diag-d0-romcheck.bin` adds the historical ROM block-1 convention self-test,
`diag-d0-pic.bin` adds the D10/8259 interrupt-mask register test,
`diag-d0-ppi.bin` adds the safe D27/8255 all-port register test,
`diag-d0-pit.bin` adds the guarded D54/D55/D57 all-counter register test,
`diag-d0-framebuffer.bin` adds the surveyed-RAM framebuffer pattern, and
`diag-d2-loader.bin` continues from that clean path into the upload/run monitor.
`diag-d0-noserial.bin` is the cumulative bench variant that checks CPU, ROM,
PIC, PPI, and all PIT channels, then jumps directly to the two-window audible
RAM fallback without touching the 8251 or requiring CTS.
`diag-d0-pit-debug.bin` replaces the generic PIT-failure tone with an audible
number for the first failed counter/readback checkpoint.
`diag-d0-row-refresh.bin` / DOS `T36HOST.BIN` is the CS00024 successor: it
retains T34's clock-safe D55 test and corrects the fail-safe refresh sweep to
the physical MA0..MA6 row inputs. T35 is retained byte-exactly as the
physically falsified high-byte-sweep checkpoint.

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
b7ab8c3c5d7b32c5402510787216e099b0adbd37d64fb2c4a01f5695eb5401cf  diag-d0-pit.bin
d77c4a381440ed9166a24762b303c8ec0407e6d00c480a151a23c807234d7dd7  diag-d0-framebuffer.bin
5396f33244bfac5eae25404958afdcc4c0aac8a06255f7b11e20d2f0bcb0bedf  diag-d2-loader.bin
df553334c23a4167b5372f1d9c69d91af0a160c67cdf13b1f4fafab9267a8922  diag-d0-noserial.bin
ea52ef2cd3b56727d9c2d2d39cce2442e5faa247ccbb88fb51e91d10978ac22c  diag-d0-pit-debug.bin
ceb55556f11318dea5ef8c36b81f931813a139ce6ba6e07b607318571c6e1274  diag-d0-refresh.bin
32264641836ce914a0fc706c916e2847d542d83b05d6737f1d6272b76d78dedb  diag-d0-row-refresh.bin
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
python3 spinoffs/jukuravi/firmware/build_d0_pit.py --check
python3 spinoffs/jukuravi/firmware/build_d0_framebuffer.py --check
python3 spinoffs/jukuravi/firmware/build_d0_noserial.py --check
python3 spinoffs/jukuravi/firmware/build_d0_pit_debug.py --check
python3 spinoffs/jukuravi/firmware/build_d2_loader.py --check
python3 spinoffs/jukuravi/firmware/build_d0_refresh.py --check
python3 spinoffs/jukuravi/firmware/build_d0_row_refresh.py --check
sync/jukuravi_d0_check.sh
sync/jukuravi_t35_check.sh
sync/jukuravi_t36_check.sh
```

The builders are the sources of truth and deterministically emit the committed
images. The alive-only executed code is 30 bytes. The combined CPU image
contains 382 bytes; the local-USART image contains 509; the serial image
contains 684; the RAM-survey image contains 1,496; the fallback image contains
1,967; the ROM-convention, PIC, and PPI builder spans are each 2,066 bytes. The
PIT image spans 2,317 bytes because its guarded extension follows the framed
tables; the framebuffer image spans 2,392 bytes across two guarded extensions;
the loader image spans 3,012 bytes and adds a third guarded extension. Their
identities are stored at `0x1F00`, and unused space is fail-closed `HLT` fill.

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
| D54/D55/D57 PIT register bad | continuous nominal 1.5 kHz after the alive beep |
| surveyed framebuffer RAM bad | continuous nominal 3 kHz after the full serial survey |
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

## Rung 5d: D54/D55/D57 all-counter register test

> **Superseded for D55, 2026-08-09.** Versions `07..1B` use this historical
> predicate. It remains useful for directly clocked D54/D57 register paths,
> but it does not establish the D54/D56 clocks needed to transfer a Mode-0
> count into D55 before latching it. D55 results from these images are invalid
> as D55 fault evidence. T34 is the corrected test; see
> [`../../../docs/jukuravi-d55-diagnostic-audit.md`](../../../docs/jukuravi-d55-diagnostic-audit.md).

The cumulative PIT image advertises ROM version `07`, historical block-1 sum
`0E`, full-image self-checksum `1882`, and these exact records:

```text
banner: A5 5A 01 04 01 07 18 82 DE
ack:    A5 5A 81 04 01 07 18 82 32
```

Only 21 bytes remained below the historical table boundary at `0800`. The rung
uses 20 of them for a stack-free additive guard over a 251-byte extension at
`0812..090C`; its exact eight-bit sum is `8A`. The banner remains at `0800` and
the ACK at `0809`. A bad extension branches to the existing ROM-fail halt before
any PIT test, USART access, or RAM write, so moving executable code beyond the
historical block does not create an unchecked execution path.

For every counter port `10..12`, `14..16`, and `18..1A`, the extension selects
binary mode 0 with MSB-only access, writes `FF`, latches the count, reads it, and
requires DB7 high. It then repeats channel 0 on each chip with `3F` and requires
DB7 low. This exercises all nine counter selects, all three control selects, and
both DB7 polarities without comparing an exact live count. The original model
assumed the written value became immediately readable. That is acceptable for
the historical C-model regression, but not for D55 hardware: its cascaded
counting elements require source-clock transitions before latch/read.

Both verdicts recover D57 channels 1 and 2 to silent mode-0 count 1. Success then
continues into the existing local-USART setup, which immediately programs D57
channel 0. Failure instead programs channel 1 for the continuous nominal 1.5 kHz
PIT-bad tone (divisor 1333) and halts before USART or RAM. D54 and D55 retain
their test programming only until the already-guarded serial-success or fallback
timer initialization; no RAM is touched before that recovery.

`tests/jukuravi_d0_pit_test.py` proves the exact image, header sums, extension
guard, all-counter traffic, both injected DB7 mismatch polarities, acknowledged
192-page survey, and no-ACK fallback predecessors. Cosim accepts only
`JUKU_PIT_FAULT=PORT:STUCK_LOW:STUCK_HIGH` for the nine counter ports. The vm80a
fixture independently executes clean, forced-D55-DB7-high, and corrupted-
extension paths through all three physical PITs, then replays the cumulative
version-7 fixed-window fallback for clean and forced-D87 outcomes with exact
PIT-prefix traffic and cadence.

## Rung 5e: surveyed-RAM framebuffer pattern

The final D0 image advertises ROM version `08`, historical block-1 sum `B3`,
full-image self-checksum `8D59`, and these exact records:

```text
banner: A5 5A 01 04 01 08 8D 59 36
ack:    A5 5A 81 04 01 08 8D 59 DA
```

The acknowledged path still completes and reports the full `4000..FFFF` RAM
survey first. It then verifies that every visible framebuffer byte retains the
survey's final `55` value before drawing anything. The exact visible range is
`D800..FDA7`: 9,640 bytes, 40 bytes by 241 rows, MSB first. A mismatch selects
a continuous nominal 3 kHz framebuffer-RAM-bad tone and halts without a pattern.
The no-ACK path never assumes that range works and retains the version-7 fixed-
window beep fallback unchanged.

On a clean framebuffer the ROM writes `high(address) XOR low(address)` to every
visible byte, reads all 9,640 values back against the same register-only oracle,
and halts in mode 0. This address-XOR field toggles every data bit and turns
address aliases or missing rows into a deterministic visual discontinuity. The
600 bytes at `FDA8..FFFF` are outside the guarded 320×241 raster and retain the
survey's `55` fill.

Rung 5e preserves the historical table boundary while extending checked code.
The first post-table extension is exactly 256 bytes at `0812..0911`, has sum
`7A`, and includes the PIT test plus the next guard. The block-1 ROM loop leaves
`C=00`; its first `DCR C` therefore covers the complete 256-byte page without a
length immediate. That verified page checks the 70-byte framebuffer extension
at `0912..0957`, whose sum is `0D`, before any USART or RAM access. Corruption in
either extension reaches the existing ROM-bad halt; corruption in the second is
caught after safe PIT recovery but before serial traffic.

`tests/jukuravi_d0_framebuffer_test.py` proves the exact image's full survey,
all 9,640 pattern writes and readbacks, a D84 fault at `D800` that reports page
`D8`/mask `01` and suppresses the draw, both extension-corruption branches, and
the no-ACK predecessor. The vm80a fixture runs the same opcodes with a one-page
`D800` survey and three loop counts shortened to 320 bytes (eight raster rows).
It proves clean draw/readback through bit-sliced D84–D91, the fault halt with
zero pattern writes, and 2,560 matching pixels from the existing abstract
serializer. Separate version-8 fallback runs retain both clean and dead-D87
physical outcomes.

## Bench variant: cumulative no-serial audible path

`diag-d0-noserial.bin` advertises ROM version `0A` and deliberately performs no
8251 I/O.  It preserves the alive and CPU tests, historical block-1 checksum,
D10 PIC, D27 PPI, and D54/D55/D57 all-counter tests.  Success then jumps
directly to the existing two-window RAM fallback.  This makes it suitable when
X3 CTS is inactive or the serial harness is absent.

The expected clean cadence is the approximately 0.5-second nominal 1 kHz alive
beep, an approximately 0.25-second nominal 125 Hz no-serial marker, both 4 KiB
RAM window tests, and three short nominal 2 kHz success pulses followed by
silence.  The existing CPU/ROM/PIC/PPI/PIT continuous failure tones remain
unchanged.  If neither RAM window works, one to eight short nominal 1 kHz
pulses identify the first failing D84-D91 bit, followed by continuous 125 Hz.
The cosim guard requires zero reads or writes at USART ports `08h` and `09h`,
zero transmitted/received bytes, the complete cumulative PIT sequence, and
both clean-window and forced-dead-D87 terminal paths.

`diag-d0-pit-debug.bin` is the focused companion, advertised as version `0B`.
It preserves the CPU/ROM/PIC/PPI gates and performs no USART or RAM access.
A clean PIT run gives three short nominal 2 kHz pulses and silence.  On the
first failed read it gives the following number of short nominal 1 kHz pulses,
then a continuous nominal 125 Hz tail. Reset repeats the report:

| Pulses | Checkpoint |
| ---: | --- |
| 1 | D54 channel 0, high (`FF`) DB7 readback |
| 2 | D54 channel 1, high (`FF`) DB7 readback |
| 3 | D54 channel 2, high (`FF`) DB7 readback |
| 4 | D54 channel 0, low (`3F`) DB7 readback |
| 5 | D55 channel 0, high (`FF`) DB7 readback |
| 6 | D55 channel 1, high (`FF`) DB7 readback |
| 7 | D55 channel 2, high (`FF`) DB7 readback |
| 8 | D55 channel 0, low (`3F`) DB7 readback |
| 9 | D57 channel 0, high (`FF`) DB7 readback |
| 10 | D57 channel 1, high (`FF`) DB7 readback |
| 11 | D57 channel 2, high (`FF`) DB7 readback |
| 12 | D57 channel 0, low (`3F`) DB7 readback |

The cosim regression injects the appropriate DB7 polarity fault at every one
of the twelve positions and checks the pulse count, first-stop behavior,
cumulative safe state, and absence of USART/RAM traffic.

`diag-d0-pit-debug-slow.bin` is the version `0C` field-readable form of that
test.  Its SHA-256 is
`34c110f209e7ccfffb3a261bea25b3b2e9d361eaaad57bcde638d744e8eed72a`.
The initial alive indication remains approximately 0.5 seconds at 1 kHz.  A
failure then has 0.75 seconds of silence, followed by 0.25-second 2 kHz count
pulses separated by 0.25 seconds of silence.  After pulse five an additional
0.75-second separator divides the count into groups of five.  A final
0.75-second pause, in addition to the normal trailing 0.25-second gap, precedes
the continuous nominal 125 Hz failure tone.  Clean success is three of the
same long 2 kHz pulses followed by silence.  Build or verify it with:

```sh
python3 spinoffs/jukuravi/firmware/build_d0_pit_debug_slow.py
python3 spinoffs/jukuravi/firmware/build_d0_pit_debug_slow.py --check
```

`diag-d0-d55-stress.bin` is version `0D` and isolates the unstable middle PIT.
Its SHA-256 is
`703514bd36ea3fb1c695b91259040571d601880f475f4562698c851ffbdfd0ce`.
It repeats each historical D55 predicate 32 times, adding eight 8080 NOP cycles after
each control write, count write, and latch command.  The slow T15 report format
is retained, but only four failure codes exist: channel 0 high, channel 1 high,
channel 2 high, and channel 0 low.  Three long 2 kHz pulses and silence mean all
128 reads passed. This image is retained to reproduce historical observations,
not for new D55 diagnosis: NOP spacing does not start the missing D54/D56
clock sources, so its four codes are invalid as D55 package/path localization.
Build or verify it with:

```sh
python3 spinoffs/jukuravi/firmware/build_d0_d55_stress.py
python3 spinoffs/jukuravi/firmware/build_d0_d55_stress.py --check
```

`diag-d0-best-effort.bin` is the dependency-aware full diagnostic, version
`0E`. Its SHA-256 is
`a9bc32c22d41acda0d8bed4708f85ce70dabc353abc2a9697a33421545adc098`.
CPU and the checksummed ROM block are the only hard gates. With interrupts
disabled, PIC, PPI, D54, D55, and D57 faults accumulate in register E and do
not stop execution. The ROM then tests and handshakes the polled USART without
using a stack or RAM and transmits a `DIAG_STATUS` fault bitmap:

| Bit | Set means |
| ---: | --- |
| 0 | PIC failed |
| 1 | PPI failed |
| 2 | D54 failed |
| 3 | historical D55 predicate failed (versions through T32: not valid D55 evidence) |
| 4 | D57 failed |

Only after that frame is acknowledged and transmitted does the ROM destructively
test the 4 KiB windows at `4000h` and `C000h`. A second `DIAG_STATUS` byte has
bit 7 set, bit 0 for a good `4000h` window, and bit 1 for a good `C000h` window.
The host prints these results directly. This ordering proves that completely
bad RAM cannot prevent the first UART report.

Audibly, six slow grouped 2 kHz pulses plus the continuous 125 Hz tail mean
UART/local handshake failure; seven mean neither RAM window worked. Three long
2 kHz pulses and silence mean the UART report completed and at least one RAM
window passed. CPU and ROM retain their earlier distinct hard-failure tones.
Build or verify with:

```sh
python3 spinoffs/jukuravi/firmware/build_d0_best_effort.py
python3 spinoffs/jukuravi/firmware/build_d0_best_effort.py --check
```

## Robust full diagnostic and upload monitor

`diag-d0-robust.bin` is version `0F`, SHA-256
`fa4376b6cb094d13350f4dfb627eac4706c17ec97940feb9bffb01a9339ef658`,
with full-image CRC16 `1786`.  It retains T17's RAM-independent CPU, ROM,
PIC, PPI, PIT, local-USART, peripheral-status, and compact RAM diagnostics.
PIC/PPI/D54/D55/D57 failures remain reportable and nonfatal.

The serial entry is hardened from the hardware findings on CS00015: stale
receive bytes are drained before transmitting the banner, the ROM scans a
bounded byte stream for one exact ACK while resynchronizing on `A5`, and host
version-0F sessions transmit four independently framed ACK copies.  Remaining
copies are drained before the loader starts.

After compact RAM reporting, the ROM destructively verifies the entire
`D800..FDA7` loader buffer/stack workspace with uniform and address-XOR
patterns, additively verifies the loader extension, and enters the persistent
D2 command monitor at `0A0C`.  The existing fixed API and CRC-framed LOAD/RUN
contract are preserved: programs load into `4000..D7FF`, each byte is read
back before acknowledgement, RUN is acknowledged and drained before `PCHL`,
and uploaded code can return with `JMP 0A06h`.

Build or verify it with:

```sh
python3 spinoffs/jukuravi/firmware/build_d0_robust.py
python3 spinoffs/jukuravi/firmware/build_d0_robust.py --check
```

`diag-d0-stopwait.bin` is the version-`10` stop-and-wait refinement, SHA-256
`050e409878d7517b1d235eb3bb63d2580aa2fcaa229cce9f40f7d3783bc1bfab`,
with full-image CRC16 `68B4`.  It preserves the complete version-0F diagnostic,
workspace verification, loader, fixed API, LOAD verification, and RUN path.
For the initial handshake, the ROM transmits each of the nine expected ACK
bytes as an individual challenge and advances only after the host echoes that
exact byte.  Each byte receives eight bounded attempts with a long receive
window.  This is the full-ROM application of T19's hardware-proven reliable
stop-and-wait behavior.

```sh
python3 spinoffs/jukuravi/firmware/build_d0_stopwait.py
python3 spinoffs/jukuravi/firmware/build_d0_stopwait.py --check
```

`diag-d0-adaptive.bin` is version `11`, SHA-256
`0a76064fc669762faf575474b8a43807d17be57f4a5786cec6d5b25d07511835`,
with full-image CRC16 `39F9`.  It is the adaptable transport image intended to
avoid further ROM changes when host-to-Juku raw byte values are unreliable.
Negotiation uses only alternating `55`/`AA`; a receive mismatch transmits
`F0,expected,received` telemetry before retrying.  Loader input then represents
each logical byte as eight MSB-first symbols (`55`=0, `AA`=1) and discards all
other physical values.  CRC framing and immediate RAM readback still validate
the reconstructed logical data.  Juku-to-host frames stay in the efficient raw
format.  The 8x upload expansion is deliberately exchanged for arbitrary-byte
correctness on the measured harness.

The real host CLI has been verified with both a RUN of an uploaded `HLT` at
`4000h` and a load-only file containing all 256 possible byte values.

```sh
python3 spinoffs/jukuravi/firmware/build_d0_adaptive.py
python3 spinoffs/jukuravi/firmware/build_d0_adaptive.py --check
```

`diag-d0-repetition.bin` is version `12`, SHA-256
`d03d39055d3ac6f5d189ee65f39f6f681cf7de63365d4b18495fd8ec60c68bde`,
with full-image CRC16 `3D2D`.  It retains adaptive negotiation and mismatch
telemetry, then uses seven fixed physical symbols per logical bit.  The ROM
always consumes all seven, counts exact `55` and `AA` votes, and selects the
larger count; other values are neutral but retain alignment.  Encoded LOAD
chunks are capped at 32 bytes, independently CRC-framed, and read back from RAM
before acknowledgement.  An emulator run uploaded and verified a file
containing all 256 byte values in eight chunks.

```sh
python3 spinoffs/jukuravi/firmware/build_d0_repetition.py
python3 spinoffs/jukuravi/firmware/build_d0_repetition.py --check
```

`diag-d0-resilient.bin` is version `13`, SHA-256
`a3182957b68d9c7e3d7c9127ca79c7131fd73bb385066e3065beb9e73b22d673`,
with full-image CRC16 `A1C1`.  It lowers the physical link to approximately
2400 baud while retaining seven-vote fixed-width symbols and 32-byte logical
LOAD chunks.  The host launches each physical symbol at a conservative 6 ms
cadence.  A bounded per-symbol ROM timeout resets the loader stack and parser,
reports a retryable bad-CRC transport error, and returns to frame sync instead
of hanging.  The host can retry each rejected LOAD chunk up to three times;
logical CRC and immediate RAM readback remain authoritative.

```sh
python3 spinoffs/jukuravi/firmware/build_d0_resilient.py
python3 spinoffs/jukuravi/firmware/build_d0_resilient.py --check
```

`diag-d0-solicited.bin` is version `14`, self-CRC16 `7AB9`, SHA-256
`6d174c0164119eda9ae7fa4438c545661f8c315ebd9bf56f8002fc886c1c8c56`.
It keeps T24's 2400-baud diagnostics, loader API, seven-vote bit encoding,
CRC, and RAM readback, but eliminates dense host-to-Juku transmission. Before
each physical symbol the ROM emits an alternating `C6`/`C7` capacity token and
accepts exactly one response. A repeated token tells the host to resend the
same symbol; a changed token proves acceptance and advances it. This preserves
vote boundaries across deleted UART characters and prevents 8251A overruns.
The ROM also writes the 8251A ER command after every received character to
clear persistent parity, overrun, and framing flags.

```sh
python3 spinoffs/jukuravi/firmware/build_d0_solicited.py
python3 spinoffs/jukuravi/firmware/build_d0_solicited.py --check
```

`diag-d0-echo-filtered.bin` is version `15`, self-CRC16 `368B`, SHA-256
`4105eadcf2a3f9a310fee82ad5349982b7ad4a85f83cf82cf6b181330177002d`.
It retains T25's receiver-driven transport but accepts only `55` and `AA` as
physical vote responses. Every other received value—including the measured
`C6`/`C7` request self-echo from the CP2102/MAX3232 harness—is discarded
without changing the request sequence or consuming a vote slot.

`diag-d0-buffer-verified.bin` is the T28 burn-once host monitor, ROM version
`17`, self-CRC16 `A6A5`, SHA-256
`e2a18fc2741cc0db10eea278bedede0787220d853ec88dc5dff7e785ba9a95ea`.
It moves all parser state and its stack to the independently tested
`C000..CFFF` window, verifies every parser and target store, protects commands
with both wire CRC8 and a CRC16 recomputed from stored RAM, and exposes
transactional PROBE, CONFIG, LOAD, READ, CRC, RUN, and RESYNC commands. CALL is
the default RUN mode: an uploaded snippet completes with ordinary 8080 `RET`,
returns A plus an optional RAM result block, and leaves the monitor active.
RUN uses an independent 32-bit execution ID, so a repeated command replays its
cached completion rather than executing a non-idempotent snippet twice. On RET
the ROM restores DI, SP, the 8251, and the 2400-baud PIT channel before replying.
Idle transport reset and host reattachment preserve uploaded RAM and avoid a
board RESET. The complete stable contract and host examples are in
[`../LOADER-API-V2.md`](../LOADER-API-V2.md).

`diag-d0-host-recover.bin` is the T29 hardware-recovery refinement, ROM
version `18`, self-CRC16 `AC40`, SHA-256
`c92b9760633c4d73a92bd1d2f737dd9c0ac94061c7331eee487be5ce02b69536`.
It retains the complete T28 host monitor and adds raw post-diagnostic progress
bytes `E0`, `E1`, `E2`, and `E3`, respectively identifying monitor handoff,
verified `C000..CFFF` workspace, verified loader ROM, and loader entry. All
loader TxRDY and TxEMPTY waits are bounded. On the first timeout T29 resets and
reprograms the 8251 and the 2400-baud PIT channel, retries once, and otherwise
takes the existing audible UART-failure path instead of hanging silently. The
emulator regression deliberately holds TxRDY low between frames and verifies
that this recovery still reaches READY, uploads code, executes it by CALL/RET,
and returns both A and a RAM result block.

`diag-d0-txready.bin` is T30, ROM version `19`, self-CRC16 `6127`, SHA-256
`804562b2a0e28f8380773b2e331587973b5a5928a646ac4f93ee99e355e51f2a`.
Physical T29 output proved that the real CS00015 board transmitted its complete
final diagnostic frame while 8251 status bit 2 nevertheless remained low.
T30 therefore retains the initial TxEMPTY sanity check that worked on the
board, but removes every later correctness dependency on TxEMPTY. The final
diagnostic handoff proceeds directly, and the loader uses a conservative fixed
drain delay before CALL instead of status bit 2. TxRDY waits remain bounded and
recoverable. Regression runs force TxEMPTY permanently low after startup and
also inject a separate one-shot TxRDY stall; READY, upload, CALL/RET, returned
A, and returned RAM all remain operational.

`diag-d0-low4k.bin` is T31, ROM version `1A`, self-CRC16 `72EF`, SHA-256
`a4fed9185616bbfbef22ab6f0b18202e6d79ad7dbe3b7c46a77a700d3af3676c`.
Repeated physical T30 captures proved an exact
`banner 19/6127 -> status 08 -> status 83 -> restart` cycle with no `E0`; its
first post-diagnostic instruction was at `100Ch`. T31 compacts the two-attempt
TxRDY recovery so every executed monitor byte fits at or below `0FFFh` (loader
end exactly `0FFFh`) and enters it directly after the compact `83` RAM gate.
It bypasses the unreachable full-workspace and loader-checksum tail above the
boundary. Cosim's `JUKU_ROM_EXEC_RESET_AT=0x1000` reproduces three exact T30
cycles, while T31 still completes READY, upload, readback, CRC, CALL/RET,
returned A, and returned RAM under the same boundary plus a historical D55-bit
fault injection. Programmer verification is the loader-ROM integrity evidence for this
workaround image.

`diag-d0-waitclass.bin` is T32, ROM version `1B`, self-CRC16 `D62B`, SHA-256
`61832807cd7e52c02384844649776efa75bb3ef25795a8124d795230ed5b5ce2`.
It preserves the exact T31 execution policy and loader end at `0FFFh`, then
adds page-aligned diagnostic programs at `1100h`, `1200h`, `1400h`, `1600h`,
`1800h`, `1A00h`, `1C00h`, and `1E00h`. These cover all eight `{A11,A10,A9}`
combinations and therefore two CAS-gated, two no-wait, and four always-wait D2
classes. Each program stores its high address byte at RAM `4100h` and jumps to
the proven loader entry at `0A0Ch`. A host reattachment plus the unique marker
proves the requested upper-ROM fetch actually ran; loader recovery alone is
not accepted as evidence. `sync/jukuravi_t32_check.sh` first guards the normal
low-4K monitor, then executes and identifies all eight entries in cosim with a
historical D55-bit fault injection. It also guards the measured CS00015 D1 model:
a 16-bit increment cannot retain an already-high A12. That one rule reproduces
PC loss at `1100h/1200h/1400h`, the lower-alias stream from `1A00h`, all-RAM
LHLD/POP/SHLD read and write results, and successful carry across
`0FFFh -> 1000h`. The independently observed first-fetch `5A00h:3E->00`
remains a separate bounded historical regression. The DOS burn image and CRLF
bench note are `dos/T32HOST.BIN` and `dos/T32INFO.TXT`.

`diag-d0-clocked-pit.bin` is T34, ROM version `1C`, self-CRC16 `A637`,
SHA-256
`63f69281e632324083bd5e7040d19a7939936b98a4d5cb245e008ea491d45cb5`.
It preserves T31's below-`1000h` monitor policy and exact loader end at
`0FFFh`, but supersedes the D55 diagnostic predicate. Before testing D55 it
starts the source-proved EKTA D54 horizontal chain without preloading D55;
after each high and low D55 count write it waits nominally 300 us, over four
complete 64 us worst-phase source periods, before latching and reading. Both
DB7 polarities are required on every D55 channel, so an unclocked stale count
cannot pass by coincidence. The result bit
means **D55 functional path failed**. It deliberately does not claim that the
D55 package is bad: D9 select, local bus/strobes, socket/power, D54 outputs and
D56 clocks remain within that path. T15/T16/T31/T32 used immediate D55
latch/read sequences without establishing these clocks and must not be used as
package evidence. The clock-faithful negative control and fault matrix are in
[`../../../docs/jukuravi-d55-diagnostic-audit.md`](../../../docs/jukuravi-d55-diagnostic-audit.md),
and the DOS burn image is `dos/T34HOST.BIN`.

```sh
python3 spinoffs/jukuravi/firmware/build_d0_clocked_pit.py
python3 spinoffs/jukuravi/firmware/build_d0_clocked_pit.py --check
sync/jukuravi_d55_clock_audit.sh
```

The T34 one-session host batch adds two RAM-resident measurements without
changing the burned image. `cpu-host-timebase-4000.asm` provides matched short
and long CALL entries separated by exactly 1,200,000 nominal 8080 T-states.
The host subtracts their RUN-ack-to-RETURN intervals to obtain effective CPU
MHz, including physical READY waits, without touching any peripheral.
`d57-raw-4000.asm` returns eight high/low DB7 samples from each D57 channel and
leaves channel-0 serial restoration to loader API v2's post-RET contract. It
restores channels 1 and 2 itself. D57 sampling runs last: if a faulty D57 loses
the serial clock while being reprogrammed, the non-invasive CPU/RAM and parser
evidence is already durable. Both snippets execute from low-A12 loader RAM,
return ordinarily on a clean board, and are assembled into a temporary
directory by `spinoffs/jukuravi/batch.py`; no additional diagnostic ROM burn is
required. `cpu-pit-ratio-4000.asm` remains an experimental direct CPU/PIT ratio
probe, but is intentionally excluded from the physical batch because it can
disrupt transport on a board that has already reported D57. The complete
host/PTTY regression is `sync/jukuravi_t34_batch_check.sh`.

### Upper-D15 data/fetch diagnostic snippets

The `rom-a12-4000.*`, `rom-read-*`, `rom-read-pair-4000.asm`,
`rom-exec-106f*`, and
`rom-reenter-4000.*` fixtures are non-destructive T31 probes loaded at `4000h`.
The read probes execute wholly from RAM and return observed D15 bytes through
RAM result blocks. `rom-read-pair-4000.asm` uses `LHLD` to expose consecutive
D15 cycles; this is what distinguished CS00015's correct isolated reads from
its exact second-read A12-low aliases. `rom-reenter-4000.bin` jumps directly
from RAM to the lower
loader entry at `0A0Ch`; `rom-exec-106f.bin` instead jumps to the upper-ROM
trampoline at `106Fh`, whose expected `C3 0C 0A` instruction returns to that
same entry. The pair separates loader re-entry from upper-ROM instruction
fetch.

The `ram-a12-{write-map,lhld-classes,instruction-classes,ready-classes,
boundary,increment-registers}-4000.asm` sources are the later T32 all-RAM and
direct-register probes. They use absolute stores for setup and low-A12 result
blocks. `ram-a12-increment-registers-4000.asm` is the decisive compact probe:
it returns INX results for BC/DE/HL/SP plus a DAD control without accessing
high-address memory. `tests/jukuravi_cpu_a12_increment_test.py` guards all six
probe classes in clean and faulted cosim.

`tests/jukuravi_t31_a12_test.py` exercises the committed payloads against the
exact T31 image, then aliases the upper ROM half to the lower half and requires
the distinct `066Ch` HLT/250 Hz CPU-failure signature. Assembly comparison and
the cosim regression are part of `sync/jukuravi_t31_check.sh`. CS00015 physical
results and raw-log provenance are in `../T31-PHYSICAL.md`.

### Uploaded speaker demo

`smoke-4000.bin` is a deliberately playful but complete T31 application proof.
Its reproducible NASM source is `smoke-4000.asm`; both are 134 bytes loaded at
`4000h`. It programs D57 channel 1 for twelve successive square-wave pitches,
leaving the independent channel-0 UART clock to the ROM's return restoration.
The pitch sequence is G4, B-flat4, C5 / G4, B-flat4, D-flat5, C5 / G4,
B-flat4, C5, B-flat4, G4.

Timing follows the published intro notation: 4/4, quarter-note = 112, with the
complete phrase represented as exactly 32 eighth-note units. A 22,321-iteration
register-only delay is nominally 267.852 ms at the 2 MHz CPU clock, versus the
ideal 267.857 ms eighth note. Per-note table entries independently select sound
and silence units, including the direct D-flat-to-C transition and five-unit
final G. Each completed note writes its remaining count to `4104h`.

After all twelve notes, the snippet writes `SMOK` to `4100h..4103h`, leaves zero
at `4104h`, returns `A=0Ch`, and executes an ordinary `RET`. T31 then restores
its serial state and remains available. `tests/jukuravi_t31_smoke_test.py`
boots the exact T31 image and uploads the committed binary through the real
cosim PTY. It requires five first-attempt CRC-verified chunks and the completion
contract, checks all 60
speaker-PIT writes, and bounds every simulated note-onset interval against the
112-BPM grid. The assembly comparison and demo run are part of
`sync/jukuravi_t31_check.sh`.

The timing reference is the published Deep Purple guitar TAB:
<https://www.deeppurple50.com/sites/g/files/g2000016886/files/2024-01/Smoke%20on%20the%20Water%20-%20Guitar%20TAB%5B21%5D.pdf>.

## Stage D2 checkpoint: chunked RAM loader

`diag-d2-loader.bin` is the cumulative version-9 image. It preserves every D0
test and the full clean framebuffer readback, then verifies a separate 452-byte
loader extension before using it. The historical block-1 sum is `D0`, the PIT
extension sum is `97`, the 99-byte framebuffer/loader-guard extension sum is
`0D`, the loader extension at `0A00..0BC3` sums to `0C`, and the full-image
self-checksum is `DF64`:

```text
banner: A5 5A 01 04 01 09 DF 64 C8
ack:    A5 5A 81 04 01 09 DF 64 24
ready:  A5 5A A3 04 01 FD 0A 00 4A
```

The READY payload is API version `01`, maximum chunk data `FD` (253 bytes), and
fixed API base `0A00`. Commands use the common CRC-8/ATM frame envelope:

| Direction | Type | Payload |
|---|---:|---|
| host → ROM | `20` LOAD | big-endian address, then 1–253 data bytes |
| host → ROM | `22` RUN | big-endian entry address |
| ROM → host | `A0` LOAD_RESULT | one status byte |
| ROM → host | `A2` RUN_ACK | empty |
| ROM → host | `A3` LOADER_READY | API version, max data, API base |
| ROM → host | `AF` LOADER_ERROR | one status byte |

Status `00` is success; `01..05` mean bad CRC, unknown command, bad length, bad
range, and RAM readback failure. Each independently checksummed LOAD chunk must
target `4000..D7FF`. The monitor buffers and validates the complete frame in the
already verified framebuffer workspace, copies into the landing range, reads
every byte back immediately, and acknowledges only an exact match. RUN accepts
the same address range, sends and drains RUN_ACK, then jumps to the entry.

The stack-free discipline remains intact through the complete RAM survey and
framebuffer verification. Only then does the loader set SP to `FDA8`, growing
down into the just-proven framebuffer tail. Four three-byte vectors are fixed:

| Address | API | Convention |
|---:|---|---|
| `0A00` | SERIAL_GET | wait for a byte, return it in A |
| `0A03` | SERIAL_PUT | transmit A and return |
| `0A06` | RETURN | abandon the uploaded stack and re-enter the loader |
| `0A09` | PRINT | transmit the zero-terminated string at HL |

`tests/jukuravi_d2_loader_test.py` boots the exact image through the real cosim
PTY, acknowledges the banner, checks the full clean survey and READY record,
and exercises corrupt CRC, short LOAD, out-of-range LOAD/RUN, and unknown-type
rejections. It loads an actual program at `4000`, executes GET, PUT, and PRINT
through the fixed vectors, returns through `0A06`, and requires a second READY
record. A separately corrupted loader extension reaches the ROM-fail halt and
never announces READY.
A second run injects a stuck-low D84 bit at `4000`, observes it in the survey,
and proves LOAD returns status `05` rather than accepting a failed readback.
The real host CLI now consumes this contract, uploads a 300-byte file as exact
253+47-byte chunks, validates both results, and runs the uploaded entry while
retaining the complete raw and JSON evidence set. Its uploaded fixture then
emits three CRC-framed, versioned, consecutive heartbeat records through
SERIAL_PUT. The host preserves their frame indices and sequences; a second
spinning fixture proves the bounded post-RUN timeout path.

The pixel comparison is explicitly the simulation-only framebuffer oracle. It
does not close the unresolved physical shared-DRAM video-slot schedule, D34/X7
levels, analog monitor behavior, or authorize a bench burn.

Broader row/column-shaped fault generators remain Stage D1 host-tool work; the
user-facing session CLI is guarded in the parent directory, and rung 4's
required serial and beep-only RAM paths are both represented by exact images.

The same command runs `sync/beeper_check.sh`, whose HDL PIT model proves that
D57 OUT1 toggles and whose connectivity guard traces `D57.13/SOUND` through the
analog handoff. Cosim does not yet synthesize the PIT waveform, and neither
guard models speaker voltage/current or authorizes a bench burn. The planned D0
firmware ladder and the first D2 loader core are now represented by exact
simulation checkpoints. Host file/chunk orchestration is guarded; D1
uploaded-test heartbeat supervision and its default-off bounded host recovery
policy are guarded as well. Physical reset hookup and liveness probes remain
measurement-dependent work; the disconnected-safe, default-off Nano-side
liveness capture/report and host evidence path are guarded separately. The host
session CLI,
DTR-commanded session
restart, bounded missing-banner retry, Nano serial bridge, and isolated startup
reset/hold are guarded separately in the parent directory.

## T35 finding and T36 physical-row correction

T35 (`1D/45C4`, SHA256
`ceb55556f11318dea5ef8c36b81f931813a139ce6ba6e07b607318571c6e1274`)
is retained byte-exactly because it produced the decisive physical evidence.
Its `MOV A,M / INR H` loop reads `4000h,4100h,...,BF00h`. The Juku drawings
show D48/D49 presenting CPU A0..A7 during the populated-bank RAS phase, while
the MK4564 contract refreshes MA0..MA6 and ignores MA7. T35 therefore refreshes
physical row `00` 128 times; it does not refresh 128 rows.

The six-second `4D00h` lane capture falsified the earlier T35 interpretation:
offset zero survived, other low-address rows decayed in structured blocks, all
eight D84..D91 lanes participated, and the loader eventually stopped. T35's
earlier long idle reattach only proved that frequently accessed loader state
could survive; it was not an all-row refresh proof.

T36 is `diag-d0-row-refresh.bin` / `dos/T36HOST.BIN`, version `1E`, CRC16
`C617`, SHA256
`32264641836ce914a0fc706c916e2847d542d83b05d6737f1d6272b76d78dedb`.
It changes the four increment opcodes to `INR L`, so the exact public entry
`07A9h` reads `4000h..407Fh` and visits every physical MA0..MA6 row once.
The routine remains 2,115 nominal T-states, preserves BC/DE/HL/SP, clobbers A
and flags, and retains the fail-safe loader policy and one-vote bootstrap.

Host command `2Ah`, the exact three-byte disable signature, RESYNC recovery,
and the cooperative-call rule are unchanged. The approximately 1.7 MHz number
is effective RAM-loop throughput including READY waits, not a direct CPU or
crystal measurement. Using it conservatively, one T36 sweep is approximately
1.234 ms and cooperative code should begin another `CALL 07A9h` within 2 ms;
non-cooperative or crashed uploaded code remains unsafe.

`tests/jukuravi_refresh_row_address_test.py` pins the drawing endpoints, local
MK4564 requirement, exact T35 artifact, and T35-one-row/T36-128-row split.
`tests/jukuravi_t36_refresh_test.py` runs T36 through the real host/PTTY path
with the corrected low-seven-bit decay model, a 1,025-byte upload, idle
reattach, all refresh controls, and torn-disable injection. Exact T35, armed at
the same `07A9h` entry, is the negative control and decays without ever
covering all 128 rows. The simulator can delay retention until that entry with
`JUKU_DRAM_RETENTION_ARM_PC=07A9`; this explicitly excludes boot-video refresh
traffic that the flat model does not implement.

The physical 2026-08-10 T36 run passed the complete boot bitmap, verified
CALL/RET, all uploaded CPU/address probes, and a 1.702797 MHz effective
RAM-loop measurement. A wire-forensic zero fill completed all 1,024 32-byte
LOAD/readback pairs over `4000h..BFFFh` with no store retry or duplicate
result frame. Its delayed post-hold
read was operator-stopped after 1,728 matching bytes (`4000h..46BFh`), already
covering every MA0..MA6 row 13--14 times; it is positive partial evidence, not
a claim that the unobserved suffix passed.

`local_ram.py` replaces that many-hour transport pattern for routine work. It
builds 792-byte probes at complementary `4000h` and `B000h` code homes, calls
the unchanged T36 `07A9h` API every 128 tested bytes, and covers the union
`4000h..BFFFh` with zero, one, checkerboard, and address-XOR patterns. The
decay-enabled host/PTTY regression proves all four patterns and both locations;
no ROM byte or public ABI changed. A second simulated run injects DB0 stuck low
at `6000h` and the compact results identify only D84, in both overlapping
stages and in exactly the patterns whose expected byte has DB0 set.

The physical local sweep subsequently completed on CS00024. Zero, one,
checkerboard, and address-XOR all passed over the complete `4000h..BFFFh`
union after six-second refresh-on holds: eight stage results, zero mismatching
bytes, XOR `00`, and no D84--D91 candidate. This proves the RAM array under
T36 refresh and supersedes the first session's delayed-prefix limit; it does
not claim six-second raw retention or validate the normal-ROM refresh schedule.

The same session retained a legacy D57 channel-2 result. The raw test returned
`99/99` for high/low programming in all eight repetitions while channels 0 and
1 responded. Its original fault interpretation is superseded: exact E3
tracing puts D57.18/CLK2 on active-low D55.13 `/VER RTR` at about 49.92 Hz,
not D57.9/CLK0's 1.23 MHz source. The old probe neither armed the raster nor
waited long enough for a guaranteed channel-2 edge.

The current `d57-raw-refresh-4000.asm` emits `D57S` v2, arms the exact Ekta
D54/D55 raster, and waits 64 T36 refresh sweeps after every channel-2 write.
A physical CS00015 control passed all eight repetitions with
`FD/3D FC/3C FE/3E`. `batch.py --only-d57` now scores channel 2 only in this
corrected format; legacy `D57R` bytes are retained but not treated as a
discriminator. CS00024 needs this rerun before electrical follow-up. See
[`../../../docs/cs00024-t36-diagnosis.md`](../../../docs/cs00024-t36-diagnosis.md).
