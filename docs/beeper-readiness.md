# Beeper readiness

Status: **STANDALONE SOUND TOGGLE AND JSON HANDOFF GUARDED**

The Icarus test instantiates D57's PIT primitive and writes control 76h
and count 4 to channel 1. It counts SOUND transitions throughout the
simulation, waits 40 input clocks after programming, and requires at
least two transitions in total. It does not verify tone frequency,
complete CPU I/O decoding, analog drive, or audible output.

- D57 is the third 8253 PIT (`0x18..0x1B`), and channel 1 / `OUT1` is the
  traced `SOUND` source.
- `kicad/juku.board.json` independently carries the traced handoff:
  `D57.OUT1 -> R90 -> VT1/VD4/R91 clamp -> R48 -> SPKR`.
- The July target-board view directly reads VD4 as `КД521В`; an independent May view corroborates the grade-В reverse face;
  the retained sheet supplies its cathode/anode connectivity.

## Command

Run from the repository root with Bash, Python 3, and Icarus Verilog
(`iverilog` and `vvp`). Simulation files are temporary and removed on
exit. After the HDL and JSON checks pass, the command overwrites this
report at its fixed path, `docs/beeper-readiness.md`.

```sh
sync/beeper_check.sh
```

## Digital Evidence

| Check | Result |
| --- | --- |
| D57 `OUT1` / `SOUND` has at least two transitions over the full simulation | PASS |

## Board Handoff Evidence

The JSON check requires the nodes below and VD4's modeled value КД521В.
Additional net members are allowed. It does not inspect photo hashes,
PCB pads, routed copper, or installed diode polarity. Detailed source
annotations remain in `kicad/juku.board.json`.

| Net | Result | Required nodes |
| --- | --- | --- |
| `SOUND` | PASS | `D57.13`, `R90.1` |
| `SND_BASE` | PASS | `R90.2`, `VD4.2`, `VT1.3` |
| `SND_CLAMP` | PASS | `VD4.1`, `R91.1` |
| `AVDC` | PASS | `R91.2`, `D26.40` |
| `SND_OUT` | PASS | `VT1.1`, `R48.1` |
| `SPKR` | PASS | `R48.2` |

## Remaining Boundary

Physical bring-up needs the speaker unit and level/current checks on real
hardware. Photo evidence establishes the clamp part designation; the
retained drawing supplies polarity. Those records are distinct from
physical continuity and powered audio verification.
