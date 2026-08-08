#include "../cosim/i8080.h"

#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef struct {
  uint16_t addr;
  uint8_t data;
} write_event;

typedef struct {
  uint8_t mem[65536];
  uint8_t ports[256];
  write_event writes[16];
  unsigned write_count;
  uint8_t last_out_port;
  uint8_t last_out_data;
  unsigned out_count;
} fixture;

static unsigned failures;
static unsigned checks;

static void fail(const char *fmt, ...) {
  failures++;
  if (failures > 20)
    return;
  va_list ap;
  va_start(ap, fmt);
  fprintf(stderr, "- ");
  vfprintf(stderr, fmt, ap);
  fprintf(stderr, "\n");
  va_end(ap);
}

#define CHECK(condition, ...)                                                   \
  do {                                                                          \
    checks++;                                                                    \
    if (!(condition))                                                            \
      fail(__VA_ARGS__);                                                         \
  } while (0)

static uint8_t read_byte(void *opaque, uint16_t addr) {
  return ((fixture *)opaque)->mem[addr];
}

static void write_byte(void *opaque, uint16_t addr, uint8_t data) {
  fixture *f = opaque;
  if (f->write_count < sizeof(f->writes) / sizeof(f->writes[0])) {
    f->writes[f->write_count].addr = addr;
    f->writes[f->write_count].data = data;
  }
  f->write_count++;
  f->mem[addr] = data;
}

static uint8_t port_in(void *opaque, uint8_t port) {
  return ((fixture *)opaque)->ports[port];
}

static void port_out(void *opaque, uint8_t port, uint8_t data) {
  fixture *f = opaque;
  f->last_out_port = port;
  f->last_out_data = data;
  f->out_count++;
}

static void prepare(i8080 *cpu, fixture *f, uint8_t opcode, uint8_t operand) {
  i8080_init(cpu);
  cpu->read_byte = read_byte;
  cpu->write_byte = write_byte;
  cpu->port_in = port_in;
  cpu->port_out = port_out;
  cpu->userdata = f;
  f->mem[0] = opcode;
  f->mem[1] = operand;
  f->mem[2] = 0;
  f->write_count = 0;
  f->out_count = 0;
}

static unsigned parity(uint8_t value) {
  unsigned ones = 0;
  for (unsigned bit = 0; bit < 8; bit++)
    ones += (value >> bit) & 1u;
  return (ones & 1u) == 0;
}

static void check_zsp(const char *name, unsigned a, unsigned b,
    const i8080 *cpu, uint8_t expected) {
  CHECK(cpu->zf == (expected == 0),
      "%s %02x,%02x: Z=%u expected %u", name, a, b, cpu->zf,
      expected == 0);
  CHECK(cpu->sf == ((expected >> 7) & 1u),
      "%s %02x,%02x: S=%u expected %u", name, a, b, cpu->sf,
      (expected >> 7) & 1u);
  CHECK(cpu->pf == parity(expected),
      "%s %02x,%02x: P=%u expected %u", name, a, b, cpu->pf,
      parity(expected));
}

static void test_arithmetic(fixture *f) {
  static const struct {
    const char *name;
    uint8_t opcode;
    unsigned subtract;
    unsigned uses_carry;
  } cases[] = {
      {"ADI", 0xC6, 0, 0}, {"ACI", 0xCE, 0, 1},
      {"SUI", 0xD6, 1, 0}, {"SBI", 0xDE, 1, 1},
  };
  i8080 cpu;

  for (unsigned k = 0; k < sizeof(cases) / sizeof(cases[0]); k++) {
    for (unsigned a = 0; a < 256; a++) {
      for (unsigned operand = 0; operand < 256; operand++) {
        for (unsigned carry_in = 0; carry_in < 2; carry_in++) {
          prepare(&cpu, f, cases[k].opcode, (uint8_t)operand);
          cpu.a = (uint8_t)a;
          cpu.cf = carry_in;
          i8080_step(&cpu);
          unsigned cin = cases[k].uses_carry ? carry_in : 0;
          unsigned wide;
          uint8_t expected;
          unsigned expected_cf;
          unsigned expected_hf;
          if (cases[k].subtract) {
            wide = a - operand - cin;
            expected = (uint8_t)wide;
            expected_cf = a < operand + cin;
            /* The 8080 exposes the complemented nibble borrow on subtraction. */
            expected_hf = (a & 0x0f) >= ((operand & 0x0f) + cin);
          } else {
            wide = a + operand + cin;
            expected = (uint8_t)wide;
            expected_cf = wide > 0xff;
            expected_hf = (a & 0x0f) + (operand & 0x0f) + cin > 0x0f;
          }
          CHECK(cpu.a == expected,
              "%s %02x,%02x,C%u: A=%02x expected %02x", cases[k].name,
              a, operand, carry_in, cpu.a, expected);
          CHECK(cpu.cf == expected_cf,
              "%s %02x,%02x,C%u: C=%u expected %u", cases[k].name,
              a, operand, carry_in, cpu.cf, expected_cf);
          CHECK(cpu.hf == expected_hf,
              "%s %02x,%02x,C%u: AC=%u expected %u", cases[k].name,
              a, operand, carry_in, cpu.hf, expected_hf);
          check_zsp(cases[k].name, a, operand, &cpu, expected);
        }
      }
    }
  }
}

