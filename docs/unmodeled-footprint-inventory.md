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
  four-section К155ЛА3. Correcting pin 10 exposes one −5 V airwire
  in the derived routed snapshot; replacement copper remains blocked.
- Sheet 1 proves D2.12 -> D105.9 and a distinct named off-sheet
  `H` arrow -> D105.10; the power legend does not equate `H` with −5 V.
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

- `D97`, `D99`, and `D102` are photographed К155АГ3 dual one-shots and use
  16-pin 7.62 mm DIP packages, matching the already traced D56 AG3
  pinout (including RC pins 14/15). The earlier 14-pin placement-only
  footprints omitted six physical holes across these three positions.
- Their two photographed rows are now package-fitted and placed from
  shared-image pitch plus the visible right board edge; the previous
  placeholder grid and its D99 clearance nudge are retired.

## FDC Device Pinout Recovery

- `D95` and `D101` are now typed as К555КП12 / 74LS253 dual
  4:1 three-state multiplexers with the documented OE/address/data/output
  pin roles: <https://gatchina.pw/datasheets/микросхемы/555/555КП12.pdf>.
- `D98` is now typed as a К155ЛП11 / SN74367 six-channel three-state
  buffer; its two enable groups and six A/Y pairs follow the device sheet:
  <https://static.chipdip.ru/lib/493/DOC048493374.pdf>.
- `D28` is now typed as the К155ЛН3 six-inverter open-collector family.
  These are device-level pin roles only; no Juku-specific signal net is
  assigned until the `.009` copper continuity is proved.

## Footprint-Only ICs

| Ref | Mark/value | Footprint | Source PCB | Routed PCB | DSN | Generator note |
| --- | --- | --- | --- | --- | --- | --- |

## Promoted FDC Pin Boundaries

These devices now have physical pin models and routed power pins. Their
remaining signal pins stay explicitly unnetted until continuity is proved.

| Ref | Untraced functional pins |
| --- | --- |
| `D28` | 1:A1, 2:Y1, 3:A2, 4:Y2, 5:A3, 6:Y3, 8:Y4, 9:A4, 10:Y5, 11:A5, 12:Y6, 13:A6 |
| `D95` | 1:OE0_N, 2:A1, 3:D03, 4:D02, 5:D01, 6:D00, 7:Q0, 9:Q1, 10:D10, 11:D11, 12:D12, 13:D13, 14:A0, 15:OE1_N |
| `D96` | 1:CLR1_N, 2:D1, 3:CLK1, 4:PRE1_N, 5:Q1, 6:Q1_N, 8:Q2_N, 9:Q2, 10:PRE2_N, 11:CLK2, 12:D2, 13:CLR2_N |
| `D97` | 1:A_N, 2:B, 3:CLR_N, 4:Q_N, 5:Q2, 6:C2, 7:RC2, 9:A2_N, 10:B2, 11:CLR2_N, 12:Q2_N, 13:Q, 14:C1, 15:RC1 |
| `D98` | 1:OE14_N, 2:A1, 4:A2, 5:Y2, 6:A3, 9:Y4, 10:A4, 11:Y5, 12:A5, 13:Y6, 14:A6, 15:OE56_N |
| `D99` | 1:A_N, 2:B, 3:CLR_N, 4:Q_N, 5:Q2, 6:C2, 7:RC2, 9:A2_N, 10:B2, 11:CLR2_N, 12:Q2_N, 13:Q, 14:C1, 15:RC1 |
| `D101` | 1:OE0_N, 2:A1, 3:D03, 4:D02, 5:D01, 6:D00, 7:Q0, 9:Q1, 10:D10, 11:D11, 12:D12, 13:D13, 14:A0, 15:OE1_N |
| `D102` | 1:A_N, 2:B, 3:CLR_N, 4:Q_N, 5:Q2, 6:C2, 7:RC2, 9:A2_N, 10:B2, 11:CLR2_N, 12:Q2_N, 13:Q, 14:C1, 15:RC1 |
| `D106` | 1:D1, 2:Q1, 3:Q0, 4:DOWN, 5:UP, 6:Q2, 7:Q3, 9:D3, 10:D2, 11:LOAD_N, 12:CO, 13:BO, 14:CLR, 15:D0 |

## Closure Rule

1. Keep every unread functional pin explicit until continuity is proved.
2. After any board-JSON net promotion, regenerate PCB/DSN/BOM reports
   and route the affected pads before claiming endpoint coverage.
3. D105 is modeled and routed. Remaining priority belongs to D2's
   truth/input rails, the `.009` WAIT-inverter handoff, D30's unread
   section-B endpoints, and the FDC support cluster.
4. `READY FOR DESIGN RELEASE` is emitted only when no footprint or
   promoted FDC functional pin remains outside the net model.
