// KR556RT4 (256 x 4 bipolar PROM) reader using the existing K155RE3
// Arduino Nano reader wiring.
//
// Existing socket wiring, reinterpreted for the RT4:
//   RT4 A0..A7 (pins 5,6,7,4,3,2,1,15)
//       -> Nano D12,D13,A0,D11,D10,D9,D8,D7
//   RT4 D0..D3 (pins 12,11,10,9)
//       -> Nano D4,D3,D2,A1
//   RT4 /CE pin 13 -> Nano D5
//   RT4 /CE pin 14 -> Nano D6, with a 3k pull-up to +5 V
//   RT4 pin 8 -> GND; pin 16 -> regulated +5 V
//
// Fit an individual external 3k pull-up from every RT4 data output
// (pins 9,10,11,12) to +5 V. Remove the old RE3 output pull-ups from
// pins 1..7. Nano D13 is safe here because it drives an address input;
// it is not sensing an open-collector output.

constexpr uint8_t ADDRESS_PINS[8] = {12, 13, A0, 11, 10, 9, 8, 7};
constexpr uint8_t DATA_PINS[4] = {4, 3, 2, A1};
constexpr uint8_t ENABLE_13_PIN = 5;
constexpr uint8_t ENABLE_14_PIN = 6;
constexpr uint8_t SAMPLE_COUNT = 8;

struct Reading {
  uint8_t raw;
  bool stable;
};

void setEnables(bool disabled13, bool disabled14) {
  digitalWrite(ENABLE_13_PIN, disabled13 ? HIGH : LOW);
  digitalWrite(ENABLE_14_PIN, disabled14 ? HIGH : LOW);
  delayMicroseconds(20);
}

void setAddress(uint8_t address) {
  for (uint8_t bit = 0; bit < 8; ++bit) {
    digitalWrite(ADDRESS_PINS[bit], (address >> bit) & 1U);
  }
  delayMicroseconds(20);
}

uint8_t sampleDataPins() {
  uint8_t value = 0;
  for (uint8_t bit = 0; bit < 4; ++bit) {
    if (digitalRead(DATA_PINS[bit])) value |= (1U << bit);
  }
  return value;
}

Reading sampleStableData() {
  const uint8_t first = sampleDataPins();
  bool stable = true;
  for (uint8_t sample = 1; sample < SAMPLE_COUNT; ++sample) {
    delayMicroseconds(5);
    if (sampleDataPins() != first) stable = false;
  }
  return {first, stable};
}

void printHexNibble(uint8_t value) {
  Serial.print(value & 0x0f, HEX);
}

bool reportDisabledCheck(const __FlashStringHelper *name, bool disabled13,
                         bool disabled14) {
  setEnables(disabled13, disabled14);
  const Reading released = sampleStableData();
  Serial.print(name);
  printHexNibble(released.raw);
  Serial.print(F(",stable="));
  Serial.println(released.stable ? F("OK") : F("UNSTABLE"));
  return released.stable && released.raw == 0x0f;
}

bool verifyReleasedOutputs() {
  // Either active-low enable being HIGH must release every output. Testing
  // both cases catches a swapped/miswired enable before the PROM is trusted.
  const bool both = reportDisabledCheck(F("# disabled_raw="), true, true);
  const bool ce14 =
      reportDisabledCheck(F("# disabled_ce14_raw="), false, true);
  const bool ce13 =
      reportDisabledCheck(F("# disabled_ce13_raw="), true, false);
  setEnables(true, true);
  if (!both || !ce14 || !ce13) {
    Serial.println(F("# SELFTEST FAIL: expected stable F with either /CE high; check pull-ups and enable wiring"));
    return false;
  }
  return true;
}

void dumpProm() {
  Serial.println(F("# reader_revision=3"));
  Serial.println(F("# data_map=D0:D4,D1:D3,D2:D2,D3:A1; address_map=A0:D12,A1:D13,A2:A0,A3:D11,A4:D10,A5:D9,A6:D8,A7:D7; CE13:D5,CE14:D6"));
  if (!verifyReleasedOutputs()) return;

  setEnables(false, false);
  uint8_t logicalDump[256];
  uint16_t unstable = 0;

  Serial.println(F("# KR556RT4 dump"));
  Serial.println(F("# addr,raw_pins,logical_active_low,stable"));

  for (uint16_t address = 0; address < 256; ++address) {
    setAddress(static_cast<uint8_t>(address));
    const Reading reading = sampleStableData();
    const uint8_t logical = (~reading.raw) & 0x0f;
    logicalDump[address] = logical;
    if (!reading.stable) ++unstable;

    if (address < 0x10) Serial.print('0');
    Serial.print(address, HEX);
    Serial.print(',');
    printHexNibble(reading.raw);
    Serial.print(',');
    printHexNibble(logical);
    Serial.print(',');
    Serial.println(reading.stable ? F("OK") : F("UNSTABLE"));
  }

  setEnables(true, true);
  Serial.println(F("# logical nibbles, 16 addresses per row"));
  for (uint16_t base = 0; base < 256; base += 16) {
    if (base < 0x10) Serial.print('0');
    Serial.print(base, HEX);
    Serial.print(F(": "));
    for (uint8_t offset = 0; offset < 16; ++offset) {
      printHexNibble(logicalDump[base + offset]);
    }
    Serial.println();
  }
  Serial.print(F("# unstable_addresses="));
  Serial.println(unstable);
  Serial.println(F("# END"));
}

void setup() {
  // Set the output latches HIGH before changing /CE pins from their reset
  // input state. The external pin-14 pull-up keeps the PROM disabled earlier.
  digitalWrite(ENABLE_13_PIN, HIGH);
  digitalWrite(ENABLE_14_PIN, HIGH);
  pinMode(ENABLE_13_PIN, OUTPUT);
  pinMode(ENABLE_14_PIN, OUTPUT);

  for (uint8_t bit = 0; bit < 8; ++bit) {
    digitalWrite(ADDRESS_PINS[bit], LOW);
    pinMode(ADDRESS_PINS[bit], OUTPUT);
  }
  for (uint8_t bit = 0; bit < 4; ++bit) {
    pinMode(DATA_PINS[bit], INPUT);  // External pull-ups are mandatory.
  }

  Serial.begin(115200);
  delay(1500);
  dumpProm();
  Serial.println(F("# Send D to dump again."));
}

void loop() {
  if (Serial.available()) {
    const char command = Serial.read();
    if (command == 'D' || command == 'd') dumpProm();
  }
}