static void test_logic_and_compare(fixture *f) {
  i8080 cpu;
  for (unsigned a = 0; a < 256; a++) {
    for (unsigned operand = 0; operand < 256; operand++) {
      prepare(&cpu, f, 0xE6, (uint8_t)operand); /* ANI */
      cpu.a = (uint8_t)a;
      cpu.cf = 1;
      i8080_step(&cpu);
      uint8_t expected = (uint8_t)(a & operand);
      CHECK(cpu.a == expected && !cpu.cf,
          "ANI %02x,%02x: A/C=%02x/%u", a, operand, cpu.a, cpu.cf);
      CHECK(cpu.hf == (((a | operand) & 0x08) != 0),
          "ANI %02x,%02x: AC=%u", a, operand, cpu.hf);
      check_zsp("ANI", a, operand, &cpu, expected);

      prepare(&cpu, f, 0xEE, (uint8_t)operand); /* XRI */
      cpu.a = (uint8_t)a;
      cpu.cf = cpu.hf = 1;
      i8080_step(&cpu);
      expected = (uint8_t)(a ^ operand);
      CHECK(cpu.a == expected && !cpu.cf && !cpu.hf,
          "XRI %02x,%02x: A/C/AC=%02x/%u/%u", a, operand, cpu.a,
          cpu.cf, cpu.hf);
      check_zsp("XRI", a, operand, &cpu, expected);

      prepare(&cpu, f, 0xF6, (uint8_t)operand); /* ORI */
      cpu.a = (uint8_t)a;
      cpu.cf = cpu.hf = 1;
      i8080_step(&cpu);
      expected = (uint8_t)(a | operand);
      CHECK(cpu.a == expected && !cpu.cf && !cpu.hf,
          "ORI %02x,%02x: A/C/AC=%02x/%u/%u", a, operand, cpu.a,
          cpu.cf, cpu.hf);
      check_zsp("ORI", a, operand, &cpu, expected);

      prepare(&cpu, f, 0xFE, (uint8_t)operand); /* CPI */
      cpu.a = (uint8_t)a;
      i8080_step(&cpu);
      expected = (uint8_t)(a - operand);
      CHECK(cpu.a == a, "CPI %02x,%02x changed A to %02x", a, operand, cpu.a);
      CHECK(cpu.cf == (a < operand), "CPI %02x,%02x: C=%u", a, operand,
          cpu.cf);
      CHECK(cpu.hf == ((a & 0x0f) >= (operand & 0x0f)),
          "CPI %02x,%02x: AC=%u", a, operand, cpu.hf);
      check_zsp("CPI", a, operand, &cpu, expected);
    }
  }
}

