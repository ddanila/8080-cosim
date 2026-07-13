# Unmodeled footprint inventory

Status: **DESIGN HOLD / FDC FUNCTIONAL PINS UNTRACED**

This generated report catches both IC footprints absent from the board
model and promoted devices whose functional pins remain untraced or on
explicit continuity-boundary nets. Closing either class requires a routed-PCB refresh and
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
untraced or carried only by explicit boundary nets. KiCad's zero-unconnected
result cannot establish remote continuity for those endpoints. They block
design release until measured or explicitly dispositioned.

## D105 Wait-Gate Boundary

- D105 inventory state: `MODELED`
- `D105` is promoted into board JSON and both PCB artifacts as a
  four-section К155ЛА3. Direct `.009` continuity proves D1.17 DBIN ->
  D105.9, pulled-up edge `H`/D13.13 -> D105.10, tied D105.4/.5, and
  D105.6 -> D5.4. The two NAND stages implement `DBIN AND H`.
- The same continuity pass proves MEMW on tied D105.12/.13 and
  D105.11 -> D30.13. This supersedes both the false D2.12-to-D105.9
  merge and the older `.006` D95 WAIT handoff.
- The derived routed snapshot predates those corrections and the source
  placement has seven collision pairs, so a full reroute remains blocked.

## D30 READY Flip-Flop Boundary

- The full-resolution sheet-1 source proves D30 section A: pin 4 `/PRE`
  and pin 2 `D` are pulled high, pin 3 `CLK` is `PHI2TTL`, pin 1
  `/CLR` is driven by `-SSTB`, and pin 5 `Q` reaches D1 READY/pin 23
  through R29 1 kΩ.
- Direct owner continuity corrects that topology: D2.12 and R6 feed D30.2;
  D30.5 reaches CPU READY through R29; D30.10/.12 share the R5 pull-up;
  and D105.11 drives D30.13. Pins 8 and 11 remain explicit boundaries.

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
| `D28` | 1:A1, 3:A2, 5:A3, 6:Y3, 9:A4, 11:A5, 13:A6 |
| `D95` | 1:OE0_N, 2:A1, 3:D03, 4:D02, 5:D01, 6:D00, 7:Q0, 9:Q1, 10:D10, 11:D11, 12:D12, 13:D13, 14:A0, 15:OE1_N |
| `D96` | 1:CLR1_N, 2:D1, 3:CLK1, 4:PRE1_N, 5:Q1, 6:Q1_N, 9:Q2, 10:PRE2_N, 11:CLK2, 12:D2, 13:CLR2_N |
| `D97` | 1:A_N, 2:B, 3:CLR_N, 4:Q_N, 5:Q2, 6:C2, 7:RC2, 9:A2_N, 10:B2, 11:CLR2_N, 12:Q2_N, 13:Q, 14:C1, 15:RC1 |
| `D98` | 1:OE14_N, 2:A1, 4:A2, 5:Y2, 6:A3, 9:Y4, 10:A4, 11:Y5, 12:A5, 13:Y6, 14:A6, 15:OE56_N |
| `D99` | 1:A_N, 4:Q_N, 5:Q2, 6:C2, 7:RC2, 9:A2_N, 10:B2, 11:CLR2_N, 12:Q2_N, 13:Q, 14:C1, 15:RC1 |
| `D101` | 1:OE0_N, 2:A1, 3:D03, 4:D02, 5:D01, 6:D00, 7:Q0, 9:Q1, 10:D10, 11:D11, 12:D12, 13:D13, 14:A0, 15:OE1_N |
| `D102` | 1:A_N, 2:B, 3:CLR_N, 4:Q_N, 5:Q2, 6:C2, 7:RC2, 9:A2_N, 10:B2, 11:CLR2_N, 12:Q2_N, 13:Q, 14:C1, 15:RC1 |
| `D106` | 1:D1, 2:Q1, 3:Q0, 4:DOWN, 5:UP, 6:Q2, 7:Q3, 9:D3, 10:D2, 11:LOAD_N, 12:CO, 13:BO, 14:CLR, 15:D0 |

## Closure Rule

1. Keep every unread functional pin explicit until continuity is proved.
2. After any board-JSON net promotion, regenerate PCB/DSN/BOM reports
   and route the affected pads before claiming endpoint coverage.
3. D105 is modeled in board JSON, the source PCB, and HDL; the routed
   snapshot predates the corrected topology. Remaining priority belongs
   to D30.8/.11 and the exact `H` pull-up/contact, D94, and the FDC
   support cluster. Physical D2 truth and its measured D0 path are adopted.
4. `READY FOR DESIGN RELEASE` is emitted only when no footprint or
   promoted FDC functional pin remains outside the net model.
