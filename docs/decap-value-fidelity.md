# Decoupling capacitor value fidelity

Status date: 2026-07-16.

Status: **DRAM-FIELD ARTWORK/POPULATION CLOSED / VALUES AND NON-FIELD PLACEMENTS PENDING**

This generated report isolates the C35-C72 decoupling-capacitor
authenticity issue. The board model and routed PCB preserve the two
array-power bypass rail groups as schematic intent. The `.009` factory
drawing and owner-board morphology close the 4x8 DRAM-field artwork and population:
fit C38/C42/C46/C50 and leave the other 28 inherited footprints empty.
The older C63 grid landing remains bare common artwork, distinct from the absent
`.009` C63 callout between D41/D40. Six non-field placement/population
dispositions and all factory capacitance values remain open.

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| All C35-C72 refs exist in board JSON | PASS | 38/38 rows |
| Rail-group connectivity matches model expectation | PASS | GND<->RAIL_H: 19, RAIL_G<->GND: 19 |
| Current model value is uniform 0,047 | PASS | 0,047: 38 |
| Target DRAM-bank C38/C42/C46/C50 placements are registered | PASS | factory drawing + owner landing/remnant sites + generator/source PCB |
| Full inherited 4x8 DRAM-grid artwork is photo-registered | PASS | 32 target landing pairs; C63 restored; C69 eighth-column placement |
| Other 28 inherited DRAM-grid sites are assembly DNP | PASS | bare tinned target footprints retained in PCB; native KiCad DNP/position metadata and populate-now BOM are guarded |
| Six non-field positions are held from fabrication | PASS | retired fit-to-space coordinates are absent from generator/source PCB; schematic intent and circuit-review gate remain |
| C63 target-board population is DNP | PASS | bare .009 callout; inherited grid verification footprint retained |
| Historical value census is reconciled per position | FAIL | raw notes report mixed values but no per-position mapping |

## Current Board Model

| Ref | Model value | Target population | Pin 1 net | Pin 2 net | Provenance note |
| --- | --- | --- | --- | --- | --- |
| C35 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND | .009 factory drawing omits C35 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic RAIL_G<->GND bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D60 |
| C36 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND | .009 factory drawing omits C36 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic RAIL_G<->GND bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D61 |
| C37 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND | .009 factory drawing omits C37 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic RAIL_G<->GND bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D62 |
| C38 | 0,047 | populate (factory drawing) | RAIL_G | GND | .009 factory drawing directly places C38 above D91 in the populated D91-D84 DRAM bank; the registered owner-board site retains the matching landing pair and clipped lead remnants after body removal. Populate for the factory replica; BOM/DSN value 0,047 remains a functional model value and the exact factory capacitance is pending |
| C39 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND | .009 factory drawing omits C39 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic RAIL_G<->GND bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D64 |
| C40 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND | .009 factory drawing omits C40 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic RAIL_G<->GND bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D65 |
| C41 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND | .009 factory drawing omits C41 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic RAIL_G<->GND bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D66 |
| C42 | 0,047 | populate (factory drawing) | RAIL_G | GND | .009 factory drawing directly places C42 above D89 in the populated D91-D84 DRAM bank; the registered owner-board site retains the matching landing pair and clipped lead remnants after body removal. Populate for the factory replica; BOM/DSN value 0,047 remains a functional model value and the exact factory capacitance is pending |
| C43 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND | .009 factory drawing omits C43 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic RAIL_G<->GND bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D15 |
| C44 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND | .009 factory drawing omits C44 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic RAIL_G<->GND bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D17 |
| C45 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND | .009 factory drawing omits C45 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic RAIL_G<->GND bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D19 |
| C46 | 0,047 | populate (factory drawing) | RAIL_G | GND | .009 factory drawing directly places C46 above D87 in the populated D91-D84 DRAM bank; the registered owner-board site retains the matching landing pair and clipped lead remnants after body removal. Populate for the factory replica; BOM/DSN value 0,047 remains a functional model value and the exact factory capacitance is pending |
| C47 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND | .009 factory drawing omits C47 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic RAIL_G<->GND bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D5 |
| C48 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND | .009 factory drawing omits C48 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic RAIL_G<->GND bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D1 |
| C49 | 0,047 | assembly DNP / footprint retained | RAIL_G | GND | .009 factory drawing omits C49 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic RAIL_G<->GND bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D10 |
| C50 | 0,047 | populate (factory drawing) | RAIL_G | GND | .009 factory drawing directly places C50 above D85 in the populated D91-D84 DRAM bank; the registered owner-board site retains the matching landing pair and clipped lead remnants after body removal. Populate for the factory replica; BOM/DSN value 0,047 remains a functional model value and the exact factory capacitance is pending |
| C51 | 0,047 | placement/population pending / no current PCB footprint | RAIL_G | GND | BOM/DSN value 0,047 and RAIL_G<->GND bypass intent remain schematic-only. The former near-D26 coordinate was an early fit-to-space assumption, not drawing/photo evidence; omit the PCB footprint until target placement and population are registered |
| C52 | 0,047 | placement/population pending / no current PCB footprint | RAIL_G | GND | BOM/DSN value 0,047 and RAIL_G<->GND bypass intent remain schematic-only. The former near-D27 coordinate was an early fit-to-space assumption, not drawing/photo evidence; omit the PCB footprint until target placement and population are registered |
| C53 | 0,047 | placement/population pending / no current PCB footprint | RAIL_G | GND | BOM/DSN value 0,047 and RAIL_G<->GND bypass intent remain schematic-only. The former near-D54 coordinate was an early fit-to-space assumption, not drawing/photo evidence; omit the PCB footprint until target placement and population are registered |
| C54 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H | .009 factory drawing omits C54 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic GND<->RAIL_H bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D55 |
| C55 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H | .009 factory drawing omits C55 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic GND<->RAIL_H bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D57 |
| C56 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H | .009 factory drawing omits C56 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic GND<->RAIL_H bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D23 |
| C57 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H | .009 factory drawing omits C57 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic GND<->RAIL_H bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D29 |
| C58 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H | .009 factory drawing omits C58 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic GND<->RAIL_H bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D6 |
| C59 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H | .009 factory drawing omits C59 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic GND<->RAIL_H bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D7 |
| C60 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H | .009 factory drawing omits C60 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic GND<->RAIL_H bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D44 |
| C61 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H | .009 factory drawing omits C61 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic GND<->RAIL_H bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D46 |
| C62 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H | .009 factory drawing omits C62 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic GND<->RAIL_H bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D48 |
| C63 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H | BOM/DSN value 0,047 and intended array-power bypass role GND<->RAIL_H are retained. The .009 factory C63 callout between D41/D40 is bare with no coherent drilled lead pair, proving assembly DNP there. Independently, registered component and solder panoramas expose the complete inherited 4x8 DRAM-decoupler artwork, including the older C63 grid landing at (176.1,145.6) mm. C63 remains assembly DNP with the fabricated footprint retained as bare common artwork; do not fit a capacitor or treat it as the absent .009 callout site |
| C64 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H | .009 factory drawing omits C64 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic GND<->RAIL_H bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D38 |
| C65 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H | .009 factory drawing omits C65 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic GND<->RAIL_H bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D35 |
| C66 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H | .009 factory drawing omits C66 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic GND<->RAIL_H bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D42 |
| C67 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H | .009 factory drawing omits C67 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic GND<->RAIL_H bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D58 |
| C68 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H | .009 factory drawing omits C68 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Schematic GND<->RAIL_H bypass intent remains modeled; the target per-position/refdes coordinate remains assumed from the old-revision .006 mapping near D14 |
| C69 | 0,047 | assembly DNP / footprint retained | GND | RAIL_H | .009 factory drawing omits C69 from the target DRAM assembly and the owner photo shows the inherited site bare with clean tinned landings; assembly DNP with the fabricated footprint retained. Registered component and solder panoramas place it at the eighth column of the fourth DRAM-decoupler row, centered at (198.4,195.8) mm; the former 3.9 mm left shift was only a routing workaround. Schematic GND<->RAIL_H bypass intent remains modeled |
| C70 | 0,047 | placement/population pending / no current PCB footprint | GND | RAIL_H | BOM/DSN value 0,047 and GND<->RAIL_H bypass intent remain schematic-only. The former near-D71 coordinate was an early fit-to-space assumption, not drawing/photo evidence; omit the PCB footprint until target placement and population are registered |
| C71 | 0,047 | placement/population pending / no current PCB footprint | GND | RAIL_H | BOM/DSN value 0,047 and GND<->RAIL_H bypass intent remain schematic-only. The former near-D79 coordinate was an early fit-to-space assumption, not drawing/photo evidence; omit the PCB footprint until target placement and population are registered |
| C72 | 0,047 | placement/population pending / no current PCB footprint | GND | RAIL_H | BOM/DSN value 0,047 and GND<->RAIL_H bypass intent remain schematic-only. The former near-D87 coordinate was an early fit-to-space assumption, not drawing/photo evidence; omit the PCB footprint until target placement and population are registered |