static void test_inr_dcr_and_rotates(fixture *f) {
  i8080 cpu;
  for (unsigned value = 0; value < 256; value++) {
    for (unsigned carry_in = 0; carry_in < 2; carry_in++) {
      prepare(&cpu, f, 0x3C, 0); /* INR A */
      cpu.a = (uint8_t)value;
      cpu.cf = carry_in;
      i8080_step(&cpu);
      uint8_t expected = (uint8_t)(value + 1);
      CHECK(cpu.a == expected && cpu.cf == carry_in,
          "INR %02x,C%u: A/C=%02x/%u", value, carry_in, cpu.a, cpu.cf);
      CHECK(cpu.hf == ((value & 0x0f) == 0x0f),
          "INR %02x: AC=%u", value, cpu.hf);
      check_zsp("INR", value, carry_in, &cpu, expected);

      prepare(&cpu, f, 0x3D, 0); /* DCR A */
      cpu.a = (uint8_t)value;
      cpu.cf = carry_in;
      i8080_step(&cpu);
      expected = (uint8_t)(value - 1);
      CHECK(cpu.a == expected && cpu.cf == carry_in,
          "DCR %02x,C%u: A/C=%02x/%u", value, carry_in, cpu.a, cpu.cf);
      CHECK(cpu.hf == ((value & 0x0f) != 0),
          "DCR %02x: AC=%u", value, cpu.hf);
      check_zsp("DCR", value, carry_in, &cpu, expected);

      const uint8_t opcodes[] = {0x07, 0x0F, 0x17, 0x1F};
      for (unsigned kind = 0; kind < 4; kind++) {
        prepare(&cpu, f, opcodes[kind], 0);
        cpu.a = (uint8_t)value;
        cpu.cf = carry_in;
        cpu.sf = 1;
        cpu.zf = 1;
        cpu.hf = 1;
        cpu.pf = 0;
        i8080_step(&cpu);
        uint8_t rotated;
        unsigned rotated_carry;
        if (kind == 0) {
          rotated_carry = value >> 7;
          rotated = (uint8_t)((value << 1) | rotated_carry);
        } else if (kind == 1) {
          rotated_carry = value & 1;
          rotated = (uint8_t)((value >> 1) | (rotated_carry << 7));
        } else if (kind == 2) {
          rotated_carry = value >> 7;
          rotated = (uint8_t)((value << 1) | carry_in);
        } else {
          rotated_carry = value & 1;
          rotated = (uint8_t)((value >> 1) | (carry_in << 7));
        }
        CHECK(cpu.a == rotated && cpu.cf == rotated_carry,
            "rotate %02x value=%02x C%u: A/C=%02x/%u expected %02x/%u",
            opcodes[kind], value, carry_in, cpu.a, cpu.cf, rotated,
            rotated_carry);
        CHECK(cpu.sf && cpu.zf && cpu.hf && !cpu.pf,
            "rotate %02x changed non-carry flags", opcodes[kind]);
      }
    }
  }
}

static uint8_t bcd(unsigned value) {
  return (uint8_t)(((value / 10) << 4) | (value % 10));
}

static void test_daa(fixture *f) {
  i8080 cpu;
  for (unsigned left = 0; left < 100; left++) {
    for (unsigned right = 0; right < 100; right++) {
      for (unsigned carry_in = 0; carry_in < 2; carry_in++) {
        prepare(&cpu, f, 0xCE, bcd(right)); /* ACI, then DAA */
        f->mem[2] = 0x27;
        cpu.a = bcd(left);
        cpu.cf = carry_in;
        i8080_step(&cpu);
        i8080_step(&cpu);
        unsigned decimal = left + right + carry_in;
        uint8_t expected = bcd(decimal % 100);
        CHECK(cpu.a == expected && cpu.cf == (decimal >= 100),
            "DAA %u+%u+C%u: A/C=%02x/%u expected %02x/%u", left,
            right, carry_in, cpu.a, cpu.cf, expected, decimal >= 100);
        check_zsp("DAA", left, right, &cpu, expected);
      }
    }
  }
}

static void test_bus_stack_control_and_io(fixture *f) {
  i8080 cpu;

  prepare(&cpu, f, 0xC5, 0); /* PUSH B */
  cpu.sp = 0x4000;
  cpu.b = 0x12;
  cpu.c = 0x34;
  i8080_step(&cpu);
  CHECK(cpu.sp == 0x3ffe && f->write_count == 2,
      "PUSH: SP/write count %04x/%u", cpu.sp, f->write_count);
  CHECK(f->writes[0].addr == 0x3fff && f->writes[0].data == 0x12 &&
          f->writes[1].addr == 0x3ffe && f->writes[1].data == 0x34,
      "PUSH bus order %04x=%02x then %04x=%02x", f->writes[0].addr,
      f->writes[0].data, f->writes[1].addr, f->writes[1].data);

  prepare(&cpu, f, 0xCD, 0x78); /* CALL 5678 */
  f->mem[2] = 0x56;
  cpu.sp = 0x4000;
  i8080_step(&cpu);
  CHECK(cpu.pc == 0x5678 && cpu.sp == 0x3ffe,
      "CALL target/SP %04x/%04x", cpu.pc, cpu.sp);
  CHECK(f->writes[0].addr == 0x3fff && f->writes[0].data == 0x00 &&
          f->writes[1].addr == 0x3ffe && f->writes[1].data == 0x03,
      "CALL return-address bus order differs");
  f->mem[0x5678] = 0xC9;
  i8080_step(&cpu);
  CHECK(cpu.pc == 3 && cpu.sp == 0x4000, "RET PC/SP %04x/%04x", cpu.pc,
      cpu.sp);

  prepare(&cpu, f, 0xDB, 0x45); /* IN */
  f->ports[0x45] = 0xA6;
  i8080_step(&cpu);
  CHECK(cpu.a == 0xA6, "IN returned %02x", cpu.a);
  prepare(&cpu, f, 0xD3, 0x67); /* OUT */
  cpu.a = 0x5A;
  i8080_step(&cpu);
  CHECK(f->out_count == 1 && f->last_out_port == 0x67 &&
          f->last_out_data == 0x5A,
      "OUT event count/port/data %u/%02x/%02x", f->out_count,
      f->last_out_port, f->last_out_data);
}

