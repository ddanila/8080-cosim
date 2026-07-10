# Decoupling capacitor value fidelity

Status date: 2026-07-10.

Status: **DECAP CONNECTIVITY GUARDED / PER-POSITION VALUE PENDING**

This generated report isolates the C35-C72 decoupling-capacitor
authenticity issue. The board model and routed PCB preserve the two
array-power bypass rail groups, but the exact factory per-position
capacitance values are not proven by current automatic evidence.

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| All C35-C72 refs exist in board JSON | PASS | 38/38 rows |
| Rail-group connectivity matches model expectation | PASS | RAIL_E<->RAIL_H: 19, RAIL_G<->RAIL_E: 19 |
| Current model value is uniform 0,047 | PASS | 0,047: 38 |
| Historical value census is reconciled per position | FAIL | raw notes report mixed values but no per-position mapping |

## Current Board Model

| Ref | Model value | Pin 1 net | Pin 2 net | Provenance note |
| --- | --- | --- | --- | --- |
| C35 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D60 remains assumed |
| C36 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D61 remains assumed |
| C37 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D62 remains assumed |
| C38 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D63 remains assumed |
| C39 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D64 remains assumed |
| C40 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D65 remains assumed |
| C41 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D66 remains assumed |
| C42 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D67 remains assumed |
| C43 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D15 remains assumed |
| C44 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D17 remains assumed |
| C45 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D19 remains assumed |
| C46 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D21 remains assumed |
| C47 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D5 remains assumed |
| C48 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D1 remains assumed |
| C49 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D10 remains assumed |
| C50 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D11 remains assumed |
| C51 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D26 remains assumed |
| C52 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D27 remains assumed |
| C53 | 0,047 | RAIL_G | RAIL_E | BOM/DSN value 0,047; traced array-power bypass group RAIL_G<->RAIL_E; per-position/refdes association near D54 remains assumed |
| C54 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D55 remains assumed |
| C55 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D57 remains assumed |
| C56 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D23 remains assumed |
| C57 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D29 remains assumed |
| C58 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D6 remains assumed |
| C59 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D7 remains assumed |
| C60 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D44 remains assumed |
| C61 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D46 remains assumed |
| C62 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D48 remains assumed |
| C63 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D40 remains assumed |
| C64 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D38 remains assumed |
| C65 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D35 remains assumed |
| C66 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D42 remains assumed |
| C67 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D58 remains assumed |
| C68 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D14 remains assumed |
| C69 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D3 remains assumed |
| C70 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D71 remains assumed |
| C71 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D79 remains assumed |
| C72 | 0,047 | RAIL_E | RAIL_H | BOM/DSN value 0,047; traced array-power bypass group RAIL_E<->RAIL_H; per-position/refdes association near D87 remains assumed |

## Evidence Reconciliation

- `kicad/juku.board.json`, `kicad/juku.dsn`, and the generated PCB
  agree that C35-C53 are the `RAIL_G` to `RAIL_E` bypass group and
  C54-C72 are the `RAIL_E` to `RAIL_H` bypass group.
- The current BOM/model value for these 38 positions is uniform
  `0,047`, which is suitable for the functional replica's modeled
  bypass role.
- The retained factory and owner-photo evidence includes aggregate
  mixed-value capacitor counts, but no defensible mapping from those
  counts to individual C35-C72 positions.
- DSN/PCB placement preserves the two physical rows, but the available
  photographs do not expose readable markings for every position.

## Boundary

- Do not silently promote the old mixed-value census into C35-C72
  values; it is a board-authenticity lead, not a per-refdes map.
- Do not treat the uniform `0,047` model as Tier-3 factory value
  proof. It is a functional and currently routed BOM/model value.
- The next data-unlocking action is a macro-photo/value read or a
  matching specification page that maps values to individual
  C35-C72 refdes positions.
