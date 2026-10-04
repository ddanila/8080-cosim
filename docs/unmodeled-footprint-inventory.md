# Unmodeled footprint inventory

Status: **DESIGN HOLD / FDC FUNCTIONAL PINS UNTRACED**

This generated report catches both IC footprints absent from the board
model and promoted devices whose functional pins remain untraced or on
explicit continuity-boundary nets. Closing either class requires source-model
and endpoint-coverage proof, followed by complete route/package regeneration.

## Command

```sh
python3 scripts/report_unmodeled_footprint_inventory.py
```

## Summary

- Board JSON SHA-256: `98864ba47523a05d05afea6a7ed11591e68a2c3de7a46e39cf00e60b880fb13c`
- Source PCB SHA-256: `c1fbfcdeae9a859f76d9c46f79c570f83e7d1a98a5a136ef60e818d801482b97`
- Routed PCB SHA-256: `f22f7ba849a6088d7b41e8f2ada8153cda9226c8848bec00128044177643e26a`
- DSN SHA-256: `28dc905fb0afdacaa39314f7a2c9dd1292da47a9ea3e7ea735d96fcedbd0fc25`
- Modeled board-JSON `D*` ICs: `106`
- Source PCB IC footprints: `106`
- Routed PCB IC footprints: `106`
- DSN IC placements: `106`
- Footprint-only ICs in any PCB/DSN artifact: `0`
- Footprint-only ICs present in source PCB, routed PCB, and DSN: `0`

## Design-Release Consequence

There are `0` IC footprints with no board-JSON representation
and `4` promoted FDC devices with functional pins still
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
- Selected D105 routed-pad checks preserve these corrections; they do not
  establish whole-board source-pad parity or zero electrical blockers.
  See [ERC/parity](main-board-erc-parity.md) and the
  [routed audit](routed-refresh-audit.md) for current release holds.
  Future P0 source closure requires complete route/package regeneration.

## D30 READY Flip-Flop Boundary

- The full-resolution sheet-1 source and direct target-board continuity agree:
  D30.1 `/CLR1`, D30.4 `/PRE1`, D30.10 `/PRE2`, and D30.12 `D2`
  share the D38.8 active-low STB conductor, pulled high through R5.
  Pin 2 `D1` is pulled high through R6, pin 3 `CLK1` is `PHI2TTL`, and
  pin 5 `Q1` reaches D1 READY/pin 23 through R29 1 kΩ.
- Owner continuity plus the native cross-sheet chase establish that D2.12
  and R6 feed D30.2;
  D30.1/.4/.10/.12 and R5 are closed to the D38.8/W8.2 status-strobe island; D30.5
  reaches CPU READY through R29;
  and D105.11 drives D30.13. Section B is also closed: D30.11 joins the
  D105.2/D13.4/D11.20 clock conductor, and D30.8 drives D29.7. Native
  sheet 1 plus `.009` placement/photo evidence close `H` at X1.107B
  with R1 2 kΩ to +5 V. The measured READY/WAIT continuity is closed;
  a powered waveform remains optional bring-up validation.

## AG3 Package Placement

- `D97`, `D99`, and `D102` are photographed К155АГ3 dual one-shots and use
  16-pin 7.62 mm DIP packages, matching the already traced D56 AG3
  pinout (including RC pins 14/15).
- Their two photographed rows are package-fitted and placed from
  shared-image pitch plus the visible right board edge.

## FDC Device Pinout Recovery

- `D95` and `D101` are typed as К555КП12 / 74LS253 dual 4:1
  three-state multiplexers. Recovered `.009` sheet 3 closes every
  D95 functional pin as the 1/2 MHz controller and 4/8 MHz separator
  clock mux; D101 retains only its explicitly listed precomp boundaries.
  Pin roles follow <https://gatchina.pw/datasheets/микросхемы/555/555КП12.pdf>.
- `D98` is typed as a К155ЛП11 / SN74367 six-channel three-state
  buffer; its two enable groups and six A/Y pairs follow the device sheet.
  Exact-revision sheet 3 uses five pairs and explicitly omits pair 4/pins 9-10:
  <https://static.chipdip.ru/lib/493/DOC048493374.pdf>.
  The five used buffers and both grounded enable groups are now structural-only
  HDL and LVS-visible; pair 4 remains an explicit structural no-connect.
- `D28` is typed as the К155ЛН3 six-inverter open-collector family.
  Factory `.009` sheet 3 closes all six sections through drive-select, READY,
  separator-clock, and DRQ/INTRQ conditioner paths. The drawing instead omits
  D98.9/.10 and complementary outputs D97.13/D102.4. The exact sheet-3
  D96.13-D99.10 junction is now retained as a sheet-1 source boundary.
  All six D28 sections are now structural-only HDL and LVS-visible.

## Footprint-Only ICs

| Ref | Mark/value | Footprint | Source PCB | Routed PCB | DSN | Generator note |
| --- | --- | --- | --- | --- | --- | --- |

## Promoted FDC Pin Boundaries

These devices now have physical pin models and routed power pins. Their
listed signal pins are either unnetted or carried by a source-risk boundary
until continuity or an explicit disposition is proved. Source-closed nets and
documented intentional no-connects are excluded.

| Ref | Untraced functional pins |
| --- | --- |
| `D96` | 9:Q2, 13:CLR2_N |
| `D99` | 2:B, 4:Q_N, 5:Q2, 10:B2, 11:CLR2_N, 12:Q2_N |
| `D100` | 3:A2, 7:A6, 9:OE_N, 11:T, 20:VCC_5V |
| `D101` | 1:OE0_N, 3:D03, 4:D02, 5:D01, 6:D00 |

## Closure Rule

1. Keep every unread functional pin explicit until continuity is proved.
2. After any board-JSON net promotion, regenerate PCB/DSN/BOM reports
   and route the affected pads before claiming endpoint coverage.
3. D105 is modeled in board JSON, the source PCB, HDL, and the promoted
   exact-source route. X1.107B/R1 close `H`;
   remaining priority belongs to D94 and the FDC (D30.8/.11 are owner-closed)
   support cluster. Physical D2 truth and its measured D0 path are adopted.
4. `READY FOR DESIGN RELEASE` is emitted only when no footprint or
   promoted FDC functional pin remains outside the net model.
