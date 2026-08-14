# Juku 19,200 receive investigation

Status: **9600 PROVEN / CS00014 19,200 MODE-2 DISK PROVEN / SCOPE CAPTURE NEXT**

This is the decision record and next-bench plan for the direction-specific
19,200-bit/s failure reproduced on CS00015 and CS00014. The complete run log
and capture filenames remain in `ekta37-netbios-notes.md`; this document keeps
the conclusions, electrical boundaries, and experiments that can still change
the diagnosis.

## Established facts

- Both machines pass the exhaustive 9600/8O1 BAUDTEST, including unpaced and
  paced 133-byte traffic in both directions and the final acknowledgement.
- Both machines reproduce the 19,200/x16 failure only from host to Juku. Short
  clean prefixes arrive, then reception stops without PE/OE/FE in nearly every
  case. A continuous 133-byte Juku-to-host packet still passes.
- Removing per-byte 8251 ER commands, draining host writes before pacing,
  adding the EktaSoft control-write gaps, selecting 8N1, replacing the cable,
  and allowing 2 ms between bytes did not remove the failure.
- The classic CP2102 cannot provide the desired exact x16 intermediate rates:
  it aliases arbitrary requests into fixed rate buckets. The 14,400/x1 attempt
  changed the 8251 sampling regime and produced parity errors, so it is not a
  valid x16 rate-threshold measurement.
- The 19,200/x64 attempt was invalid. D57 remained in 8253 mode 3, whose
  periodic minimum count is two; count one cannot create the required clock.
  That image has been removed and the simulator now rejects the invalid case.
- Cosim passes the full x16 suite at 9600 and 19,200, including a deliberately
  slow 1.5 MHz CPU and wire-rate one-byte overrun behavior. Software polling
  throughput and test recovery are therefore covered; analog behavior is not.
- Physical CS00014 passes all six 19,200/x16 mode-2/count-4 BAUDTEST2 cases and
  the sustained network-disk soak described below. The latter completed 108
  reads and 67 writes with zero protocol retries, wrote and byte-verified an
  8 KiB file after close/reopen, deleted it, and emitted `M2PASS!`.

The conservative cross-board resident network-disk setting remains
**9600/8O1**. **19,200/8O1 with PIT mode 2/count 4 is now physically proven for
sustained filesystem traffic on CS00014**, but has not yet been repeated on
CS00015 or adopted as the general default.

## Drawing and device reconciliation

The exact FDC-era `.009 E3` sheet 1 confirms the receive path:

```text
host/MAX output -> X3.4 S_SIN -> D104.4 -> D104.13 -> D11.3 RxD
                                      K170UP2       KR580VV51A

D57.10 OUT0 --------------------------+-> D11.25 RxC
                                      +-> D11.9  TxC
```

D57.10 is common to transmit and receive clocks. The correct 133-byte
Juku-to-host packet at 19,200 therefore substantially de-risks a wrong D57
divider and the common clock source. It does **not** prove that the waveform
at D11.25 has adequate level, duty cycle, or edge quality for the receiver.

With the observed `16 MHz / 13` source, D57 mode-3 count 8 produces a
153.846 kHz clock and nominal 9615.4 bit/s. Count 4 produces 307.692 kHz and
nominal 19230.8 bit/s. The expected clock periods and half-periods are:

| setting | D57 clock period | high / low |
| --- | ---: | ---: |
| 9600/x16, mode 3 count 8 | 6.500 us | 3.250 us / 3.250 us |
| 19,200/x16, mode 3 count 4 | 3.250 us | 1.625 us / 1.625 us |
| 19,200/x16, mode 2 count 4 | 3.250 us | 2.438 us / 0.813 us |

Intel specifies asynchronous 8251A operation through 19.2 kbit/s and x1, x16,
or x64 clocks. The documented Soviet Korvet implementation also operates a
KR580VV51A near 19.5 kbit/s with an approximately 312 kHz x16 clock. Thus the
requested rate is not intrinsically outside the USART family's intended use.
Neither reference proves the Juku analog path or the condition of its parts.

