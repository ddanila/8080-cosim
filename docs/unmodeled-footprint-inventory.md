# Unmodeled footprint inventory

Status: **DESIGN HOLD / FDC FUNCTIONAL PINS UNTRACED**

This generated report catches both IC footprints absent from the board
model and promoted devices whose functional pins remain outside named
nets. Adding either class of endpoint requires a routed-PCB refresh and
endpoint-coverage proof.

## Command

```sh
python3 scripts/report_unmodeled_footprint_inventory.py
```

## Summary

- Modeled board-JSON `D*` ICs: `106`
- Source PCB IC footprints: `106`
- Routed PCB IC footprints: `106`
- DSN IC placements: `106`
- Footprint-only ICs in any PCB/DSN artifact: `0`
- Footprint-only ICs present in source PCB, routed PCB, and DSN: `0`

## Design-Release Consequence

There are `0` IC footprints with no board-JSON representation
and `9` promoted FDC devices with functional pins still
outside named nets. KiCad's zero-unconnected result cannot detect either class
until those endpoints are modeled. Both classes block design release.

## D105 Wait-Gate Boundary

- D105 inventory state: `MODELED`
- `D105` is promoted into board JSON and both PCB artifacts as a
  four-section К155ЛА3. The regenerated route has zero unrouted items.
- Sheet 1 proves D2.12 -> D105.9, D105.10 -> `H`/−5 V,
  D105.8 -> tied inputs 4+5, D13.4/MWR -> inputs 2/1, and the
  tied-input MRD inverter 12+13 -> 11 -> D30.13.
- D105.6 is traced to a D95 inverter on the older `.006` sheet and
  onward as `-WAIT` to E8-1. The `.009` BOM reassigns D95 to an FDC
  К555КП12, so that revision-specific inverter destination remains an
  explicit boundary rather than being assigned to the wrong footprint.

## D30 READY Flip-Flop Boundary

- The full-resolution sheet-1 source proves D30 section A: pin 4 `/PRE`
  and pin 2 `D` are pulled high, pin 3 `CLK` is `PHI2TTL`, pin 1
  `/CLR` is driven by `-SSTB`, and pin 5 `Q` reaches D1 READY/pin 23
  through R29 1 kΩ.
- D30 section A, R5, R6, and R29 are now promoted into board JSON. In
  section B, pins 10+12 are tied, pins 6+9 are intentional no-connects,
  and D105.11 now drives pin 13. Pin 8, pin 11, and the upstream source
  of pins 10+12 still require end-to-end reads.

## AG3 Package Correction

- `D97`, `D99`, and `D102` are КМ555АГ3 dual one-shots and use
  16-pin 7.62 mm DIP packages, matching the already traced D56 AG3
  pinout (including RC pins 14/15). The earlier 14-pin placement-only
  footprints omitted six physical holes across these three positions.
- D99 is shifted 0.7 mm within its explicitly assumed photo placement
  to clear R75 after restoring the full package length.

## Footprint-Only ICs

| Ref | Mark/value | Footprint | Source PCB | Routed PCB | DSN | Generator note |
| --- | --- | --- | --- | --- | --- | --- |

## Promoted FDC Pin Boundaries

These devices now have physical pin models and routed power pins. Their
remaining signal pins stay explicitly unnetted until continuity is proved.

| Ref | Untraced functional pins |
| --- | --- |
| `D28` | 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13 |
| `D95` | 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15 |
| `D96` | 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13 |
| `D97` | 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15 |
| `D98` | 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15 |
| `D99` | 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15 |
| `D101` | 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15 |
| `D102` | 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15 |
| `D106` | 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15 |

## Closure Rule

1. Keep every unread functional pin explicit until continuity is proved.
2. After any board-JSON net promotion, regenerate PCB/DSN/BOM reports
   and route the affected pads before claiming endpoint coverage.
3. D105 is modeled and routed. Remaining priority belongs to D2's
   truth/input rails, the `.009` WAIT-inverter handoff, D30's unread
   section-B endpoints, and the FDC support cluster.
4. `READY FOR DESIGN RELEASE` is emitted only when no footprint or
   promoted FDC functional pin remains outside the net model.
