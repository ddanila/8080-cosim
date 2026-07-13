// К155РЕ3 (32 x 8 bipolar PROM) reader for Arduino Nano / ATmega328P.
//
// Wiring:
//   PROM A0..A4 (pins 10,11,12,13,14) -> Nano D2..D6
//   PROM /E     (pin 15)              -> Nano D7
//   PROM D0..D7 (pins 1,2,3,4,5,6,7,9) -> Nano D8..D13,A0,A1
//   PROM pin 8 -> GND; pin 16 -> +5 V
//   Each data output requires a 1k..4.7k pull-up to +5 V.

constexpr uint8_t ADDRESS_PINS[5] = {2, 3, 4, 5, 6};
constexpr uint8_t ENABLE_PIN = 7;
constexpr uint8_t DATA_PINS[8] = {8, 9, 10, 11, 12, 13, A0, A1};
constexpr uint8_t SAMPLE_COUNT = 8;

struct Reading {
  uint8_t raw;
  bool stable;
};

void setAddress(uint8_t address) {
  digitalWrite(ENABLE_PIN, HIGH);
  for (uint8_t bit = 0; bit < 5; ++bit) {
    digitalWrite(ADDRESS_PINS[bit], (address >> bit) & 1);
  }
  delayMicroseconds(5);
}

uint8_t sampleDataPins() {
  uint8_t value = 0;
  for (uint8_t bit = 0; bit < 8; ++bit) {
    if (digitalRead(DATA_PINS[bit])) value |= (1U << bit);
  }
  return value;
}

Reading readAddress(uint8_t address) {
  setAddress(address);
  digitalWrite(ENABLE_PIN, LOW);
  delayMicroseconds(20);

  const uint8_t first = sampleDataPins();
  bool stable = true;
  for (uint8_t sample = 1; sample < SAMPLE_COUNT; ++sample) {
    delayMicroseconds(5);
    if (sampleDataPins() != first) stable = false;
  }

  digitalWrite(ENABLE_PIN, HIGH);
  return {first, stable};
}

void printHexByte(uint8_t value) {
  if (value < 0x10) Serial.print('0');
  Serial.print(value, HEX);
}

void dumpProm() {
  uint8_t rawDump[32];
  uint8_t unstable = 0;

  Serial.println(F("# K155RE3 dump"));
  Serial.println(F("# addr,raw_pins,stable"));

  for (uint8_t address = 0; address < 32; ++address) {
    const Reading reading = readAddress(address);
    rawDump[address] = reading.raw;
    if (!reading.stable) ++unstable;

    printHexByte(address);
    Serial.print(',');
    printHexByte(reading.raw);
    Serial.print(',');
    Serial.println(reading.stable ? F("OK") : F("UNSTABLE"));
  }

  Serial.println(F("# active-low asserted bytes, 16 addresses per row"));
  for (uint8_t base = 0; base < 32; base += 16) {
    printHexByte(base);
    Serial.print(F(": "));
    for (uint8_t offset = 0; offset < 16; ++offset) {
      printHexByte(~rawDump[base + offset]);
    }
    Serial.println();
  }

  Serial.print(F("# unstable_addresses="));
  Serial.println(unstable);
  Serial.println(F("# END"));
}

void setup() {
  digitalWrite(ENABLE_PIN, HIGH);
  pinMode(ENABLE_PIN, OUTPUT);

  for (uint8_t bit = 0; bit < 5; ++bit) {
    pinMode(ADDRESS_PINS[bit], OUTPUT);
    digitalWrite(ADDRESS_PINS[bit], LOW);
  }
  for (uint8_t bit = 0; bit < 8; ++bit) {
    pinMode(DATA_PINS[bit], INPUT);
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
