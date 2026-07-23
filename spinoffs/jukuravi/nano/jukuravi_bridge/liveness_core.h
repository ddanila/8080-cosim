#pragma once

#include <stddef.h>
#include <stdint.h>

namespace jukuravi {

// These are Nano-side roles only. D2/D3/D6 must receive conditioned,
// active-low open-collector signals from a future voltage-safe/isolated
// harness; they must never connect directly to a Juku net. D7 is a local
// service jumper to Nano GND and leaves the whole feature disabled when open.
constexpr uint8_t kClockSeenPin = 2;
constexpr uint8_t kMrdcSeenPin = 3;
constexpr uint8_t kResetReleasedPin = 6;
constexpr uint8_t kLivenessEnablePin = 7;
constexpr uint32_t kLivenessObservationMs = 100;

constexpr uint8_t kNanoLivenessType = 0x40;
constexpr uint8_t kNanoLivenessVersion = 1;
constexpr uint8_t kLivenessEnabledFlag = 0x01;
constexpr uint8_t kResetReleasedFlag = 0x02;
constexpr uint8_t kClockSeenFlag = 0x04;
constexpr uint8_t kMrdcSeenFlag = 0x08;
constexpr uint8_t kLivenessKnownFlags = 0x0F;

constexpr bool livenessEnabledRequested(bool input_high) {
  return !input_high;
}

struct LivenessState {
  bool bridge_ready;
  bool observing;
  bool emit_report;
  uint8_t flags;
};

class LivenessMonitor {
 public:
  void begin(bool enabled) {
    enabled_ = enabled;
    resetObservation();
  }

  LivenessState update(uint32_t now_ms, bool board_ready,
                       bool reset_released, bool clock_seen, bool mrdc_seen) {
    if (!enabled_) return {board_ready, false, false, 0};
    if (!board_ready) {
      resetObservation();
      return {false, false, false, 0};
    }
    if (!observing_ && !reported_) {
      observation_started_ms_ = now_ms;
      observing_ = true;
    }
    reset_released_seen_ = reset_released_seen_ || reset_released;
    clock_seen_ = clock_seen_ || clock_seen;
    mrdc_seen_ = mrdc_seen_ || mrdc_seen;

    bool emit = false;
    if (observing_ &&
        now_ms - observation_started_ms_ >= kLivenessObservationMs) {
      observing_ = false;
      reported_ = true;
      emit = true;
    }
    return {reported_, observing_, emit, flags()};
  }

 private:
  void resetObservation() {
    observation_started_ms_ = 0;
    observing_ = false;
    reported_ = false;
    reset_released_seen_ = false;
    clock_seen_ = false;
    mrdc_seen_ = false;
  }

  uint8_t flags() const {
    return static_cast<uint8_t>(
        kLivenessEnabledFlag |
        (reset_released_seen_ ? kResetReleasedFlag : 0) |
        (clock_seen_ ? kClockSeenFlag : 0) |
        (mrdc_seen_ ? kMrdcSeenFlag : 0));
  }

  bool enabled_ = false;
  uint32_t observation_started_ms_ = 0;
  bool observing_ = false;
  bool reported_ = false;
  bool reset_released_seen_ = false;
  bool clock_seen_ = false;
  bool mrdc_seen_ = false;
};

inline uint8_t crc8AtmUpdate(uint8_t crc, uint8_t value) {
  crc ^= value;
  for (uint8_t bit = 0; bit < 8; ++bit) {
    crc = static_cast<uint8_t>(
        (crc & 0x80) ? static_cast<uint8_t>((crc << 1) ^ 0x07)
                     : static_cast<uint8_t>(crc << 1));
  }
  return crc;
}

template <typename Sink>
size_t writeNanoLivenessFrame(Sink &sink, uint8_t flags) {
  const uint8_t body[] = {
      kNanoLivenessType,
      0x02,
      kNanoLivenessVersion,
      static_cast<uint8_t>(flags & kLivenessKnownFlags),
  };
  uint8_t crc = 0;
  for (const uint8_t value : body) crc = crc8AtmUpdate(crc, value);
  const uint8_t frame[] = {0xA5, 0x5A, body[0], body[1],
                           body[2], body[3], crc};
  size_t written = 0;
  for (const uint8_t value : frame) written += sink.write(value);
  return written;
}

}  // namespace jukuravi