D104 is the only board component exclusive to the failing data direction. Its
datasheet identifies four line receivers, with channel 4->13 used for SIN,
+5 V on pin 15, +12 V on pin 16, ground on pin 8, and threshold-control pins
1, 2, 3, and 14. It specifies +3 V/-3 V switching boundaries and at most
45/50 ns propagation delay. A healthy part is therefore fast relative to the
52 us bit cell; supply margin, threshold-control disposition, input amplitude,
loading, or a marginal part remain open. The exact drawing and current board
model do not yet close the physical disposition of those four threshold pins
or D104's local +12 V quality.

## Current diagnosis after the mode-2 disk pass

The decisive clue is now the controlled mode comparison. At the same nominal
19,200 rate, framing, serial data waveform, CPU loop, and D11 setup, mode 3
usually stops after a correct prefix while mode 2 passes both 133-byte probes
and sustained filesystem traffic. Only the D57 output duty/edge waveform was
intentionally changed. This rejects serial-line bandwidth, D104 data-path
bandwidth, host pacing, parity, and CPU service latency as explanations for
the mode-3 failure.

The ranked boundaries are:

1. **D11 receive-clock waveform at pin 25**: correct average frequency but a
   mode-3 edge, level, ringing, duty, or recovery-time problem at the pin.
2. **D57 channel-0 output/loading**: the mode-2 low pulse and subsequent rising
   edge are accepted where the symmetric mode-3 waveform is not. This can be
   D57 itself or board loading; the software result alone cannot distinguish
   them.
3. **D11 receive-clock input sensitivity**: a marginal threshold/input stage
   can produce the same mode dependence even with a serviceable D57.
4. **RxD/D104 data path**, now a lower-ranked control: it remains worth
   capturing, but unchanged 19,200 data passing under mode 2 argues strongly
   against it as the cause of the observed mode-3 boundary.

The DOSRAVI 57,600/8N1 loopback lowers suspicion on the gross bandwidth of the
external CP2102/MAX chain, but it does not duplicate the Juku D104 input load,
thresholds, ground reference, framing, or receiver clock. It cannot clear the
external signal amplitude at X3.4 under the actual Juku load.

## Next bench session

The first experiment should be one repeatable BAUDTEST run at 9600 followed by
19,200, observed at the actual receiver. No new ROM is needed.

1. Use a two-channel oscilloscope. Reference both probes to confirmed signal
   ground X3.7. Use a 10x probe on the bipolar X3.4 RS-232-level signal; never
   attach a TTL-only logic analyzer there.
2. Observe X3.4/D104.4 on channel 1 and D104.13/D11.3 on channel 2. Trigger on
   the first host start edge and capture a complete 133-byte case. At both
   rates record X3.4 positive/negative levels, D104.13 logic levels and edge
   times, and whether the output stops toggling when BAUDTEST stops counting.
3. In a second capture observe D57.10 and D11.25 during count 8 and count 4.
   Confirm the frequencies and periods above, TTL amplitude, duty cycle,
   ringing, and continuity of the waveform at the USART pin.
4. With power on but serial traffic idle, measure D104 pin 15 (+5 V), pin 16
   (+12 V), and pin 8 ground. Record the DC state of pins 1, 2, 3, and 14 and
   trace their actual board connections rather than inferring them from the
   generic datasheet.

The result gives a direct decision tree:

- X3.4 stops or loses valid bipolar levels: external driver, grounding, or
  loading before D104.
- X3.4 stays valid but D104.13 stops or distorts: D104 channel, supplies, or
  threshold network.
- D104.13 remains a clean decoded stream but D11 reports no bytes: inspect
  D11.25 RxC; if it is clean too, the D11 receive half becomes the leading
  suspect.
- D11.25 is malformed only at count 4: inspect D57.10-to-D11 loading and D57
  channel 0 before replacing D104 or D11.

For a logic analyzer, use only the TTL nodes D104.13/D11.3 and
D57.10/D11.25. A UART decoder may be configured for the data stream, but the
raw transitions must also be retained because a decoder can hide runt pulses
or a signal stuck at idle.

## Follow-up experiments, only if needed

- Use a generator or programmable UART with adjustable bipolar amplitude at
  X3.4 and observe D104.13. This can map the actual switching margin without
  involving the CP2102's fixed baud aliases.
