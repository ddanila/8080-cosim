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

### EK37 ROM-swap discriminator

Later on 2026-08-22, the owner replaced the stock `#0031` pair with the known
EktaSoft 3.7 / Serial `#0037` ROM pair. CS00000 then started normally and
produced a correct display. Subsequent repeated cold starts remained 100%
successful at the time of reporting; the exact run count was not recorded.

This is strong evidence against a broad post-PSU mainboard or video-output
failure. It narrows the immediate no-display behavior to the removed `#0031`
ROM pair, its socket/contact state, or a firmware-specific startup dependency.
It does not yet prove that either `#0031` device is electrically bad: changing
the ROMs also reseated the sockets and changed the exact cold-start event. The
`#0031` pair should be preserved, identified by socket, read repeatedly, and
compared before any repair conclusion.

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
physical cold run with the new C host was subsequently completed as described
below.

### Native C-host physical confirmation

On 2026-08-22, with the known-working EK37 / RomBios 3.43m pair fitted, native
C host `0.3.0-m6` completed the complete stock-assisted V15 path from one
command. It learned Janet identity `02 -> 01`, sent the 128-byte core with no
reject and a zero-millisecond destination-zero guard, switched to
19,200/8N1, received the core acknowledgement after two probes, and installed
the 9,267-byte compressed stream with CRC16/IBM `1C42`. Extension and stream
retry counts were both zero.

CP/M Plus reached `A>` and served 22 NetDisk read requests / 66 records at
19,200/8O1. The session ended cleanly with exit 0 and counters `rx=370`,
`tx=14066`, `retries=0`, `target-resets=0`, and `uart-errors=0`. The portable
evidence converter accepts the 371-record capture and matching 22-request log.
The retained artifacts begin at
[`cs00000-ek37-c-host-v15-20260822T103131Z.boot.json`](evidence/juku-serial/cs00000-ek37-c-host-v15-20260822T103131Z.boot.json).

This physically confirms the adaptive C-host/JF15 implementation on CS00000.
It does not replace the still-useful controlled `#0031` comparison: EK37 was
fitted during this run, so the exact removed stock pair has not yet repeated
the new-host path.

### Subsequent `Wait` state: host parser defect

A subsequent EK37 run accepted Janet identity `02 -> 01` but left the stock
loader visibly in `Wait`. This did not reproduce a target USART or mainboard
failure. The binary capture shows a truncated data-frame header
`E4 E4 02 01 07` immediately followed by repeated valid directed poll frames.
The C parser treated the first byte of the next poll as a length of 228 and,
after the resulting checksum failure, retained an old complete poll rather
than the newest incomplete frame prefix. It consequently received 22,667
bytes but transmitted only 18 before its stock-bootstrap timeout.

Host `0.3.1-m6` recovers to the newest incomplete Janet sync/header, and the
exact truncated-header/repeated-poll pattern is a portable core regression.
All Linux host gates, including complete stock-V15 cosim boot, pass with the
fix. The diagnostic run itself was postponed when CS00000 was switched off;
no additional hardware conclusion is drawn from this failed host session.
The retained log and capture begin at
[`cs00000-ek37-diag06-20260822T162818Z.log`](evidence/juku-serial/cs00000-ek37-diag06-20260822T162818Z.log).

### Post-fix physical confirmation and DIAG 0.6

The next cold experiment used fixed host `0.3.1-m6` and the latest CP/M Plus
native recovery image. The already-active EK37 Janet session was learned as
`02 -> 01`; the one-record stock bootstrap completed with five ACKs and zero
rejects. JF15 then acknowledged after two probes, accepted its extension and
9,267-byte compressed stream with CRC16/IBM `1C42`, and reached NetDisk v3
without extension or stream retries. The first valid disk request arrived
8.234 seconds after host start.

