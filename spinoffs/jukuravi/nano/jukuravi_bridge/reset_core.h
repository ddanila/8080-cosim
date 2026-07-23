#pragma once

#include <stdint.h>

namespace jukuravi {

// The 8080A requires RESET for at least three clock cycles. A switch-like
// 250 ms closure is intentionally conservative and easy to verify on a meter
// or logic analyzer. Keep the bridge quiet briefly after release so the board
// reset network and CPU fetch path settle before any bytes become evidence.
constexpr uint32_t kStartupResetPulseMs = 250;
constexpr uint32_t kStartupResetRecoveryMs = 50;
constexpr uint8_t kResetDrivePin = 4;
constexpr uint8_t kResetHoldPin = 5;

// D5 uses INPUT_PULLUP. A service jumper or maintained switch to Nano GND asks
// for reset, while an open or disconnected control fails safe to AUTO mode.
constexpr bool resetHoldRequested(bool input_high) { return !input_high; }

struct StartupResetState {
  bool asserted;
  bool bridge_ready;
};

class StartupResetSequencer {
 public:
  void begin(uint32_t now_ms) {
    phase_started_ms_ = now_ms;
    phase_ = Phase::kAsserted;
  }

  StartupResetState update(uint32_t now_ms, bool hold_requested = false) {
    if (phase_ == Phase::kUnstarted) return {false, false};

    // A hold request always wins, including after startup. Starting a new
    // assertion interval here guarantees a later release still gets the full
    // minimum pulse and recovery gate.
    if (hold_requested && phase_ != Phase::kAsserted) {
      phase_started_ms_ = now_ms;
      phase_ = Phase::kAsserted;
    }

    if (!hold_requested && phase_ == Phase::kAsserted &&
        now_ms - phase_started_ms_ >= kStartupResetPulseMs) {
      phase_started_ms_ = now_ms;
      phase_ = Phase::kRecovery;
    } else if (!hold_requested && phase_ == Phase::kRecovery &&
               now_ms - phase_started_ms_ >= kStartupResetRecoveryMs) {
      phase_ = Phase::kReady;
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

  // Unsigned subtraction keeps both intervals safe across millis() rollover.
  // Ready remains latched unless the explicit hold input requests a new pulse.
  uint32_t phase_started_ms_ = 0;
  Phase phase_ = Phase::kUnstarted;
};

}  // namespace jukuravi