- After electrically isolating D104.13 from its output, inject a known-clean
  TTL stream at D11.3. Do not drive D104.13 and an external source against one
  another. A socket/removal or deliberate series isolation is required.
- Obtain an adapter or MCU that can generate exact 10,989, 12,821, and 15,385
  rates, then run a pure x16 ladder with D57 counts 7, 6, and 5. A modern
  arbitrary-rate UART is preferable to reprogramming the classic CP2102's
  persistent EEPROM alias table.
- A valid x64/9600 control is possible with D57 mode 3 count 2, but it tests
  x64 reception rather than the 19,200 boundary and has lower diagnostic
  value. There is no valid periodic count-one mode-2/3 route to x64/19,200
  from the existing D57 clock.
- A 19,200 mode-2/count-4 clock changes duty cycle without changing the
  nominal rate. This discriminator has now passed on CS00014; the sustained
  disk-soak experiment below is the next software test, while direct clock
  capture remains the decisive electrical follow-up.

Do not spend another bench session on parity, host byte pacing, per-byte ER,
cable replacement, x1 mode, or the invalid count-one x64 image: today’s
controls already resolved those questions.

## Automatically loaded BAUDTEST2

CP/Mish now builds a finite, monitorless `BAUDTST2.COM` matrix that is loaded
over the proven 9600 network path. It adds the useful software discriminators
that do not require a scope: exact lengths 1 through 20, nine data patterns,
repeated identical PRBS frames, idle and preamble variants, chunking, one byte
per 100 ms, a host two-stop-bit control, valid x64/9600, and mode-2/19,200.
Its bare receive path starts under `DI`.

The protocol is designed for the observed failure rather than assuming a
reliable stream. Each case resets D11 and has its own timeout; target frames
are checksummed and repeated; input searches for a sync byte; no ACK can block
progress; results include the first mismatch triple and final D11 status; JSON
is saved incrementally. Even with the host removed, the target advances through
bounded timeouts and restores stock mode-3/count-8/x16 9600 before returning.
Cosim proves all 68 ideal cases and separately truncates one case to prove the
rest of the matrix and final restoration survive.

The corrected 2026-08-13 physical CS00014 run completed the entire matrix and
restored 9600. Stock 19,200/x16 mode 3/count 4 passed four of 59 cases and
otherwise stopped after short correct prefixes with no PE/OE/FE. The 9600/x64
stage failed its three cases. Crucially, 19,200/x16 mode 2/count 4 passed all
six cases, including unpaced 64-byte alternating/PRBS and 133-byte
incrementing/PRBS frames. Because the serial line, framing, baud rate, CPU
loop, and D11 are unchanged, this is strong evidence of receive-clock
edge/duty sensitivity in the D57.10-to-D11.25 path. It is not yet proof that
D57 itself is faulty: loading, threshold margin, or the D11 clock input can
produce the same mode-dependent result.

The new `juku-net-mode2-soak-system.bin` therefore keeps the stock ROM
bootstrap at 9600, then runs the resident network BIOS at 19,200/x16 mode 2.
Its automatic transient writes 8 KiB to remote A:, closes/reopens it, reads
and verifies every byte, deletes the file, and emits `M2PASS!` before the
monitorless smoke tune. This tests sustained bidirectional Janet disk traffic,
not merely isolated payload frames. The host writes only an in-memory copy of
the volume and records timestamped console/log output plus incremental JSON.

### Physical CS00014 disk result and throughput

On 2026-08-13 CS00014 (station 09) accepted the stock Janet request, loaded the
6,784-byte bootstrap at 9600/8O1, then changed to 19,200/8O1 with D57 mode 2,
count 4. The disk phase completed 108 reads and 67 writes—175 successful
128-byte record transactions and 22,400 bytes of aggregate record payload—with
zero retries. The test file contributed 64 writes plus 64 reads; the remainder
was CP/M directory/open/close/delete traffic. `M2PASS!` proved the close,
reopen, full byte comparison, and delete all completed. Linux UART counters
reported zero frame, parity, overrun, buffer-overrun, and break deltas.

