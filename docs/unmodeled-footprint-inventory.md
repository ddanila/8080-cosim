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

- Modeled board-JSON `D*` ICs: `95`
- Source PCB IC footprints: `106`
- Routed PCB IC footprints: `106`
- DSN IC placements: `106`
- Footprint-only ICs in any PCB/DSN artifact: `11`
- Footprint-only ICs present in source PCB, routed PCB, and DSN: `11`

## Design-Release Consequence

There are `11` IC footprints in PCB/DSN artifacts with no
pin-level representation in board JSON. KiCad's zero-unconnected result
cannot detect missing connections on placement-only footprints. Every row
below therefore blocks design release until it is either modeled and routed
or explicitly dispositioned as a redesign/DNP and removed from the released
PCB artifacts. Closing D105 alone is not sufficient.

## D105 Wait-Gate Boundary

- D105 inventory state: `PENDING MODEL + REROUTE`
- `D105` is an official `.009` `К155ЛА3` footprint present in
  `kicad/gen_kicad_pcb.py`, `kicad/juku.dsn`, `kicad/juku.kicad_pcb`,
  and `kicad/juku_routed.kicad_pcb`, but absent from
  `kicad/juku.board.json`.
- Existing sheet-1 evidence narrows the first useful closure to the
  wait-state chain: D2 `DO`/pin 12 feeds D105 pin 9; D105 has the two
  visible NAND sections `(9,10)->8` and `(4,5)->6`; D2 `V1/V2` are tied
  to ground. The same sheet also shows D105 `(1,2)->3` with D13.4 and
  MWR inputs, plus `(12,13)->11` used as an MRD inverter.
- Do not promote D105 into board JSON from this partial read alone. The
  remaining automatic/owner work is to trace the D105.10 `H` source and
  the D105.6 destination, then rerun PCB generation/routing so both
  source and routed PCB pad nets match the model.

## D30 READY Flip-Flop Boundary

- The full-resolution sheet-1 source proves D30 section A: pin 4 `/PRE`
  and pin 2 `D` are pulled high, pin 3 `CLK` is `PHI2TTL`, pin 1
  `/CLR` is driven by `-SSTB`, and pin 5 `Q` reaches D1 READY/pin 23
  through R29 1 kΩ.
- This establishes the CPU READY function and replaces the former generic
  'D30 support' description with exact pins. D30 section B (pins 8-13)
  is visibly wired on the same sheet but its crossed rail destinations
  still require a clean end-to-end read before D30 is promoted and routed.

## Footprint-Only ICs

| Ref | Mark/value | Footprint | Source PCB | Routed PCB | DSN | Generator note |
| --- | --- | --- | --- | --- | --- | --- |
| `D28` | `К155ЛН3` | `DIP-14_W7.62mm` | yes | yes | `К155ЛН3` | row 2 [.009: D28=ЛН3 -- NOT РЕ3; the old misread] |
| `D30` | `КМ555ТМ2` | `DIP-14_W7.62mm` | yes | yes | `КМ555ТМ2` | [emaplaat]  # ready ТМ2 [photo; 176.8 sat inside D1's DIP-40 body] |
| `D95` | `К555КП12` | `DIP-16_W7.62mm` | yes | yes | `К555КП12` | row 3: КП12 #1 [.009: D95] |
| `D96` | `КМ555ТМ2` | `DIP-14_W7.62mm` | yes | yes | `КМ555ТМ2` | row 2 [.009: D96=ТМ2] |
| `D97` | `КМ555АГ3` | `DIP-14_W7.62mm` | yes | yes | `КМ555АГ3` | row 3 [.009 АГ3 pool D97/D99/D102; per-position ASSUMED] |
| `D98` | `К155ЛП11` | `DIP-16_W7.62mm` | yes | yes | `К155ЛП11` | row 1 [.009: D98=ЛП11 ✓] |
| `D99` | `КМ555АГ3` | `DIP-14_W7.62mm` | yes | yes | `КМ555АГ3` | row 4 middle [pool, ASSUMED] |
| `D101` | `К555КП12` | `DIP-16_W7.62mm` | yes | yes | `К555КП12` | row 4: КП12 #2 [.009: D101] |
| `D102` | `КМ555АГ3` | `DIP-14_W7.62mm` | yes | yes | `КМ555АГ3` | row 4 right [pool, ASSUMED] |
| `D105` | `К155ЛА3` | `DIP-14_W7.62mm` | yes | yes | `К155ЛА3` | below D13 [emaplaat; was stacked ON D13 at 205.2]  # [.009 official] |
| `D106` | `К555ИЕ7` | `DIP-16_W7.62mm` | yes | yes | `К555ИЕ7` | row 2: the 5th ИЕ7 [.009: D106=ИЕ7] |

## Closure Rule

1. Keep placement-only official footprints here until their pins are
   traceable enough to add to `kicad/juku.board.json`.
2. After board JSON promotion, regenerate PCB/DSN/BOM reports and route
   the affected pads before claiming endpoint coverage.
3. D105 has first priority because it is tied to D2's wait-state PROM
   output and CPU wait behavior; D30 READY support and the FDC support
   cluster still require their own complete dispositions.
4. `READY FOR DESIGN RELEASE` is emitted only when no IC footprint
   remains outside the board-JSON pin model.
