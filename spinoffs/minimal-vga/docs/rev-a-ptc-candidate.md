# Rev A PTC candidate readiness

Status date: **2026-07-23**.

Status: **EXACT F1 CANDIDATE GUARDED / THERMAL AND FIRST-ARTICLE CHECK OPEN**.

This report guards Bourns MF-RG300-0-14 as the exact Rev-A F1
candidate. It checks the preserved manufacturer datasheet, board
topology, committed KiCad fit geometry, electrical planning facts, and
ordering identifiers. It is not a thermal qualification, live-stock
claim, or fabrication authorization.

## Command

```sh
python3 spinoffs/minimal-vga/kicad/report_rev_a_ptc_candidate.py
```

## Guarded checks

| Check | Result | Evidence |
| --- | --- | --- |
| Manufacturer datasheet and interpretation are pinned | PASS | Bourns MF-RG datasheet SHA-256 7c6cc82e2566fe7ba904d3783122320fa87f043bf7a720467cdfb637c7e803ef |
| Board model preserves raw-to-fused power topology | PASS | F1.1=VCC_RAW and F1.2=VCC |
| Committed PCB embeds the guarded Bourns footprint and pad contract | PASS | Fuse_Bourns_MF-RG300; pads 1/2 are VCC_RAW/VCC with 1.01 mm drills |
| Nominal lead span and drill match the kinked radial part | PASS | 5.100 mm span matches C; 1.200 mm undimensioned stagger; 1.01 mm drill for 0.81 mm lead |
| Fabrication outline carries the maximum body width and depth | PASS | F.Fab is 7.1 x 3.0 mm, matching data-sheet A max and E max |
| Engineering BOM and assembly checklist name the exact orderable part | PASS | F1 = Bourns MF-RG300-0-14 / C3761779 in both ordering artifacts |
| Electrical and thermal planning facts are explicit | PASS | 16 V; 3.0 A hold and 5.1 A trip at 23 C; 2.6 A at 40 C; 2.1 A at 60 C |
| Room-temperature hold current exceeds the planning load | PASS | 3.0 A / 1.81 A = 1.66x at 23 C |

## Static disposition

- Eligible exact part: **Bourns MF-RG300-0-14**, distributor assembly ID
  **C3761779**.
- Exact role: radial resettable PTC between `VCC_RAW` and `VCC` for
  gross short and wiring-fault protection.
- The committed horizontal span is the drawing's nominal 5.1 mm
  and the total hole separation is 5.239 mm; the 1.01 mm
  drill accepts the 0.81 mm nominal lead. The stock 1.2 mm
  undimensioned stagger remains a first-article fit check.
- At 23 C, 3.0 A hold is 1.66x the
  1.81 A planning load. Thermal derating remains
  explicit rather than being hidden by that room-temperature ratio.

## Remaining gates

- The pad-2 stagger is a stock KiCad fit accommodation, not a manufacturer-dimensioned coordinate. Verify insertion, body seating, and solder fillets on the first assembled article.
- The 3.0 A rating is specified at 23 C. Confirm actual enclosure/board ambient and load margin; the data-sheet hold current falls to 2.6 A at 40 C and 2.1 A at 60 C.
- Recheck C3761779 live stock, assembly availability, and the current manufacturer datasheet immediately before ordering.
- Review source capability, J1/J3 and trace current/temperature rise, and nearby-part clearance. F1 is gross-fault protection, not a precise current limiter.
- This closes the exact F1 variant contract only. The Rev-A TVS and socketed-part pin-1 reviews remain separate.

## Primary evidence

- Official Bourns product page:
  `https://www.bourns.com/products/circuit-protection/resettable-fuses-multifuse-pptc-aec-q200-compliant/product/MF-RG`.
- Preserved Bourns series datasheet:
  `ref/datasheets/bourns-mf-rg.pdf`.
- Datasheet SHA-256: `7c6cc82e2566fe7ba904d3783122320fa87f043bf7a720467cdfb637c7e803ef`.