The timestamped disk phase took approximately 16–17 seconds, or roughly
**1.3–1.4 kB/s aggregate useful record payload**. The 19,200/8O1 wire carries
1,745 characters/s. One 128-byte record transaction consumes 142 wire bytes
(request plus response) and the host currently adds a 2 ms reply guard, giving
a theoretical protocol ceiling of about **1.54 kB/s**. The measured disk phase
is therefore approximately **86–91% of that ceiling**. A standalone 8 KiB
sequential read or write should take around six seconds before CP/M directory
overhead; this is suitable for interactive CP/M but far slower than a local
floppy's burst transfer.

The stock bootstrap is the conspicuously slow part: its 6,784 bytes took about
81 seconds after the request was accepted, only about **84 B/s of loaded image**,
because the preserved Janet loader performs many small framed/acknowledged
turns. The resident disk protocol is roughly sixteen times faster in useful
payload. Optimizing boot framing is a separate opportunity and does not limit
the already-running network disk.

### Physical interactive CP/M baseline

A later 2026-08-13 CS00014 run validated the corrected CP/Mish `NETROM1`
handoff and interactive path. The bootstrap server learned the physical
station pair `01 -> 09`, loaded 6,784 bytes through the stock 9600/8O1
protocol, and then served A: at 19200/8O1 in mode 2/count 4. The physical
keyboard accepted `DIR`; `TYPE README.TXT` completed sustained sequential disk
reads and console output; and `Ctrl-C` warm boot followed by another `DIR`
worked. All server requests through sequence `90` returned status zero. The
screen remained clean, unlike the earlier BIOS-owned interrupt-handler attempt
which had bypassed the RomBios dispatcher and produced vertical-line garbage.

The native character generator displayed a printable Estonian glyph while a
control-key combination was entered. Treat selectable native/English glyphs or
caret notation as future console work; first establish the original RomBios
control-character convention. It is not a blocker for the validated network
disk baseline.

## Future network-boot work

Keep two distinct and permanently testable boot paths.

### 1. Fastest possible server for the stock ROM protocol

Stock EktaSoft NetBios compatibility is a preservation requirement, not a
temporary stepping stone. `tools/janet_netboot.py` must remain able to boot all
five archived system images through an unmodified ROM. Optimize only the host
implementation and timing that the existing client permits: profile every
poll/frame/ACK turn, remove avoidable host-side waits, batch writes where the
ROM accepts them, and tune retry/poll scheduling from captures rather than
changing protocol semantics.

The acceptance gates are:

- all five archived images still reach `CA00h` byte-exactly in
  `sync/janet_netboot_check.sh`;
- physical stock-ROM boot remains reliable on CS00014 and CS00015;
- no increase in rejects, retries, or sensitivity to USB-UART scheduling;
- report request-to-entry time, loaded-image B/s, frame/ACK/reject counts, and
  the exact server settings for every benchmark.

The physical CS00014 baseline is 6,784 bytes in approximately 81 seconds after
request acceptance, 334 transmitted frames, 161 positive acknowledgements,
and zero rejects. This track may improve that substantially, but remains bound
by the ROM's many acknowledged turns.

### 2. New bulk netboot protocol where both ends are controlled

The preferred first design is now implemented in cosim and does **not** require
replacing the stock ROM. Stock Janet loads the 558-byte
`juku-fastboot-stage1.bin` executable at 9600; stage 1 changes D57 channel 0 to
mode 2/count 4, reinitializes D11 for 19,200/8O1, and receives the fixed CP/Mish
resident system as thirteen 512-byte blocks. See `janet-fastboot.md` for the
wire contract, command, regression evidence, and physical benchmark plan. A
custom ROM can enter the same stage directly later, while the stock-ROM route
and the original all-stock server remain available alongside it.

The implemented single-client baseline fixes the only supported layout at
B400h-CDFFh with entry CA00h, avoiding general address/length fields in the
stock-loaded stage. Each block carries its sequence and CRC16-CCITT; bounded
timeouts, retry, stream resynchronization, duplicate ACK, and a final
whole-image CRC are implemented. Stop-and-wait is the baseline. Benchmark a
small window only if it produces a material physical gain without weakening
recovery. Compression remains optional only if a small 8080 decoder
demonstrably reduces total boot time.

