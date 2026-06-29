# Transcription — Clock subsystem (Sheet 2, A3)

Discrete clock (no 8224). Crystal Z1 + ЛН1 oscillator (D59) + phase gates
(D33 ЛА3, D35 ЛН5, D36 ЛА12, D38 ЛА1) → PST CLK → Φ1/Φ2/ФRTTL/STB.

## Hardened (scan) — the outputs that cross to the CPU/8238
- **Φ1 ← D35 (ЛН5) pin 10** (input pin 11), via R37 360Ω → CPU Φ1 (pin 22). [scan]
- **Φ2 ← D35 (ЛН5) pin 12** (input pin 13), via R36 360Ω → CPU Φ2 (pin 15). [scan]
- **STB ← D38 (ЛА1) pin 8** (4-input NAND) → 8238 STSTB (pin 1). [scan]
- ⇒ nets `PHI1`, `PHI2`, `STSTB` flipped to **scan**. Provenance **44 → 47/99**.

## Remaining (structural, lower value — gate-level timing)
- **OSC distribution**: D59 (ЛН1) oscillator output pin + how PST CLK reaches the
  phase gates (D33/D36) — `OSC` net still `assumed`.
- **ФRTTL / PHI2TTL**: the TTL-level phase to the video counter (D44) — pin uncertain.
- The exact phase-derivation gate-by-gate logic (how Φ1/Φ2 are formed from PST CLK).
- **RESET** (from D13 RC, Sheet 1) and **READY** (from D30, Sheet 1) — separate
  Sheet-1 circuits, not the Sheet-2 clock gen (address with A6).
