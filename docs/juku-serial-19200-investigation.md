# Juku 19,200 receive investigation

Status: **9600 PROVEN / CS00014 19,200 MODE-2 DISK PROVEN / SCOPE CAPTURE NEXT**

This is the decision record and next-bench plan for the direction-specific
19,200-bit/s failure reproduced on CS00015 and CS00014. The retained captures
are indexed below; [the Janet analysis](ekta37-netbios-notes.md) describes the
ROM protocol and handoff. This document keeps
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
  [sustained network-disk soak](#physical-cs00014-disk-result-and-throughput).

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
intentionally changed. This makes receive-clock sensitivity the leading
explanation and lowers suspicion on serial-line bandwidth, D104 data-path
bandwidth, host pacing, parity, and CPU service latency. The software comparison
does not exclude interactions between data timing and the receive-clock waveform;
measure both at D11 before assigning a component fault.

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

Compare the passing 9600 mode-3/count-8 control, failing 19,200
mode-3/count-4 case, and passing 19,200 mode-2/count-4 case at the actual
receiver. Use the existing BAUDTEST2 matrix; no new ROM is needed.

1. Use a two-channel oscilloscope. Reference both probes to confirmed signal
   ground X3.7. Use a 10x probe on the bipolar X3.4 RS-232-level signal; never
   attach a TTL-only logic analyzer there.
2. Observe X3.4/D104.4 on channel 1 and D104.13/D11.3 on channel 2. Trigger on
   the first host start edge and capture a complete 133-byte case. At both
   rates record X3.4 positive/negative levels, D104.13 logic levels and edge
   times, and whether the output stops toggling when BAUDTEST stops counting.
3. In a second capture observe D57.10 and D11.25 for all three clock settings.
   Confirm the frequencies and periods above, TTL amplitude, duty cycle,
   ringing, and continuity of the waveform at the USART pin.
4. With power on but serial traffic idle, measure D104 pin 15 (+5 V), pin 16
   (+12 V), and pin 8 ground. Record the DC state of pins 1, 2, 3, and 14 and
   trace their actual board connections rather than inferring them from the
   generic datasheet.

Before applying power, resolve the D104.16 rail by continuity to a known X8
+12 V landing. The exact `.009` sheet-1 power table leaves the К170УП2 +12 V
cell blank even though the preserved device pinout identifies pin 16 as its
+12 V supply; the owner component photo does not expose the contact's full
route. See `ref/schematics/d104-pin16-rail-conflict.json`.

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
Do not spend another bench session on parity, host byte pacing, per-byte ER,
cable replacement, x1 mode, or the invalid count-one x64 image: the retained
controls already cover those questions.

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
incrementing/PRBS frames. The [diagnosis above](#current-diagnosis-after-the-mode-2-disk-pass)
separates the receive-clock inference from component-fault proof.

The historical `juku-net-mode2-soak-system.bin` keeps the stock ROM
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

The retained log places the disk phase at approximately 16–17 seconds
(one-second timestamp resolution), or **1.3–1.4 kB/s aggregate record
payload**. The stock 6,784-byte bootstrap took approximately 81 seconds.
These measurements describe this historical soak and loader; current host
performance and bootstrap behavior require their own matching profile.

### Other resident-protocol qualification

CS00015 also exercised NetDisk v2 at 19,200 on 2026-08-15: three retry-free
boots reached disk service, `DIR` passed, and `RDBENCH` completed 75 requests.
That is evidence for the tested resident image and serial profile; it does not
clear the mode-3 receive failure or establish current host defaults. The
qualification records are retained in CP/Mish's `juku` branch.

Compact-record benchmarks, read-ahead development, and earlier CP/M Plus
bootstrap failures are separate from this electrical diagnosis. Use the
[portable host contract](portable-c-host-plan.md) for the supported protocols
and regression commands, and the recovery guide below for current boot behavior.

The separate interactive CP/M result and ROM interrupt-dispatcher handoff rule
are documented in [the Janet analysis](ekta37-netbios-notes.md).

## Current bootstrap boundary

The experiments above qualify specific historical images and serial profiles.
They do not define the current production host defaults. Use
[the stock bootstrap and recovery guide](janet-fastboot.md) for current
commands: recoverable stock-ROM sessions use **JF17 at 9600/8O1 throughout**.
The C host also retains exact JF15 compatibility and a separate network-ROM
JF16 workflow; their artifact and serial profiles must match the target.

The former CP/M Plus stock-`TN` final-ACK failure was an observed historical
wrapper failure, not an unresolved limitation of the current JF17 path.
[The CS00014 JF17 record](evidence/juku-serial/cs00014-stock-jf17-20260905/README.md)
qualifies boot, operator-selected reset recovery and live host replacement.
It does not qualify 19,200 mode-3 reception or reset during disk writes.

For implementation and regression commands, see the
[portable C host contract](portable-c-host-plan.md). Older fast-stage timings,
optimization sequences and proposed boot designs remain in Git history; the
physical baud evidence below remains relevant to the electrical diagnosis.

## Retained baud evidence

Machine-readable evidence is
[`cs00014-mode2-soak-20260813.json`](evidence/juku-serial/cs00014-mode2-soak-20260813.json).
The [184-line timestamped bench log](evidence/juku-serial/cs00014-mode2-soak-20260813.log)
has SHA-256
`d19f7f76af697a9662283b621ac8107fc9c6e408cbf76bd72bf99f87972aa555`.
The complete preceding 68-case discriminator is preserved as
[`cs00014-baudtest2-20260813.json`](evidence/juku-serial/cs00014-baudtest2-20260813.json).

BAUDTEST2 records Linux serial driver frame/parity/overrun counters through
`TIOCGICOUNT` when supported. The retained JSON records the observed deltas;
these counters complement the target's D11 status and byte comparisons.

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
