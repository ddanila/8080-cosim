# Unmodeled footprint inventory

Status: **UNMODELED FOOTPRINT INVENTORY GUARDED**

This generated report catches IC footprints that exist in the generated
PCB/DSN artifacts but are not yet part of `kicad/juku.board.json`.
These parts are placement-only for the current upload-ready package:
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

## D105 Wait-Gate Boundary

- D105 inventory state: `PASS`
- `D105` is an official `.009` `К155ЛА3` footprint present in
  `kicad/gen_kicad_pcb.py`, `kicad/juku.dsn`, `kicad/juku.kicad_pcb`,
  and `kicad/juku_routed.kicad_pcb`, but absent from
  `kicad/juku.board.json`.
- Existing sheet-1 evidence narrows the first useful closure to the
  wait-state chain: D2 `DO`/pin 12 feeds D105 pin 9; D105 has the two
  visible NAND sections `(9,10)->8` and `(4,5)->6`; D2 `V1/V2` are tied
  to ground.
- Do not promote D105 into board JSON from this partial read alone. The
  remaining automatic/owner work is to trace the D105.10 `H` source and
  the D105.6 destination, then rerun PCB generation/routing so both
  source and routed PCB pad nets match the model.

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
3. D105 has priority over the other placement-only extras because it is
   already tied to D2's wait-state PROM output and CPU wait behavior.
