# Rev A TVS candidate readiness

Status date: **2026-07-23**.

Status: **EXACT D1 CANDIDATE GUARDED / SURGE AND FIRST-ARTICLE CHECK OPEN**.

This report guards Littelfuse P4KE6.8A-B as the exact Rev-A D1
candidate. It checks the preserved manufacturer datasheet, fused-rail
polarity, corrected DO-41 geometry, local routed clearance, and ordering
identifiers. It is not a surge qualification, live-stock claim, or
fabrication authorization.

## Command

```sh
python3 spinoffs/minimal-vga/kicad/report_rev_a_tvs_candidate.py
```

## Guarded checks

| Check | Result | Evidence |
| --- | --- | --- |
| Manufacturer datasheet and interpretation are pinned | PASS | Littelfuse P4KE datasheet SHA-256 cab61a39ecf2d397cba37e06ec78765050ddfae63687ae4cf4dc3f83c1b7a845 |
| Board model preserves exact value, polarity, and fused-rail topology | PASS | D1=P4KE6.8A-B; pad 1=cathode/VCC and pad 2=anode/GND |
| Unidirectional TVS is reverse-biased across fused VCC | PASS | cathode on VCC after F1; anode on GND |
| Committed PCB embeds the corrected DO-41 footprint and pad contract | PASS | DO-41/SOD81 P7.62; 2.20 mm pads and 1.10 mm drills; pad centers unchanged |
| PCB generator preserves the exact D1 footprint and value | PASS | regeneration maps D_TVS_THT to DO-41/SOD81 P7.62 and silk P4KE6.8A |
| Fabrication and courtyard envelopes carry the DO-41 maximum body | PASS | F.Fab=5.20 x 2.70 mm; F.CrtYd=10.32 x 3.20 mm |
| Larger DO-41 pads retain routed-copper clearance | PASS | nearest unrelated track is VCC_RAW with 0.230 mm edge clearance |
| Bounded VCC_RAW detour preserves the replaced segment endpoints | PASS | five connected F.Cu segments join (47.7212,43.2554) to (23.9117,19.4458) |
| Engineering BOM and assembly checklist name the exact catalogued part | PASS | D1 = Littelfuse P4KE6.8A-B / C1666224 in both ordering artifacts |

## Static disposition

- Exact catalogued candidate: **Littelfuse P4KE6.8A-B**, distributor ID
  **C1666224**.
- Exact role: unidirectional 400 W pulse TVS from fused `VCC`
  (cathode) to `GND` (anode), after F1.
- The corrected standard DO-41 footprint keeps the original 7.62 mm
  centers, expands the holes for the 0.86 mm maximum leads, and
  represents the full 5.20 x 2.70 mm maximum body.
- A bounded local `VCC_RAW` detour preserves at least the board's
  0.20 mm copper-clearance contract around the larger pad.
- 5.80 V stand-off is above the nominal 5.0 V rail. Breakdown begins
  at 6.45 V minimum; the rated 39 A pulse clamps at 10.5 V maximum.

## Remaining gates

- The 10.5 V maximum clamp is the 39 A pulse point, not a 5 V rail ceiling. Define and review the accepted EFT/ESD/surge environment against every protected device's limits.
- D1 is not sustained wrong-supply or USB-C source-fault protection. Use a current-limited bench supply for bring-up and never infer USB-PD behavior from this shunt.
- Verify the 7.62 mm lead forming, cathode-band orientation, body seating, nearby clearance, and rail waveform on the first assembled article.
- C1666224 was out of stock during this static review. Recheck live stock, exact manufacturer identity, and manual/factory through-hole assembly capability immediately before ordering.
- This closes the exact D1 variant and copper-fit contract only. Socketed-part pin-1 orientation and the existing F1/J3 first-article gates remain separate.

## Primary evidence

- Official Littelfuse product page:
  `https://www.littelfuse.com/products/overvoltage-protection/tvs-diodes/leaded/p4ke/p4ke6-8a`.
- Preserved Littelfuse P4KE series datasheet:
  `ref/datasheets/littelfuse-p4ke.pdf`.
- Datasheet SHA-256: `cab61a39ecf2d397cba37e06ec78765050ddfae63687ae4cf4dc3f83c1b7a845`.
