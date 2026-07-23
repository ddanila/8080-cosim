#include <stdint.h>

#include <cstdlib>
#include <deque>
#include <iostream>
#include <vector>

#include "bridge_core.h"
#include "reset_core.h"

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

void expectReset(jukuravi::StartupResetSequencer &reset, uint32_t now,
                 bool asserted, bool bridge_ready, const char *message,
                 bool hold_requested = false) {
  const jukuravi::StartupResetState state = reset.update(now, hold_requested);
  expect(state.asserted == asserted && state.bridge_ready == bridge_ready,
         message);
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

  jukuravi::StartupResetSequencer reset;
  expectReset(reset, 0, false, false,
              "unstarted reset sequencer was active or ready");
  reset.begin(1000);
  expectReset(reset, 1000, true, false, "reset did not assert at startup");
  expectReset(reset, 1249, true, false, "reset pulse ended one ms early");
  expectReset(reset, 1250, false, false,
              "reset did not release at the pulse boundary");
  expectReset(reset, 1299, false, false,
              "bridge became ready before recovery completed");
  expectReset(reset, 1300, false, true,
              "bridge did not become ready after recovery");

  constexpr uint32_t wrapStart = UINT32_MAX - 99;
  reset.begin(wrapStart);
  expectReset(reset, static_cast<uint32_t>(wrapStart + 249), true, false,
              "rollover reset pulse ended early");
  expectReset(reset, static_cast<uint32_t>(wrapStart + 250), false, false,
              "rollover reset did not enter recovery");
  expectReset(reset, static_cast<uint32_t>(wrapStart + 300), false, true,
              "rollover reset never made the bridge ready");
  expectReset(reset, wrapStart, false, true,
              "ready reset sequencer reasserted after a full timestamp cycle");

  jukuravi::StartupResetSequencer lateReset;
  lateReset.begin(100);
  expectReset(lateReset, 400, false, false,
              "late first update did not enter recovery");
  expectReset(lateReset, 449, false, false,
              "late first update shortened recovery");
  expectReset(lateReset, 450, false, true,
              "late first update recovery did not complete");

  expect(jukuravi::kResetDrivePin == 4 && jukuravi::kResetHoldPin == 5,
         "reset drive/hold pin contract differs");
  expect(jukuravi::resetHoldRequested(false) &&
             !jukuravi::resetHoldRequested(true),
         "reset hold input is not active-low");

  jukuravi::StartupResetSequencer heldReset;
  heldReset.begin(1000);
  expectReset(heldReset, 1250, true, false,
              "hold did not extend the startup reset", true);
  expectReset(heldReset, 5000, true, false,
              "long hold released reset or enabled the bridge", true);
  expectReset(heldReset, 5000, false, false,
              "hold release did not enter quiet recovery");
  expectReset(heldReset, 5049, false, false,
              "hold release recovery ended one ms early");
  expectReset(heldReset, 5050, false, true,
              "hold release did not enable the bridge after recovery");

  expectReset(heldReset, 6000, true, false,
              "ready sequencer ignored a new hold request", true);
  expectReset(heldReset, 6249, true, false,
              "reasserted reset pulse ended early");
  expectReset(heldReset, 6250, false, false,
              "reasserted reset did not enter recovery");
  expectReset(heldReset, 6300, false, true,
              "reasserted reset did not complete recovery");

  jukuravi::StartupResetSequencer wrapHold;
  wrapHold.begin(0);
  expectReset(wrapHold, 250, false, false,
              "hold rollover setup did not enter recovery");
  expectReset(wrapHold, 300, false, true,
              "hold rollover setup did not become ready");
  expectReset(wrapHold, wrapStart, true, false,
              "rollover hold did not reassert reset", true);
  expectReset(wrapHold, static_cast<uint32_t>(wrapStart + 249), true, false,
              "rollover-held reset pulse ended early");
  expectReset(wrapHold, static_cast<uint32_t>(wrapStart + 250), false, false,
              "rollover-held reset did not enter recovery");
  expectReset(wrapHold, static_cast<uint32_t>(wrapStart + 299), false, false,
              "rollover hold recovery ended early");
  expectReset(wrapHold, static_cast<uint32_t>(wrapStart + 300), false, true,
              "rollover hold recovery did not complete");

  FakeStream gatedUsb({0x81});
  FakeStream gatedJuku({0x55});
  jukuravi::BridgeCounters gatedCounters;
  expect(!jukuravi::pumpBridgeIfReady(
             false, gatedUsb, gatedJuku, gatedCounters),
         "bridge reported activity while reset recovery blocked it");
  expect(gatedUsb.output().empty() && gatedJuku.output().empty() &&
             gatedCounters.usb_to_juku == 0 &&
             gatedCounters.juku_to_usb == 0,
         "bridge moved bytes while reset recovery blocked it");
  expect(jukuravi::pumpBridgeIfReady(
             true, gatedUsb, gatedJuku, gatedCounters),
         "ready bridge did not run");
  expect(gatedUsb.output() == std::vector<uint8_t>({0x55}) &&
             gatedJuku.output() == std::vector<uint8_t>({0x81}),
         "ready bridge did not release both queued directions");

  std::cout
      << "JUKURAVI-NANO-BRIDGE: PASS (all 256 byte values; exact ACK; "
         "bounded pump; rollover-safe 250+50 ms reset with D5 hold)\n";
  return 0;
}
