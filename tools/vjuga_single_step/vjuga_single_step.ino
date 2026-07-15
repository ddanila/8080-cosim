// VJUGA single-step bus tracer for Arduino UNO / ATmega328P (5 V-native).
//
// Purpose (docs/phase4-bench-bringup.md 4.3): drive the Z80 clock statically and
// snapshot the full bus each step, printing one line per M1 opcode fetch in the
// EXACT format the simulation twin emits (tools/.../gen_reference_trace.sh), so a
// bench session is `diff`-compared to the twin reference to find the first fetch
// where a socketed chip diverges.
//
// Clock: install the J96 shunt to tri-state the canned oscillator (U50), then
//   wire CLOCK_PIN -> J92.10 (CLK). The Z80/82C55 are static CMOS; hold time is
//   unbounded, so a hand-clocked or serial-paced clock is fine.
//
// Bus capture: four 74HC165 parallel-in/serial-out registers chained QH->SER,
//   parallel-loaded from the board and read into a 32-bit snapshot. Wire the
//   165 parallel inputs so the shifted-in word (first bit = last register's H)
//   lands as:
//     bits  0..15 : A0..A15   (J90.1-8 + J97.1-8)
//     bits 16..23 : D0..D7    (J91.1-8)
//     bits 24..29 : MREQ_N IORQ_N RD_N WR_N M1_N RFSH_N   (J98.1-6)
//     bit  30     : WAIT_N    (J98.7)
//     bit  31     : DEC_ROM_N (J95.1, D6 РТ4 O1) -- decode cross-check
//   Adjust BIT_* below if your harness orders the chain differently.
//
// Serial protocol @ 115200: 's' = one clock + snapshot; 'r' = run RUN_STEPS
//   clocks; 'z' = reset trace counter. Only M1 fetches print (one per opcode).

constexpr uint8_t CLOCK_PIN = 3;   // -> J92.10 (Z80 CLK), oscillator tri-stated
constexpr uint8_t SHLD_PIN  = 4;   // 74HC165 SH/LD_N (LOW = parallel load)
constexpr uint8_t SCLK_PIN  = 5;   // 74HC165 shift clock (CP)
constexpr uint8_t SDATA_PIN = 6;   // 74HC165 serial out (QH of the last chip)
constexpr uint16_t RUN_STEPS = 400;

// Bit positions within the 32-bit snapshot (see wiring note above).
constexpr uint8_t BIT_A0     = 0;    // A0..A15 occupy bits 0..15
constexpr uint8_t BIT_D0     = 16;   // D0..D7 occupy bits 16..23
constexpr uint8_t BIT_MREQ_N = 24;
constexpr uint8_t BIT_IORQ_N = 25;
constexpr uint8_t BIT_RD_N   = 26;
constexpr uint8_t BIT_WR_N   = 27;
constexpr uint8_t BIT_M1_N   = 28;
constexpr uint8_t BIT_RFSH_N = 29;
constexpr uint8_t BIT_WAIT_N = 30;
constexpr uint8_t BIT_DEC_ROM_N = 31;

uint32_t g_fetch = 0;
bool g_m1_prev = false;

uint32_t readSnapshot() {
  // Latch the parallel bus, then shift 32 bits MSB-first out of the chain.
  digitalWrite(SHLD_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(SHLD_PIN, HIGH);
  uint32_t v = 0;
  for (uint8_t i = 0; i < 32; i++) {
    v = (v << 1) | (digitalRead(SDATA_PIN) ? 1UL : 0UL);
    digitalWrite(SCLK_PIN, HIGH);
    delayMicroseconds(1);
    digitalWrite(SCLK_PIN, LOW);
  }
  return v;
}

inline uint8_t bit(uint32_t v, uint8_t b) { return (v >> b) & 1UL; }

void oneClock() {
  digitalWrite(CLOCK_PIN, HIGH);
  delayMicroseconds(2);
  digitalWrite(CLOCK_PIN, LOW);
  delayMicroseconds(2);
}

void snapshotAndReport() {
  uint32_t v = readSnapshot();
  bool m1_fetch = !bit(v, BIT_M1_N) && !bit(v, BIT_MREQ_N) && !bit(v, BIT_RD_N);
  if (m1_fetch && !g_m1_prev) {
    uint16_t addr = (uint16_t)((v >> BIT_A0) & 0xFFFF);
    uint8_t data = (uint8_t)((v >> BIT_D0) & 0xFF);
    char line[64];
    // Match the twin: "F<n>: addr=<hhhh> data=<hh> m1=<b> mreq=<b> rd=<b>"
    snprintf(line, sizeof(line), "F%lu: addr=%04x data=%02x m1=%u mreq=%u rd=%u",
             (unsigned long)g_fetch, addr, data,
             bit(v, BIT_M1_N), bit(v, BIT_MREQ_N), bit(v, BIT_RD_N));
    Serial.println(line);
    g_fetch++;
  }
  g_m1_prev = m1_fetch;
}

void setup() {
  pinMode(CLOCK_PIN, OUTPUT);
  pinMode(SHLD_PIN, OUTPUT);
  pinMode(SCLK_PIN, OUTPUT);
  pinMode(SDATA_PIN, INPUT);
  digitalWrite(CLOCK_PIN, LOW);
  digitalWrite(SHLD_PIN, HIGH);
  digitalWrite(SCLK_PIN, LOW);
  Serial.begin(115200);
  Serial.println("# VJUGA single-step tracer ready: s=step, r=run, z=zero");
}

void loop() {
  if (!Serial.available()) return;
  char c = Serial.read();
  if (c == 's') {
    oneClock();
    snapshotAndReport();
  } else if (c == 'r') {
    for (uint16_t i = 0; i < RUN_STEPS; i++) {
      oneClock();
      snapshotAndReport();
    }
  } else if (c == 'z') {
    g_fetch = 0;
    g_m1_prev = false;
    Serial.println("# trace counter reset");
  }
}
