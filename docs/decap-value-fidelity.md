# Decoupling capacitor value fidelity

Status: **DRAM OPTIONAL PAD IDENTITIES / VALUES AND NON-FIELD PLACEMENTS PENDING**

This generated report isolates the C35-C72 decoupling-capacitor
authenticity issue. The board model and routed PCB preserve the two
array-power bypass rail groups as schematic intent. The `.009` factory
drawing identifies C38/C42/C46/C50 for factory population and omits
the other 28 older grid refdes. Independent capacitor pad pairs remain
unproved: a proposed C35 pair
coincides with adjacent D67.16/D66.1 package contacts. The older C63
grid slot is distinct from the absent
`.009` C83 callout between D41/D40. Six non-field placement/population
dispositions and all factory capacitance values remain open.

## Command

Run from the repository root:

```sh
python3 scripts/report_decap_value_fidelity.py
```

A zero exit status confirms the guarded model, population and placement
contracts. Physical HOLD rows and the unresolved historical value census
remain release limits even when those contracts pass.

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| All C35-C72 refs exist in board JSON | PASS | 38/38 rows |
| Rail-group connectivity matches model expectation | PASS | GND<->RAIL_H: 19, RAIL_G<->GND: 19 |
| Current model value is uniform 0,047 | PASS | 0,047: 38 |
| Factory C38/C42/C46/C50 callouts are registered | PASS | exact .009 assembly labels + current model positions; owner pad identities remain open |
| Owner-board removal of the four fitted capacitors is proved | HOLD | no bodies visible; bright marks at all four sites lead to DRAM pin1/RAIL_H and pin16/GND, not the modeled capacitor pairs |
| Historical 4x8 measurements fit the model lattice | PASS | registered features are DRAM package contacts, not capacitor pads |
| Independent optional capacitor pad pairs are proved | HOLD | first C35 midpoint matches D67.16/D66.1 package contacts; two-sided D67-local projection of modeled C35 pads has no holes; audit all 28 optional sites |
| Other 28 inherited DRAM-grid refs are assembly DNP | PASS | .009 drawing omits them; modeled PCB footprints remain provisional pending hole identity |
| Six non-field positions are held from fabrication | PASS | retired fit-to-space coordinates are absent from generator/source PCB; schematic intent and circuit-review gate remain |
| C63 target-board population is DNP | PASS | .009 omits C63; independent inherited pad pair remains unverified; D41/D40 callout is C83 |
| Historical value census is reconciled per position | FAIL | raw notes report mixed values but no per-position mapping |

## Current Board Model

Per-refdes provenance is retained in [the board model](../kicad/juku.board.json).

| Ref | Model value | Target population | Pin 1 net | Pin 2 net |
| --- | --- | --- | --- | --- |
| C35 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND |
| C36 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND |
| C37 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND |
| C38 | 0,047 | populate (factory drawing) | RAIL_G | GND |
| C39 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND |
| C40 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND |
| C41 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND |
| C42 | 0,047 | populate (factory drawing) | RAIL_G | GND |
| C43 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND |
| C44 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND |
| C45 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND |
| C46 | 0,047 | populate (factory drawing) | RAIL_G | GND |
| C47 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND |
| C48 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND |
| C49 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND |
| C50 | 0,047 | populate (factory drawing) | RAIL_G | GND |
| C51 | 0,047 | placement/population pending / no current PCB footprint | RAIL_G | GND |
| C52 | 0,047 | placement/population pending / no current PCB footprint | RAIL_G | GND |
| C53 | 0,047 | placement/population pending / no current PCB footprint | RAIL_G | GND |
| C54 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H |
| C55 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H |
| C56 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H |
| C57 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H |
| C58 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H |
| C59 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H |
| C60 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H |
| C61 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H |
| C62 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H |
| C63 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H |
| C64 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H |
| C65 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H |
| C66 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H |
| C67 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H |
| C68 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H |
| C69 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H |
| C70 | 0,047 | placement/population pending / no current PCB footprint | GND | RAIL_H |
| C71 | 0,047 | placement/population pending / no current PCB footprint | GND | RAIL_H |
| C72 | 0,047 | placement/population pending / no current PCB footprint | GND | RAIL_H |

## Evidence and boundary

- The `.009` power corner puts C35-C53 between E4-selected rail G and
  E/GND, and C54-C72 between rail H/-5 V and E/GND. C34 separately joins
  E/GND to F/+5 V. The model preserves these source branch groups.
- The `.009` assembly labels C38/C42/C46/C50 above D91/D89/D87/D85.
  These are the factory population targets, but their independent pad
  identities remain open. Bright owner-photo marks reach DRAM pin1/RAIL_H
  and pin16/GND; they do not prove capacitor pads or owner-board removal.
- The other 28 inherited grid references are assembly DNP. Their modeled
  footprints remain provisional and excluded from the populate-now BOM.
  Registered lattice features are DRAM package contacts, not proof of
  independent capacitor holes.
- C51-C53/C70-C72 remain absent from the source PCB until target placement
  and population are proved. C63's inherited grid slot is unverified and
  distinct from the `.009` C83 callout between D41/D40.
- Uniform `0,047` is a model/BOM assignment. This guard checks its consistency;
  it does not establish factory capacitance or electrical suitability.
  Aggregate mixed-value counts do not supply a per-refdes value map.
- Close the holds with identified capacitor holes, macro value reads or a
  matching factory specification. Keep pad identity, population and value
  evidence separate. Detailed registration evidence is linked by the board
  provenance and retained under `ref/photos/dgsh5-109-009-sb/`.
