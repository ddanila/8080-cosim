# VJUGA rev B — R5.J3 independent pre-upload review

Status: **PASS / ORDER HOLD** on 2026-08-28. Reviewer: **Codex**.
Review signature: `Codex / 2026-08-28 / package source 6962a9a4`.

This review covers the five independent bare-PCB release archives only. It does
not authorize upload, add an item to a vendor cart, or place an order. The owner
must still perform R5.R1 and explicitly change `ORDER HOLD` before any upload.

## Independently rendered package review

`kicad/revb/review_revb_release.py --self-test` reads the ZIP contents rather
than the export directories and renders them with gerbv 2.10.0-2build1. The
reviewed candidate uses source revision
`6962a9a4ec6bfa67703112bbc828287d94ebc5b8` and JLC profile SHA-256
`71389d73858ecb5950a5eb2066258915e2b87e4176dba02c59e6ebf1302f036a`.

| Design | Separate Gerber/drill renders | Top/bottom composites | Result |
|---|---:|---:|---|
| CPU | 8 | 2 | PASS |
| Memory | 8 | 2 | PASS |
| I/O | 8 | 2 | PASS |
| Backplane | 8 | 2 | PASS |
| Video | 10 | 2 | PASS |
| **Total** | **42** | **10** | **PASS** |

Visual checklist:

- [x] Every copper, mask, silk, outline and Excellon member renders separately.
- [x] Each board has one closed rectangular outline at its intended aspect ratio.
- [x] Top/bottom copper, mask apertures and drill hits share one origin and align.
- [x] Connector rows, IC land patterns, polarised footprints and mounting holes
      appear in the intended locations; no layer is visibly translated or clipped.
- [x] Video In1 is a continuous GND plane and In2 a continuous VCC plane, with
      the expected antipads and without an unintended split/island.
- [x] Top legends are legible and retain the revision/orientation/no-hot-plug
      markings. Video's sparse bottom legend renders correctly.
- [x] CPU, Memory, I/O and Backplane bottom legend files render blank as intended;
      these are the only permitted blank production graphics.
- [x] Mirrored bottom composites have the expected fabrication-view orientation.
- [x] No unresolved visual finding remains.

The independent gate also rejects a wrong footprint count, a changed programmed
artifact hash, and a programmed device moved into the DNP set.

## First-system BOM and programming reconciliation

The machine-readable contract is `kicad/revb/five-board-bom.json`. Its references
are independently compared with the five routed PCB sources and their five
connectivity descriptions.

| Design | PCB footprints | First-system populated | DNP |
|---|---:|---:|---:|
| CPU | 7 | 7 | 0 |
| Memory | 10 | 10 | 0 |
| I/O | 19 | 12 | 7 |
| Backplane | 41 | 41 | 0 |
| Video | 54 | 54 | 0 |
| **Total** | **131** | **124** | **7** |

The seven DNP footprints are I/O `U4`, `U5`, `U6`, `C4`, `C5`, `C6` and
`J_KBD`, reserved for B3. The first system needs **six programmed devices**:
Memory `U1` 27C256, Memory `U3` and I/O `U2` GALs, and Video `U5`/`U6`/`U7`
GALs. All six artifact sizes and SHA-256 values match the contract. Thus the
five reproducible JEDECs are necessary but not sufficient: the physical
27C256 image is the sixth programmed artifact.

## Dated JLCPCB pre-upload quote

Captured at `2026-08-28T07:40:54+03:00` with Google Chrome 151 from the
[official JLCPCB instant quote](https://cart.jlcpcb.com/quote/), without a file
upload, cart mutation or login. Each row is five copies of one independent
single-PCB design: FR-4 TG135, 1.6 mm, green mask, white silk, lead-free HASL,
1 oz outer copper, flying-probe test, regular ±0.2 mm outline tolerance, no
vendor mark, and production-file confirmation **Yes**. The four-layer quote
uses its 0.5 oz inner copper and no controlled impedance.

| Design | Size | Layers | Via covering | Qty | Web fabrication | Standard build |
|---|---:|---:|---|---:|---:|---:|
| CPU | 100×70 mm | 2 | Tented | 5 | $6.34 | 2 days |
| Memory | 100×60 mm | 2 | Tented | 5 | $6.24 | 2 days |
| I/O | 100×100 mm | 2 | Tented | 5 | $6.34 | 2 days |
| Backplane | 100×100 mm | 2 | Tented | 5 | $6.34 | 2 days |
| Video | 100×100 mm | 4 | Plugged | 5 | $13.24 | 3–4 days |
| **Pre-upload fabrication subtotal** |  |  |  | **25 PCBs** | **$38.50** | **3–4 days critical path** |

The form displayed no configuration warning for these selections. It allows
Tented vias for the two-layer rows but disables that button for the standard
four-layer row and selects Plugged; the frozen profile now encodes that split.
Production-file confirmation contributes $1.04 per design and is included above.

The $38.50 subtotal is a dated web estimate, not a payable total. It excludes
combined shipping, tax, coupons and exchange-rate movement. The page showed a
standalone DHL estimate of $28.67 for each separately evaluated row; those
standalone estimates must not be added together or treated as the combined-cart
shipping quote. Actual detected dimensions/layers, DFM warnings, combined
shipping and the payable total remain R5.O1 upload/checkout evidence after owner
release. The official ordering instructions likewise make Gerber upload the
point where dimensions and layers are automatically analysed.

## Exact reviewed archive identity

| Design | ZIP bytes | SHA-256 |
|---|---:|---|
| CPU | 14,884 | `b83ee98722bf3035059c192ac25406cf69e41931704c2f4493dca2f8f981e0a0` |
| Memory | 18,797 | `002ecd84ecfefde6b6ae8fc3b2859b8d4599294e5821dd443b451916e708831e` |
| I/O | 24,678 | `a86c1ac422bdfb5dbd4225fde0fc26016438b93e21161c7f6de1e3c487c1589a` |
| Backplane | 26,147 | `8ed116a001f1c575df0355800d52206de8297ae7a64e4c7661400cd625a4deca` |
| Video | 407,054 | `05180d8fa2084feec9bfdc4fa5aba89350dc681e643ac5a4e3f239ed69d17dc1` |

R5.J3 is therefore complete. The next gate is R5.R1: present this evidence to
the owner and retain `ORDER HOLD` unless the owner explicitly releases these
exact hashes for upload.
