// Jukuravi Stage D1 serial bridge for a classic ATmega328P Arduino Nano.
//
// D0/D1 remain the Nano's 115200-baud hardware UART to its USB adapter.
// D8/D9 form a 9600-baud software UART on the TTL side of a MAX3232-class
// transceiver. D10 drives the transceiver's second transmitter input to hold
// the Juku's RS-232 CTS asserted. D4 drives only the LED/input side of an
// isolated reset-switch closure. Never connect any Nano pin directly to X3 or
// the Juku reset network.

#include <SoftwareSerial.h>

#include "bridge_core.h"
#include "reset_core.h"

constexpr uint32_t kUsbBaud = 115200;
constexpr uint32_t kJukuBaud = 9600;
constexpr uint8_t kJukuRxPin = 8;   // MAX3232 R1OUT -> Nano (Juku TX)
constexpr uint8_t kJukuTxPin = 9;   // Nano -> MAX3232 T1IN (Juku RX)
constexpr uint8_t kCtsPin = 10;     // Nano -> MAX3232 T2IN (Juku CTS)
constexpr uint8_t kResetDrivePin = 4;  // Nano -> resistor -> optocoupler LED
constexpr uint8_t kErrorLedPin = LED_BUILTIN;

SoftwareSerial jukuSerial(kJukuRxPin, kJukuTxPin, false);
jukuravi::BridgeCounters bridgeCounters;
jukuravi::StartupResetSequencer startupReset;

void setup() {
  // A MAX3232 driver inverts: LOW at T2IN produces the positive RS-232 level
  // used for asserted CTS. Load LOW before enabling the Nano output. The
  // harness must also fit a 10 kOhm pull-down at T2IN so CTS stays asserted
  // during bootloader/reset intervals while D10 is high impedance.
  digitalWrite(kCtsPin, LOW);
  pinMode(kCtsPin, OUTPUT);

  // D4 never touches the board-side reset node. A 10 kOhm pull-down keeps the
  // optocoupler LED off while the bootloader owns the Nano. Load the safe level
  // before enabling the output, then close the isolated switch as early as
  // possible and start the measured pulse after both serial ports are ready.
  digitalWrite(kResetDrivePin, LOW);
  pinMode(kResetDrivePin, OUTPUT);
  digitalWrite(kResetDrivePin, HIGH);

  digitalWrite(kErrorLedPin, LOW);
  pinMode(kErrorLedPin, OUTPUT);

  Serial.begin(kUsbBaud);
  jukuSerial.begin(kJukuBaud);
  jukuSerial.listen();
  startupReset.begin(millis());
}

void loop() {
  const jukuravi::StartupResetState reset = startupReset.update(millis());
  digitalWrite(kResetDrivePin, reset.asserted ? HIGH : LOW);
  jukuravi::pumpBridgeIfReady(
      reset.bridge_ready, Serial, jukuSerial, bridgeCounters);

  // SoftwareSerial exposes a sticky receive-overflow flag. Keep the data path
  // byte-transparent: signal loss on the onboard LED instead of inserting a
  // diagnostic message into the framed host stream.
  if (jukuSerial.overflow()) digitalWrite(kErrorLedPin, HIGH);
}