## Evidence Reconciliation

- The native sheet-2 ground symbol directly identifies rail E as GND.
  Board JSON retains C35-C53 between `RAIL_G` and `GND`, and C54-C72
  between `GND` and `RAIL_H` as schematic intent. The source PCB does
  not fabricate C51-C53/C70-C72 until their target positions are proved.
- C34 is separately source-closed across rail E/GND and rail F/+5 V;
  the former `RAIL_H`-to-GND assignment was a scan-reading error.
- The current BOM/model value for these 38 positions is uniform
  `0,047`, which is suitable for the functional replica's modeled
  bypass role. C63 is not populated at its `.009` callout; its inherited
  DRAM-grid landing pair remains fabricated as common artwork.
- The `.009` drawing directly labels C38, C42, C46, and C50 above
  D91, D89, D87, and D85 respectively. The owner component photo
  shows a matching landing pair with solder and clipped lead remnants
  at each site but no body. Those four parts are therefore populated
  in the factory replica; the photographed board records later removal.
- The same complete target view omits the other 28 positions in the
  older `.006` 4x8 zigzag. The owner view shows those inherited sites
  as clean bare tinned landings, including the four alternate bottom-row
  sites. They remain fabricated verification footprints but are marked
  assembly DNP and excluded from the populate-now BOM.
- The retained factory and owner-photo evidence includes aggregate
  mixed-value capacitor counts, but no defensible mapping from those
  counts to individual C35-C72 positions.
- C51-C53 and C70-C72 still require target-revision placement/population
  disposition. Their former near-chip coordinates were early fit-to-space
  assumptions and are now retired from the generator and source PCB. Exact
  target-artwork placement of those six remains unresolved. The full
  inherited 4x8 grid is now photogrammetrically registered from the
  target board, including C63 and the corrected C69 column.

## Boundary

- Do not silently promote the old mixed-value census into C35-C72
  values; it is a board-authenticity lead, not a per-refdes map.
- Do not treat the uniform `0,047` model as Tier-3 factory value
  proof. It is a functional and currently routed BOM/model value.
- The next data-unlocking action is a macro-photo/value read or a
  matching specification page that maps values to individual
  C35-C72 refdes positions.