static void test_interrupts_and_undocumented(fixture *f) {
  i8080 cpu;
  prepare(&cpu, f, 0xFB, 0); /* EI; NOP; interrupt RST 1 */
  f->mem[1] = 0x00;
  f->mem[2] = 0x76;
  cpu.sp = 0x4000;
  i8080_interrupt(&cpu, 0xCF);
  i8080_step(&cpu);
  CHECK(cpu.pc == 1 && cpu.iff && cpu.interrupt_delay == 1,
      "EI state PC/IFF/delay %04x/%u/%u", cpu.pc, cpu.iff,
      cpu.interrupt_delay);
  i8080_step(&cpu);
  CHECK(cpu.pc == 2 && cpu.interrupt_pending && cpu.interrupt_delay == 0,
      "EI delay did not execute exactly one instruction");
  i8080_step(&cpu);
  CHECK(cpu.pc == 0x0008 && !cpu.iff && !cpu.interrupt_pending,
      "interrupt service PC/IFF/pending %04x/%u/%u", cpu.pc, cpu.iff,
      cpu.interrupt_pending);
  CHECK(f->writes[0].addr == 0x3fff && f->writes[0].data == 0x00 &&
          f->writes[1].addr == 0x3ffe && f->writes[1].data == 0x02,
      "interrupt RST stack bus order differs");

  static const uint8_t nops[] = {0x08, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38};
  for (unsigned n = 0; n < sizeof(nops); n++) {
    prepare(&cpu, f, nops[n], 0);
    cpu.a = 0xA5;
    cpu.b = 0x5A;
    cpu.cf = 1;
    i8080_step(&cpu);
    CHECK(cpu.pc == 1 && cpu.a == 0xA5 && cpu.b == 0x5A && cpu.cf,
        "undocumented NOP %02x changed state", nops[n]);
  }

  prepare(&cpu, f, 0xCB, 0x34); /* undocumented JMP */
  f->mem[2] = 0x12;
  i8080_step(&cpu);
  CHECK(cpu.pc == 0x1234, "undocumented JMP target %04x", cpu.pc);

  static const uint8_t calls[] = {0xDD, 0xED, 0xFD};
  for (unsigned n = 0; n < sizeof(calls); n++) {
    prepare(&cpu, f, calls[n], 0x34);
    f->mem[2] = 0x12;
    cpu.sp = 0x4000;
    i8080_step(&cpu);
    CHECK(cpu.pc == 0x1234 && cpu.sp == 0x3ffe,
        "undocumented CALL %02x target/SP %04x/%04x", calls[n], cpu.pc,
        cpu.sp);
  }

  prepare(&cpu, f, 0xD9, 0); /* undocumented RET */
  cpu.sp = 0x3ffe;
  f->mem[0x3ffe] = 0x78;
  f->mem[0x3fff] = 0x56;
  i8080_step(&cpu);
  CHECK(cpu.pc == 0x5678 && cpu.sp == 0x4000,
      "undocumented RET PC/SP %04x/%04x", cpu.pc, cpu.sp);
}

int main(void) {
  static fixture f;
  memset(&f, 0, sizeof(f));
  test_arithmetic(&f);
  test_logic_and_compare(&f);
  test_inr_dcr_and_rotates(&f);
  test_daa(&f);
  test_bus_stack_control_and_io(&f);
  test_interrupts_and_undocumented(&f);

  if (failures) {
    fprintf(stderr, "I8080-CONFORMANCE: FAIL (%u failures; first 20 shown)\n",
        failures);
    return 1;
  }
  printf("I8080-CONFORMANCE: PASS (%u independent assertions; exhaustive "
         "8-bit ALU/flags, DAA, rotates, stack bus order, I/O, EI, aliases)\n",
      checks);
  return 0;
}
