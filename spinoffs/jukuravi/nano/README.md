# Jukuravi Nano firmware

Status: the Stage D1 serial bridge and isolated startup-reset driver are
implemented and guarded; liveness probes remain measurement-gated follow-up
work.

## Serial bridge checkpoint

`jukuravi_bridge/jukuravi_bridge.ino` targets a classic 5 V, 16 MHz,
ATmega328P Arduino Nano. It leaves D0/RX and D1/TX on the Nano's hardware UART
for the onboard USB adapter at 115200 baud and uses the bundled Arduino
`SoftwareSerial` implementation on D8/D9 for the diagnostic ROM's nominal 9600
baud 8N1 link. The pump is byte-transparent and services the slower Juku-to-USB
direction first in bounded chunks. This is sufficient for D0's half-duplex
banner/ACK/survey protocol; it is not a claim of arbitrary simultaneous
full-duplex operation.

TTL-side wiring:

| Nano | Direction | MAX3232-class pin role | Purpose |
|---|---|---|---|
| D8 | input | R1OUT | receive Juku TX after RS-232 level conversion |
| D9 | output | T1IN | send to Juku RX through the first line driver |
| D10 | output | T2IN | assert Juku CTS through the second line driver |
| GND | — | GND | common reference; bond to continuity-confirmed X3 signal ground |

Never connect D8, D9, or D10 directly to X3: X3 is an RS-232-level connector.
The X3 signal/contact assignment remains continuity-gated on the real board.
Use a MAX3232-class two-driver/two-receiver circuit with its datasheet charge
pump capacitors. A MAX3232 is not an isolator: connect its ground to the X3
signal-ground contact only after that contact and the three signals are
continuity-confirmed.

The MAX3232 driver inverts its input, so firmware holds D10/T2IN low to produce
the positive RS-232 control voltage used for asserted CTS. Fit a 10 kOhm
pull-down from T2IN to GND: D10 is high impedance while the Nano bootloader or
reset is active, but the Juku 8251 must see CTS asserted before its diagnostic
ROM starts. This polarity follows the driver/receiver truth tables in the
[TI MAX3232 datasheet](https://www.ti.com/lit/ds/symlink/max3232.pdf). The
second receiver is currently spare.

The onboard D13 LED latches on if the Juku-side `SoftwareSerial` receive FIFO
overflows. Nothing is injected into the USB stream because that would corrupt
the host's framed evidence. Power-cycle or reset the Nano to clear the LED.

## Isolated startup reset checkpoint

Nano D4 is the low-voltage reset-drive output. Wire D4 through a 1 kOhm series
resistor to the optocoupler LED anode, return its cathode to Nano GND, and fit a
10 kOhm pull-down from D4 to Nano GND.
The pull-down keeps the LED off while D4 is high impedance in the bootloader.
The optocoupler transistor or a bidirectional PhotoMOS contact is the only part
that may eventually cross the selected S1 contacts: D4 and Nano GND must never
touch the Juku reset-RC network.

On every sketch start, firmware asserts D4 for 250 ms, releases it, waits a
further 50 ms, and only then enables the transparent bridge. The Intel 8080A
requires RESET for at least three clock cycles; the switch-like 250 ms closure
is deliberately conservative and easy to verify ([Intel MCS-80 Microcomputer
Systems User's Manual](https://www.bitsavers.org/components/intel/MCS80/98-153B_Intel_8080_Microcomputer_Systems_Users_Manual_197509.pdf)).
The portable sequencer uses unsigned elapsed time and is tested across the
`millis()` rollover. The host now deliberately releases DTR for 50 ms and
reasserts it before each real `--port` session, exercising the classic Nano's
DTR-coupled USB auto-reset circuit shown in the [official classic Nano
schematic](https://docs.arduino.cc/resources/schematics/A000005-schematics.pdf)
and starting this sequence. The host logs a successfully sent DTR pulse without
claiming that the physical reset was observed; its durable completion field is
set only after the following transport flush also succeeds. Adapters with
auto-reset disabled require `--no-nano-reset` plus a Nano reset-button press or
power cycle before the session.

This is a firmware and isolated-input checkpoint, not permission to attach the
board side. S1 is SPDT: current evidence identifies S1.1 with `RES_RC` and
S1.2 with the D98/D97 read-data branch, while S1.3 remains unresolved. Measure
which pair closes in the reset position and its polarity/voltage before placing
the isolated contact across any pair.

Build and test with:

```sh
sync/jukuravi_nano_check.sh
```

The always-available host test sends all 256 byte values plus the exact
version-8 ACK through the shared bridge core in both directions, checks the
per-direction work bound and counters, and proves reset assertion, release,
recovery, and rollover boundaries. When `arduino-cli` and the `arduino:avr`
core are installed, the same guard also compiles the actual Nano sketch. To
upload manually after a successful build:

```sh
arduino-cli compile --fqbn arduino:avr:nano:cpu=atmega328 \
  --upload --port /dev/ttyUSB0 \
  spinoffs/jukuravi/nano/jukuravi_bridge
```

Some clone Nanos require `cpu=atmega328old` for upload; that changes only the
bootloader/upload protocol, not this sketch's compiled ATmega328P behavior.

## Remaining D1 hardware work

The reset driver cannot make a bench session safe or unattended until the real
S1 contact pair is measured and the isolated harness is built. Session-start
restart is now host-commanded through DTR; automatic retry after a missing
heartbeat and reset-hold control remain later host/firmware work. Derived-clock
and `-MRDC` probe pins will likewise be assigned only after continuity
identifies accessible, voltage-safe testpoints.
