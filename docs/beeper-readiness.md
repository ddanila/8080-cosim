# Beeper readiness

Status: **DIGITAL BEEPER SOURCE READY**

This guard proves the runnable digital source of the Juku beeper path:

- D57 is the third 8253 PIT (`0x18..0x1B`), and channel 1 / `OUT1` is the
  traced `SOUND` source.
- `hdl/sim/beeper_path_tb.v` programs D57 channel 1 with a small reload value
  and requires `OUT1` to toggle.
- The physical analog path after `SOUND` is already traced in the board data:
  `D57.OUT1 -> R90 -> VT1/VD4/R91 clamp -> R48 -> SPKR`.

## Command

```sh
sync/beeper_check.sh
```

## Evidence

| Check | Result |
| --- | --- |
| D57 channel 1 accepts control/data writes | PASS |
| D57 `OUT1` / `SOUND` toggles after programming | PASS |

## Remaining Boundary

- This is a digital source guard, not an analog speaker model. Physical bring-up
  still needs the speaker unit, clamp polarity, and level/current check on real
  hardware.
