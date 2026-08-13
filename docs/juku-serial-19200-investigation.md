# Juku 19,200 receive investigation

Status: **9600 PROVEN / 19,200 RECEIVE BOUNDARY LOCALIZED / SCOPE CAPTURE NEXT**

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

The stable resident network-disk setting remains **9600/8O1**. There is no
evidence yet that 19,200 is safe for filesystem traffic.

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

| BAUDTEST setting | D57 clock period | mode-3 high/low |
| --- | ---: | ---: |
| 9600/x16, count 8 | 6.500 us | 3.250 us / 3.250 us |
| 19,200/x16, count 4 | 3.250 us | 1.625 us / 1.625 us |

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

## Current diagnosis

The strongest clue is not merely that long packets fail. Reception usually
ends after a correct prefix with no D11 error flag, while the target remains
able to transmit. That is consistent with D11 ceasing to recognize start bits
because its RxD input remains at the idle level or because its receive clock is
unusable. It is less consistent with ordinary CPU overrun or occasional data
corruption, which the revised test would report as OE, PE, FE, or mismatches.

The ranked boundaries are:

1. **D104 input/output electrical margin**: voltage or loading at X3.4,
   D104 supplies/threshold network, or the D104.4->13 receiver channel.
2. **D11 receive-clock waveform at pin 25**: correct average frequency but
   marginal level, duty cycle, ringing, or loading at the USART pin.
3. **D104.13-to-D11.3 connection/load**: a board-level receive-only node that
   the external loopbacks do not exercise.
4. **D11 receive half**: possible only after RxD and RxC are shown valid at the
   pins during a failed frame. Reproduction on two boards makes two unrelated
   rare internal failures less attractive than a shared electrical boundary.

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
- A 19,200 mode-2/count-4 clock can change duty cycle without changing the
  nominal rate. Try it only after measuring the current symmetric mode-3
  waveform; an unexplained pass would point to clock-edge sensitivity, while
  a failure would add little.

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
