# Diymore FT232BL adapter investigation

Status date: 2026-08-28

The corrected selector orientation and replacement charge-pump capacitors
enabled the recorded CS00000 C9/V16 boot and NetDisk session. This note
retains the device configuration, measurements and limits of that result.

## Device identity and selector topology

The exact product is the
[Diymore multifunction converter](https://www.diymore.cc/products/usb-to-serial-rs232-uart-ttl-rs485-db9-adapter-converter-module-for-ftdi-ft232bm-bl-provide-the-usb-driver-for-linux-for-windows).
Linux enumerated it as `0403:6001`, bound it to `ftdi_sio`, and created
`/dev/serial/by-id/usb-FTDI_USB__-__Serial-if00-port0`. Its USB descriptor has
`bcdDevice=4.00`, no serial string, 64-byte bulk endpoints, and reports a
bus-powered 90 mA configuration. The USB ID alone does not identify the FTDI
generation, but the product photograph and the owner's board both show an
`FT232BL` package. The socketed line-interface parts are a `MAX232CPE` and a
MAX485-family transceiver.

FTDI describes the BL as the lead-free FT232BM, its second-generation USB UART,
not as an FT232R. The [FT232BL/BQ datasheet](https://ftdichip.com/wp-content/uploads/2020/08/DS_FT232BL_BQ.pdf)
specifies 7/8 data bits, 1/2 stop bits, odd/even/mark/space/no parity,
line-break support, and RS-232 rates through 1 Mbaud. Linux exposed the normal
16 ms receive latency timer. Neither that latency nor the generation's speed
limit can turn a repeated 90-second Janet request into zero received bytes.

The two shunts occupy the `TXD` and `RXD` rows of a three-column header whose
silkscreen reads `RS232-RS485`. The photograph therefore supports a
per-direction RS-232/RS-485 selection interpretation, but the vendor publishes
neither a schematic, connector pinout, nor jumper instructions. The internal schematic remains unverified. The observed behavior is:

- with the shunts correctly oriented as photographed, the DB9 loop and
  August 28 Juku boot work;
- removing the MAX485 did not change the earlier DB9 loop or cure the
  failed Juku setup;
- with both shunts open, the TTL header plus the known external level converter
  boots Juku successfully;
- using the TTL header in the earlier installed-shunt setup produced an exact echo
  of every host byte; the mechanism was not instrumented, so it is recorded as
  simultaneous-path contention/routing evidence rather than assigned to one
  chip.

FT232R EEPROM inversion fields do not apply to this FT232B generation.
The [D2XX Programmer's Guide](https://ftdichip.com/wp-content/uploads/2023/09/D2XX_Programmers_Guide.pdf)
gives FT232B only the common EEPROM header; the FT232R structure separately
contains `InvertTXD`, `InvertRXD`, and related fields. EEPROM inversion is
therefore not a supported remedy for this module.

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
to be bonded to a second device's ground. The later successful Juku test supplies the missing external-driver evidence.

### MAX232 capacitor audit

Before the August 28 replacement, the plain `MAX232CPE` was paired with
four charge-pump capacitors marked `C104` (0.1 µF), as in the product photograph. This was a design/BOM
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
can reduce transmitter margin under an external load. The August 28
replacement corrected it, but its effect on reception was not isolated.

### 2026-08-28 capacitor-replacement retest

The owner replaced the four charge-pump capacitors to match the plain
`MAX232CPE` application circuit, then repeated the bench work with the same
`0403:6001` / `ftdi_sio` adapter identity. A stronger local DB9 pin-2/pin-3
loop returned every byte exactly: 6,144 bytes at 9,600/8O1, 12,288 at
19,200/8N1, and 12,288 at 19,200/8O1.

The initial C9 trial returned the host's transmitted probes and deliberately
non-protocol payloads byte-for-byte, with no target response. This was local
echo in the adapter path; a software filter could not restore communication.
The owner then found the decisive assembly error: both selector shunts had
been installed 90 degrees from their orientation in the product photograph.
Removing them eliminated the echo but disconnected the DB9 path (`tx=6215`,
`rx=0` after a reset-controlled C9 run). Installing them exactly as photographed
also eliminated the echo, then let the unchanged host complete the C9 V16
stream and switch from 19,200/8N1 to 19,200/8O1 NetDisk. The final V16 reply
was missed, but the intended NetDisk confirmation followed. By the end of the
session the host had completed 22 reads serving 66 records, with zero retries
and zero UART errors. The host's final exit status 4 occurred only after the
USB serial device itself disappeared during shutdown; that exit status does
not invalidate the preceding CS00000 traffic or establish a target-side failure.

This qualifies the corrected selector orientation, FT232BL/MAX232 data path,
external ground reference, CS00000 C9 boot, framing handoff, and sustained
read traffic together. The capacitor replacement corrects the documented
plain-MAX232 mismatch, but its independent effect is not isolated because the
selector orientation was corrected in the same revisit. The historical
failure was therefore hardware configuration, not a host-parser defect.
This recorded session does not establish endurance or compatibility with every
machine.

### Earlier comparison evidence

Before the selector correction, both cable data orders produced zero received
bytes. The retained direct/crossed logs are from
[August 22](evidence/juku-serial/cs00000-ek37-ft232-20260822T185556Z.log),
[August 22 crossed](evidence/juku-serial/cs00000-ek37-ft232-crossed-20260822T192424Z.log),
[August 23](evidence/juku-serial/cs00000-ek37-ft232-direct-20260823T193804Z.log), and
[August 23 crossed](evidence/juku-serial/cs00000-ek37-ft232-crossed-20260823T195054Z.log).
Those runs did not isolate a faulty component. Their `tx=0` is expected:
the stock host waits for a valid Janet request before replying, so `rx=0`
also prevents transmission.

The unchanged Juku, ROM, cable, and host artifacts worked with the known
CP2102/MAX3232 control: stock/JF15 reached `A>` and served 30 reads / 90 records
without retries or UART errors. The
[control boot record](evidence/juku-serial/cs00000-ek37-cp2102-control-20260822T202538Z.boot.json)
preserves its artifact identities. Unloaded voltage readings and temporary
adapter cross-tests did not capture loaded waveforms or joined-device ground
references; they do not establish a MAX232 incompatibility.

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

## If the symptom returns

Preserve the successful selector orientation and replacement capacitor
configuration. Compare a new capture with the August 28 result before
changing host software or Juku components. If reception again becomes silent,
verify the cable and module signal-ground bonds, map the selector/DB9 paths
by powered-off continuity, and observe MAX232 RIN and ROUT under an
independently referenced driver. The former ground, receiver and selector
hypotheses are fallback diagnostic checks, not current unresolved faults.
