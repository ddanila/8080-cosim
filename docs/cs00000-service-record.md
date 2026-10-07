# CS00000 service record

Status date: 2026-08-22

This record covers the August 2026 service and stock-ROM tests. The later
[deployment profile](machines/CS00000.json) records the corrected C12 pair
installed in September.

CS00000 is a home-lab Juku received from Arvutimuuseum. Its then-fitted stock ROM
identifies itself on screen as ROM `#0031`, RomBios `3.43`, and Janet `1.2`.
Those strings are owner-observed; this record contains no dump or content
hash for that pair.

## Reported startup behavior

The machine generally reaches the stock monitor, but some cold starts produce
silence or the continuous low failure tone. A later start can succeed without
a recorded repair. This intermittent power-on symptom remains open and must
not be conflated with the serial result below.

## PSU failure and subsequent startup state

On 2026-08-22, one of the two parallel `22 uF / 350 V` primary-bus
electrolytic capacitors in the CS00000 power supply failed. The computer
continued operating at the time, but that supply is now out of service pending
repair and verification.

### PSU and ROM-swap controls

| Configuration | Owner-observed result | Evidence limit |
| --- | --- | --- |
| CS00024 PSU with stock `#0031` ROMs | Short startup beep, usually no display; one attempt showed garbage | Some video output was possible, but correct timing, framebuffer contents, CPU execution and POST were not established. |
| CS00024 PSU with known EK37 / RomBios 3.43m / Serial `#0037` pair, 2026-08-22 | Normal startup and correct display; repeated cold starts were all successful at reporting | Run count was not recorded. The swap also reseated sockets and changed the cold-start event. |

The no-display state followed earlier successful stock-ROM starts. It does
not prove mainboard damage from the PSU failure. A relationship between the
failed capacitor and the earlier silent/continuous-tone starts remains a
hypothesis pending supply, board-rail, reset and clock measurements.

The EK37 control argues against a broad mainboard or video-output failure and
narrows the immediate symptom to the removed `#0031` pair, socket/contact state
or a firmware-specific startup dependency. It does not prove either EPROM bad.
Preserve the pair by socket, read it repeatedly and compare it before assigning
a repair conclusion.

## Stock Janet and S21

The initially reported S21 value was `00101000`. With the stock-ROM meaning of
the switches, `00000001` selected the onboard D11 network path and a usable
station configuration. The host learned the actual request identity rather
than requiring a machine-specific number; the retained exchange was station
`02 -> 01`.

Early stock transfers reached visible `Load >02` or `Load >03` and then a new
`Load` line before stalling or corrupting the screen. A complete stock RAM-BIOS
load succeeded when the server allowed 10 ms after the destination-zero line
handover. CP/M Plus then reached `A>` and served NetDisk-v3 traffic at
19,200/8O1. This establishes working end-to-end D11 receive and transmit paths;
the earlier “broken USART” suspicion is rejected.

## Diagnostics

The network-loaded diagnostic program produced these owner-observed results:

| Test | Result | Interpretation |
| --- | --- | --- |
| CPU | pass | no CPU failure detected by this suite |
| RAM | pass | no RAM failure detected by this suite |
| PIT | pass | no PIT failure detected by this suite |
| D11 | pass | local USART diagnostic passed |
| ROM ABI | mask `01` | expected mismatch: fitted stock ROM has no JukuNet ABI |
| video/console | mask `01` | custom-ROM service prerequisite absent; not a video-hardware diagnosis |
| keyboard/S21 | mask `01` | custom-ROM service prerequisite absent; not a keyboard-hardware diagnosis |

All other invoked diagnostic groups passed. The three mask-`01` results must
not be promoted into component faults because the tested service ABI does not
exist in the fitted stock ROM.

## Stock-ROM transport qualification

These retained captures qualify historical host/JF15 configurations. The
[deployment profile](machines/CS00000.json) owns the current configuration.

| Configuration and evidence | Result and scope |
| --- | --- |
| Stock `#0031`, retired Python host: [V15 isolation record](evidence/juku-serial/cs00000-stock-v15-20260821.json) | The host exhausted its probe window after loading the core. Direct 19,200/8N1 attachment completed the same core without RESET or extension/stream retries, isolating a host synchronization defect. |
| EK37, C host `0.3.0-m6`: [boot capture](evidence/juku-serial/cs00000-ek37-c-host-v15-20260822T103131Z.boot.json) | One-command Janet/JF15 boot reached CP/M Plus `A>` and served 22 NetDisk requests / 66 records at 19,200/8O1, with no retries, target resets or UART errors. |
| EK37, truncated Janet header: [failed capture](evidence/juku-serial/cs00000-ek37-diag06-20260822T162818Z.log) | The `Wait` state was a host parser defect. Recovery after a truncated header followed by directed polls is covered by `host/tests/core_test.c`; it supplies no additional target-hardware diagnosis. |
| EK37, fixed C host `0.3.1-m6`: [DIAG 0.6 capture](evidence/juku-serial/cs00000-ek37-diag06-fixed-20260822T183458Z.boot.json) | Janet/JF15 reached NetDisk v3 without bootstrap rejects or extension/stream retries. Bare `DIAG` detected EK37 and displayed help; `DIAG ALL` passed on screen without the JukuNet diagnostic ABI. The session served 59 reads / 177 records and exited 0, with no retries, bootstrap restarts, target resets, reconnects or UART errors. |

The removed `#0031` pair has not repeated the native C-host path. Its controlled
comparison with EK37 remains open.

### USB/RS-232 adapter comparison

The [adapter investigation](ft232bl-adapter-investigation.md) owns the
Diymore FT232BL wiring, retained comparison captures, and owner-reported
August 28 retest. The reported corrected selector orientation and replacement
charge-pump capacitors enabled
CS00000 C9/V16 boot and retry-free NetDisk reads through the onboard MAX232/DB9
route. The capacitor replacement's independent effect was not isolated.
Earlier receive silence does not establish a Juku USART fault; the unchanged
machine also passed the [CP2102/MAX3232 control](evidence/juku-serial/cs00000-ek37-cp2102-control-20260822T202538Z.boot.json).

## Follow-up from the August investigation

The [deployment profile](machines/CS00000.json) owns the current fitted
firmware and qualification scope. The August investigation left these repair
and comparison tasks:

- Do not use the failed CS00000 PSU until both parallel primary capacitors and
  the affected primary-side circuitry have been repaired and verified.
- With the known-working CS00024 PSU, record the beep sequence and board rails
  if the startup symptom returns.
- Preserve and repeatedly dump the removed `#0031` D15/D16 pair, then
  inspect/clean its socket contacts before a controlled comparison run. The
  reported EK37 cold starts were successful, but their count was not recorded.
- Characterize the intermittent silent/continuous-tone cold-start symptom as
  a separate power/reset/clock investigation.
