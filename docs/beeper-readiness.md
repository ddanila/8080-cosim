# Beeper readiness

Status: **DIGITAL BEEPER SOURCE + BOARD HANDOFF READY**

This guard proves the runnable digital source of the Juku beeper path and
cross-checks the traced board handoff into the analog driver.

- D57 is the third 8253 PIT (`0x18..0x1B`), and channel 1 / `OUT1` is the
  traced `SOUND` source.
- `hdl/sim/beeper_path_tb.v` programs D57 channel 1 with a small reload value
  and requires `OUT1` to toggle.
- `kicad/juku.board.json` independently carries the traced handoff:
  `D57.OUT1 -> R90 -> VT1/VD4/R91 clamp -> R48 -> SPKR`.

## Command

```sh
sync/beeper_check.sh
```

## Digital Evidence

| Check | Result |
| --- | --- |
| D57 channel 1 accepts control/data writes | PASS |
| D57 `OUT1` / `SOUND` toggles after programming | PASS |

## Board Handoff Evidence

| Net | Result | Required nodes | Source |
| --- | --- | --- | --- |
| `SOUND` | PASS | `D57.13`, `R90.1` | traced sheet-2 (crops s2_d57_outs/s2_beeper): D57.OUT1 (pin 13) -> bundle tag 10 -> R90 2k (beeper drive) |
| `SND_BASE` | PASS | `R90.2`, `VD4.2`, `VT1.3` | traced sheet-2 (crops s2_d57_outs/s2_beeper): R90 -> VT1 КТ972 physical base pin 3; VD4 anode clamp |
| `SND_CLAMP` | PASS | `VD4.1`, `R91.1` | traced sheet-2 (crops s2_d57_outs/s2_beeper): VD4 cathode -> R91 1k -> AVDC rail |
| `AVDC` | PASS | `R91.2`, `D26.40` | traced both ends: sheet-2 R91 -> rail -> "(1)" export (crop s2_spkr_edge); sheet-1 arrival found (crop s1_avdc_band6): label reads AUDC = D26 ВВ55 pin 40 (PA4), port-A row between SC0-SC3 (PA0-3) and PREN/STB (PA6/7); no edge arrow on that row -> cross-sheet only. The 'AVDC' on sheet 2 is the same handwritten label (U/V ambiguity) |
| `SND_OUT` | PASS | `VT1.1`, `R48.1` | traced sheet-2 (crops s2_d57_outs/s2_beeper): VT1 emitter-follower out -> R48 8.2R -> speaker line |
| `SPKR` | PASS | `R48.2` | traced sheet-2 (crop s2_spkr_edge): R48 -> WIRE POST 1 (SB spot 252.7,205.2); post 2 (252.7,199.9) = GND return -- the ДГШ5.884.001 speaker unit solders to posts, no connector |

## Remaining Boundary

- This is a digital source plus board-handoff guard, not an analog speaker
  model. Physical bring-up still needs the speaker unit, clamp polarity,
  and level/current check on real hardware.
