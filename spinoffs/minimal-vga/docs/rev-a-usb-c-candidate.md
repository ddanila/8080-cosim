# Rev A USB-C candidate readiness

Status date: **2026-07-23**.

Status: **EXACT J3 CANDIDATE GUARDED / ORDER-TIME CHECK OPEN**.

This report guards HRO TYPE-C-31-M-17 as the exact Rev-A J3 candidate.
It checks the preserved manufacturer drawing, board-level power-only
contract, committed KiCad geometry, and ordering identifiers. It is not
a live-stock claim or fabrication authorization.

## Command

```sh
python3 spinoffs/minimal-vga/kicad/report_rev_a_usb_c_candidate.py
```

## Guarded checks

| Check | Result | Evidence |
| --- | --- | --- |
| Manufacturer drawing and interpretation are pinned | PASS | HRO drawing SHA-256 e38df7ca56f6fa10a78f0c84ee40d26c90af25a1c6c3a692508e46bee2ee11d1 |
| Board model uses the exact six-contact power-only contract | PASS | A5/B5=CC1/CC2, A9/B9=VCC_RAW, A12/B12/shell=GND; no data pins |
| Both configuration-channel inputs have independent Rd pulldowns | PASS | R30/R31 are separate 5.1 kΩ CC1/CC2-to-GND USB-C sink pulldowns |
| Committed PCB embeds the exact HRO footprint | PASS | USB_C_Receptacle_HRO_TYPE-C-31-M-17 |
| All six contact pads match the recommended component-side layout | PASS | centres, 0.70/0.80/0.90 x 1.60 mm copper, and CC/VBUS/GND nets match |
| All four shell tabs match the drawing | PASS | 8.64 x 3.80 mm centre rectangle; 1.00 x 1.70 mm copper; 0.50 x 1.20 mm slots |
| Fabrication outline matches the 8.94 x 6.80 mm body | PASS | F.Fab rectangle spans x=-4.47..4.47 mm and y=-3.40..3.40 mm |
| Engineering BOM and assembly checklist name the same exact candidate | PASS | J3 = HRO TYPE-C-31-M-17 / C283540 in both ordering artifacts |

## Static disposition

- Eligible part: **HRO TYPE-C-31-M-17**, distributor assembly ID
  **C283540**.
- Exact role: optional six-contact, power-only USB-C 5 V sink feeding
  `VCC_RAW` before F1, with independent 5.1 kΩ CC1/CC2 Rd pulldowns.
- The drawing's contact centres, copper sizes, shell slots, and
  8.94 x 6.80 mm body agree with the committed footprint.

## Remaining gates

- The connector is eligible only for Rev-A's power-only 5 V sink role; do not infer USB data connectivity from the Type-C shell.
- The connector's 5 A contact rating does not negotiate or guarantee source current. Keep the existing power-budget caveat and use one of J1/J3 at a time.
- Recheck C283540 live stock, the vendor's current land pattern, and assembly orientation immediately before ordering; inspect a first article before any larger build.
- This closes only J3. The Rev-A PTC, TVS, and socketed-part pin-1 review items remain separate.

## Primary evidence

- Official HRO product page:
  `https://en.krhro.com/Product-Details/722.html`.
- Preserved HRO drawing:
  `ref/datasheets/hro-type-c-31-m-17.pdf`.
- Drawing SHA-256: `e38df7ca56f6fa10a78f0c84ee40d26c90af25a1c6c3a692508e46bee2ee11d1`.
