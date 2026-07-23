# Jukuravi Nano firmware

Status: the Stage D1 serial bridge is implemented and guarded in simulation;
hardware reset and liveness probes remain measurement-gated follow-up work.

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

Build and test with:

```sh
sync/jukuravi_nano_check.sh
```

The always-available host test sends all 256 byte values plus the exact
version-8 ACK through the shared bridge core in both directions and checks the
per-direction work bound and counters. When `arduino-cli` and the
`arduino:avr` core are installed, the same guard also compiles the actual Nano
sketch. To upload manually after a successful build:

```sh
arduino-cli compile --fqbn arduino:avr:nano:cpu=atmega328 \
  --upload --port /dev/ttyUSB0 \
  spinoffs/jukuravi/nano/jukuravi_bridge
```

Some clone Nanos require `cpu=atmega328old` for upload; that changes only the
bootloader/upload protocol, not this sketch's compiled ATmega328P behavior.

## Remaining D1 hardware work

The bridge does not yet make a bench session safe or unattended. Before adding
the reset output, identify the real S1 contact pair and verify its asserted
polarity. The future Nano output will drive only an optocoupler LED or
open-collector transistor placed across those contacts; it must never drive the
board reset-RC node push-pull. Likewise, derived-clock and `-MRDC` probe pins
will be assigned only after continuity identifies accessible, voltage-safe
testpoints. Until those measurements exist, open the USB port first and reset
the Juku manually after the bridge is listening.