Physical CS00015 passed the complete path on 2026-08-14. Preserve the
same-machine results as **Fast stage v1** (17.508 s, 42 stock frames) and
**Original stock 9600** (73.873 s, 330 stock frames), measured from the first
valid Janet request to the first valid A: request. Both reached the visible
CP/M prompt. Fast stage v1 recovered one block-0 timeout automatically and was
4.22x faster. Later optimization results must be added as separate variants;
see `janet-fastboot.md` for the frozen table and evidence JSON.

Start at the already proven **19,200/8O1, x16, PIT mode 2/count 4**. At that
wire rate the raw 6,784-byte lower bound is about 3.9 seconds, so a practical
4–6 second bulk load is a reasonable initial goal. Later test mode 2/count 2
for nominal 38,400 only as a separately recoverable bench experiment; do not
make it a default until the D11/D57 limits and more than one physical board are
proven. Every high-speed failure must fall back cleanly to the stock 9600 path.

Keep protocol/version negotiation explicit so the same host can serve:

1. original stock Janet at 9600;
2. stock Janet loading the high-speed stage 1;
3. a future custom-ROM direct bulk bootstrap.

Cosim now injects complete-block loss, payload corruption, duplication, and a
lost target ACK against the assembled 8080 stage, and verifies the exact RAM
image before CA00h. Automated delayed-reply and power-reset/re-discovery remain before
full bench qualification. Physical benchmarks should include
CS00014 and CS00015, cold and warm runs, at least ten consecutive boots, exact
RAM comparison before entry, and recorded UART/kernel error counters.

Machine-readable evidence is
[`cs00014-mode2-soak-20260813.json`](evidence/juku-serial/cs00014-mode2-soak-20260813.json).
The [184-line timestamped bench log](evidence/juku-serial/cs00014-mode2-soak-20260813.log)
has SHA-256
`d19f7f76af697a9662283b621ac8107fc9c6e408cbf76bd72bf99f87972aa555`.
The complete preceding 68-case discriminator is preserved as
[`cs00014-baudtest2-20260813.json`](evidence/juku-serial/cs00014-baudtest2-20260813.json).

This reflects standard vendor debugging guidance: verify both endpoints'
framing, use known/reference patterns and error counters, compare each signal
stage, distinguish hardware overrun from framing/parity errors, and start the
receiver before the transmitter. BAUDTEST2 additionally records Linux serial
driver frame/parity/overrun counters through `TIOCGICOUNT` when supported.
See the [TI UART diagnostic guidance](https://software-dl.ti.com/processor-sdk-linux/esd/AM57X/08_02_01_00/exports/docs/linux/Foundational_Components/Kernel/Kernel_Drivers/UART.html),
[TI interface-debug checklist](https://software-dl.ti.com/simplelink/esd/simplelink_lowpower_f3_sdk/8.10.01.02/exports/docs/proprietary-rf/proprietary-rf-users-guide/proprietary-rf/debugging-cc23xx/debugging/debugging-index-cc23xx.html),
and [Silicon Labs AN197](https://www.silabs.com/documents/public/application-notes/an197-serial-communications-guide-cp210x.pdf).

## Sources

- Exact board drawing: `../ref/photos/dgsh5-109-009-e3/`, sheet 1 detail
  frames `PXL_20260718_101817644.jpg` and
  `PXL_20260718_101820818.MP.jpg`.
- Local D104 reference: `../ref/datasheets/k170up2.pdf` and
  `../ref/datasheets/k170up2-pinout.txt`.
- [Intel 8251A datasheet](https://community.intel.com/cipcp26785/attachments/cipcp26785/programmable-devices/89914/1/P8251A.pdf).
- [Intel 8253 datasheet](https://www.cpcwiki.eu/imgs/e/e3/8253.pdf).
- [Silicon Labs AN205, classic CP2102/3 baud aliases](https://www.freecalypso.org/pub/GSM/Pirelli/chips/silabs_an205.pdf).
- [Linux cp210x driver, AN205 quantization table](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/drivers/usb/serial/cp210x.c).
- [Korvet technical documentation](https://emu80.org/docs/korvet_techinfo).
