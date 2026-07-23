// Jukuravi Stage D1 serial bridge for a classic ATmega328P Arduino Nano.
//
// D0/D1 remain the Nano's 115200-baud hardware UART to its USB adapter.
// D8/D9 form a 9600-baud software UART on the TTL side of a MAX3232-class
// transceiver. D10 drives the transceiver's second transmitter input to hold
// the Juku's RS-232 CTS asserted. Never connect any Nano pin directly to X3.

#include <SoftwareSerial.h>

#include "bridge_core.h"

constexpr uint32_t kUsbBaud = 115200;
constexpr uint32_t kJukuBaud = 9600;
constexpr uint8_t kJukuRxPin = 8;   // MAX3232 R1OUT -> Nano (Juku TX)
constexpr uint8_t kJukuTxPin = 9;   // Nano -> MAX3232 T1IN (Juku RX)
constexpr uint8_t kCtsPin = 10;     // Nano -> MAX3232 T2IN (Juku CTS)
constexpr uint8_t kErrorLedPin = LED_BUILTIN;

SoftwareSerial jukuSerial(kJukuRxPin, kJukuTxPin, false);
jukuravi::BridgeCounters bridgeCounters;

void setup() {
  // A MAX3232 driver inverts: LOW at T2IN produces the positive RS-232 level
  // used for asserted CTS. Load LOW before enabling the Nano output. The
  // harness must also fit a 10 kOhm pull-down at T2IN so CTS stays asserted
  // during bootloader/reset intervals while D10 is high impedance.
  digitalWrite(kCtsPin, LOW);
  pinMode(kCtsPin, OUTPUT);

  digitalWrite(kErrorLedPin, LOW);
  pinMode(kErrorLedPin, OUTPUT);

  Serial.begin(kUsbBaud);
  jukuSerial.begin(kJukuBaud);
  jukuSerial.listen();
}

void loop() {
  jukuravi::pumpBridge(Serial, jukuSerial, bridgeCounters);

  // SoftwareSerial exposes a sticky receive-overflow flag. Keep the data path
  // byte-transparent: signal loss on the onboard LED instead of inserting a
  // diagnostic message into the framed host stream.
  if (jukuSerial.overflow()) digitalWrite(kErrorLedPin, HIGH);
}
