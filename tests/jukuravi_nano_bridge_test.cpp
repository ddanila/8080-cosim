#include <stdint.h>

#include <cstdlib>
#include <deque>
#include <iostream>
#include <vector>

#include "bridge_core.h"

namespace {

class FakeStream {
 public:
  explicit FakeStream(const std::vector<uint8_t> &input = {})
      : input_(input.begin(), input.end()) {}

  int available() const { return static_cast<int>(input_.size()); }

  int read() {
    if (input_.empty()) return -1;
    const uint8_t value = input_.front();
    input_.pop_front();
    return value;
  }

  size_t write(uint8_t value) {
    output_.push_back(value);
    return 1;
  }

  bool empty() const { return input_.empty(); }
  const std::vector<uint8_t> &output() const { return output_; }

 private:
  std::deque<uint8_t> input_;
  std::vector<uint8_t> output_;
};

[[noreturn]] void fail(const char *message) {
  std::cerr << "JUKURAVI-NANO-BRIDGE: FAIL: " << message << '\n';
  std::exit(1);
}

void expect(bool condition, const char *message) {
  if (!condition) fail(message);
}

std::vector<uint8_t> byteRange(size_t count, uint8_t first) {
  std::vector<uint8_t> bytes;
  bytes.reserve(count);
  for (size_t index = 0; index < count; ++index) {
    bytes.push_back(static_cast<uint8_t>(first + index));
  }
  return bytes;
}

}  // namespace

int main() {
  const std::vector<uint8_t> jukuBytes = byteRange(256, 0);
  const std::vector<uint8_t> usbBytes = {
      0xA5, 0x5A, 0x81, 0x04, 0x01, 0x08, 0x8D, 0x59, 0x1F,
  };
  FakeStream usb(usbBytes);
  FakeStream juku(jukuBytes);
  jukuravi::BridgeCounters counters;

  jukuravi::pumpBridge(usb, juku, counters);
  expect(usb.output().size() == jukuravi::kDirectionBudget,
         "first pump did not enforce the Juku-to-USB budget");
  expect(juku.output() == usbBytes,
         "first pump did not preserve the complete nine-byte ACK");

  while (!usb.empty() || !juku.empty()) {
    jukuravi::pumpBridge(usb, juku, counters);
  }

  expect(usb.output() == jukuBytes,
         "Juku-to-USB transfer was not binary-transparent");
  expect(juku.output() == usbBytes,
         "USB-to-Juku transfer was not binary-transparent");
  expect(counters.juku_to_usb == jukuBytes.size(),
         "Juku-to-USB counter differs from transferred bytes");
  expect(counters.usb_to_juku == usbBytes.size(),
         "USB-to-Juku counter differs from transferred bytes");

  FakeStream empty;
  expect(jukuravi::forwardBytes(empty, usb, 0) == 0,
         "zero transfer budget moved a byte");

  std::cout
      << "JUKURAVI-NANO-BRIDGE: PASS (all 256 byte values; exact ACK; "
         "bounded bidirectional pump)\n";
  return 0;
}
