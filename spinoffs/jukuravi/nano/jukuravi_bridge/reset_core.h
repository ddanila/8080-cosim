#pragma once

#include <stdint.h>

namespace jukuravi {

// The 8080A requires RESET for at least three clock cycles. A switch-like
// 250 ms closure is intentionally conservative and easy to verify on a meter
// or logic analyzer. Keep the bridge quiet briefly after release so the board
// reset network and CPU fetch path settle before any bytes become evidence.
constexpr uint32_t kStartupResetPulseMs = 250;
constexpr uint32_t kStartupResetRecoveryMs = 50;

struct StartupResetState {
  bool asserted;
  bool bridge_ready;
};

class StartupResetSequencer {
 public:
  void begin(uint32_t now_ms) {
    started_ms_ = now_ms;
    phase_ = Phase::kAsserted;
  }

  StartupResetState update(uint32_t now_ms) {
    if (phase_ == Phase::kAsserted || phase_ == Phase::kRecovery) {
      // Unsigned subtraction makes the one startup interval safe across a
      // millis() rollover. Ready is latched so a complete 49.7-day timestamp
      // cycle can never start a second, unintended pulse.
      const uint32_t elapsed = now_ms - started_ms_;
      if (elapsed >= kStartupResetPulseMs + kStartupResetRecoveryMs) {
        phase_ = Phase::kReady;
      } else if (elapsed >= kStartupResetPulseMs) {
        phase_ = Phase::kRecovery;
      }
    }
    return {
        phase_ == Phase::kAsserted,
        phase_ == Phase::kReady,
    };
  }

 private:
  enum class Phase : uint8_t {
    kUnstarted,
    kAsserted,
    kRecovery,
    kReady,
  };

  uint32_t started_ms_ = 0;
  Phase phase_ = Phase::kUnstarted;
};

}  // namespace jukuravi
