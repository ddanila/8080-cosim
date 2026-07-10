# Unmodeled footprint inventory

Status: **DESIGN HOLD / FUNCTIONAL FOOTPRINTS UNMODELED**

This generated report catches IC footprints that exist in the generated
PCB/DSN artifacts but are not yet part of `kicad/juku.board.json`.
These parts are placement-only in the current engineering package:
promoting any of them to modeled nets changes the netlist and requires
a routed-PCB refresh plus endpoint-coverage proof.

## Command

```sh
python3 scripts/report_unmodeled_footprint_inventory.py
```

## Summary

- Modeled board-JSON `D*` ICs: `97`
- Source PCB IC footprints: `106`
- Routed PCB IC footprints: `106`
- DSN IC placements: `106`
- Footprint-only ICs in any PCB/DSN artifact: `9`
- Footprint-only ICs present in source PCB, routed PCB, and DSN: `9`

## Design-Release Consequence

There are `9` IC footprints in PCB/DSN artifacts with no
pin-level representation in board JSON. KiCad's zero-unconnected result
cannot detect missing connections on placement-only footprints. Every row
below therefore blocks design release until it is either modeled and routed
or explicitly dispositioned as a redesign/DNP and removed from the released
PCB artifacts. Closing D105 alone is not sufficient.

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
| `D28` | `К155ЛН3` | `DIP-14_W7.62mm` | yes | yes | `К155ЛН3` | row 2 [.009: D28=ЛН3 -- NOT РЕ3; the old misread] |
| `D95` | `К555КП12` | `DIP-16_W7.62mm` | yes | yes | `К555КП12` | row 3: КП12 #1 [.009: D95] |
| `D96` | `КМ555ТМ2` | `DIP-14_W7.62mm` | yes | yes | `КМ555ТМ2` | row 2 [.009: D96=ТМ2] |
| `D97` | `КМ555АГ3` | `DIP-16_W7.62mm` | yes | yes | `КМ555АГ3` | row 3 [.009 АГ3 pool D97/D99/D102; per-position ASSUMED] |
| `D98` | `К155ЛП11` | `DIP-16_W7.62mm` | yes | yes | `К155ЛП11` | row 1 [.009: D98=ЛП11 ✓] |
| `D99` | `КМ555АГ3` | `DIP-16_W7.62mm` | yes | yes | `КМ555АГ3` | row 4 middle [pool, ASSUMED; shifted 0.7 mm for 16-pin package clearance] |
| `D101` | `К555КП12` | `DIP-16_W7.62mm` | yes | yes | `К555КП12` | row 4: КП12 #2 [.009: D101] |
| `D102` | `КМ555АГ3` | `DIP-16_W7.62mm` | yes | yes | `КМ555АГ3` | row 4 right [pool, ASSUMED] |
| `D106` | `К555ИЕ7` | `DIP-16_W7.62mm` | yes | yes | `К555ИЕ7` | row 2: the 5th ИЕ7 [.009: D106=ИЕ7] |

## Closure Rule

1. Keep placement-only official footprints here until their pins are
   traceable enough to add to `kicad/juku.board.json`.
2. After board JSON promotion, regenerate PCB/DSN/BOM reports and route
   the affected pads before claiming endpoint coverage.
3. D105 is modeled and routed. Remaining priority belongs to D2's
   truth/input rails, the `.009` WAIT-inverter handoff, D30's unread
   section-B endpoints, and the FDC support cluster.
4. `READY FOR DESIGN RELEASE` is emitted only when no IC footprint
   remains outside the board-JSON pin model.
