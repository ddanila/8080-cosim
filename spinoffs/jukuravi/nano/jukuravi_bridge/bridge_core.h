#pragma once

#include <stddef.h>
#include <stdint.h>

namespace jukuravi {

// Bound each direction so a continuously busy input cannot starve the other
// side forever. The diagnostic protocol itself is request/response, but the
// bound also keeps the bridge responsive while a host port is being drained.
constexpr uint8_t kDirectionBudget = 16;

struct BridgeCounters {
  uint32_t usb_to_juku = 0;
  uint32_t juku_to_usb = 0;
};

template <typename Source, typename Sink>
uint8_t forwardBytes(Source &source, Sink &sink,
                     uint8_t budget = kDirectionBudget) {
  uint8_t moved = 0;
  while (moved < budget && source.available() > 0) {
    const int value = source.read();
    if (value < 0) break;
    if (sink.write(static_cast<uint8_t>(value)) != 1) break;
    ++moved;
  }
  return moved;
}

template <typename UsbPort, typename JukuPort>
void pumpBridge(UsbPort &usb, JukuPort &juku, BridgeCounters &counters) {
  // Drain the slower diagnostic transmitter first. Its SoftwareSerial receive
  // FIFO is the constrained side; USB hardware serial is roughly 12x faster.
  counters.juku_to_usb += forwardBytes(juku, usb);
  counters.usb_to_juku += forwardBytes(usb, juku);
}

template <typename UsbPort, typename JukuPort>
bool pumpBridgeIfReady(bool ready, UsbPort &usb, JukuPort &juku,
                       BridgeCounters &counters) {
  if (!ready) return false;
  pumpBridge(usb, juku, counters);
  return true;
}

}  // namespace jukuravi
