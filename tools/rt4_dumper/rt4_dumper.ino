// КР556РТ4 (256 x 4 bipolar PROM) reader for Arduino Nano / ATmega328P.
//
// Wiring:
//   PROM A0..A7 (pins 5,6,7,4,3,2,1,15) -> Nano D2..D9
//   PROM D0..D3 (pins 12,11,10,9)         -> Nano D10,D11,D12,A0
//   PROM pin 13 -> GND; pin 14 (/CE) -> Nano A1
//   PROM pin 8 -> GND; pin 16 -> +5 V
//   Each data output requires a 1k..4.7k pull-up to +5 V.
//
// Revision 2 deliberately leaves Nano D13 disconnected: its on-board LED is
// an avoidable load on an open-collector PROM output. Controlling one /CE input
// also proves that all four pull-ups release HIGH before every dump. A failed
// release check aborts the capture.

constexpr uint8_t ADDRESS_PINS[8] = {2, 3, 4, 5, 6, 7, 8, 9};
constexpr uint8_t DATA_PINS[4] = {10, 11, 12, A0};
constexpr uint8_t ENABLE_PIN = A1;
constexpr uint8_t SAMPLE_COUNT = 8;

struct Reading {
  uint8_t raw;
  bool stable;
};

void setAddress(uint8_t address) {
  for (uint8_t bit = 0; bit < 8; ++bit) {
    digitalWrite(ADDRESS_PINS[bit], (address >> bit) & 1);
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

Reading readAddress(uint8_t address) {
  setAddress(address);
  return sampleStableData();
}

void printHexNibble(uint8_t value) {
  Serial.print(value & 0x0f, HEX);
}

bool verifyReleasedOutputs() {
  digitalWrite(ENABLE_PIN, HIGH);
  delayMicroseconds(20);
  const Reading released = sampleStableData();
  Serial.print(F("# disabled_raw="));
  printHexNibble(released.raw);
  Serial.print(F(",stable="));
  Serial.println(released.stable ? F("OK") : F("UNSTABLE"));
  if (!released.stable || released.raw != 0x0f) {
    Serial.println(F("# SELFTEST FAIL: expected disabled_raw=F; check external pull-ups and data wiring"));
    return false;
  }
  return true;
}

void dumpProm() {
  Serial.println(F("# reader_revision=2"));
  Serial.println(F("# data_map=D0:D10,D1:D11,D2:D12,D3:A0; CE14:A1; Nano_D13:NC"));
  if (!verifyReleasedOutputs()) return;
  digitalWrite(ENABLE_PIN, LOW);
  delayMicroseconds(20);

  uint8_t logicalDump[256];
  uint16_t unstable = 0;

  Serial.println(F("# KR556RT4 dump"));
  Serial.println(F("# addr,raw_pins,logical_active_low,stable"));

  for (uint16_t address = 0; address < 256; ++address) {
    const Reading reading = readAddress(static_cast<uint8_t>(address));
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
  digitalWrite(ENABLE_PIN, HIGH);
}

void setup() {
  for (uint8_t bit = 0; bit < 8; ++bit) {
    pinMode(ADDRESS_PINS[bit], OUTPUT);
    digitalWrite(ADDRESS_PINS[bit], LOW);
  }
  for (uint8_t bit = 0; bit < 4; ++bit) {
    pinMode(DATA_PINS[bit], INPUT);
  }
  digitalWrite(ENABLE_PIN, HIGH);
  pinMode(ENABLE_PIN, OUTPUT);

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
