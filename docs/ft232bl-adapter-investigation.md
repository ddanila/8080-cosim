# Diymore FT232BL adapter investigation

Status date: 2026-08-28

This note records the desk review and bench evidence for the Diymore
USB/RS-232/TTL/RS-485 module tried with Juku CS00000. It deliberately separates
what the measurements prove from hypotheses that still need an electrically
observed two-endpoint test.

## Device identity and selector topology

The exact product is the
[Diymore multifunction converter](https://www.diymore.cc/products/usb-to-serial-rs232-uart-ttl-rs485-db9-adapter-converter-module-for-ftdi-ft232bm-bl-provide-the-usb-driver-for-linux-for-windows).
Linux enumerated it as `0403:6001`, bound it to `ftdi_sio`, and created
`/dev/serial/by-id/usb-FTDI_USB__-__Serial-if00-port0`. Its USB descriptor has
`bcdDevice=4.00`, no serial string, 64-byte bulk endpoints, and reports a
bus-powered 90 mA configuration. The USB ID alone does not identify the FTDI
generation, but the product photograph and the owner's board both show an
`FT232BL` package. The socketed line-interface parts are a `MAX232CPE` and a
MAX485-family transceiver; the former must no longer be described as a
MAX3232-family device.

FTDI describes the BL as the lead-free FT232BM, its second-generation USB UART,
not as an FT232R. The [FT232BL/BQ datasheet](https://ftdichip.com/wp-content/uploads/2020/08/DS_FT232BL_BQ.pdf)
specifies 7/8 data bits, 1/2 stop bits, odd/even/mark/space/no parity,
line-break support, and RS-232 rates through 1 Mbaud. Linux exposed the normal
16 ms receive latency timer. Neither that latency nor the generation's speed
limit can turn a repeated 90-second Janet request into zero received bytes.

The two shunts occupy the `TXD` and `RXD` rows of a three-column header whose
silkscreen reads `RS232-RS485`. The photograph therefore supports a
per-direction RS-232/RS-485 selection interpretation, but the vendor publishes
neither a schematic, connector pinout, nor jumper instructions. The earlier
claim that these select TTL versus a combined RS-232/RS-485 group was too
strong and is withdrawn. The empirical contracts are narrower and sufficient:

- with the shunts in the photographed positions, the DB9 loop works;
- removing the MAX485 does not change that DB9 loop or cure the Juku failure;
- with both shunts open, the TTL header plus the known external level converter
  boots Juku successfully;
- using the TTL header while the shunts were installed produced an exact echo
  of every host byte; the mechanism was not instrumented, so it is recorded as
  simultaneous-path contention/routing evidence rather than assigned to one
  chip.

## Correct Juku cable contract

The board drawings and qualified CS00015 continuity give this Juku-side
contract:

| Juku X3 | Meaning | PC-style DB9 DTE |
| --- | --- | --- |
| X3.9 | Juku `SOUT` | pin 2, adapter receive |
| X3.4 | Juku `SIN` | pin 3, adapter transmit |
| X3.7 | signal ground | pin 5 |
| X3.10 to X3.5 | local Juku `RTS` to `CTS` loop | no host handshake wire required |

The portable host correctly uses software flow control `none`. Asking the
adapter to drive Juku CTS is unnecessary with this cable; the local X3 loop is
the already-qualified arrangement. The owner checked connector numbering,
continuity, ground, and the RTS/CTS short before the comparison.

## Bench observations

### Local module tests

With physical DB9 pins 2 and 3 shorted, the module returned the exact transmitted
payload at all three tested configurations:

- 9,600 baud, 8O1: 23/23 bytes;
- 19,200 baud, 8N1: 24/24 bytes;
- 19,200 baud, 8O1: 24/24 bytes.

With the DB9 open, pin 3 measured approximately -9 V relative to pin 5 and pin
2 measured 0 V. An open-port transmit returned 20 zero bytes rather than the
transmitted payload, so the successful exact loop was not merely a permanent
software-internal echo.

The open-input result is not a valid receiver qualification. A MAX232 receiver
has defined positive- and negative-going thresholds and input hysteresis, but
0 V is inside the transition region rather than a valid RS-232 mark or space.
The fitted part's
[MAX220-MAX249 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/max220-max249.pdf)
gives a 3-7 kΩ receiver input, 1.8 V typical/2.4 V maximum high threshold,
0.8 V minimum/1.3 V typical low threshold, and 0.5 V typical hysteresis. Juku's
9,600 and 19,200 baud are not intrinsically too fast for a healthy MAX232 path.

Attempts to observe BREAK and a continuous `00` stream with a handheld DC
voltmeter left pin 3 apparently steady at -9 V. That conflicts with the exact
physical loop result and is therefore **inconclusive**, not proof of inverted
data or a stuck transmitter. A DMM can hide short serial transitions, and the
module's undocumented routing adds another uncertainty. The FT232BL itself
does support BREAK; Linux also defines driver BREAK control, but neither fact
validates this particular voltage-observation method.

### Complete far-end loop

The later test kept the photographed shunt positions and assembled the whole
physical harness from USB through both DB9 connections to the Juku motherboard
connector, with the harness disconnected from Juku. Shorting motherboard-side
X3.4 to X3.9 returned exact payloads at all three settings:

- 9,600/8O1: 18/18 bytes;
- 19,200/8N1: 19/19 bytes;
- 19,200/8O1: 19/19 bytes.

This is stronger than the local pin-2/pin-3 loop: it qualifies the selected
FTDI transmit path, MAX232 transmitter, both DB9 joins, both data conductors,
MAX232 receiver, selected FTDI receive path, and UART framing as one closed
loop. It still does **not** qualify data-direction assignment or the external
signal-ground path. Joining the two data conductors makes their order
symmetrical, and a return into the same transceiver does not need cable pin 5
to be bonded to a second device's ground. That limitation becomes central to
the diagnosis below.

### MAX232 capacitor audit

The installed part is a plain `MAX232CPE`, while the product photograph shows
four charge-pump capacitors marked `C104` (0.1 µF). This is a real design/BOM
mismatch. Analog Devices specifies 1 µF for plain MAX232 and 0.1 µF for the
improved MAX232A; its
[MAX232 capacitor FAQ](https://ez.analog.com/jp/other-products/w/faqs/32681/max232)
warns that a plain MAX232 with 0.1 µF may not generate enough voltage. The
[MAX220-MAX249 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/max220-max249.pdf)
likewise separates the 1 µF MAX232 circuit from the 0.1 µF MAX232A circuit.

This mismatch is **not** a sufficient explanation for the observed receive
silence. The charge pump supplies this adapter's RS-232 transmitters. Its
receiver input is specified from the 5 V logic supply and presents the same
3-7 kΩ load as MAX3232. The measured -9 V idle and both exact loopbacks also
show that this instance can generate and receive its own levels. The mismatch
can reduce transmitter margin under an external load and should be corrected
before qualifying the module, but replacing the chip solely to fix Juku-to-host
reception would be an unsupported diagnosis.

### 2026-08-28 capacitor-replacement retest

The owner replaced the four charge-pump capacitors to match the plain
`MAX232CPE` application circuit, then repeated the bench work with the same
`0403:6001` / `ftdi_sio` adapter identity. A stronger local DB9 pin-2/pin-3
loop returned every byte exactly: 6,144 bytes at 9,600/8O1, 12,288 at
19,200/8N1, and 12,288 at 19,200/8O1.

The first C9 Network ROM trial exposed exact local echo: the host transmitted
11,993 bytes of V16 probes and received the same 11,993-byte stream, while
three deliberately non-protocol raw payloads were also returned byte-for-byte.
A temporary host echo filter correctly removed that stream and passed a full
echo-plus-real-target cosim, but a reset-controlled physical retry contained
only 11,963 returned host bytes and no C9 response. This proved that filtering
could not repair the physical routing and was not retained in the host.

The owner then found the decisive assembly error: both selector shunts had
been installed 90 degrees from their orientation in the product photograph.
Removing them eliminated the echo but disconnected the DB9 path (`tx=6215`,
`rx=0` after a reset-controlled C9 run). Installing them exactly as photographed
also eliminated the echo, then let the unchanged host complete the C9 V16
stream and switch from 19,200/8N1 to 19,200/8O1 NetDisk. The final V16 reply
was missed, but the intended NetDisk confirmation followed. By the end of the
session the host had completed 22 reads serving 66 records, with zero retries
and zero UART errors. The host's final exit status 4 occurred only after the
USB serial device itself disappeared during shutdown; it does not qualify the
successful CS00000 traffic or indicate a target-side failure.

This qualifies the corrected selector orientation, FT232BL/MAX232 data path,
external ground reference, CS00000 C9 boot, framing handoff, and sustained
read traffic together. The capacitor replacement corrects the documented
plain-MAX232 mismatch, but its independent effect is not isolated because the
selector orientation was corrected in the same revisit. The historical
failure was therefore hardware configuration, not a host-parser defect.

### Juku comparison

Two fixed-host `0.3.1-m6` attempts were retained:

| Arrangement | Target result | Host result |
| --- | --- | --- |
| documented data order | EK37 stayed in `Wait` | timeout, `rx=0`; no reply attempted |
| data pair swapped | EK37 stayed in `Wait` | timeout, `rx=0`; no reply attempted |

The raw captures and logs begin at
[`cs00000-ek37-ft232-20260822T185556Z.log`](evidence/juku-serial/cs00000-ek37-ft232-20260822T185556Z.log)
and
[`cs00000-ek37-ft232-crossed-20260822T192424Z.log`](evidence/juku-serial/cs00000-ek37-ft232-crossed-20260822T192424Z.log).
Receiving zero raw bytes rules out Janet framing, parity interpretation, and
the higher-level host parser as the immediate failure mechanism.

On 2026-08-23 the owner confirmed that both complete mappings had each been
tried twice: DB9.2 to X3.4 plus DB9.3 to X3.9, and DB9.2 to X3.9 plus DB9.3 to
X3.4. A separate raw 9,600/8O1 receiver was armed with POSIX `INPCK|PARMRK`
and without `IGNPAR` before RESET and `TN`. It received neither valid bytes nor
parity/framing/break markers. Two matching-artifact production-host attempts
then again ended with `rx=0`; their logs are retained as
[`cs00000-ek37-ft232-direct-20260823T193804Z.log`](evidence/juku-serial/cs00000-ek37-ft232-direct-20260823T193804Z.log)
and
[`cs00000-ek37-ft232-crossed-20260823T195054Z.log`](evidence/juku-serial/cs00000-ek37-ft232-crossed-20260823T195054Z.log).

The `tx=0` field is not evidence that the adapter-to-Juku direction also
failed. The stock host deliberately waits for a checksum-valid Janet request
before writing its first response; zero receive therefore causes zero transmit
by construction. Only the Juku-to-adapter receive direction is isolated by
these host sessions.

With the cable disconnected from the Diymore module while Juku displayed
`Wait`, the FTDI-facing cable end measured 0 V on DB9.2 and approximately -9 V
on DB9.3 relative to DB9.5. This identifies the Juku transmitter at pin 3 for
that particular assembled mapping and confirms a valid idle magnitude at the
unloaded cable end. It does not show the positive level during a byte, the
level under the MAX232 receiver load, or the ground reference after the two
devices are joined. The cable was crossed afterward but not remeasured before
the bench session ended; the repeated full mappings above remain the stronger
direction evidence.

A temporary FT232BL-to-known-CP2102/MAX3232 cross-test received zero bytes in
both directions at 9,600/8O1, 19,200/8N1, and 19,200/8O1, under both attempted
data orders. Ground and line levels were not captured while that temporary join
was assembled, so it is useful negative evidence but not sufficient to assign
the fault to a particular driver, receiver, selector, or conductor.

Finally the known CP2102 + MAX3232 chain was restored without changing the
Juku, ROM, Juku-side cable, or host artifacts. It immediately completed the
stock/JF15 path, reached `A>`, and served 30 disk reads / 90 records with zero
retries or UART errors. Evidence begins at
[`cs00000-ek37-cp2102-control-20260822T202538Z.boot.json`](evidence/juku-serial/cs00000-ek37-cp2102-control-20260822T202538Z.boot.json).

## Corrections to the live diagnosis

The desk review corrects or narrows several live suggestions:

1. `0403:6001` did not establish an FT232R. The photographed part is FT232BL,
   and FTDI documents it as the lead-free FT232BM generation.
2. FT232R EEPROM signal-inversion settings must not be projected onto FT232B.
   FTDI's [D2XX Programmer's Guide](https://ftdichip.com/wp-content/uploads/2023/09/D2XX_Programmers_Guide.pdf)
   gives the FT232B EEPROM structure only the common header, whereas the FT232R
   structure separately contains `InvertTXD`, `InvertRXD`, and related fields.
   Reading the external EEPROM may still identify descriptors and power options,
   but it is not a supported TX/RX inversion fix for this generation.
3. The yellow shunts route RXD and TXD between interface groups; they are not a
   software-controlled crossover. Their exact schematic must not be inferred
   beyond the photographed silkscreen and empirical open/installed behavior.
4. Juku CTS was already handled correctly by the local X3.10-to-X3.5 loop. Host
   RTS was not missing from the known cable.
5. A two-pin local loopback proves an end-to-end loop through some local transmit
   and receive path, but not independent transmit and receive interoperability.
6. The BREAK/DMM and open-receiver observations are not reliable polarity or
   health tests and must not be promoted into a fault diagnosis.
7. `tx=0` in a stock-bootstrap timeout is a consequence of `rx=0`, not an
   independent transmit-path result.
8. Plain MAX232 with 0.1 µF charge-pump capacitors is outside the documented
   application circuit, but that concerns the adapter's transmitter margin and
   does not explain a receiver-only zero-byte result.
9. MAX232 and MAX3232 are not opposite-polarity alternatives. Both perform the
   same RS-232 inversion, present 3-7 kΩ receiver inputs, and have nearly the
   same receiver thresholds at 5 V. The known MAX3232 chain's success does not
   imply a protocol or polarity difference.

## Datasheet compatibility check

The Juku driver is not nominally too weak for the fitted receiver. The local
K170AP2 source is the Soviet counterpart of SN75150. TI's
[SN75150 datasheet](https://www.ti.com/lit/gpn/SN75150) guarantees at least +5 V
and at most -5 V into 3-7 kΩ, with transition times below 2 µs at the full
2,500 pF load. The local K170AP2 reference gives the same +/-5 V limits. Both
MAX232 and the successful
[MAX3232](https://www.ti.com/lit/ds/symlink/max3232.pdf) specify 3-7 kΩ
receiver inputs and maximum positive thresholds of 2.4 V. Their typical
thresholds differ by only tenths of a volt, with no polarity difference.

Therefore a healthy, correctly grounded MAX232 must accept a healthy Juku
K170AP2 waveform. If a scope later shows that it does not, the result diagnoses
this board, this socketed component, its selector/contact path, or its ground;
it does not establish a generic MAX232-versus-Juku incompatibility.

## Ranked diagnosis

CS00000, its D11 path, the Juku cable, local CTS loop, host, and images are
qualified by the immediate CP2102 control. The Diymore adapter is **not
qualified for Juku**. The new evidence rules out several broad explanations but
still does not identify one failed component.

1. **DB9 signal-ground bond or external reference path.** This is now the
   strongest single untested explanation. Neither the local nor the complete
   far-end data loop requires DB9.5 to connect two device grounds. A missing or
   high-resistance DB9.5-to-board-ground bond explains the two loopback passes,
   zero external reception, the failed adapter-to-adapter join, and the working
   TTL-header path, whose header GND was explicitly connected. The owner's
   cable continuity check qualifies the harness; the module's internal DB9.5
   bond to MAX232 pin 15/TTL GND remains unrecorded.
2. **Board-local MAX232 receive path under an independently referenced load.**
   A damaged or counterfeit receiver, socket contact, selector contact, or
   waveform collapse visible only when the Juku driver and module receiver are
   joined remains possible. The far loop proves the same receiver works with
   its own transmitter, so this must be observed at MAX232 RIN and ROUT rather
   than inferred from another loop.
3. **Unverified selector topology.** MAX485 removal makes direct contention
   from that socketed chip unlikely, and restored photographed positions pass
   DB9 loopback. Hidden routing remains possible but ranks below ground and a
   board-local analog/contact fault.
4. **Data crossover.** Both end-to-end mappings were exercised twice. A final
   post-swap voltage/continuity map would improve the record, but repeated zero
   receive in both mappings makes crossover a low-ranked explanation.

Software framing, baud rate, host parsing, FTDI latency, RTS/CTS, FT232R-style
EEPROM inversion, MAX485 presence, and a generic MAX232/MAX3232 polarity or
threshold difference are rejected by direct evidence or the datasheets.

## Next discriminating test

If this module is revisited, do not repeat blind crossover or Janet tests. Use
this order:

1. With everything unpowered, measure resistance from module DB9.5 to the TTL
   header GND, RS485 terminal GND, MAX232 pin 15, and USB logic ground. Expect a
   near-short, not merely a DMM voltage reference. Reconfirm cable DB9.5 to
   X3.7 separately.
2. If the module bond is open or high, temporarily join TTL-header GND to Juku
   X3.7 with power off, then retry the documented data pair. Do not substitute
   either connector shell for signal ground.
3. If ground is sound, map DB9.2/3 to MAX232 RIN/TOUT and the jumper centres by
   powered-off continuity. This replaces the remaining selector inference with
   facts.
4. Use a common-ground breakout and send repeating `55` from Juku or the known
   adapter. Scope the selected MAX232 RIN and matching ROUT simultaneously.
   Record positive and negative peaks under load. A bipolar-rated 10x probe is
   required at RIN; use a logic probe only at ROUT/FT232 RXD.
5. Only after those checks, swap the socketed part as a component diagnostic.
   A genuine `MAX232ACPE+` or ST232C matches the fitted 0.1 µF capacitors. Such
   a swap tests this IC and corrects transmitter-margin noncompliance; it must
   not be presented in advance as the proven receive fix.

No EEPROM write, driver replacement, further host change, or Juku hardware
change is justified by the current evidence.
