# Diymore FT232BL adapter investigation

Status date: 2026-08-22

This note records the desk review and bench evidence for the Diymore
USB/RS-232/TTL/RS-485 module tried with Juku CS00000. It deliberately separates
what the measurements prove from hypotheses that still need an electrically
observed two-endpoint test.

## Device identity and selector topology

The exact product is the
[Diymore multifunction converter](https://www.diymore.cc/products/usb-to-serial-rs232-uart-ttl-rs485-db9-adapter-converter-module-for-ftdi-ft232bm-bl-provide-the-usb-driver-for-linux-for-windows).
Linux enumerated it as `0403:6001`, bound it to `ftdi_sio`, and created
`/dev/serial/by-id/usb-FTDI_USB__-__Serial-if00-port0`. The USB ID alone does
not identify the FTDI generation. The product photograph shows an `FT232BL`
package, plus a MAX3232-family RS-232 transceiver and a MAX485-family
transceiver.

FTDI describes the BL as the lead-free FT232BM, its second-generation USB UART,
not as an FT232R. The [FT232BL/BQ datasheet](https://ftdichip.com/wp-content/uploads/2020/08/DS_FT232BL_BQ.pdf)
specifies 7/8 data bits, 1/2 stop bits, all normal parity choices, line-break
support, and rates well above the Juku's 9,600 and 19,200 baud.

The two yellow shunts in the product photograph are individually labelled
`RXD` and `TXD`. The silkscreen places `TTL-UART` on one side and
`RS232-RS485` on the other. They are therefore per-direction routing selectors,
not a DTE/DCE crossover and not one combined RS-232/RS-485 mode selector. Both
directions must be selected toward `RS232-RS485` for the DB9/MAX3232 path. The
owner reported that they were already in that position during the Juku tests.
The board's exact RS-232-versus-RS-485 selection circuitry remains undocumented
because the vendor publishes neither a schematic nor a connector pinout.

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

The open-input result is not a valid receiver qualification. A MAX3232 receiver
has defined positive- and negative-going thresholds and input hysteresis, but
0 V is inside the transition region rather than a valid RS-232 mark or space.
The [TI MAX3232 datasheet](https://www.ti.com/lit/ds/symlink/max3232.pdf) gives
the applicable thresholds and specifies the transceiver to at least 150 kbit/s,
so 19,200 baud is not intrinsically too fast for a healthy MAX3232 path.

Attempts to observe BREAK and a continuous `00` stream with a handheld DC
voltmeter left pin 3 apparently steady at -9 V. That conflicts with the exact
physical loop result and is therefore **inconclusive**, not proof of inverted
data or a stuck transmitter. A DMM can hide short serial transitions, and the
module's undocumented routing adds another uncertainty. The FT232BL itself
does support BREAK; Linux also defines driver BREAK control, but neither fact
validates this particular voltage-observation method.

### Juku comparison

Two fixed-host `0.3.1-m6` attempts were retained:

| Arrangement | Target result | Host result |
| --- | --- | --- |
| documented data order | EK37 stayed in `Wait` | timeout, `rx=0`, `tx=0` |
| data pair swapped | EK37 stayed in `Wait` | timeout, `rx=0`, `tx=0` |

The raw captures and logs begin at
[`cs00000-ek37-ft232-20260822T185556Z.log`](evidence/juku-serial/cs00000-ek37-ft232-20260822T185556Z.log)
and
[`cs00000-ek37-ft232-crossed-20260822T192424Z.log`](evidence/juku-serial/cs00000-ek37-ft232-crossed-20260822T192424Z.log).
Receiving zero raw bytes rules out Janet framing, parity interpretation, and
the higher-level host parser as the immediate failure mechanism.

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
   software-controlled crossover. Swapping the cable cannot compensate for a
   direction left on the TTL side.
4. Juku CTS was already handled correctly by the local X3.10-to-X3.5 loop. Host
   RTS was not missing from the known cable.
5. A two-pin local loopback proves an end-to-end loop through some local transmit
   and receive path, but not independent transmit and receive interoperability.
6. The BREAK/DMM and open-receiver observations are not reliable polarity or
   health tests and must not be promoted into a fault diagnosis.

## Conclusion and next discriminating test

CS00000, its D11 path, the Juku cable, local CTS loop, host, and images are
qualified by the immediate CP2102 control. The Diymore adapter is **not
qualified for Juku**, but the retained evidence does not justify calling it
defective. The unresolved boundary is its undocumented interface selection and
independent RS-232 transmit/receive behavior.

If this module is revisited, do one instrumented test rather than more blind
crossover combinations:

1. Verify both RXD/TXD shunts toward `RS232-RS485` with power removed.
2. Use a breakout and common pin-5 ground. Drive a repeating `55` pattern from
   each endpoint in turn.
3. Observe the driving DB9 pin and receiving DB9 pin with an oscilloscope or
   logic instrument rated for bipolar RS-232. Record idle level, positive and
   negative peaks, and transitions. Do not infer a waveform from a DMM average.
4. Test the FT232BL transmitter against the known CP2102/MAX receiver, then the
   known transmitter against the FT232BL receiver as two separate one-way
   experiments. This distinguishes selector/routing, TX, and RX faults without
   involving Janet or Juku timing.

No EEPROM write, driver replacement, or Juku hardware change is justified by
the current evidence.
