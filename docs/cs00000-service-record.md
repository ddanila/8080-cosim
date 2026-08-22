# CS00000 service record

Status date: 2026-08-22

CS00000 is a home-lab Juku received from Arvutimuuseum. Its fitted stock ROM
identifies itself on screen as ROM `#0031`, RomBios `3.43`, and Janet `1.2`.
Those strings are owner-observed; the two ROM devices have not been dumped in
this session, so no content hash is claimed.

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

CS00000 was subsequently tried with the power supply from CS00024. It produced
a short startup beep, but normally produced no visible display output. On one
attempt the display contained garbage, establishing that the monitor and at
least part of the physical video-output path could produce a signal; it does
not establish correct video timing, framebuffer contents, CPU execution, or
successful POST. No further diagnosis is claimed yet, and continued bench
experiments are pending.

This new state supersedes the earlier observation that CS00000 generally
reached the monitor. It does not by itself prove that the mainboard was damaged
by the PSU failure. The prior intermittent silence/continuous-tone starts and
the failed primary capacitor may be related, but that remains only a hypothesis
until the supply and board rails/reset/clock behavior are measured.

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

## V15 failure isolation

The retired Python stock-fastboot wrapper successfully loaded and executed the
exact 128-byte JF15 core at 0100h, but exhausted its fixed extension-probe
window after roughly four seconds and returned to 9,600-baud stock discovery.
The display remained at `Janet Load 01`.

Without RESET or another stock transfer, a direct 19,200/8N1 attachment then
received the core's `C5` acknowledgement immediately. It authenticated the
267-byte extension and 9,267-byte ZX0 stream, installed 16,384 system bytes
with CRC16/IBM `1C42`, and entered NetDisk v3. The transfer took 6.28 seconds
for the bulk phase and needed zero extension or stream retries. The first disk
request arrived 6.945 seconds after attachment. Exact artifact identities and
measurements are retained in
[`evidence/juku-serial/cs00000-stock-v15-20260821.json`](evidence/juku-serial/cs00000-stock-v15-20260821.json).

This proves the failed one-command run was a host synchronization policy bug:
the stock-loaded core and CS00000's 19,200-baud receive path were both alive.
The portable C host `0.3.0-m6` consequently admits exact JF15, adapts Janet
line-turn delay only when the client resumes polling or rejects a frame, and
probes the core until the configured boot deadline. Simulator regressions
cover a five-second core delay and the complete stock-ROM-to-CP/M path. A
physical cold run with the new C host remains the final confirmation.

## Remaining work

- Do not use the failed CS00000 PSU until both parallel primary capacitors and
  the affected primary-side circuitry have been repaired and verified.
- With the known-working CS00024 PSU, record the exact beep sequence and check
  the CS00000 supply rails at the board, reset, CPU clock, and earliest POST
  progress before inferring a video-only fault.
- Repeat the stock-assisted JF15 cold boot using C host `0.3.0-m6`; retain its
  log and capture.
- Characterize the intermittent silent/continuous-tone cold-start symptom as
  a separate power/reset/clock investigation.
- Do not replace D11 based on the superseded suspicion: local D11 diagnostics,
  stock Janet, 19,200 Fastboot reception, and sustained NetDisk all passed.