At the physical `A>` prompt, bare `DIAG` detected the fitted EK37 ROM and
showed the new no-argument help behavior. `DIAG ALL` then reported every test
as `PASS` on screen. This physically confirms the self-contained DIAG 0.6 path
on a known stock/remix ROM without depending on the JukuNet ROM diagnostic
ABI. The clean session served 59 read requests / 177 records and stopped with
exit 0, zero retries, bootstrap restarts, target resets, reconnects, or UART
errors. Its retained evidence begins at
[`cs00000-ek37-diag06-fixed-20260822T183458Z.boot.json`](evidence/juku-serial/cs00000-ek37-diag06-fixed-20260822T183458Z.boot.json).

### USB/RS-232 adapter comparison

A Diymore multifunction FT232BL module (`0403:6001`, Linux `ftdi_sio`, DB9
male, socketed MAX232CPE) was evaluated as an alternative to the known
CP2102/MAX3232 chain. Its local
DB9 pin-2/pin-3 loopback returned exact bytes at 9,600/8O1, 19,200/8N1, and
19,200/8O1. With the DB9 open, pin 3 measured approximately -9 V relative to
pin 5 while pin 2 measured 0 V. These observations prove a working local USB
UART/DB9 loop but do not by themselves prove interoperability with a separate
RS-232 driver.

Repeated Juku trials used the documented X3 wiring and the existing local
X3.10/RTS-to-X3.5/CTS loop. Both complete data mappings were tried twice and
left EK37 in `Wait`; native host `0.3.1-m6` received zero bytes before its
bounded timeout. Its zero transmit count is expected because the stock host
does not answer before receiving a valid Janet request. A separate
`INPCK|PARMRK` 9,600/8O1 capture received neither data nor parity, framing, or
break markers. A direct FTDI-to-CP2102/MAX cross-test also
received zero bytes in both directions under both attempted data orders. Since
that temporary join was not electrically instrumented, this does not prove
which multifunction-module path or join was at fault. The Diymore module is
therefore **not qualified for Juku**, but is not declared defective.

A later full far-end loop ran through the selected onboard MAX232, both DB9
joins, the entire Juku harness, and a motherboard-end X3.4-to-X3.9 short. It
passed exact payloads at 9,600/8O1, 19,200/8N1, and 19,200/8O1. This closes both
data conductors but still does not exercise an external signal-ground
reference. The strongest remaining common explanation is therefore the
unmeasured module-internal DB9.5 bond to MAX232/TTL ground, followed by a
board-local receiver/socket/selector fault visible only with an independently
referenced driver. The fitted plain MAX232CPE with four 0.1 µF `C104`
charge-pump capacitors is a genuine BOM/application-circuit mismatch, but it
affects transmitter margin and does not explain the isolated receive silence.

The original CP2102 + MAX3232 chain was then restored without changing
CS00000, EK37, the Juku-side cable, or host artifacts. It immediately learned
Janet `02 -> 01`, completed stock/JF15 boot with zero rejects or retries,
reached `A>`, served 30 reads / 90 records, and stopped with exit 0 and zero
UART errors. This control keeps CS00000, its X3 wiring, local CTS loop, and the
production host qualified; only the alternative adapter path remains open.
Evidence begins at
[`cs00000-ek37-cp2102-control-20260822T202538Z.boot.json`](evidence/juku-serial/cs00000-ek37-cp2102-control-20260822T202538Z.boot.json).
The exact module identity, selector interpretation, corrected live assumptions,
and next discriminating bench test are recorded in
[`ft232bl-adapter-investigation.md`](ft232bl-adapter-investigation.md).

## Remaining work

- Do not use the failed CS00000 PSU until both parallel primary capacitors and
  the affected primary-side circuitry have been repaired and verified.
- With the known-working CS00024 PSU, record the exact beep sequence and check
  the CS00000 supply rails at the board. The successful EK37 start lowers the
  priority of broad reset/clock/video diagnosis unless the symptom returns with
  EK37.
- Preserve and repeatedly dump the removed `#0031` D15/D16 pair, then
  inspect/clean its socket contacts before a controlled comparison run. The
  repeated EK37 cold-start control is complete and remained fully stable.
- Characterize the intermittent silent/continuous-tone cold-start symptom as
  a separate power/reset/clock investigation.
- Do not replace D11 based on the superseded suspicion: local D11 diagnostics,
  stock Janet, 19,200 Fastboot reception, and sustained NetDisk all passed.
